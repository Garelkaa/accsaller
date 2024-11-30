import os
import random
import shutil
import zipfile
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram import F
from signature import BotSettings
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
        self.dp.message(FSMAddAcc.amount)(self.set_amount_acc)
        self.dp.message(F.document, FSMAddAcc.document)(self.download_doc_acc)
        self.dp.message(FSMAddBalanceAdm.uid)(self.add_balance_user_id)
        self.dp.message(FSMAddBalanceAdm.balance)(self.add_balance_amount)

    async def adm(self, m: Message, state: FSMContext):
        await state.clear()
        await m.answer("Admin panel", reply_markup=await kb.adminpanel())

    async def set_acc(self, call: CallbackQuery, state: FSMContext):
        await state.clear()
        await call.message.answer("Enter the amount of accounts.")
        await state.set_state(FSMAddAcc.amount)

    async def set_amount_acc(self, m: Message, state: FSMContext):
        amount = m.text

        if not amount.isdigit() or int(amount) <= 0:
            await m.answer("Invalid amount. Please enter a positive number.")
            return

        await state.update_data(amount=amount)
        await m.answer("Upload the document.")
        await state.set_state(FSMAddAcc.document)

    async def download_doc_acc(self, m: Message, state: FSMContext):
        data = await state.get_data()
        price = data.get("amount")

        session_folder = "accounts/session"
        tdata_folder = "accounts/tdata"
        os.makedirs(session_folder, exist_ok=True)
        os.makedirs(tdata_folder, exist_ok=True)

        temp_folder = f"temp_processed/{m.from_user.id}"
        os.makedirs(temp_folder, exist_ok=True)

        documents = []

        # Собираем все документы из сообщения
        if m.document:
            documents.append(m.document)
        elif m.media_group_id:
            media_group = await self.bot.get_media_group_documents(m.media_group_id)
            documents.extend(media_group)

        if not documents:
            await m.answer("Не загружено ни одного файла.")
            return

        for file in documents:
            file_id = file.file_id
            file_name = file.file_name

            file_path = os.path.join("temp_download", file_name)
            os.makedirs("temp_download", exist_ok=True)

            downloaded_file = await self.bot.get_file(file_id)
            await self.bot.download_file(downloaded_file.file_path, destination=file_path)

            # Проверка формата файла
            if file_name.endswith(('.json', '.session')):
                shutil.copy(file_path, temp_folder)
                await m.answer(f"Файл {file_name} успешно обработан.")
            else:
                await m.answer(f"Неверный формат файла: {file_name}. Допустимы только .json и .session.")
            
            os.remove(file_path)

        if not os.listdir(temp_folder):
            await m.answer("Не найдено допустимых файлов.")
            shutil.rmtree(temp_folder)
            return

        folder_choice = random.choice([session_folder, tdata_folder])
        new_archive_path = os.path.join(folder_choice, f"{m.from_user.id}.zip")

        # Создание архива с обработанными файлами
        with zipfile.ZipFile(new_archive_path, 'w') as new_archive:
            for root, _, files in os.walk(temp_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_folder)
                    new_archive.write(file_path, arcname)

        shutil.rmtree(temp_folder)

        await self.adb.add_acc(account_name=os.path.basename(new_archive_path), price=int(price))
        await m.answer("Все файлы успешно обработаны и сохранены.")
        await state.clear()

    async def add_balance_start(self, call: CallbackQuery, state: FSMContext):
        await call.message.answer("Enter user ID.")
        await state.clear()
        await state.set_state(FSMAddBalanceAdm.uid)

    async def add_balance_user_id(self, m: Message, state: FSMContext):
        user_id = m.text
        if not user_id.isdigit():
            await m.answer("Invalid user ID. Please enter a number.")
            return

        await state.update_data(user_id=user_id)
        await m.answer("Enter the amount.")
        await state.set_state(FSMAddBalanceAdm.balance)

    async def add_balance_amount(self, m: Message, state: FSMContext):
        amount = m.text
        if not amount.isdigit() or int(amount) <= 0:
            await m.answer("Invalid amount. Please enter a positive number.")
            return

        data = await state.get_data()
        user_id = int(data.get("user_id"))
        amount = int(amount)

        user = await self.db.get_user(user_id)
        if not user:
            await m.answer("User not found.")
            await state.clear()
            return

        await self.db.add_balance(user_id, amount)
        await m.answer("Balance added successfully.")
        await state.clear()
