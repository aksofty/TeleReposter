
import feedparser
from loguru import logger
from telethon import TelegramClient
from db.rss_sources import RssSources

def get_new_rss_messages(rss_source_id: int, reverse: bool=True):
    rss_source = RssSources.rss[rss_source_id]
    rss_url = str(rss_source.url)
    feed = feedparser.parse(rss_url)

    if feed.bozo:
        logger.info(f"Rss parsing error")
    else:
        logger.info(f"[{rss_source.url} -> {rss_source.target}]:  Requesting for new messages...")
        entries = reversed(feed.entries) if reverse else feed.entries

        last_identifier = rss_source.last_identifier
        skip_post = True if last_identifier else False     

        count = 0
        for entry in entries:
            if skip_post:
                if last_identifier == entry.link:
                    skip_post = False
                continue
            if count >= rss_source.limit:
                break

            count   = count + 1
            yield entry

async def post_new_rss_messages(client: TelegramClient, rss_source_id: int, reverse: bool=True):
    new_identifier = None

    for post in get_new_rss_messages(rss_source_id, reverse):
        await send_message_to_tg(client, rss_source_id, post)
        new_identifier = str(post.link)

    if new_identifier:
        await RssSources.update_last_identifier(rss_source_id, new_identifier)
        logger.info(f"New rss messages posted")
    else:
        logger.info("No new rss messages found")
   

async def send_message_to_tg(client: TelegramClient, rss_source_id: int, post: feedparser.FeedParserDict):
    rss_source = RssSources.rss[rss_source_id]
    post_text = f"**{post.title}**\n\n{post.description}"

    tags = []
    if 'tags' in post:
        for tag in post.tags:
            tags.append(f"#{tag.term.strip().replace(['-', ' '],'')}")

    message = make_text_message(rss_source_id, post_text, tags)
    enclosures = []
    if 'enclosures' in post:
        for enclosure in post.enclosures:
            enclosures.append(enclosure.href)

    if enclosures == []:
        await client.send_message(rss_source.target, message)
    elif len(enclosures) == 1:
        await client.send_file(rss_source.target, enclosures[0], caption=message)
    else:
        await client.send_file(rss_source.target, enclosures, caption=message)    

def make_text_message(rss_source_id: int, post_text: str, tags: list=[], max_len: int=1024)->str:
    rss_source = RssSources.rss[rss_source_id]

    header = f"{rss_source.header}" if rss_source.header else ""
    footer = f"\n{rss_source.footer}" if rss_source.footer else ""

    message = f"{header}{post_text}"
    message = f"{message}\n{' '.join(tags)}" if len(tags) > 0 else message
    message = f"{message}\n\n{footer}"

    len_penalty = max_len - len(message)
    if len_penalty < 0:
        message = make_text_message(rss_source_id, post_text[:len_penalty], tags)

    return message


