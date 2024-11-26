import requests

transaction_hash = "71bd958160bb34acbd7e2edda4719a6953a1d841d4e098e6e47f13ba9d18083d"
api_url = "https://apilist.tronscan.org/api/transaction-info"

def fetch_transaction_by_hash(tx_hash):
    try:
        response = requests.get(api_url, params={"hash": tx_hash})
        response.raise_for_status()
        response_json = response.json()

        if response_json.get("hash") == tx_hash:
            return response_json
        else:
            print(f"Transaction not found or invalid response: {response_json}")
            return None
    except Exception as e:
        print(f"Error fetching transaction: {e}")
        return None

if __name__ == "__main__":
    transaction = fetch_transaction_by_hash(transaction_hash)

    if transaction:
        print(transaction)
    else:
        print("Transaction not found.")
