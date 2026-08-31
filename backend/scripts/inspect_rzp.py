import sys
import os
sys.path.insert(0, os.path.abspath("."))
import httpx
from app.core.config import settings

def inspect_links():
    auth = (settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    res = httpx.get("https://api.razorpay.com/v1/payment_links", auth=auth)
    items = res.json().get("payment_links", [])
    print(f"Total links: {len(items)}")
    for x in items:
        print(f"ID: {x.get('id')} | Amount: {x.get('amount')/100} | Status: {x.get('status')} | URL: {x.get('short_url')}")

if __name__ == "__main__":
    inspect_links()
