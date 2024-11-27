import os
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram import F
from signature import BotSettings
from utils.language import languages
from utils.user_state import FSMAddAcc, FSMAddBalanceAdm
from keyboards.client_kb import ReplyKb as kb

class Admin:
    def __init__(self, bot: BotSettings):
        self.bot = bot.bot
        self.dp = bot.dp
        self.db = bot.db
        self.adb = bot.adb

    async def register_handlers(self):
        self.dp.message(F.text == '/adm')(self.adm)
        self.dp.callback_query(F.data == 'add_doc')(self.set_acc)
        self.dp.callback_query(F.data == 'change_balance')(self.add_balance_start)
        self.dp.callback_query(FSMAddAcc.typeacc)(self.set_type_acc)
        self.dp.message(FSMAddAcc.amount)(self.set_amount_acc)
        self.dp.message(FSMAddAcc.document)(self.download_doc_acc)
        self.dp.message(FSMAddBalanceAdm.uid)(self.add_balance_user_id)
        self.dp.message(FSMAddBalanceAdm.balance)(self.add_balance_amount)
        
    async def adm(self, m: Message, state: FSMContext):
        await state.clear()
        await m.answer("Admin panel", reply_markup=await kb.adminpanel())
        
    async def set_acc(self, call: CallbackQuery, state: FSMContext):
        user_language = await self.db.get_user_language(call.from_user.id) or 'en'
        translation = languages.get(user_language, languages["en"])
        await state.clear()
        
        await call.message.answer(translation["typeacc_adm"], reply_markup=await kb.addacctype())
        await state.set_state(FSMAddAcc.typeacc)
        
    async def set_type_acc(self, call: CallbackQuery, state: FSMContext):
        user_language = await self.db.get_user_language(call.from_user.id) or 'en'
        translation = languages.get(user_language, languages["en"])
        typeacc = call.data

        await state.update_data(typeacc=typeacc)
        
        await call.message.answer(translation["amountacc_adm"])
        await state.set_state(FSMAddAcc.amount)
        
    async def set_amount_acc(self, m: Message, state: FSMContext):
        user_language = await self.db.get_user_language(m.from_user.id) or 'en'
        translation = languages.get(user_language, languages["en"])
        amount = m.text
        
        await state.update_data(amount=amount)
        
        await m.answer(translation["documentacc_adm"], reply_markup=None)
        await state.set_state(FSMAddAcc.document)
        
    async def download_doc_acc(self, m: Message, state: FSMContext):
        user_language = await self.db.get_user_language(m.from_user.id) or 'en'
        translation = languages.get(user_language, languages["en"])
        
        data = await state.get_data()
        typeacc = data.get("typeacc")
        price = data.get("amount")
        print(typeacc)
        
        if typeacc == "add_session_json":
            folder_path = "accounts/session"
        elif typeacc == "add_tdata":
            folder_path = "accounts/tdata"
        else:
            await m.answer(translation["not_found"])
            return
        
        os.makedirs(folder_path, exist_ok=True)
        
        file_id = m.document.file_id
        file = await self.bot.get_file(file_id)
        file_path = os.path.join(folder_path, m.document.file_name)
        
        await self.bot.download_file(file.file_path, destination=file_path)

        await m.answer(translation["filedownload_success"])
        print(m.document.file_name)
        await self.adb.add_acc(account_name=f"{m.document.file_name}", price=int(price))
        
        await state.clear()

    async def add_balance_start(self, call: CallbackQuery, state: FSMContext):
        await call.message.answer("Enter user id")
        await state.clear()
        await state.set_state(FSMAddBalanceAdm.uid)
        
    async def add_balance_user_id(self, m: Message, state: FSMContext):
        user_id = m.text
        if not user_id.isdigit():
            await m.answer("not the right type")
            return

        await state.update_data(user_id=user_id)
        await m.answer("enter the amount")
        await state.set_state(FSMAddBalanceAdm.balance)
        
    async def add_balance_amount(self, m: Message, state: FSMContext):
        amount = m.text
        if not amount.isdigit() or int(amount) <= 0:
            await m.answer("not the right type")
            return

        data = await state.get_data()
        user_id = int(data.get("user_id"))
        print(user_id)
        amount = int(amount)
        
        user = await self.db.get_user(user_id)
        if not user:
            await m.answer("user is not found")
            await state.clear()
            return

        await self.db.add_balance(user_id, amount)
        await m.answer("Balance sheet issued successfully")
        await state.clear()
