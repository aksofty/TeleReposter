from telethon import TelegramClient
from app.cruds.source_tg import update_tg_source_last_message_id
from app.cruds.source import get_source
from app.models.source import Source
from app.utils.source_utils import is_valid_source_content
from app.utils.gen_api_utils import gen_api_send
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

async def get_messages(client: TelegramClient, tg_source: Source, limit: int=10):
    """Получает поток сообщений из источника, фильтруя технические и пустые сообщения."""
    min_id = tg_source.last_message_id if tg_source.last_message_id else 0
    smart_limit = limit if min_id>0 else 1
    source = tg_source.source

    if min_id > 0:
        messages = client.iter_messages(source, min_id=min_id, limit=smart_limit, reverse=True) 
    else:
        messages = client.iter_messages(source, limit=smart_limit)

    if messages:
        async for message in messages:
            # Пропускаем сервисные сообщения и пустые части альбомов без текста
            if message.id == 1 or (message.grouped_id and not message.text):
                continue
            yield message



async def get_all_messages_from_group(client: TelegramClient, source: str, first_id: int, group_id: int, limit: int = 10):  
    """Ищет все сообщения, принадлежащие одной группе (альбому).""" 
    async for message in client.iter_messages(source, min_id=first_id, limit=limit):
        if message.grouped_id == group_id:
            yield message 


#async def post_validated_messages(
async def post_handler_tg(
    client: TelegramClient, session: AsyncSession, source_id: int, gen_api_token: str="", gen_api_model: str=""):
    """Репостит сообщения, которые прошли валидацию"""

    tg_source = await get_source(session, source_id)
    if tg_source:
        logger.info(f"[{tg_source.source} -> {tg_source.target}]: Ищу новые сообщения...")
        found_any = False
        posted_count = 0

        async for message in get_messages(client, tg_source, 30):
            if posted_count >= tg_source.limit:
                logger.info(f"[{tg_source.source} -> {tg_source.target}]: Максимальное количество сообщений {tg_source.limit} опубликовано")
                return
            
            # обновляем метку последнего сообщения в канале в любом случае
            await update_tg_source_last_message_id(session, tg_source, message.id)
            found_any = True

            if is_valid_source_content(tg_source, message.text):
                # добавляем id сообщения в список пересылаемых
                message_ids = [message.id]
                message_media = []
                if message.media:
                    message_media.append(message.media)

                # если сообщение является частью альбома - ищем все сообщения альбома и добавляем их к списку message_ids
                if message.grouped_id:
                    logger.info(f"Сообщение №{message.id} - часть группы {message.grouped_id}. Собираю список...")
                    async for g_message in get_all_messages_from_group(client, tg_source.source, message.id, message.grouped_id):
                        await update_tg_source_last_message_id(session, tg_source, g_message.id)
                        message_ids.append(g_message.id)
                        if g_message.media:
                            message_media.append(g_message.media)
                                
                    logger.info(f"Найдено {len(message_ids)} сообщений в группе №{message.grouped_id}")
                    
                # Делаем простой репост если установлен флаг repost (даже если указан промпт)
                if tg_source.repost:
                    posted_count +=1
                    await forward_message(client, message_ids, tg_source)
                    continue
                    
                text_to_send = message.text
                if tg_source.ai_prompt:
                    message_media.clear() #если используем ИИ, то фото не пересылаем (пока так)
                    text_to_send = await gen_api_send(
                        message.text, 
                        tg_source.ai_prompt.prompt, 
                        gen_api_token, 
                        model=tg_source.ai_model.value, 
                        response_format="text"
                    )
                        
                    if text_to_send is None:
                        continue
                    
                await send_message(client, text_to_send, tg_source.target, message_media)
                posted_count +=1
    
        if not found_any:  
            logger.info("Новых сообщений нет")
    else:
        logger.error(f"Источник не наден")

async def send_message(client: TelegramClient, text: str, target: str, message_media: list=[]):
    if message_media == []:
        await client.send_message(target, text, link_preview=False)
    else:
        await client.send_file(target, message_media, caption=text)
    logger.info(f"Сообщение отправлено в {target}")


async def forward_message(client: TelegramClient, message_ids: list[int], tg_source: Source): 
     await client.forward_messages(
            entity=tg_source.target, 
            messages=message_ids,
            from_peer=tg_source.source,
            drop_author=tg_source.drop_author
            )   
     logger.info(f"Сообщение №{message_ids} переслано")