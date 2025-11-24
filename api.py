from flask import Flask, request
import cloudscraper
import re
import binascii
import json
from faker import Faker

try:
    from Crypto.Cipher import AES
except ImportError:
    from Cryptodome.Cipher import AES

app = Flask(__name__)
faker = Faker()

# Reuse scraper (but refresh per request for clean session)
def get_scraper():
    return cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'android', 'mobile': True}
    )

def decrypt_cookie(a, b, c):
    a = binascii.unhexlify(a)
    b = binascii.unhexlify(b)
    c = binascii.unhexlify(c)
    return binascii.hexlify(AES.new(a, AES.MODE_CBC, b).decrypt(c)).decode()

def solve_aes(html):
    nums = re.findall(r'toNumbers\("([0-9a-f]+)"\)', html)
    if len(nums) >= 3:
        return decrypt_cookie(nums[0], nums[1], nums[2])
    return None

def fetch(scraper, url, method="GET", data=None):
    while True:
        r = scraper.request(method, url, data=data)
        if "slowAES" in r.text:
            cookie = solve_aes(r.text)
            if cookie:
                scraper.cookies.set("__test", cookie, domain=".42web.io")
            continue
        return r

def lookup_number(mobile):
    mobile = mobile.strip()
    if not (mobile.isdigit() and len(mobile) == 10):
        return "Invalid Number! Send 10-digit Indian mobile number."

    scraper = get_scraper()
    base = "https://zentrixomega.42web.io"

    try:
        # Step 1: Open register page
        fetch(scraper, f"{base}/index.php?i=1")

        # Step 2: Register fake user
        fetch(scraper, f"{base}/index.php?i=1", "POST", data={
            "name": faker.first_name(),
            "username": faker.user_name()[:15],
            "email": faker.email(),
            "password": "Basic_Coders",
            "register": ""
        })

        # Step 3: Go to dashboard
        fetch(scraper, f"{base}/index.php")

        # Step 4: Send /number command
        fetch(scraper, f"{base}/index.php", "POST", data={
            "message": f"/number {mobile}",
            "send_message": ""
        })

        # Step 5: Get bot response
        resp = fetch(scraper, f"{base}/index.php?ajax=get_messages")
        data = json.loads(resp.text)

        # Find latest bot message
        bot_message = None
        for msg in data.get("messages", []):
            if msg.get("type") == "bot":
                bot_message = msg

        if not bot_message:
            return "Data not found"

        raw_data = bot_message.get("response_data", {}).get("raw_data") or bot_message.get("response_data", {})

        if not raw_data or "records" not in raw_data or not raw_data["records"]:
            return "Data not found"

        result = f"Number Details for {mobile}\n\n"
        for i, record in enumerate(raw_data["records"], 1):
            r = record
            result += f"Record: DATA{i}\n"
            result += f"Mobile: {mobile}\n"
            result += f"Name:  {r.get('name', 'N/A').strip() or 'N/A'}\n"
            result += f"Father Name: {r.get('father_name', 'N/A') or 'N/A'}\n"
            result += f"Address:   {r.get('address', 'N/A').strip() or 'N/A'}\n"
            result += f"Circle: {r.get('circle', 'N/A') or 'N/A'}\n"
            result += f"ID Number: {r.get('id_number', 'N/A') or 'N/A'}\n"
            result += f"Email: {r.get('email', 'N/A') or 'N/A'}\n"
            result += f"Alternate Mobile: {r.get('alternate_mobile', 'N/A') or 'N/A'}\n\n"

        result += "Dev: @Dhruv0757"
        return result

    except Exception as e:
        return "Data not found"

@app.route("/")
def home():
    num = request.args.get("num")

    if not num:
        return '''
        <center><br><br>
        <h1>Indian Number Lookup API</h1>
        <p><b>Usage:</b> /num=9408438047</p>
        <p>Example: <a href="/num=9408438047">Click Here</a></p>
        <br><b>Dev: @Dhruv0757</b>
        </center>
        '''

    result = lookup_number(num)
    return f"<pre>{result}</pre>"

if __name__ == "__main:
    app.run(host="0.0.0.0", port=8080)