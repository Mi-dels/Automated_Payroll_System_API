import requests
from django.conf import settings

FLUTTERWAVE_BASE_URL = "https://api.flutterwave.com/v3"


def initiate_transfer(amount, account_number, bank_code, account_name, reference, narration="Salary Payment"):
    headers = {
        "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "account_bank": bank_code,
        "account_number": account_number,
        "amount": float(amount),
        "narration": narration,
        "currency": "NGN",
        "reference": reference,
        "debit_currency": "NGN",
    }

    response = requests.post(
        f"{FLUTTERWAVE_BASE_URL}/transfers",
        json=payload,
        headers=headers
    )

    data = response.json()

    if response.status_code == 200 and data.get("status") == "success":
        return {
            "success": True,
            "transfer_id": data["data"]["id"],
            "reference": data["data"]["reference"],
            "status": data["data"]["status"],
        }
    else:
        raise Exception(f"Flutterwave transfer failed: {data.get('message', 'Unknown error')}")


def verify_transfer(transfer_id):
    headers = {
        "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.get(
        f"{FLUTTERWAVE_BASE_URL}/transfers/{transfer_id}",
        headers=headers
    )

    data = response.json()

    if response.status_code == 200:
        return {
            "status": data["data"]["status"],
            "reference": data["data"]["reference"],
            "amount": data["data"]["amount"],
        }
    else:
        raise Exception(f"Flutterwave verification failed: {data.get('message', 'Unknown error')}")