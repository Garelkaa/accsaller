import os
import random
import shutil
import zipfile
from collections import defaultdict
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
        self.dp.message(FSMAddAcc.document)(self.download_doc_acc)
        self.dp.message(FSMAddAcc.price_option)(self.set_price_option)
        self.dp.message(FSMAddAcc.price)(self.set_prices)
        self.dp.message(FSMAddBalanceAdm.uid)(self.add_balance_user_id)
        self.dp.message(FSMAddBalanceAdm.balance)(self.add_balance_amount)

    async def adm(self, m: Message, state: FSMContext):
        await state.clear()
        await m.answer("Admin Panel", reply_markup=await kb.adminpanel())

    async def set_acc(self, call: CallbackQuery, state: FSMContext):
        await state.clear()
        await call.message.answer("Upload the account files.")
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
                os.remove(file_path)
            else:
                shutil.copy(file_path, temp_folder)
                os.remove(file_path)

        for root, _, files in os.walk(temp_folder):
            for file in files:
                if file.endswith(('.json', '.session')):
                    account_id = file.split('.')[0]
                    account_files[account_id].append(os.path.join(root, file))

        if not account_files:
            await m.answer("No valid files found.")
            shutil.rmtree(temp_folder)
            return

        existing_data = await state.get_data()
        if 'account_files' in existing_data:
            updated_files = {**existing_data['account_files'], **dict(account_files)}
            await state.update_data(account_files=updated_files)
        else:
            await state.update_data(account_files=dict(account_files))

        if not existing_data.get("message_sent"):
            account_files = await state.get_data()
            account_count = len(account_files["account_files"])
            accounts_list = "\n".join([f"- {account_id}" for account_id in account_files["account_files"].keys()])
            await m.answer(
                f"Found {account_count} accounts:\n{accounts_list}\n\nChoose a pricing method:\n"
                "1. Single price for all accounts.\n"
                "2. Prices for each account, separated by commas.\n"
                "3. Enter prices one by one for each account."
            )
            await state.update_data(message_sent=True)
            await state.set_state(FSMAddAcc.price_option)

    async def set_price_option(self, m: Message, state: FSMContext):
        option = m.text.strip()
        if option == "1":
            await m.answer("Enter a single price for all accounts.")
            await state.update_data(price_option="single")
            await state.set_state(FSMAddAcc.price)
        elif option == "2":
            await m.answer("Enter prices for each account, separated by commas.")
            await state.update_data(price_option="bulk")
            await state.set_state(FSMAddAcc.price)
        elif option == "3":
            data = await state.get_data()
            accounts = list(data["account_files"].keys())
            await m.answer(f"Enter the price for account {accounts[0]}")
            await state.update_data(price_option="sequential", current_account_index=0, prices={})
            await state.set_state(FSMAddAcc.price)
        else:
            await m.answer("Invalid choice. Try again.")

    async def set_prices(self, m: Message, state: FSMContext):
        data = await state.get_data()
        account_files = data["account_files"]
        price_option = data["price_option"]

        def parse_price(value):
            try:
                price = float(value.strip())
                if price <= 0:
                    raise ValueError
                return price
            except ValueError:
                return None

        if price_option == "single":
            price = parse_price(m.text)
            if price is None:
                await m.answer("Price must be a positive number (integer or float). Try again.")
                return

            prices = {account_id: price for account_id in account_files.keys()}
            await self.process_accounts(m, state, account_files, prices)

        elif price_option == "bulk":
            try:
                prices_input = [parse_price(price) for price in m.text.split(",")]
                if None in prices_input:
                    raise ValueError
                if len(prices_input) != len(account_files):
                    await m.answer(
                        f"The number of prices ({len(prices_input)}) doesn't match the number of accounts ({len(account_files)}). Try again."
                    )
                    return
                prices = dict(zip(account_files.keys(), prices_input))
                await self.process_accounts(m, state, account_files, prices)
            except ValueError:
                await m.answer("Prices must be positive numbers (integer or float) separated by commas. Try again.")
                return

        elif price_option == "sequential":
            prices = data["prices"]
            current_index = data["current_account_index"]
            accounts = list(account_files.keys())

            price = parse_price(m.text)
            if price is None:
                await m.answer("Price must be a positive number (integer or float). Try again.")
                return

            prices[accounts[current_index]] = price
            current_index += 1

            if current_index < len(accounts):
                await m.answer(f"Enter the price for account {accounts[current_index]}")
                await state.update_data(prices=prices, current_account_index=current_index)
            else:
                await self.process_accounts(m, state, account_files, prices)

    async def process_accounts(self, m: Message, state: FSMContext, account_files: dict, prices: dict):
        session_folder = "accounts/session"
        tdata_folder = "accounts/tdata"
        os.makedirs(session_folder, exist_ok=True)
        os.makedirs(tdata_folder, exist_ok=True)

        success_accounts = []

        for account_id, files in account_files.items():
            price = prices[account_id]
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
            await self.adb.add_acc(account_name=os.path.basename(archive_path), price=price)
            success_accounts.append(account_id)

        success_message = "\n".join([f"Account {acc_id} processed successfully." for acc_id in success_accounts])
        await m.answer(f"Processing complete:\n{success_message}\n\nAll files processed successfully.")
        await state.clear()

    async def add_balance_start(self, call: CallbackQuery, state: FSMContext):
        await call.message.answer("Enter the user ID.")
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
