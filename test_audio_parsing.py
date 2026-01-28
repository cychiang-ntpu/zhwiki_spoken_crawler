#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""測試音檔解析功能"""

import requests
import re

WIKI_API = "https://zh.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "Test-Script/1.0"}

def get_page_wikitext(title):
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
    filenames = set()
    
    # 找 file_name = xxx
    file_name_pattern = re.compile(r"file_name\s*=\s*([^|\n\r]+)", re.IGNORECASE)
    for m in file_name_pattern.finditer(wikitext):
        raw = m.group(1).strip()
        raw = re.split(r"[}|]", raw)[0].strip()
        if raw and not raw.lower().startswith("file:"):
            if not re.search(r"\.(ogg|oga|opus)$", raw, re.IGNORECASE):
                raw = raw + ".ogg"
            filenames.add(raw)
    
    # 找 [[File:Zh-xxx.ogg]]
    file_link_pattern = re.compile(r"\[\[\s*File\s*:\s*([^|\]]+\.ogg)", re.IGNORECASE)
    for m in file_link_pattern.finditer(wikitext):
        raw = m.group(1).strip()
        raw = raw.replace("_", " ")
        raw = re.split(r"[#|]", raw)[0].strip()
        filenames.add(raw)
    
    # 找 {{Spoken Wikipedia|檔名.ogg|...}}
    spoken_wiki_pattern = re.compile(r"\{\{\s*Spoken\s+Wikipedia\s*\|\s*([^|}\n]+\.ogg)", re.IGNORECASE)
    for m in spoken_wiki_pattern.finditer(wikitext):
        raw = m.group(1).strip()
        filenames.add(raw)

    # 找 {{Spoken Wikipedia-2|檔名1.ogg|檔名2.ogg|...}}
    spoken_wiki2_pattern = re.compile(r"\{\{\s*Spoken\s+Wikipedia-2\s*\|([^}]+)\}\}", re.IGNORECASE)
    for m in spoken_wiki2_pattern.finditer(wikitext):
        params = m.group(1)
        parts = params.split('|')
        for part in parts:
            part = part.strip()
            if '.ogg' in part.lower():
                fname = re.search(r'([^|}\n]+\.ogg)', part, re.IGNORECASE)
                if fname:
                    filenames.add(fname.group(1).strip())
    
    normalized = []
    for f in filenames:
        if f.lower().startswith("file:"):
            normalized.append(f.split(":", 1)[1].strip())
        else:
            normalized.append(f.strip())
    
    return list(dict.fromkeys(normalized))

# 測試幾個條目
test_titles = [
    "韓國教育",
    "2008年夏季奧林匹克運動會女子公路自行車比賽",
    "颱風",
    "0號元素"
]

for title in test_titles:
    print(f"\n{'='*60}")
    print(f"條目: {title}")
    print('='*60)
    
    try:
        wikitext = get_page_wikitext(title)
        print(f"Wikitext 長度: {len(wikitext)}")
        
        # 顯示包含 "spoken" 或 "Zh-" 的行
        relevant_lines = [line for line in wikitext.split('\n') 
                         if 'spoken' in line.lower() or 'zh-' in line.lower() or 'file_name' in line.lower()]
        
        if relevant_lines:
            print(f"\n找到 {len(relevant_lines)} 行相關內容:")
            for i, line in enumerate(relevant_lines[:10], 1):
                print(f"  {i}. {line.strip()[:200]}")
        else:
            print("\n未找到包含 'spoken'、'Zh-' 或 'file_name' 的行")
        
        # 測試解析
        audio_files = parse_audio_filenames_from_wikitext(wikitext)
        if audio_files:
            print(f"\n✓ 解析到 {len(audio_files)} 個音檔:")
            for fname in audio_files:
                print(f"  - {fname}")
        else:
            print("\n✗ 未解析到任何音檔")
            
    except Exception as e:
        print(f"錯誤: {e}")
