#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Crawler for Chinese Wikipedia spoken articles (有声条目).

功能：
1. 透過 MediaWiki API 取得 Category:有声条目 裡所有條目標題。
2. 對每個條目：
   - 抓純文字 extract （當作 transcript）
   - 抓 wikitext 並從中解析出有聲檔名（File:Zh-xxx.ogg）
   - 從 Wikimedia Commons 下載對應 OGG 檔
3. 存成 data/<title>/ 底下的 transcript.txt + .ogg 檔案。

授權提醒：
- 中文維基文字：CC BY-SA 4.0
- 音訊檔：通常為 CC BY-SA / GFDL 等自由授權
使用時請遵守相應授權條款（署名與相同方式分享）。
"""

import os
import re
import time
from pathlib import Path

import requests

WIKI_API = "https://zh.wikipedia.org/w/api.php"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
OUTPUT_DIR = Path("data")
CATEGORY_TITLE = "Category:有声条目"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def get_category_members(category_title, namespace=0, limit_per_req=500):
    """
    取得分類底下所有條目標題。
    :param category_title: 例如 "Category:有声条目"
    :param namespace: 0 = 條目
    :param limit_per_req: 每次 API 呼叫的最大筆數
    :return: list of page titles
    """
    titles = []
    cmcontinue = None

    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": category_title,
            "cmnamespace": namespace,
            "cmlimit": limit_per_req,
            "format": "json",
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue

        resp = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        members = data.get("query", {}).get("categorymembers", [])
        for m in members:
            titles.append(m["title"])

        cmcontinue = data.get("continue", {}).get("cmcontinue")
        if not cmcontinue:
            break

        # 禮貌一點，避免壓垮 Wikipedia
        time.sleep(0.5)

    return titles


def get_page_extract(title):
    """
    抓條目的純文字 extract（已去除 wiki markup）。
    """
    params = {
        "action": "query",
        "prop": "extracts",
        "explaintext": 1,
        "titles": title,
        "format": "json",
    }
    resp = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    pages = data.get("query", {}).get("pages", {})
    if not pages:
        return ""

    page = next(iter(pages.values()))
    return page.get("extract", "") or ""


def get_page_wikitext(title):
    """
    抓條目的 wikitext 原始內容，方便解析模板與檔案連結。
    """
    params = {
        "action": "query",
        "prop": "revisions",
        "rvprop": "content",
        "rvslots": "main",
        "formatversion": 2,
        "titles": title,
        "format": "json",
    }
    resp = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    pages = data.get("query", {}).get("pages", [])
    if not pages:
        return ""

    page = pages[0]
    revisions = page.get("revisions")
    if not revisions:
        return ""
    return revisions[0].get("slots", {}).get("main", {}).get("content", "") or ""


def parse_audio_filenames_from_wikitext(wikitext):
    """
    從 wikitext 裡嘗試找出有聲檔名：
    1. 找 template 參數 file_name = xxx
    2. 找 [[File:Zh-xxx.ogg]] 類型的連結
    3. 找 {{Spoken Wikipedia}} 模板
    4. 找 {{Spoken Wikipedia-2}} 模板

    回傳純粹檔名，不含 'File:'，例如：
    ['Zh-韓國教育-part_1.ogg', 'Zh-韓國教育-part_2.ogg']
    """
    filenames = set()

    # 1) 嘗試抓模板參數 file_name = xxx
    #    e.g. file_name = Zh-韓國教育-part_2
    file_name_pattern = re.compile(r"file_name\s*=\s*([^|\n\r]+)", re.IGNORECASE)
    for m in file_name_pattern.finditer(wikitext):
        raw = m.group(1).strip()
        # 去掉可能的結尾空白或模板標記
        raw = re.split(r"[}|]", raw)[0].strip()
        if raw and not raw.lower().startswith("file:"):
            # 補 .ogg 若沒寫副檔名（保守作法）
            if not re.search(r"\.(ogg|oga|opus)$", raw, re.IGNORECASE):
                raw = raw + ".ogg"
            filenames.add(raw)

    # 2) 抓 [[File:Zh-xxx.ogg]] 類型
    file_link_pattern = re.compile(r"\[\[\s*File\s*:\s*([^|\]]+\.ogg)", re.IGNORECASE)
    for m in file_link_pattern.finditer(wikitext):
        raw = m.group(1).strip()
        raw = raw.replace("_", " ")
        # 去掉任何 fragment 或多餘空白
        raw = re.split(r"[#|]", raw)[0].strip()
        filenames.add(raw)

    # 3) 抓 {{Spoken Wikipedia|檔名.ogg|...}} 模板（第一個參數是檔名）
    spoken_wiki_pattern = re.compile(r"\{\{\s*Spoken\s+Wikipedia\s*\|\s*([^|}\n]+\.ogg)", re.IGNORECASE)
    for m in spoken_wiki_pattern.finditer(wikitext):
        raw = m.group(1).strip()
        filenames.add(raw)

    # 4) 抓 {{Spoken Wikipedia-2|檔名1.ogg|檔名2.ogg|...}} 模板
    spoken_wiki2_pattern = re.compile(r"\{\{\s*Spoken\s+Wikipedia-2\s*\|([^}]+)\}\}", re.IGNORECASE)
    for m in spoken_wiki2_pattern.finditer(wikitext):
        params = m.group(1)
        # 分割參數，找出所有 .ogg 檔案
        parts = params.split('|')
        for part in parts:
            part = part.strip()
            if '.ogg' in part.lower():
                # 可能是檔名
                fname = re.search(r'([^|}\n]+\.ogg)', part, re.IGNORECASE)
                if fname:
                    filenames.add(fname.group(1).strip())

    # 正規化檔名：移除前綴 File:
    normalized = []
    for f in filenames:
        if f.lower().startswith("file:"):
            normalized.append(f.split(":", 1)[1].strip())
        else:
            normalized.append(f.strip())

    # 去重
    normalized = list(dict.fromkeys(normalized))
    return normalized


def get_commons_file_url(filename):
    """
    給定檔名（不含 'File:'），向 Commons 查詢實際檔案 URL。
    若 Commons 查不到，可再加一個備案改查 zh.wikipedia（此處先簡化只查 Commons）。
    """
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
    """
    下載檔案到 dest_path。
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"  下載音訊: {url} -> {dest_path}")
    with requests.get(url, stream=True, headers=HEADERS, timeout=60) as r:
        r.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)


def sanitize_dirname(name):
    """
    將條目標題轉為適合檔案系統使用的資料夾名稱。
    """
    # 簡單替換非法字元
    return re.sub(r"[\\/:\*\?\"<>\|]", "_", name)


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    print("取得 Category:有声条目 的條目列表...")
    titles = get_category_members(CATEGORY_TITLE)
    print(f"共取得 {len(titles)} 個條目。")

    for idx, title in enumerate(titles, start=1):
        print(f"\n[{idx}/{len(titles)}] 處理條目：{title}")

        dirname = sanitize_dirname(title)
        page_dir = OUTPUT_DIR / dirname
        page_dir.mkdir(parents=True, exist_ok=True)

        # 抓純文字 transcript
        try:
            transcript = get_page_extract(title)
        except Exception as e:
            print(f"  抓取文字失敗: {e}")
            continue

        if not transcript.strip():
            print("  無文字內容（略過或之後人工檢查）。")
        else:
            transcript_path = page_dir / "transcript.txt"
            with open(transcript_path, "w", encoding="utf-8") as f:
                f.write(transcript)
            print(f"  已儲存文字到 {transcript_path}")

        # 抓 wikitext，解析音訊檔名
        try:
            wikitext = get_page_wikitext(title)
        except Exception as e:
            print(f"  抓取 wikitext 失敗: {e}")
            continue

        audio_files = parse_audio_filenames_from_wikitext(wikitext)
        if not audio_files:
            print("  沒有在條目中找到任何 .ogg 檔案連結。")
            continue

        print(f"  在條目中找到 {len(audio_files)} 個音訊檔：")
        for fname in audio_files:
            print(f"    - {fname}")

        # 下載每一個音訊檔
        for fname in audio_files:
            dest_path = page_dir / fname
            if dest_path.exists():
                print(f"  檔案已存在，略過：{dest_path}")
                continue

            url = None
            try:
                url = get_commons_file_url(fname)
            except Exception as e:
                print(f"  從 Commons 取得 URL 失敗: {fname} ({e})")

            if not url:
                print(f"  找不到 {fname} 的 Commons 下載 URL，可能是本地檔或名稱不符，需要人工檢查。")
                continue

            try:
                download_file(url, dest_path)
                # 禮貌限速，避免 429 錯誤
                time.sleep(3.0)
            except Exception as e:
                print(f"  下載檔案失敗: {e}")
                # 如果遇到 429 錯誤，等待更久
                if "429" in str(e):
                    print(f"  遇到速率限制，等待 30 秒後繼續...")
                    time.sleep(30)

        # 每個條目之間稍微 sleep，避免太頻繁
        time.sleep(1.0)


if __name__ == "__main__":
    main()
