import requests
import re
import urllib.parse

keyword = "北京 五月天"
encoded_kw = urllib.parse.quote(keyword)
url = f"https://www.piaoniu.com/sh-all/s_{encoded_kw}"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

print(f"Searching: {url}")
resp = requests.get(url, headers=headers)
ids = re.findall(r'activity/(\d+)', resp.text)
print(f"Found IDs: {list(dict.fromkeys(ids))}")
