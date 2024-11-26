import requests
from datetime import datetime

def get_bnb_amount(dollars) -> float:
    # URL для получения цены BNB в USD
    api_url_price = "https://api.coingecko.com/api/v3/simple/price?ids=binancecoin&vs_currencies=usd"
    try:
        # Запрос к API
        response = requests.get(api_url_price)
        response.raise_for_status()
        response_json = response.json()
        
        # Получаем стоимость 1 BNB в USD
        bnb_price_usd = response_json['binancecoin']['usd']
        
        # Вычисляем количество BNB
        bnb_amount = dollars / bnb_price_usd
        
        # Округляем до 4 знаков после запятой
        bnb_amount = round(bnb_amount, 4)
        
        return bnb_amount
    except Exception as e:
        print(f"Ошибка при получении цены BNB: {e}")
        return 0

def find_transaction_by_amount(API_KEY, ADDRESS, TARGET_AMOUNT_BNB):
    start_block = 0
    end_block = 99999999
    transactions_fetched = True

    while transactions_fetched:
        url = f"https://api.bscscan.com/api?module=account&action=tokentx&address={ADDRESS}&startblock={start_block}&endblock={end_block}&sort=desc&apikey={API_KEY}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            if data['status'] == '1':
                transactions = data['result']
            else:
                print(f"BSCScan API Error: {data['message']}")
                return "API Error"
        except Exception as e:
            print(e)
            return "Request Error"

        for transaction in transactions:
            # Вычисляем сумму в BSC-USD
            amount_bsc_usd = float(int(transaction['value'])) / (10**int(transaction['tokenDecimal']))
            
            # Проверяем на совпадение суммы
            if amount_bsc_usd == TARGET_AMOUNT_BNB:
                return True

        if len(transactions) > 0:
            start_block = int(transactions[-1]['blockNumber']) + 1  # чтобы не зацикливаться на одном блоке
        transactions_fetched = len(transactions) < 100

    return False
