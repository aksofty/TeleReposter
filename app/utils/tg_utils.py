from loguru import logger
import qrcode
from telethon import TelegramClient

async def tg_auth_qr(client: TelegramClient, one_try: bool=False):
    """Авторизация через QR-код с обработкой перегенерации."""
    if await client.is_user_authorized():
        return

    while True:
        qr_login = await client.qr_login()

        # Вывод QR прямо в консоль
        qr = qrcode.QRCode()
        qr.add_data(qr_login.url)
        qr.print_ascii()
        
        try:
            await qr_login.wait(timeout=60)
            break
        except Exception:
            if one_try:
                logger.warning("QR code expired or login failed. Session must be updated!")
                exit(1)        
            logger.warning("QR code expired or login failed. Regenerating...")
            continue
