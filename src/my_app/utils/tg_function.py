import qrcode
from telethon import TelegramClient
from db.sources import Sources
from schemas.message_schema import MessageSchema
from schemas.sources_schema import SourceSchema

async def get_last_messages(client: TelegramClient, source_id: int):
    source = Sources.items[source_id]
    async for message in client.iter_messages(
        source.source, min_id=source.last_message_id, limit=source.limit):
        return message
    return None

async def repost_new_messages(client: TelegramClient, source_id: int):
    message = await get_last_messages(client, source_id)
    source = Sources.items[source_id]
    if message is not None:
        try:
            await Sources.update_last_message_id(source_id, message.id)
            MessageSchema(
                content=message.text,
                forbidden=source.forbidden,
                allowed=source.allowed)
            await repost_message(client, message.id, source_id)
            print(f"Notice: [{source.source} -> {source.target}]: The message {message.id} posted")
        except ValueError as e:
            print(f"Notice: [{source.source} -> {source.target}]: The message {message.id} did not validate")
    else:
        print(f"Notice: [{source.source} -> {source.target}]: no more messages")

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