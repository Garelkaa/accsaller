from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode


from database.models import CreateDatabase
from database.requests import UserReq, AccountReq

from config import settings

class BotSettings:
    def __init__(self):
        self.bot = Bot(token=settings.TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        self.dp = Dispatcher()
        self.db_manager = CreateDatabase(database_url=settings.get_db_url(), echo=False)
        self.db = UserReq(db_session_maker=self.db_manager.get_session)
        self.adb = AccountReq(db_session_maker=self.db_manager.get_session)
        