from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from utils.language import languages

class ReplyKb:
    @staticmethod
    async def main_menu(language_code: str = 'en'):
        translation = languages.get(language_code, languages["en"])

        buttons = [
            translation["buy_account"],
            translation["top_up_balance"],
            translation["change_language"],
            translation["profile"],
            translation["support"],
        ]

        builder = ReplyKeyboardBuilder()
        
        for button in buttons:
            builder.add(KeyboardButton(text=button))

        builder.adjust(2, 2, 1)
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    async def change_language(language_code: str = 'en'):
        translation = languages.get(language_code, languages["en"])
        buttons = [
            ("🇺🇸", "set_lang:en"),
            ("🇷🇺", "set_lang:ru"),
            ("🇨🇳", "set_lang:ch"),
            (translation["cancel"], "cancel"),
        ]

        builder = InlineKeyboardBuilder()
        
        for text, callback_data in buttons:
            builder.button(text=text, callback_data=callback_data)

        return builder.adjust(1).as_markup()

    @staticmethod
    async def adminpanel():
        buttons = [
            ("Add account", "add_doc"),
            ("Add Balance", "change_balance"),
            ("Cancel", "cancel"),
        ]

        builder = InlineKeyboardBuilder()
        
        for text, callback_data in buttons:
            builder.button(text=text, callback_data=callback_data)

        return builder.adjust(1).as_markup()

    @staticmethod
    async def confirmmorend(total_price: int, language_code: str = 'en'):
        translation = languages.get(language_code, languages["en"])

        buttons = [
            (translation["confirm_purchase"], f"confirm_purchase:{total_price}"),
            (translation["cancel"], "cancel_purchase"),
        ]

        menu = InlineKeyboardBuilder()
        for text, callback_data in buttons:
            menu.button(text=text, callback_data=callback_data)

        return menu.adjust(1).as_markup()
    
    @staticmethod
    async def confirmpaymentbsc(bsc: int, new_balance: float, language_code: str = 'en'):
        translation = languages.get(language_code, languages["en"])

        buttons = [
            (translation["check_pay"], f"check_pay_bsc:{bsc}%{new_balance}"),
        ]

        menu = InlineKeyboardBuilder()
        for text, callback_data in buttons:
            menu.button(text=text, callback_data=callback_data)

        return menu.adjust(1).as_markup()
    
    @staticmethod
    async def confirmpaymentusdt(usdt: int, new_balance: float, language_code: str = 'en'):
        translation = languages.get(language_code, languages["en"])

        buttons = [
            (translation["check_pay"], f"check_pay_usdt:{usdt}%{new_balance}"),
        ]

        menu = InlineKeyboardBuilder()
        for text, callback_data in buttons:
            menu.button(text=text, callback_data=callback_data)

        return menu.adjust(1).as_markup()
    
    @staticmethod
    async def confirmpaymentron(trx: int, new_balance: float, language_code: str = 'en'):
        translation = languages.get(language_code, languages["en"])

        buttons = [
            (translation["check_pay"], f"check_pay_tron:{trx}%{new_balance}"),
        ]

        menu = InlineKeyboardBuilder()
        for text, callback_data in buttons:
            menu.button(text=text, callback_data=callback_data)

        return menu.adjust(1).as_markup()
    
    @staticmethod
    async def buyacctype():
        buttons = [
            ("TDATA", "buy_tdata"),
            ("Session + JSON", "buy_session_json"),
        ]

        menu = InlineKeyboardBuilder()
        
        for text, callback_data in buttons:
            menu.button(text=text, callback_data=callback_data)

        return menu.adjust(1).as_markup()
    
    @staticmethod
    async def addacctype():
        buttons = [
            ("TDATA", "add_tdata"),
            ("Session + JSON", "add_session_json"),
        ]

        menu = InlineKeyboardBuilder()
        
        for text, callback_data in buttons:
            menu.button(text=text, callback_data=callback_data)

        return menu.adjust(1).as_markup()
    
    @staticmethod
    async def select_valuta_kb(balance: int):
        buttons = [
            ("🪙 USDT", f"add_balance_usdt:{balance}"),
        ]

        menu = InlineKeyboardBuilder()
        
        for text, callback_data in buttons:
            menu.button(text=text, callback_data=callback_data)

        return menu .adjust(1).as_markup()
    
    @staticmethod
    async def generate_sum_keyboard(language_code: str):
        sums = [5, 10, 20, 50, 100, 300, 500, 1000]
        menu = InlineKeyboardBuilder()

        for amount in sums:
            menu.button(
                text=f"💵 {amount} USDT",
                callback_data=f"select_sum:{amount}"
            )
        
        menu.adjust(2)

        back_button_text = languages.get(language_code, languages["en"])["cancel"]
        menu.button(
            text=f"🔙 {back_button_text}",
            callback_data="cancel"
        )

        return menu.adjust(2, 1).as_markup()
    
    @staticmethod
    async def build_region_keyboard(
        country_codes: dict, available_regions: set, current_page: int = 0, language_code: str = 'en'
    ):
        if not isinstance(country_codes, dict):
            raise ValueError("country_codes должен быть словарем.")

        region_translations = {
            "en": {
                "ru": "Russia",
                "us": "United States",
                "de": "Germany",
                "fr": "France",
                "cancel": "Cancel",
            },
            "ru": {
                "ru": "Россия",
                "us": "США",
                "de": "Германия",
                "fr": "Франция",
                "cancel": "Отмена",
            },
        }

        translations = region_translations.get(language_code, region_translations["en"])

        filtered_regions = {
            code: region for code, region in country_codes.items() if region in available_regions
        }

        regions_list = sorted(filtered_regions.items(), key=lambda x: x[1])
        
        total_pages = len(regions_list)
        current_page = max(0, min(current_page, total_pages - 1))
        
        builder = InlineKeyboardBuilder()

        if regions_list:
            code, region = regions_list[current_page]
            region_name = translations.get(region, region)
            builder.button(text=f"{region_name} ({code})", callback_data=f"select_region:{region}")
        
        if current_page > 0:
            builder.button(text="⬅️ Назад", callback_data=f"region_page:{current_page - 1}")
        if current_page < total_pages - 1:
            builder.button(text="➡️ Вперед", callback_data=f"region_page:{current_page + 1}")
        
        builder.button(text=translations["cancel"], callback_data="cancel")
        
        return builder.adjust(1).as_markup()
    