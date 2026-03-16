
import io
from itertools import dropwhile
import re
import feedparser
import httpx
from loguru import logger
from telethon import TelegramClient
from utils.gen_api_utils import gen_api_send
from db.rss_sources import RssSources

async def prepare_media_from_urls(urls, max_size_mb=5):
    # 5mb x 10 (максимальное количество прикрепленных файлов) = 50 mb памяти
    # Переводим МБ в байты
    MAX_SIZE = max_size_mb * 1024 * 1024
    media_list = []
    
    async with httpx.AsyncClient() as client:
        for url in urls:
            try:
                # 1. Сначала проверяем только заголовок (без скачивания контента)
                head = await client.head(url, follow_redirects=True)
                file_size = int(head.headers.get("Content-Length", 0))

                if file_size > MAX_SIZE:
                    print(f"Пропуск {url}: файл слишком большой ({file_size / 1024 / 1024:.2f} MB)")
                    continue

                # 2. Если размер ок, скачиваем полностью
                response = await client.get(url, timeout=10.0)
                if response.status_code == 200:
                    file = io.BytesIO(response.content)
                    
                    # Формируем чистое имя файла (без параметров после ?)
                    clean_name = url.split('/')[-1].split('?')[0] or "image.jpg"
                    file.name = clean_name
                    
                    media_list.append(file)
            except Exception as e:
                print(f"Ошибка при обработке {url}: {e}")
                
    return media_list

def get_new_rss_messages(rss_source_id: int, reverse: bool=True):
    rss_source = RssSources.rss[rss_source_id]
    rss_url = str(rss_source.url)
    feed = feedparser.parse(rss_url)

    if feed.bozo:
        logger.error(f"RSS parsing error for {rss_source.url}: {feed.bozo_exception}")
    else:
        logger.info(f"[{rss_source.url} -> {rss_source.target}]:  cheking for updates...")

        entries = list(reversed(feed.entries)) if reverse else feed.entries
        last_identifier = rss_source.last_identifier

        if last_identifier:
            entries = list(dropwhile(lambda e: e.link != last_identifier, entries))
            if entries: entries.pop(0)

        for count, entry in enumerate(entries):
            if count >= rss_source.limit:
                break
            yield entry

async def post_new_rss_messages(
        client: TelegramClient, 
        rss_source_id: int, 
        gen_api_token: str="", 
        gen_api_model: str="", 
        reverse: bool=True
    ):

    new_identifier = None
    rss_source = RssSources.rss[rss_source_id]

    new_posts = get_new_rss_messages(rss_source_id, reverse)
    if not new_posts:
        logger.info(f"Source {rss_source_id}: No new messages")
        return

    for post in new_posts:
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

        await send_message_to_tg(client, rss_source_id, post, response_content)
        new_identifier = str(post.link)

    if new_identifier:
        await RssSources.update_last_identifier(rss_source_id, new_identifier)
        logger.info(f"Source {rss_source_id}: New messages posted")
    
   

async def send_message_to_tg(client: TelegramClient, rss_source_id: int, post: feedparser.FeedParserDict, ai_text: str|None=None):
    rss_source = RssSources.rss[rss_source_id]

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

def make_text_message(rss_source, title: str, body: str, tags: list, max_len: int = 1024) -> str:
    header = f"{rss_source.header}" if rss_source.header else ""
    footer = f"\n\n{rss_source.footer}" if rss_source.footer else ""
    tags_str = f"\n{' '.join(tags)}" if tags else ""
    
    # Считаем доступное место для основного текста
    service_info_len = len(header) + len(footer) + len(tags_str) + 10 # 10 запас
    max_body_len = max_len - service_info_len - len(title)
    
    clean_body = body[:max_body_len] + "..." if len(body) > max_body_len else body
    
    return f"{header}**{title}**\n\n{clean_body}{tags_str}{footer}"


