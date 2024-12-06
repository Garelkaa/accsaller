import asyncio
from datetime import datetime, timezone
import os
import random
import time
import zipfile
from aiogram.types import Message, FSInputFile, CallbackQuery
from aiogram.filters.command import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram import F
from aiogram.filters import BaseFilter
from signature import BotSettings
from utils.bsc import find_transaction_by_amount
from utils.language import languages
from utils.tron import display_transactions_tron, fetch_transactions_tron, get_tron_amount
from utils.user_state import FSMChangeLanguage, FSMSetRegion, FSMAddBalance
from utils.usdt import main
from keyboards.client_kb import ReplyKb as kb

class ExpectingCallbackFilter(BaseFilter):
    async def __call__(self, message: Message, state: FSMContext) -> bool:
        current_state = await state.get_state()
        return current_state in {FSMAddBalance.balance, FSMChangeLanguage.language}


class Client:
    def __init__(self, bot: BotSettings):
        self.bot = bot.bot
        self.dp = bot.dp
        self.db = bot.db
        self.adb = bot.adb
        self.country_codes = {
            '1': 'us', 
            '7': 'ru', 
            '86': 'cn', 
            '44': 'gb', 
            '49': 'de'
        }

    async def register_handlers(self):
        self.dp.message(CommandStart())(self.main_menu)
        self.dp.message(F.text == '🛒 Купить аккаунт')(self.buy_acc)
        self.dp.message(F.text == '🌐 Сменить язык')(self.change_language_start)
        self.dp.message(F.text == '👤 Профиль')(self.profile)
        self.dp.message(F.text == '👤 Profile')(self.profile)
        self.dp.message(F.text == '👤 个人资料')(self.profile)
        self.dp.callback_query(F.data.startswith("set_lang"))(self.change_language_end)
        self.dp.callback_query(F.data.startswith("select_region"))(self.set_region)
        self.dp.message(F.text == '💵 Пополнить баланс')(self.select_sum)
        self.dp.message(F.text == '💵 Top Up Balance')(self.select_sum)
        self.dp.message(F.text == '💵 充值余额')(self.select_sum)
        self.dp.callback_query(F.data.startswith('add_balance_usdt'))(self.process_add_balance_usdt)
        self.dp.callback_query(F.data.startswith('add_balance_tron'))(self.process_add_balance_tron)
        self.dp.callback_query(F.data.startswith('add_balance_bsc'))(self.process_add_balance_bsc)
        self.dp.callback_query(F.data == 'cancel')(self.cancel)
        self.dp.message(F.text == '🛒 Buy Account')(self.buy_acc)
        self.dp.message(F.text == '🌐 Change Language')(self.change_language_start)
        self.dp.message(F.text == '🛒 购买账户')(self.buy_acc)
        self.dp.message(F.text == '🌐 更改语言')(self.change_language_start)
        self.dp.message(F.text == '☎️ Support')(self.support)
        self.dp.message(F.text == '☎️ Поддержка')(self.support)
        self.dp.message(F.text == '☎️ 支持')(self.support)
        self.dp.callback_query(F.data.startswith("confirm_purchase"))(self.confirm_purchase)
        self.dp.callback_query(F.data.startswith("check_pay_usdt"))(self.check_pay_usdt)
        self.dp.callback_query(F.data.startswith("check_pay_tron"))(self.check_pay_tron)
        self.dp.callback_query(F.data.startswith("check_pay_bsc"))(self.check_pay_bsc)
        self.dp.callback_query(F.data == "cancel_purchase")(self.cancel_purchase)
        self.dp.callback_query(lambda c: c.data and "region_page:" in c.data)(self.paginate_regions)
        self.dp.message(FSMSetRegion.region)(self.set_region)
        self.dp.message(FSMSetRegion.quantity)(self.handle_quantity_input)
        self.dp.callback_query(F.data.startswith('select_sum'))(self.add_balance)
        self.dp.message(ExpectingCallbackFilter())(self.text_during_callback)

    async def main_menu(self, m: Message):
        await self.db.add_user(m.from_user.id, m.from_user.username or m.from_user.first_name)
        user_language = await self.db.get_user_language(m.from_user.id) or 'en'
        translation = languages.get(user_language, languages["ch"])
        await m.answer(translation["main_menu"], reply_markup=await kb.main_menu(language_code=user_language))

    async def profile(self, m: Message, state: FSMContext):
        await state.clear()
        balance = await self.db.get_balance_user(m.from_user.id)
        user_language = await self.db.get_user_language(m.from_user.id) or 'en'
        translation = languages.get(user_language, languages["ch"])

        transactions = await self.db.get_user_transactions(m.from_user.id)
        transaction_details = '\n'.join(
            [f"{t.date}: {t.value} {t.valuta}" for t in transactions]
        ) if transactions else translation['no_transactions']

        profile_info = translation['profile_info'].format(
            balance=balance,
            user_language=user_language,
            transaction=transaction_details
        )

        await m.answer(profile_info)

    async def change_language_start(self, m: Message, state: FSMContext):
        user_language = await self.db.get_user_language(m.from_user.id) or 'en'
        await state.clear()
        translation = languages.get(user_language, languages["ch"])
        await m.answer(translation["change_language"], reply_markup=await kb.change_language(user_language))
        await state.set_state(FSMChangeLanguage.language)

    async def change_language_end(self, call: CallbackQuery, state: FSMContext):
        user_language = await self.db.get_user_language(call.from_user.id) or 'en'
        translation = languages.get(user_language, languages["ch"])
        
        language = call.data.split(":")[1]
        if language in {'en', 'ru', 'ch'}:
            success = await self.db.set_user_language(uid=call.from_user .id, new_language=language)
            user_language = await self.db.get_user_language(call.from_user.id) or 'en'
            translation = languages.get(user_language, languages["ch"])
            if success:
                await call.message.answer(translation["language_changed"], reply_markup=await kb.main_menu(language))
                updated_language = await self.db.get_user_language(call.message.from_user.id)
            else:
                await call.message.answer(translation["language_change_error"])
            await state.clear()
        else:
            await call.message.answer(translation["language_not_available"])

    async def buy_acc(self, m: Message, state: FSMContext):
        user_language = await self.db.get_user_language(m.from_user.id) or 'en'
        translation = languages.get(user_language, languages["en"])
        await state.clear()

        if await self.db.get_balance_user(m.from_user.id) >= 1:
            paths = ['accounts/session', 'accounts/tdata']
            available_regions = set()
            available_stock = {}

            for path in paths:
                if os.path.exists(path):
                    for filename in os.listdir(path):
                        if filename.endswith('.zip'):
                            for code, region in self.country_codes.items():
                                if filename.startswith(code):
                                    available_regions.add(region)
                                    if region not in available_stock:
                                        available_stock[region] = 0
                                    available_stock[region] += 1
            
            if available_regions:
                await m.answer(
                    translation["but_acc_select_country"],
                    reply_markup=await kb.build_region_keyboard(
                        self.country_codes, available_regions, language_code=user_language
                    )
                )
            else:
                await m.answer(translation["no_acc"])
        else:
            await m.answer(translation["but_acc_balance_low"])

    async def select_random_account(self, region, quantity):
        base_path = 'accounts'
        account_types = ['session', 'tdata']
        
        selected_type = random.choice(account_types)
        account_path = os.path.join(base_path, selected_type)

        if not os.path.exists(account_path):
            print(f"Account path does not exist: {account_path}")
            return None, None, 0

        matching_files = [
            f for f in os.listdir(account_path)
            if os.path.isfile(os.path.join(account_path, f)) and
            any(f.startswith(code) for code, reg in self.country_codes.items() if reg == region)
        ]

        if matching_files:
            selected_files = random.sample(matching_files, min(quantity, len(matching_files)))
            return selected_files, selected_type, len(selected_files)
        return None, None, 0

    async def select_random_files(self, region, quantity):
        base_paths = {
            'session': os.path.join('accounts', 'session'),
            'tdata': os.path.join('accounts', 'tdata')
        }

        selected_files = []
        for account_type, base_path in base_paths.items():
            if not os.path.exists(base_path):
                continue

            matching_files = [
                f for f in os.listdir(base_path)
                if os.path.isfile(os.path.join(base_path, f)) and
                any(f.startswith(code) for code, reg in self.country_codes.items() if reg == region)
            ]

            if matching_files:
                files_to_add = min(quantity - len(selected_files), len(matching_files))
                selected_files.extend(
                    (account_type, file) for file in random.sample(matching_files, files_to_add)
                )

            if len(selected_files) >= quantity:
                break

        return selected_files

    async def set_region(self, call: CallbackQuery, state: FSMContext):
        user_language = await self.db.get_user_language(call.from_user.id) or 'en'
        translation = languages.get(user_language, languages["ch"])

        region = call.data.split(":")[1]
        if region in set(self.country_codes.values()):
            await state.update_data(region=region)
            user_data = await state.get_data()
            region = user_data.get("region")

            available_stock = await self.get_available_stock(region)
            
            if available_stock > 0:
                
                await call.message.answer(
                    translation["enter_quantity"].format(stock=available_stock)
                )
                await state.update_data(stock_quantity=available_stock)
                await state.set_state(FSMSetRegion.quantity)
            else:
                print(2222)
                await call.message.answer(translation["account_not_found"])
        else:
            print(3333)
            await call.message.answer(translation["region_not_available"])

    async def get_available_stock(self, region):
        available_stock = 0
        paths = ['accounts/session', 'accounts/tdata']
        for path in paths:
            if os.path.exists(path):
                for filename in os.listdir(path):
                    if filename.endswith('.zip'):
                        for code, country in self.country_codes.items():
                            if country == region and filename.startswith(code):
                                available_stock += 1
        return available_stock

    async def handle_quantity_input(self, message: Message, state: FSMContext):
        user_data = await state.get_data()
        region = user_data.get("region")
        user_language = await self.db.get_user_language(message.from_user.id) or 'en'
        translation = languages.get(user_language, languages["ch"])

        try:
            quantity = int(message.text)
        except ValueError:
            await message.answer(translation["invalid_quantity"])
            return

        if quantity <= 0:
            await message.answer(translation["invalid_quantity"])
            return

        selected_files = await self.select_random_files(region, quantity)
        count = len(selected_files)

        if count < quantity:
            await message.answer(translation["quantity_exceeds_stock"])
            return

        await state.update_data(account_files=selected_files, quantity=quantity)

        total_price = 0
        file_info_list = []
        for file in selected_files:
            file_name = file[1]
            price = await self.adb.get_account_price(file_name)
            total_price += price
            file_info_list.append((
                file_name.split('.')[0],
                region,
                price,
                'session + JSON' if file[0] == 'session' else 'TDATA'
            ))

        confirmation_text = "\n\n".join([
            (
                f"🔢 {translation['account_number']}: {info[0]}\n"
                f"{translation['region']}: {info[1]}\n"
                f"{translation['price']}: {float(info[2])}$\n"
                f"📤 {translation['issue_type']}: {info[3]}"
            )
            for info in file_info_list
        ])
        confirmation_text += f"\n\n{translation['price']}: {total_price}$"

        await message.answer(
            confirmation_text,
            reply_markup=await kb.confirmmorend(total_price, user_language)
        )

    async def confirm_purchase(self, call: CallbackQuery, state: FSMContext):
        user_data = await state.get_data()
        selected_files = user_data.get("account_files")
        quantity = user_data.get("quantity")
        user_language = await self.db.get_user_language(call.from_user.id) or 'en'
        translation = languages.get(user_language, languages["ch"])

        unit_price = await self.adb.get_account_price(selected_files[0][1])
        total_price = call.data.split(":")[1]

        if total_price is not None and await self.db.get_balance_user(call.from_user.id) >= float(total_price):
            region_code = self.get_region_code_from_files([file[1] for file in selected_files])
            timestamp = time.strftime('%Y%m%d%H%M%S')
            zip_filename = f"{region_code}_{quantity}pcs_{timestamp}.zip"
            zip_dir = 'archives'

            os.makedirs(zip_dir, exist_ok=True)
            zip_path = os.path.join(zip_dir, zip_filename)

            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for account_type, account_file in selected_files:
                    full_path = os.path.join('accounts', account_type, account_file)
                    zipf.write(full_path, os.path.basename(account_file))

            account_file = FSInputFile(zip_path)
            await call.message.answer_document(account_file)
            await call.message.answer(translation["purchase_success"])

            await self.db.decrement_balance(call.from_user.id, float(total_price))

            for account_type, account_file in selected_files:
                full_path = os.path.join('accounts', account_type, account_file)
                os.remove(full_path)

                # Удаляем запись из базы данных
                deletion_success = await self.adb.delete_account(account_file)
                if not deletion_success:
                    await call.message.answer(translation["deletion_error"])

            os.remove(zip_path)

            await state.clear()
        else:
            await call.message.answer(translation["insufficient_funds"])
        await call.answer()

    def get_region_code_from_files(self, account_files):
        if account_files:
            filename = os.path.basename(account_files[0])
            for code, country in self.country_codes.items():
                if filename.startswith(code):
                    return code
        return ''

    async def cancel_purchase(self, call: CallbackQuery, state: FSMContext):
        user_language = await self.db.get_user_language(call.from_user.id) or 'en'
        translation = languages.get(user_language, languages["ch"])
        await state.clear()
        await call.message.answer(translation["purchase_canceled"], reply_markup=await kb.main_menu(user_language))
        await call.answer()

    async def cancel(self, m: Message, state: FSMContext):
        user_language = await self.db.get_user .language(m.from_user.id) or 'en'
        translation = languages.get(user_language, languages["ch"])
        await state.clear()
        await m.answer(translation["purchase_canceled"], reply_markup=await kb.main_menu(user_language))

    async def select_sum(self, m: Message, state: FSMContext):
        user_language = await self.db.get_user_language(m.from_user.id) or 'en'
        await state.clear()
        translation = languages.get(user_language, languages["ch"])
        
        await m.answer(translation["select_sum"], reply_markup=await kb.generate_sum_keyboard(language_code=user_language))
        await state.set_state(FSMAddBalance.balance)

    async def add_balance(self, call: CallbackQuery, state: FSMContext):
        user_language = await self.db.get_user_language(call.from_user.id) or 'en'
        translation = languages.get(user_language, languages["ch"])
        balance = float(call.data.split(":")[1])
        await call.message.answer(translation['select_valuta'], reply_markup=await kb.select_valuta_kb(balance=balance))

    async def process_add_balance_usdt(self, call: CallbackQuery, state: FSMContext):
        user_language = await self.db.get_user_language(call.from_user.id) or 'en'
        translation = languages.get(user_language, languages["ch"])
        data = call.data
        try:
            balance = data.split(":")[1]
            new_balance = round(float(balance), 2)

            tolerance = random.uniform(0.0001, 0.1000)
            usdt_with_tolerance = round(new_balance + tolerance, 4)
            
            await call.message.answer(
                translation["pls_send_money_usdt"].format(usdt=usdt_with_tolerance, dollar=new_balance)
            )

            asyncio.create_task(self.check_payment_timer(call.from_user.id, usdt_with_tolerance, new_balance, state))

        except ValueError:
            await call.message.answer(translation["pls_correct_sum_usdt"])
            await state.clear()


    async def check_payment_timer(self, user_id: int, usdt: float, new_balance: float, state: FSMContext):
        user_language = await self.db.get_user_language(user_id) or 'en'
        translation = languages.get(user_language, languages["ch"])

        for _ in range(10):
            success = main(usdt)
            if success:
                await self.db.add_balance(user_id, new_balance)
                balance = await self.db.get_balance_user(user_id)
                await self.db.add_transaction(
                    user_id=user_id,
                    value=new_balance,
                    valuta='USDT',
                    date=datetime.now(timezone.utc),
                )
                await self.bot.send_message(
                    chat_id=user_id,
                    text=translation["balance_updated"].format(balance=balance)
                )
                await state.clear()
                return
            await asyncio.sleep(60)

        await self.bot.send_message(
            chat_id=user_id,
            text=translation["payment_timeout"]
        )
        await state.clear()
        
        
    async def process_add_balance_bsc(self, call: CallbackQuery, state: FSMContext):
        user_language = await self.db.get_user_language(call.from_user.id) or 'en'
        translation = languages.get(user_language, languages["ch"])
        await call.message.answer(translation['error_oplata_vid'])

    async def check_pay_bsc(self, call: CallbackQuery, state: FSMContext):
        user_language = await self.db.get_user_language(call.from_user.id) or 'en'
        translation = languages.get(user_language, languages["ch"])
        data = call.data
        bsc = data.split(":")[1].split("%")[0]
        new_balance = float(data.split(":")[1].split("%")[1])
        
        success = find_transaction_by_amount("6M36JU21ZD1UZFKCHZ3YX28RPU5PB41A25", "0x10985cbF89D5b983C01A4C790A2D548525d3849d", bsc)

        if success:
            balance = await self.db.get_balance_user(call.from_user.id)
            await call.message.answer(
                translation["balance_updated"].format(balance=balance)
            )
            await self.db.add_balance(call.from_user.id, new_balance)
            await state.clear()

    async def process_add_balance_tron(self, call: CallbackQuery, state: FSMContext):
        user_language = await self.db.get_user_language(call.from_user.id) or 'en'
        translation = languages.get(user_language, languages["ch"])
        data = call.data
        try:
            balance = data.split(":")[1]
            new_balance = round(float(balance), 2)

            tron = get_tron_amount(new_balance)
            
            tolerance = random.uniform(0, 0.0001)
            tron_with_tolerance = round(tron + tolerance, 4)

            await call.message.answer (translation["pls_send_money_tron"].format(trx=tron_with_tolerance, dollar=new_balance),
                reply_markup=await kb.confirmpaymentron(trx=tron_with_tolerance, new_balance=new_balance, language_code=user_language)
            )
        except ValueError:
            await call.message.answer(translation["pls_correct_sum_tron"])
            await state.clear()

    async def check_pay_tron(self, call: CallbackQuery, state: FSMContext):
        user_language = await self.db.get_user_language(call.from_user.id) or 'en'
        translation = languages.get(user_language, languages["ch"])
        data = call.data
        trx = data.split(":")[1].split("%")[0]
        new_balance = float(data.split(":")[1].split("%")[1])
        
        transaction = fetch_transactions_tron(wallet_address="TTHhZ9wY6wzikAH2QxodknUX51JMpmcxdL", limit=10, start=0)
        success = display_transactions_tron(transaction, float(trx))

        if success:
            balance = await self.db.get_balance_user(call.from_user.id)
            await call.message.answer(
                translation["balance_updated"].format(balance=balance)
            )
            await self.db.add_balance(call.from_user.id, new_balance)
            await state.clear()

    async def cancel(self, call: CallbackQuery, state: FSMContext):
        user_language = await self.db.get_user_language(call.from_user.id) or 'en'
        translation = languages.get(user_language, languages["ch"])
        await state.clear()
        await call.message.answer(translation["cancel"], reply_markup=await kb.main_menu(user_language))

    async def paginate_regions(self, callback_query: CallbackQuery):
        data = callback_query.data
        if "region_page:" in data:
            current_page = int(data.split(":")[1])
            country_codes = {
                '1': 'us', 
                '7': 'ru', 
                '86': 'cn', 
                '44': 'gb', 
                '49': 'de'
            }

            new_keyboard = await kb.build_region_keyboard(
                country_codes=country_codes,
                current_page=current_page,
                language_code="en"
            )

            await self.bot.edit_message_reply_markup(
                chat_id=callback_query.message.chat.id,
                message_id=callback_query.message.message_id,
                reply_markup=new_keyboard
            )
            await callback_query.answer()
            
    async def support(self, m: Message, state: FSMContext):
        user_language = await self.db.get_user_language(m.from_user.id) or 'en'
        translation = languages.get(user_language, languages["ch"])
        await state.clear()
        await m.answer(
            translation["support_message"]
        )
            
    async def text_during_callback(self, message: Message, state: FSMContext):
        user_language = await self.db.get_user_language(message.from_user.id) or 'en'
        translation = languages.get(user_language, languages["ch"])
        await message.answer(
            translation["callback_expected"]
        )
        