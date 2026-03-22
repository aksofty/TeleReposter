
from itertools import dropwhile
import re
import feedparser
from loguru import logger
from telethon import TelegramClient
from utils.source_utils import is_valid_source_content
from utils.common_utils import prepare_media_from_urls
from utils.gen_api_utils import gen_api_send
from models.source import Source
from cruds.source_rss import try_rss_type, update_rss_source_last_post_url
from cruds.source import get_source
from sqlalchemy.ext.asyncio import AsyncSession

async def publish_rss_posts_on_telegram(
        client: TelegramClient, session: AsyncSession,
        source_id: int, gen_api_token: str="", gen_api_model: str=""):
    
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
            
            response_content = None
            if rss_source.ai_prompt:
                response_content = await gen_api_send(
                    post_text, rss_source.ai_prompt.prompt, gen_api_token, gen_api_model)
                if response_content in (None, "Fail"):
                    logger.error(f"Сообщение не прошло модерацию ИИ")
                    continue

                logger.info(f"Сообщение прошло обработку ИИ")

            await publish_validated_rss_post(client, rss_source, post, response_content)
            any_post = True

        if any_post:          
            logger.info(f"RSS {rss_source.id}: Новые сообщения опубликованы")
        else:
            logger.info(f"RSS {rss_source.id}: Нет новых сообщений для публикации")


async def publish_validated_rss_post(
        client: TelegramClient, rss_source: Source, post: feedparser.FeedParserDict, ai_text: str|None=None):
    try_rss_type(rss_source)

    tags = get_tags(post)

    caption = make_text_message(
            rss_source, title=post.get('title', ''),  # type: ignore
            body=post.get('description', ''),  # type: ignore
            tags=tags
        ) if ai_text is None else ai_text

    enclosures = [e.href for e in getattr(post, 'enclosures', [])]
    if not enclosures:
        await client.send_message(rss_source.target, caption, parse_mode='md')
    else:
        #telethon плохо работает со списком ссылок на файлы в интернете, поэтому скачиваем в память если файл не один 
        prepared_files = enclosures[0] \
            if len(enclosures) == 1 \
            else await prepare_media_from_urls(enclosures)
        
        await client.send_file(rss_source.target, prepared_files, caption=caption, parse_mode='md')


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