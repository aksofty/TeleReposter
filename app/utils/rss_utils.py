
import io
from itertools import dropwhile
import feedparser
import httpx
from loguru import logger
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
                    logger.error(f"Пропускаем {url}: Слишком большой файл ({file_size / 1024 / 1024:.2f} MB)")
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
                logger.info(f"Ошибка обработки файла {url}: {e}")
                
    return media_list

def get_new_rss_messages(rss_source_id: int, reverse: bool=True):
    rss_source = RssSources.rss[rss_source_id]
    rss_url = str(rss_source.source)
    feed = feedparser.parse(rss_url)

    if feed.bozo:
        logger.error(f"Ошибка обработки RSS {rss_source.source}: {feed.bozo_exception}")
    else:
        logger.info(f"[{rss_source.source} -> {rss_source.target}]:  Ищу новые записи...")

        entries = list(reversed(feed.entries)) if reverse else feed.entries
        last_identifier = rss_source.last_message_id

        if last_identifier:
            entries = list(dropwhile(lambda e: e.link != last_identifier, entries))
            if entries: entries.pop(0)

        for count, entry in enumerate(entries):
            if count >= rss_source.limit:
                break
            yield entry