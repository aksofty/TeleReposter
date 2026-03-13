import qrcode
from telethon import TelegramClient
from db.sources import Sources
from schemas.message_schema import MessageSchema
from schemas.sources_schema import SourceSchema
from loguru import logger

@logger.catch
async def repost_new_messages(client: TelegramClient, source_id: int):
    have_message = False
    source = Sources.items[source_id]

    logger.info(f"[{source.source} -> {source.target}]:  Requesting for new messages...")

    if source.last_message_id > 0:
        messages = client.iter_messages(source.source, min_id=source.last_message_id, limit=source.limit)
    else:
        messages = client.iter_messages(source.source, limit=source.limit)
    
    async for message in messages:
        have_message = True
        if message is not None:
            try:
                await Sources.update_last_message_id(source_id, message.id)
                MessageSchema(
                    content=message.text,
                    forbidden=source.forbidden,
                    allowed=source.allowed)
                await repost_message(client, message.id, source_id)
                logger.info(f"The message {message.id} posted")
            except ValueError as e:
                logger.info(f"The message {message.id} did not validate")

    if not have_message:  
        logger.info(f"There are no messages to post")

@logger.catch
async def repost_message(client: TelegramClient, message_id: int, source_id: int):
     await client.forward_messages(
            entity=Sources.items[source_id].target, 
            messages=message_id,
            from_peer=Sources.items[source_id].source)   
     await Sources.update_last_message_id(source_id, message_id)

async def print_auth_qr(qr_login):
    qr = qrcode.QRCode()
    qr.add_data(qr_login.url)
    qr.print_ascii()

@logger.catch
async def tg_auth_qr(client: TelegramClient):
    if not await client.is_user_authorized():
        qr_login = await client.qr_login()
        await print_auth_qr(qr_login)

        while True:
            try:
                await qr_login.wait()
                break
            except Exception:
                qr_login = await client.qr_login()
                await print_auth_qr(qr_login)