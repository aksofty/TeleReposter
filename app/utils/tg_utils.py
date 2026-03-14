import qrcode
from telethon import TelegramClient
from db.sources import Sources
from schemas.message_schema import MessageSchema
from schemas.sources_schema import SourceSchema
from loguru import logger

async def get_messages(client: TelegramClient, source: str, min_id: int, limit: int):
    if min_id > 0:
        messages = client.iter_messages(source, min_id=min_id, limit=limit) 
    else:
        messages = client.iter_messages(source, limit=limit)

    if messages:
        async for message in messages:
            if message.id == 1:
                # пропускаем первое сообщение канала (id:1 "канал создан") 
                continue
            if message.grouped_id and not message.text:
                continue

            yield message

async def get_message_group(client: TelegramClient, source: str, first_id: int, group_id: int, limit: int = 10):   
    async for message in client.iter_messages(source, min_id=first_id, limit=limit):
        if message.grouped_id == group_id:
            yield message 


@logger.catch
async def repost_validated_messages(client: TelegramClient, source_id: int):
    have_message = False
    source = Sources.items[source_id]

    logger.info(f"[{source.source} -> {source.target}]:  Requesting for new messages...")
    async for message in get_messages(client, source.source, source.last_message_id, source.limit):
        if message:
            have_message = True
            await Sources.update_last_message_id(source_id, message.id)
            msg = MessageSchema(
                content=message.text,
                forbidden=source.forbidden,
                allowed=source.allowed
            )

            if msg.is_valid_content():
                message_ids = [message.id]

                if message.grouped_id:
                    logger.info(f"{message.id} is from group {message.grouped_id}. Searching all messages from this group...")
                    async for g_message in get_message_group(client, source.source, message.id, message.grouped_id):
                        if g_message:
                            message_ids.append(g_message.id)
                            logger.info(f"The message #{g_message.id} from group #{message.grouped_id} founded")

                await repost_message(client, message_ids, source_id)
                logger.info(f"(The) message(s) {message_ids} posted")
            else:
                logger.info(f"The message #{message.id} did not validate {msg.content}")

    if not have_message:  
        logger.info(f"There are no messages to post")

@logger.catch
async def repost_message(client: TelegramClient, message_ids: list[int], source_id: int):
     await client.forward_messages(
            entity=Sources.items[source_id].target, 
            messages=message_ids,
            from_peer=Sources.items[source_id].source,
            drop_author=Sources.items[source_id].drop_author)   
     await Sources.update_last_message_id(source_id, max(message_ids))

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
    else:   
        pass