from telethon import TelegramClient
from cruds.source_tg import update_tg_source_last_message_id
from cruds.source import get_source
from models.source import Source
from utils.common_utils import is_valid_content
from utils.gen_api_utils import gen_api_send
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



async def get_all_messages_from_group(client: TelegramClient, tg_source: Source, first_id: int, group_id: int, limit: int = 10):  
    """Ищет все сообщения, принадлежащие одной группе (альбому).""" 
    async for message in client.iter_messages(tg_source.source, min_id=first_id, limit=limit):
        if message.grouped_id == group_id:
            yield message 


async def post_validated_messages(
    client: TelegramClient, session: AsyncSession, 
    source_id: int, gen_api_token: str="", gen_api_model: str=""):
    """Репостит сообщения, которые прошли валидацию"""

    tg_source = await get_source(session, source_id)
    if tg_source:
        source = tg_source.source 
        target = tg_source.target
        logger.info(f"[{source} -> {target}]: Ищу новые сообщения...")

        found_any = False
        posted_count = 0
        
        async for message in get_messages(client, tg_source, 30):
            if posted_count >= tg_source.limit:
                logger.info(f"[{source} -> {target}]: Максимальное количество сообщений {tg_source.limit} опубликовано")
                return
            
            # обновляем метку последнего сообщения в канале
            await update_tg_source_last_message_id(session, tg_source, message.id)
            found_any = True

            allowed_str = tg_source.allowed_filter.keywords\
                if tg_source.allowed_filter else None
            forbidden_str = tg_source.forbidden_filter.keywords \
                if tg_source.forbidden_filter else None

            if is_valid_content(
                message.text, allowed_str, forbidden_str):

                # добавляем id сообщения в список пересылаемых
                message_ids = [message.id]
                message_media = []
                if message.media:
                    message_media.append(message.media)

                # если сообщение является частью альбома - ищем все сообщения альбома и добавляем их к списку message_ids
                if message.grouped_id:
                    logger.info(f"Сообщение №{message.id} - часть группы {message.grouped_id}. Собираю список...")
                    async for g_message in get_all_messages_from_group(client, source, message.id, message.grouped_id):
                        if g_message:
                            await update_tg_source_last_message_id(session, tg_source, g_message.id)
                            message_ids.append(g_message.id)
                            if g_message.media:
                                message_media.append(g_message.media)
                            
                    logger.info(f"Найдено {len(message_ids)} сообщений в группе №{message.grouped_id}")
                
                # Делаем простой репост (даже если указан промптпше)
                if tg_source.repost:
                    posted_count +=1
                    await forward_message(client, message_ids, tg_source)
                    continue
                
                # Отправляем новое сообщение
                text_to_send = message.text

                # Обрабатываем с помощью ИИ
                if tg_source.ai_prompt:
                    # очищаем медиа для поста отредактированного ИИ
                    message_media.clear()
                    
                    text_to_send = await gen_api_send(
                        message.text, tg_source.ai_prompt.prompt, gen_api_token, gen_api_model)
                    
                    if text_to_send in (None, "Fail"):
                        logger.error(f"Сообщение №{message_ids} НЕ ПРОШЛО валидацию ИИ")
                        posted_count +=1
                        continue
                    
                    logger.info(f"Сообщение №{message_ids} обработано ИИ")
                
                if message_media == []:
                    await client.send_message(target, text_to_send, link_preview=False)
                else:
                    await client.send_file(target, message_media, caption=text_to_send)

                posted_count +=1
                logger.info(f"Сообщение №{message_ids} отправлено в {target}")
    
            else:
                logger.error(f"Сообщение №{message.id} не прошло валидацию по фильтру")

        if not found_any:  
            logger.info("Новых сообщений нет")
    else:
        logger.error(f"Источник не наден")


async def forward_message(client: TelegramClient, message_ids: list[int], tg_source: Source):  
     print(f"drop_author {tg_source.drop_author}")
     print(f"repost {tg_source.repost}")
     await client.forward_messages(
            entity=tg_source.target, 
            messages=message_ids,
            from_peer=tg_source.source,
            drop_author=tg_source.drop_author
            )   
     logger.info(f"Сообщение №{message_ids} переслано")