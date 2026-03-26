
from itertools import dropwhile
import json
import re
import feedparser
from loguru import logger
from telethon import TelegramClient
from app.utils.source_utils import is_valid_source_content
from app.utils.common_utils import prepare_media_from_urls
from app.utils.gen_api_utils import gen_api_send
from app.models.source import Source
from app.cruds.source_rss import try_rss_type, update_rss_source_last_post_url
from app.cruds.source import get_source
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.parse_utils import get_clean_body_html

#async def publish_rss_posts_on_telegram(
async def post_handler_rss(
        client: TelegramClient, session: AsyncSession, source_id: int, gen_api_token: str=""):
    
    rss_source = await get_source(session, source_id)

    if rss_source:
        new_last_post_url = None
        any_post = False

        async for post in get_new_rss_posts(rss_source):
            new_last_post_url = str(post.link)
            await update_rss_source_last_post_url(session, rss_source, new_last_post_url) 

            post_text = f"{post.get('title', '')} {post.get('description', '')}"
            if(not is_valid_source_content(rss_source, post_text)):
                continue
            
            response_content = None # переменная для хранения текста статьи преобразованного ИИ
            parsed_image = None # переменная для изменения(добавления) enclosure статьи

            if rss_source.ai_prompt:
                if rss_source.parse_link: # парсим детальную страницу статьи если установлен флаг
                    html_content = await get_clean_body_html(new_last_post_url)

                    if html_content: # отправляем на обработку ИИ html код страницы статьи
                        response_json = await gen_api_send(
                            html_content, 
                            rss_source.ai_prompt.prompt, 
                            gen_api_token,
                            model=str(rss_source.ai_model.value),
                            response_format="json_object"
                        )

                        if response_json: # Если получили ответ от ИИ
                            data = json.loads(response_json)
                            response_content = data['text'] if data['text'] else None
                            parsed_image = data['image'] if data['image'] else None

                else: # если не надо парсить - отправляем ИИ текст статьи из rss фида "title + description"
                    response_content = await gen_api_send(
                        post_text, 
                        rss_source.ai_prompt.prompt, 
                        gen_api_token, 
                        model=str(rss_source.ai_model.value),
                        response_format="text"
                    )
                
                if response_content is None:
                    continue
            
            await publish_validated_rss_post(client, rss_source, post, response_content, parsed_image)
            any_post = True

        if not any_post:          
            logger.info(f"RSS {rss_source.id}: Нет новых сообщений для публикации")


async def publish_validated_rss_post(
        client: TelegramClient, rss_source: Source, post: feedparser.FeedParserDict, ai_text: str|None=None, parsed_image: str|None=None):
    try_rss_type(rss_source)

    tags = get_tags(post)

    caption = make_text_message(
            rss_source, title=post.get('title', ''),  # type: ignore
            body=post.get('description', ''),  # type: ignore
            tags=tags
        ) if ai_text is None else ai_text

    enclosures = [e.href for e in getattr(post, 'enclosures', [])]
    enclosures = [parsed_image] if parsed_image else enclosures 

    try:
        if not enclosures:
            await client.send_message(rss_source.target, caption, link_preview=False, parse_mode='md')
        else:
            #telethon плохо работает со списком ссылок на файлы в интернете, поэтому скачиваем в память 
            prepared_files = await prepare_media_from_urls(enclosures)
            await client.send_file(rss_source.target, prepared_files, caption=caption, parse_mode='md')
    except Exception as e:
        logger.error(f"Ошибка при отправки сообщения: rss {rss_source.id}: {e}")
    
    logger.info(f"Сообщение отправлено: rss {rss_source.id}")


async def get_new_rss_posts(rss_source: Source):
    try_rss_type(rss_source)
    feed = feedparser.parse(rss_source.url)

    if feed.bozo:
        logger.error(f"Ошибка обработки RSS {rss_source.url}: {feed.bozo_exception}")
    else:
        logger.info(f"[{rss_source.url}]:  Ищу новые записи...")

        entries = list(reversed(feed.entries)) if rss_source.reverse else feed.entries
        if rss_source.last_post_url:
            entries = list(dropwhile(lambda e: e.link != rss_source.last_post_url, entries))
            if entries: entries.pop(0)

        for count, entry in enumerate(entries):
            if count >= rss_source.limit:
                break
            yield entry


def make_text_message(
        rss_source, 
        title: str, 
        body: str, 
        tags: list, 
        max_len: int = 1024
    ) -> str:

    template = rss_source.template if rss_source.template else "**{title}**\n\n{body}\n{tags}"

    tags_str = f"{' '.join(tags)}" if tags else ""
    
    # Считаем доступное место для основного текста
    service_info_len = len(template) + len(tags_str)# 10 запас
    max_body_len = max_len - service_info_len - len(title)

    clean_body = body[:max_body_len] + "..." if len(body) > max_body_len else body
    return template \
            .replace("{title}", title) \
            .replace("{body}", clean_body) \
            .replace("{tags}", tags_str)

def get_tags(post):
    tags = []
    for tag in getattr(post, 'tags', []):
        clean_tag = re.sub(r'[-\s]+', '', tag.term)
        tags.append(f"#{clean_tag}")
    return tags