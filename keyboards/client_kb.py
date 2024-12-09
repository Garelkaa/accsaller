from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import KeyboardButton
from utils.language import languages

class ReplyKb:
    @staticmethod
    async def main_menu(language_code: str = 'ch'):
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
    async def change_language(language_code: str = 'ch'):
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
    async def confirmmorend(total_price: int, language_code: str = 'ch'):
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
    async def confirmpaymentbsc(bsc: int, new_balance: float, language_code: str = 'ch'):
        translation = languages.get(language_code, languages["en"])

        buttons = [
            (translation["check_pay"], f"check_pay_bsc:{bsc}%{new_balance}"),
        ]

        menu = InlineKeyboardBuilder()
        for text, callback_data in buttons:
            menu.button(text=text, callback_data=callback_data)

        return menu.adjust(1).as_markup()
    
    @staticmethod
    async def confirmpaymentusdt(usdt: int, new_balance: float, language_code: str = 'ch'):
        translation = languages.get(language_code, languages["en"])

        buttons = [
            (translation["check_pay"], f"check_pay_usdt:{usdt}%{new_balance}"),
        ]

        menu = InlineKeyboardBuilder()
        for text, callback_data in buttons:
            menu.button(text=text, callback_data=callback_data)

        return menu.adjust(1).as_markup()
    
    @staticmethod
    async def confirmpaymentron(trx: int, new_balance: float, language_code: str = 'ch'):
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
        sums = [5, 10, 20, 50, 100, 300, 500, 1000, 2000, 3000, 5000]
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
        country_codes: dict,
        available_regions: set,
        available_stock: dict,
        language_code: str = 'ch',
    ):
        if not isinstance(country_codes, dict):
            raise ValueError("country_codes должен быть словарем.")

        region_translations = {
            "en": {
                "ru": "Russia",
                "us": "United States",
                "de": "Germany",
                "fr": "France",
                "cn": "China",
                "jp": "Japan",
                "in": "India",
                "br": "Brazil",
                "gb": "United Kingdom",
                "it": "Italy",
                "es": "Spain",
                "ca": "Canada",
                "au": "Australia",
                "mx": "Mexico",
                "za": "South Africa",
                "kr": "South Korea",
                "ar": "Argentina",
                "sa": "Saudi Arabia",
                "ng": "Nigeria",
                "eg": "Egypt",
                "tr": "Turkey",
                "pk": "Pakistan",
                "id": "Indonesia",
                "pl": "Poland",
                "nl": "Netherlands",
                "se": "Sweden",
                "ch": "Switzerland",
                "be": "Belgium",
                "gr": "Greece",
                "pt": "Portugal",
                "no": "Norway",
                "dk": "Denmark",
                "fi": "Finland",
                "is": "Iceland",
                "ie": "Ireland",
                "sg": "Singapore",
                "ph": "Philippines",
                "th": "Thailand",
                "vn": "Vietnam",
                "my": "Malaysia",
                "ua": "Ukraine",
                "ro": "Romania",
                "bg": "Bulgaria",
                "cz": "Czech Republic",
                "hu": "Hungary",
                "at": "Austria",
                "cl": "Chile",
                "co": "Colombia",
                "pe": "Peru",
                "ve": "Venezuela",
                "cancel": "Cancel",
            },
            "ru": {
                "ru": "Россия",
                "us": "США",
                "de": "Германия",
                "fr": "Франция",
                "cn": "Китай",
                "jp": "Япония",
                "in": "Индия",
                "br": "Бразилия",
                "gb": "Великобритания",
                "it": "Италия",
                "es": "Испания",
                "ca": "Канада",
                "au": "Австралия",
                "mx": "Мексика",
                "za": "Южная Африка",
                "kr": "Южная Корея",
                "ar": "Аргентина",
                "sa": "Саудовская Аравия",
                "ng": "Нигерия",
                "eg": "Египет",
                "tr": "Турция",
                "pk": "Пакистан",
                "id": "Индонезия",
                "pl": "Польша",
                "nl": "Нидерланды",
                "se": "Швеция",
                "ch": "Швейцария",
                "be": "Бельгия",
                "gr": "Греция",
                "pt": "Португалия",
                "no": "Норвегия",
                "dk": "Дания",
                "fi": "Финляндия",
                "is": "Исландия",
                "ie": "Ирландия",
                "sg": "Сингапур",
                "ph": "Филиппины",
                "th": "Таиланд",
                "vn": "Вьетнам",
                "my": "Малайзия",
                "ua": "Украина",
                "ro": "Румыния",
                "bg": "Болгария",
                "cz": "Чехия",
                "hu": "Венгрия",
                "at": "Австрия",
                "cl": "Чили",
                "co": "Колумбия",
                "pe": "Перу",
                "ve": "Венесуэла",
                "cancel": "Отмена",
            },
            "ch": {
                "ru": "俄罗斯",
                "us": "美国",
                "de": "德国",
                "fr": "法国",
                "cn": "中国",
                "jp": "日本",
                "in": "印度",
                "br": "巴西",
                "gb": "英国",
                "it": "意大利",
                "es": "西班牙",
                "ca": "加拿大",
                "au": "澳大利亚",
                "mx": "墨西哥",
                "za": "南非",
                "kr": "韩国",
                "ar": "阿根廷",
                "sa": "沙特阿拉伯",
                "ng": "尼日利亚",
                "eg": "埃及",
                "tr": "土耳其",
                "pk": "巴基斯坦",
                "id": "印度尼西亚",
                "pl": "波兰",
                "nl": "荷兰",
                "se": "瑞典",
                "ch": "瑞士",
                "be": "比利时",
                "gr": "希腊",
                "pt": "葡萄牙",
                "no": "挪威",
                "dk": "丹麦",
                "fi": "芬兰",
                "is": "冰岛",
                "ie": "爱尔兰",
                "sg": "新加坡",
                "ph": "菲律宾",
                "th": "泰国",
                "vn": "越南",
                "my": "马来西亚",
                "ua": "乌克兰",
                "ro": "罗马尼亚",
                "bg": "保加利亚",
                "cz": "捷克",
                "hu": "匈牙利",
                "at": "奥地利",
                "cl": "智利",
                "co": "哥伦比亚",
                "pe": "秘鲁",
                "ve": "委内瑞拉",
                "cancel": "取消",
            },
        }


        translations = region_translations.get(language_code, region_translations["en"])

        builder = InlineKeyboardBuilder()

        for code, region in country_codes.items():
            if region in available_regions:
                stock = available_stock.get(region, 0)
                builder.button(
                    text=f"{translations.get(region, region)} ({code}) - {stock} pcs",
                    callback_data=f"select_region:{region}",
                )

        builder.button(text=translations["cancel"], callback_data="cancel")
        return builder.adjust(3).as_markup()
