import httpx
import asyncio
from bs4 import BeautifulSoup, Comment
from loguru import logger

async def get_clean_body_html(url: str) -> str|None:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        try:
            response = await client.get(url, timeout=15.0)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Находим тело страницы
            body = soup.find('article') or soup.find('body')

            if not body:
                logger.error(f"Тег <body> не найден")
                return None

            # Удаляем все скрипты (теги <script>)
            for script in body.find_all(["script", "style", "footer", "header"]):
                script.decompose()

            for div in body.find_all(["div", "ul", "span", "aside", "section", "a", "h3", "h2"]):
                div.unwrap()

            # 2. Обработка списков: заменяем <li> на текст с тире
            for li in body.find_all("li"):
                # Добавляем "-" в начало текста внутри тега
                li.insert_before("- ")
                li.append("\n") # Добавляем перенос строки для красоты
                li.unwrap()
            
            comments = body.find_all(string=lambda text: isinstance(text, Comment))
            for comment in comments:
                comment.decompose()

            # Возвращаем очищенное содержимое (только внутренний HTML или весь тег)
            return body.decode_contents()  # decode_contents() вернет всё ВНУТРИ body
            
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            return None

# Пример вызова:
# html_content = asyncio.run(get_clean_body_html("https://example.com"))
# print(html_content)
