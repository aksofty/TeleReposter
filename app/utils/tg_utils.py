import json
from typing import Set

import qrcode
from telethon import TelegramClient
from utils.gen_api_utils import gen_api_send
from db.sources import Sources
from schemas.message_schema import MessageSchema
from schemas.sources_schema import SourceSchema
from loguru import logger

async def get_messages(client: TelegramClient, source: str, min_id: int, limit: int):
    """Получает поток сообщений из источника, фильтруя технические и пустые сообщения."""
    if min_id > 0:
        messages = client.iter_messages(source, min_id=min_id, limit=limit) 
    else:
        messages = client.iter_messages(source, limit=limit)

    if messages:
        async for message in messages:
            # Пропускаем сервисные сообщения и пустые части альбомов без текста
            if message.id == 1 or (message.grouped_id and not message.text):
                continue
            yield message

async def get_message_group(client: TelegramClient, source: str, first_id: int, group_id: int, limit: int = 10):  
    """Ищет все сообщения, принадлежащие одной группе (альбому).""" 
    async for message in client.iter_messages(source, min_id=first_id, limit=limit):
        if message.grouped_id == group_id:
            yield message 


@logger.catch
async def repost_validated_messages(client: TelegramClient, source_id: int, gen_api_token: str="", gen_api_model: str=""):
    """Репостит сообщения, которые прошли валидацию"""
    source = Sources.items[source_id]
    found_any = False

    logger.info(f"[{source.source} -> {source.target}]:  Requesting for new messages...")
    async for message in get_messages(client, source.source, source.last_message_id, source.limit):
        found_any = True

        # обновляем метку последнего сообщения в канале
        await Sources.update_last_message_id(source_id, message.id)
        msg_validator = MessageSchema(
            content=message.text,
            forbidden=source.forbidden,
            allowed=source.allowed
        )

        if msg_validator.is_valid_content():
            # добавляем id сообщения в список пересылаемых
            message_ids = [message.id]

            # если сообщение является частью альбома - ищем все сообщения альбома и добавляем их к списку message_ids
            if message.grouped_id:
                logger.info(f"Message {message.id} is part of group {message.grouped_id}. Collecting...")
                async for g_message in get_message_group(client, source.source, message.id, message.grouped_id):
                    if g_message:
                        message_ids.append(g_message.id)
                        
                logger.info(f"Found {len(message_ids)} messages in group {message.grouped_id}")

            if not source.ai_prompt:
                await forward_and_update(client, message_ids, source_id)
                return
            
            response_content = await gen_api_send(message.text, source.ai_prompt, gen_api_token, gen_api_model)
            
            if response_content in (None, "Fail"):
                logger.error(f"Message {message_ids} was NOT moderated by AI.")
                return
            
            await client.send_message(source.target, response_content, link_preview=False)
            logger.info(f"Message {message_ids} was moderated by AI and sent to {source.target}")
   
        else:
            logger.info(f"The message #{message.id} did not validate")

    if not found_any:  
        logger.info("No new messages found")

@logger.catch
async def forward_and_update(client: TelegramClient, message_ids: list[int], source_id: int):
     await client.forward_messages(
            entity=Sources.items[source_id].target, 
            messages=message_ids,
            from_peer=Sources.items[source_id].source,
            drop_author=Sources.items[source_id].drop_author)   
     
     new_last_id = max(message_ids)
     
     await Sources.update_last_message_id(source_id, new_last_id)
     logger.info(f"Messages {message_ids} forwarded.")


async def tg_auth_qr(client: TelegramClient):
    """Авторизация через QR-код с обработкой перегенерации."""
    if await client.is_user_authorized():
        return

    while True:
        qr_login = await client.qr_login()

        # Вывод QR прямо в консоль
        qr = qrcode.QRCode()
        qr.add_data(qr_login.url)
        qr.print_ascii()
        
        try:
            await qr_login.wait(timeout=60)
            break
        except Exception:
            logger.warning("QR code expired or login failed. Regenerating...")
            continue