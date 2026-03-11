import asyncio
from telethon import TelegramClient
from config import Config
from src.my_app.utils.tg_function import tg_auth_qr

async def main():

    client = TelegramClient(
        Config.SESSION_NAME, Config.CLIENT_ID, Config.CLIENT_TOKEN) # type: ignore

    await client.connect() # type: ignore
    await tg_auth_qr(client)

    me = await client.get_me()
    print(f"Logged in as: {me.username} (Phone: {me.phone})") # type: ignore

    await client.run_until_disconnected() # type: ignore
	

if __name__ == '__main__':
    asyncio.run(main())
    # Use the client within a 'with' block to handle starting and stopping
    # the client and running the async main function
    '''with client:
        client.loop.run_until_complete(main())'''