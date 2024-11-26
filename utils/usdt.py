import requests
from datetime import datetime

# Константы
WALLET_ADDRESS = 'TKQ4eT1xfJCPt6eV9hBx4b2iEhzwWT18er'
TRX_API_URL = f"https://apilist.tronscanapi.com/api/transfer/trc20?address={WALLET_ADDRESS}&trc20Id=TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t&start=0&limit=10&direction=0&reverse=true&db_version=1"
COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price?ids=tether&vs_currencies=usd"

# Получение курса USDT/USD
def get_usd_rate(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return float(data["tether"]["usd"])
    except Exception as e:
        print(f"Ошибка получения курса USDT/USD: {e}")
        return None

# Получение данных о транзакциях
def fetch_transactions(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Ошибка получения данных о транзакциях: {e}")
        return None

# Форматирование временной метки
def format_timestamp(timestamp_ms):
    try:
        timestamp_sec = timestamp_ms / 1000
        return datetime.utcfromtimestamp(timestamp_sec).strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        print(f"Ошибка форматирования времени: {e}")
        return "Неизвестное время"

# Проверка транзакций
def check_transactions(transactions, target_amount_trx):
    for transaction in transactions:
        try:
            amount_trx = float(transaction.get("amount")) / (10**6)
            print(f"Проверяем сумму {amount_trx}, целевая: {target_amount_trx}")  # Debug
            if abs(amount_trx - target_amount_trx) < 0.001:
                print("🚀 Обнаружена транзакция с заданной суммой!")
                return True
        except Exception as e:
            print(f"Ошибка при проверке транзакции: {e}")
    return False


# Вывод информации о транзакциях
def display_transactions(transactions, usd_rate):
    for transaction in transactions:
        try:
            amount_trx = float(transaction.get("amount")) / (10**6)
            usd_amount = amount_trx * usd_rate
            readable_date = format_timestamp(transaction.get("block_timestamp"))
            from_address = transaction.get("from")
            to_address = transaction.get("to")
            txn_hash = transaction.get("hash")
            status = transaction.get("contract_ret")
            
            print(f"""Транзакция:
Hash: {txn_hash}
Сумма (TRX): {amount_trx}
Сумма (USD): {usd_amount:.5f}
Отправитель: {from_address}
Получатель: {to_address}
Дата: {readable_date}
Статус: {status}
""")
        except Exception as e:
            print(f"Ошибка обработки транзакции: {e}")

# Основная функция
def main(target_usd: float):
    try:
        target_usd = float(target_usd)  # Преобразование в float
    except ValueError:
        print(f"Ошибка: {target_usd} не может быть преобразовано в число.")
        return
    usd_rate = get_usd_rate(COINGECKO_API_URL)
    if usd_rate is None:
        return

    target_amount_trx = target_usd / usd_rate

    trx_data = fetch_transactions(TRX_API_URL)
    if trx_data is None:
        return

    transactions = trx_data.get("data", [])
    if not transactions:
        print("Нет доступных транзакций.")
        return

    if check_transactions(transactions, target_amount_trx):
        print("✅ Транзакция найдена.")
        return True
    else:
        print("❌ Транзакция не найдена.")
    
    display_transactions(transactions, usd_rate)

