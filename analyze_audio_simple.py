#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""分析音檔語言分類（快速版）"""

from pathlib import Path
import re

def classify_language(filename):
    """根據檔名判斷語言"""
    filename_lower = filename.lower()
    
    # 粵語
    if 'yue' in filename_lower or '粵' in filename:
        return 'cantonese'
    
    # 英文檔名（只有英文字母、數字、連字號、底線、點）
    if re.match(r'^[a-zA-Z0-9\-_\s\.]+$', filename):
        return 'english'
    
    # 含有中文且非粵語，判定為國語
    if re.search(r'[\u4e00-\u9fff]', filename):
        return 'mandarin'
    
    # 其他
    return 'other'

data_dir = Path("data")
all_files = list(data_dir.rglob("*.ogg"))

print(f"總共找到 {len(all_files)} 個音檔\n")

# 分類統計
stats = {
    'mandarin': {'count': 0, 'files': [], 'size': 0},
    'cantonese': {'count': 0, 'files': [], 'size': 0},
    'english': {'count': 0, 'files': [], 'size': 0},
    'other': {'count': 0, 'files': [], 'size': 0}
}

for file_path in all_files:
    filename = file_path.name
    lang = classify_language(filename)
    
    stats[lang]['count'] += 1
    stats[lang]['files'].append(filename)
    stats[lang]['size'] += file_path.stat().st_size

print("="*70)
print("統計結果")
print("="*70)

for lang_key, lang_name in [('mandarin', '國語（普通話）'), 
                             ('cantonese', '粵語'),
                             ('english', '英文檔名（可能非中文）'),
                             ('other', '其他')]:
    data = stats[lang_key]
    size_mb = data['size'] / (1024 * 1024)
    print(f"\n{lang_name}:")
    print(f"  檔案數: {data['count']}")
    print(f"  總大小: {size_mb:.1f} MB")
    
    if data['count'] > 0:
        print(f"  檔名範例（顯示前 5 個）:")
        for fn in data['files'][:5]:
            print(f"    - {fn}")
        if data['count'] > 5:
            print(f"    ... 還有 {data['count'] - 5} 個檔案")

print("\n" + "="*70)
print(f"總檔案數: {len(all_files)}")
total_size = sum(s['size'] for s in stats.values())
print(f"總大小: {total_size/(1024*1024):.1f} MB = {total_size/(1024*1024*1024):.2f} GB")
print("="*70)

# 預估時長（假設平均 OGG 編碼約 0.5 MB/分鐘）
print("\n預估時長（基於檔案大小，假設 OGG 平均品質約 0.5 MB/分鐘）:")
for lang_key, lang_name in [('mandarin', '國語'), ('cantonese', '粵語')]:
    size_mb = stats[lang_key]['size'] / (1024 * 1024)
    est_minutes = size_mb / 0.5
    est_hours = est_minutes / 60
    print(f"  {lang_name}: 約 {est_hours:.1f} 小時")
