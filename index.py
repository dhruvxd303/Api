import json
import re
import binascii
from faker import Faker
import cloudscraper

# AES fallback
try:
    from Crypto.Cipher import AES
except ImportError:
    from Cryptodome.Cipher import AES

faker = Faker()

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

def lookup(mobile):
    if not (mobile.isdigit() and len(mobile) == 10):
        return "Invalid 10-digit number!"

    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'android', 'mobile': True}
    )
    base = "https://zentrixomega.42web.io"

    try:
        fetch(scraper, f"{base}/index.php?i=1")

        fetch(scraper, f"{base}/index.php?i=1", "POST", data={
            "name": faker.first_name(),
            "username": faker.user_name()[:12],
            "email": faker.email(),
            "password": "Basic_Coders",
            "register": ""
        })

        fetch(scraper, f"{base}/index.php")

        fetch(scraper, f"{base}/index.php", "POST", data={
            "message": f"/number {mobile}",
            "send_message": ""
        })

        resp = fetch(scraper, f"{base}/index.php?ajax=get_messages")
        data = json.loads(resp.text)

        bot_msg = None
        for msg in data.get("messages", []):
            if msg.get("type") == "bot":
                bot_msg = msg

        if not bot_msg:
            return "Data not found"

        raw = bot_msg.get("response_data", {}).get("raw_data") or bot_msg.get("response_data", {})

        if not raw or "records" not in raw or not raw["records"]:
            return "Data not found"

        result = f"Number Details for {mobile}\n\n"
        for i, r in enumerate(raw["records"], 1):
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

    except:
        return "Data not found"

# Vercel Handler
def handler(request):
    num = request.args.get("num")

    if not num:
        html = """
        <center style="margin-top:100px;font-family:Arial">
        <h1>Indian Number Lookup API</h1>
        <p><b>Usage:</b> ?num=9408438047</p>
        <p><a href="?num=9408438047">Test with 9408438047</a></p>
        <br><b>Dev: @Dhruv0757</b>
        </center>
        """
        return html

    result = lookup(num.strip())
    return f"<pre>{result}</pre>"

# For Vercel Python
from mangum import Mangum
app = Mangum(handler)