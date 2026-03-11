import qrcode
from telethon import TelegramClient

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