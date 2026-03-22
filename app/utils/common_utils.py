import io
import httpx
from loguru import logger

def is_valid_content(
        text: str, allowed_str: str|None, forbidden_str: str|None) -> bool: 
    if not text:
        return False
    
    text_lower = text.lower()

    def prepare_list(s: str|None) -> list[str]:
        if not s:
            return []
        return [w.strip().lower() for w in s.split(',') if w.strip()]

    forbidden = prepare_list(forbidden_str)
    if forbidden:
        if any(word in text_lower for word in forbidden):
            return False
        
    allowed = prepare_list(allowed_str)
    if allowed:
        return any(word in text_lower for word in allowed)

    return True


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