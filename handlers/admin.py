import os
import random
import shutil
import zipfile
from collections import defaultdict
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram import F
from signature import BotSettings
from utils.user_state import FSMAddAcc
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
        self.dp.message(FSMAddAcc.country_code)(self.process_country_code)
        self.dp.message(FSMAddAcc.update_price)(self.update_price)
        self.dp.message(FSMAddAcc.new_price)(self.set_new_price)
        self.dp.message(FSMAddAcc.document)(self.download_doc_acc)

    async def adm(self, m: Message, state: FSMContext):
        await state.clear()
        await m.answer("Admin Panel", reply_markup=await kb.adminpanel())

    async def set_acc(self, call: CallbackQuery, state: FSMContext):
        await state.clear()
        await call.message.answer("Enter the country code for the accounts.")
        await state.set_state(FSMAddAcc.country_code)

    async def process_country_code(self, m: Message, state: FSMContext):
        country_code = m.text.strip()
        existing_code = await self.adb.get_country_code(country_code)

        if existing_code:
            await state.update_data(country_code_id=existing_code.id)
            await m.answer(
                f"The country code '{country_code}' already exists with a price of {existing_code.price}.\n"
                "Do you want to change the price? (yes/no)"
            )
            await state.set_state(FSMAddAcc.update_price)
        else:
            await m.answer(f"The country code '{country_code}' is new. Enter the price for this code.")
            await state.update_data(country_code=country_code)
            await state.set_state(FSMAddAcc.new_price)

    async def update_price(self, m: Message, state: FSMContext):
        if m.text.strip().lower() == "yes":
            await m.answer("Enter the new price:")
            await state.set_state(FSMAddAcc.new_price)
        else:
            await self.proceed_with_country_code(m, state)

    async def set_new_price(self, m: Message, state: FSMContext):
        try:
            price = float(m.text.strip())
            if price <= 0:
                raise ValueError
        except ValueError:
            await m.answer("Price must be a positive number. Try again.")
            return

        data = await state.get_data()
        country_code = data.get("country_code")
        if country_code:
            country_code_id = await self.adb.add_country_code(country_code, price)
            await state.update_data(country_code_id=country_code_id)
        else:
            country_code_id = data.get("country_code_id")
            await self.adb.update_country_code_price(country_code_id, price)

        await self.proceed_with_country_code(m, state)

    async def proceed_with_country_code(self, m: Message, state: FSMContext):
        await m.answer("Upload the account files.")
        await state.set_state(FSMAddAcc.document)

    async def download_doc_acc(self, m: Message, state: FSMContext):
        temp_folder = f"temp_processed/{m.from_user.id}"
        os.makedirs(temp_folder, exist_ok=True)

        documents = []
        if m.document:
            documents.append(m.document)
        elif m.media_group_id:
            media_group = await self.bot.get_media_group_documents(m.media_group_id)
            documents.extend(media_group)

        if not documents:
            await m.answer("No files uploaded.")
            return

        account_files = defaultdict(list)

        for file in documents:
            file_id = file.file_id
            file_name = file.file_name
            file_path = os.path.join("temp_download", file_name)
            os.makedirs("temp_download", exist_ok=True)

            downloaded_file = await self.bot.get_file(file_id)
            await self.bot.download_file(downloaded_file.file_path, destination=file_path)

            if file_name.endswith('.zip'):
                with zipfile.ZipFile(file_path, 'r') as z:
                    z.extractall(temp_folder)
                # Сохраняем исходный архив в список для включения в итоговый архив
                shutil.copy(file_path, temp_folder)
                os.remove(file_path)
            else:
                shutil.copy(file_path, temp_folder)
                os.remove(file_path)

        for root, _, files in os.walk(temp_folder):
            for file in files:
                if file.endswith(('.json', '.session', '.zip')):
                    account_id = file.split('.')[0]
                    account_files[account_id].append(os.path.join(root, file))

        if not account_files:
            await m.answer("No valid files found.")
            shutil.rmtree(temp_folder)
            return

        data = await state.get_data()
        country_code_id = data["country_code_id"]

        session_folder = "accounts/session"
        tdata_folder = "accounts/tdata"
        os.makedirs(session_folder, exist_ok=True)
        os.makedirs(tdata_folder, exist_ok=True)

        success_accounts = []

        for account_id, files in account_files.items():
            account_folder = os.path.join("temp_processed", account_id)
            os.makedirs(account_folder, exist_ok=True)

            for file_path in files:
                shutil.copy(file_path, account_folder)

            folder_choice = random.choice([session_folder, tdata_folder])
            archive_path = os.path.join(folder_choice, f"{account_id}.zip")

            with zipfile.ZipFile(archive_path, 'w') as new_archive:
                for root, _, files in os.walk(account_folder):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, account_folder)
                        new_archive.write(file_path, arcname)

            shutil.rmtree(account_folder)
            await self.adb.add_acc(account_name=os.path.basename(archive_path), country_code_id=country_code_id)
            success_accounts.append(account_id)

        success_message = "\n".join([f"Account {acc_id} processed successfully." for acc_id in success_accounts])
        await m.answer(f"Processing complete:\n{success_message}\n\nAll files processed successfully.")
        await state.clear()

