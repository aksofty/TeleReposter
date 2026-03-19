import re
import feedparser
import qrcode
from telethon import TelegramClient
from schemas.sources_schema import SourceSchema
from utils.common_utils import is_valid_content
from utils.rss_utils import get_new_rss_messages, prepare_media_from_urls
from utils.gen_api_utils import gen_api_send
from db.rss_sources import RssSources
from db.sources import Sources
from schemas.rss_sources_schema import RssSourceSchema
from loguru import logger

async def get_messages(client: TelegramClient, source: str, min_id: int, limit: int):
    """Получает поток сообщений из источника, фильтруя технические и пустые сообщения."""
    if min_id > 0:
        messages = client.iter_messages(source, min_id=min_id, limit=limit, reverse=True) 
    else:
        messages = client.iter_messages(source, limit=limit)

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


@logger.catch
async def repost_validated_messages(
    client: TelegramClient, source_id: int, gen_api_token: str="", gen_api_model: str=""):
    """Репостит сообщения, которые прошли валидацию"""

    source = Sources.items[source_id]
    logger.info(f"[{source.source} -> {source.target}]: Ищу новые сообщения...")

    found_any = False
    posted_count = 0
    
    async for message in get_messages(client, source.source, source.last_message_id, 30):
        if posted_count >= source.limit:
            logger.info(f"[{source.source} -> {source.target}]: Максимальное количество сообщений {source.limit} опубликовано")
            return
        
        # обновляем метку последнего сообщения в канале
        await Sources.update_last_message_id(source_id, message.id)
        found_any = True

        if is_valid_content(
            message.text, source.allowed, source.forbidden):

            # добавляем id сообщения в список пересылаемых
            message_ids = [message.id]
            message_media = []
            if message.media:
                message_media.append(message.media)
            

            # если сообщение является частью альбома - ищем все сообщения альбома и добавляем их к списку message_ids
            if message.grouped_id:
                logger.info(f"Сообщение №{message.id} - часть группы {message.grouped_id}. Собираю список...")
                async for g_message in get_all_messages_from_group(client, source.source, message.id, message.grouped_id):
                    if g_message:
                        await Sources.update_last_message_id(source_id, g_message.id)
                        message_ids.append(g_message.id)
                        if g_message.media:
                            message_media.append(g_message.media)
                        
                logger.info(f"Найдено {len(message_ids)} сообщений в группе №{message.grouped_id}")
            
            # Делаем простой репост (даже если указан промпт)
            if source.repost:
                posted_count +=1
                await forward_message(client, message_ids, source)
                continue
            
            # Отправляем новое сообщение
            text_to_send = message.text

            # Обрабатываем с помощью ИИ
            if source.ai_prompt:
                # очищаем медиа для поста отредактированного ИИ
                message_media.clear()
                
                text_to_send = await gen_api_send(
                    message.text, source.ai_prompt, gen_api_token, gen_api_model)
                
                if text_to_send in (None, "Fail"):
                    logger.error(f"Сообщение №{message_ids} НЕ ПРОШЛО валидацию ИИ")
                    posted_count +=1
                    continue
                
                logger.info(f"Сообщение №{message_ids} обработано ИИ")
            
            if message_media == []:
                await client.send_message(source.target, text_to_send, link_preview=False)
            else:
                await client.send_file(source.target, message_media, caption=text_to_send)

            posted_count +=1
            logger.info(f"Сообщение №{message_ids} отправлено в {source.target}")
   
        else:
            logger.error(f"Сообщение №{message.id} не прошло валидацию по фильтру")

    if not found_any:  
        logger.info("Новых сообщений нет")


@logger.catch
async def forward_message(client: TelegramClient, message_ids: list[int], source: SourceSchema):  
     await client.forward_messages(
            entity=source.target, 
            messages=message_ids,
            from_peer=source.source,
            drop_author=source.drop_author
            )   
     logger.info(f"Сообщение №{message_ids} переслано")

async def send_message_to_tg(
    client: TelegramClient, 
    rss_source: RssSourceSchema, 
    post: feedparser.FeedParserDict, 
    ai_text: str|None=None
    ):

    tags = []
    for tag in getattr(post, 'tags', []):
        clean_tag = re.sub(r'[-\s]+', '', tag.term)
        tags.append(f"#{clean_tag}")

    if ai_text is None:
        caption = make_text_message(
            rss_source, 
            title=post.get('title', ''),  # type: ignore
            body=post.get('description', ''),  # type: ignore
            tags=tags
        )
    else:
        caption = ai_text

    enclosures = [e.href for e in getattr(post, 'enclosures', [])]

    if not enclosures:
        await client.send_message(rss_source.target, caption, parse_mode='md')
    else:
        #telethon плохо работает со списком ссылок на файлы в интернете, поэтому скачиваем в память если файл не один 
        prepared_files = enclosures[0] \
            if len(enclosures) == 1 \
            else await prepare_media_from_urls(enclosures)
        
        await client.send_file(rss_source.target, prepared_files, caption=caption, parse_mode='md')

async def post_new_rss_messages_to_tg(
        client: TelegramClient, 
        rss_source_id: int, 
        gen_api_token: str="", 
        gen_api_model: str="", 
        reverse: bool=True
    ):

    new_identifier = None
    rss_source = RssSources.rss[rss_source_id]

    for post in get_new_rss_messages(rss_source_id, reverse):
        response_content = None

        if rss_source.ai_prompt:
            post_text = f"{post.get('title', '')} {post.get('description', '')}"
            response_content = await gen_api_send(
                post_text, 
                rss_source.ai_prompt, 
                gen_api_token, 
                gen_api_model
            )
            if response_content in (None, "Fail"):
                logger.error(f"Message was NOT moderated by AI.")
                return
            
            logger.info(f"Message was moderated by AI and sent to {rss_source.target}")

        await send_message_to_tg(client, rss_source, post, response_content)
        new_identifier = str(post.link)

    if new_identifier:
        await RssSources.update_last_identifier(rss_source_id, new_identifier)
        logger.info(f"Source {rss_source_id}: New messages posted")
    else:
        logger.info(f"Source {rss_source_id}: No new messages")

def make_text_message(
        rss_source, 
        title: str, 
        body: str, 
        tags: list, 
        max_len: int = 1024
    ) -> str:
    
    header = f"{rss_source.header}" if rss_source.header else ""
    footer = f"\n\n{rss_source.footer}" if rss_source.footer else ""
    tags_str = f"\n{' '.join(tags)}" if tags else ""
    
    # Считаем доступное место для основного текста
    service_info_len = len(header) + len(footer) + len(tags_str) + 10 # 10 запас
    max_body_len = max_len - service_info_len - len(title)
    
    clean_body = body[:max_body_len] + "..." if len(body) > max_body_len else body
    
    return f"{header}**{title}**\n\n{clean_body}{tags_str}{footer}"


async def tg_auth_qr(client: TelegramClient, one_try: bool=False):
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
            if one_try:
                logger.warning("QR code expired or login failed. Session must be updated!")
                exit(1)        
            logger.warning("QR code expired or login failed. Regenerating...")
            continue
