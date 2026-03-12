import qrcode
from telethon import TelegramClient
from db.sources import Sources
from schemas.sources_schema import SourceSchema

async def get_last_messages(client: TelegramClient, source: SourceSchema):
    async for message in client.iter_messages(source.source, min_id=source.last_message_id, limit=source.limit):
        print(f"[{source}] ID: {message.id}, Текст: {message.text[:30]}")
        return message.id
    return -1

async def repost_message(client: TelegramClient, message_id: int, source_id: int):
     await client.forward_messages(
            entity=Sources.items[source_id].target, 
            messages=message_id,
            from_peer=Sources.items[source_id].source)   
     await Sources.update_last_message_id(source_id, message_id)
     
async def repost_new_messages(client: TelegramClient, k: int):
    message_id = await get_last_messages(client, Sources.items[k])
    if message_id > 0:
        await repost_message(client, message_id, k)
        print(f"message {message_id} posted")
    else:
        print("no messages")

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