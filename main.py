import asyncio
from handlers.admin import Admin
from handlers.client import Client
from signature import BotSettings
from utils.logger import setup_logger


class BotRunner:
    def __init__(self):
        self.bot_instance = BotSettings()


    async def setup(self):
        await self.bot_instance.db_manager.async_main()
        user_client = Client(bot=self.bot_instance)
        admin_client = Admin(bot=self.bot_instance)
        
        await user_client.register_handlers()
        await admin_client.register_handlers()
        
        await setup_logger(level="DEBUG")

    async def start(self):
        await self.bot_instance.dp.start_polling(self.bot_instance.bot)


    async def run(self):
        await self.setup()
        await self.start()


if __name__ == '__main__':
    bot_runner = BotRunner()
    try:
        asyncio.run(bot_runner.run())
    except KeyboardInterrupt:
        print("Bot stopped!")