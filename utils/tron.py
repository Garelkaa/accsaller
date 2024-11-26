import requests
import json
import time
 
wallet_address = "TTHhZ9wY6wzikAH2QxodknUX51JMpmcxdL"
api_url = "https://apilist.tronscan.org/api/transaction"
api_url_price = "https://api.coingecko.com/api/v3/simple/price?ids=tron&vs_currencies=usd"


def get_tron_amount(dollars) -> int:
    response = requests.get(api_url_price)
    response.raise_for_status()
    response_json = response.json()

    trx_price_usd = response_json['tron']['usd']
    trx_amount = dollars / trx_price_usd

    trx_amount = round(trx_amount, 4)

    return trx_amount


def fetch_transactions_tron(wallet_address, limit=10, start=0):
  params = {
    "address": wallet_address,
    "limit": limit,
    "start": start,
  }

  try:
    response = requests.get(api_url, params=params)
    response.raise_for_status()
    response_json = response.json()

    if "data" in response_json:
      return response_json["data"]
    else: 
      print(f"{response_json.get('message')}")
      return None
  except Exception as e:
     print(e)


def display_transactions_tron(transactions, amountt):
    
    if transactions:
        for transaction in transactions:
            try:
                amount_trx = int(transaction['amount']) / (10**6) 
                if abs(amount_trx - amountt) < 0.0001:
                    print("трутрутру")
                    return True
                else:
                    print("Соси яички")
            except Exception as e:
                print(e)

    else:
        print("None")
