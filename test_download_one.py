#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""測試下載一個音檔"""

import requests
from pathlib import Path

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "Test-Script/1.0"}

def get_commons_file_url(filename):
    title = "File:" + filename
    params = {
        "action": "query",
        "titles": title,
        "prop": "imageinfo",
        "iiprop": "url",
        "format": "json",
    }
    resp = requests.get(COMMONS_API, params=params, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    pages = data.get("query", {}).get("pages", {})
    if not pages:
        return None

    page = next(iter(pages.values()))
    imageinfo = page.get("imageinfo")
    if not imageinfo:
        return None

    return imageinfo[0].get("url")

def download_file(url, dest_path):
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"下載: {url}")
    print(f"儲存到: {dest_path}")
    with requests.get(url, stream=True, headers=HEADERS, timeout=60) as r:
        r.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    print(f"✓ 下載完成！檔案大小: {dest_path.stat().st_size:,} bytes")

# 測試下載
test_file = "0號元素 - zh-yue.ogg"
print(f"測試檔案: {test_file}")

url = get_commons_file_url(test_file)
if url:
    print(f"✓ 找到 URL: {url}")
    dest_path = Path("test_download") / test_file
    download_file(url, dest_path)
else:
    print("✗ 找不到檔案 URL")
