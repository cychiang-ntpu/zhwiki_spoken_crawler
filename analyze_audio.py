#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""分析音檔語言和總時長"""

import subprocess
from pathlib import Path
import re

def get_audio_duration(file_path):
    """使用 ffprobe 取得音檔時長（秒）"""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 
             'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', 
             str(file_path)],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except:
        pass
    return None

def classify_language(filename):
    """根據檔名判斷語言"""
    filename_lower = filename.lower()
    
    # 粵語
    if 'yue' in filename_lower or '粵' in filename:
        return 'cantonese'
    
    # 英文檔名（只有英文字母、數字、連字號、底線）
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
    'mandarin': {'count': 0, 'files': [], 'total_duration': 0},
    'cantonese': {'count': 0, 'files': [], 'total_duration': 0},
    'english': {'count': 0, 'files': [], 'total_duration': 0},
    'other': {'count': 0, 'files': [], 'total_duration': 0}
}

print("正在分析音檔...")
for i, file_path in enumerate(all_files, 1):
    if i % 20 == 0:
        print(f"  處理進度: {i}/{len(all_files)}")
    
    filename = file_path.name
    lang = classify_language(filename)
    
    duration = get_audio_duration(file_path)
    
    stats[lang]['count'] += 1
    stats[lang]['files'].append(filename)
    if duration:
        stats[lang]['total_duration'] += duration

print("\n" + "="*70)
print("統計結果")
print("="*70)

for lang_key, lang_name in [('mandarin', '國語（普通話）'), 
                             ('cantonese', '粵語'),
                             ('english', '英文檔名'),
                             ('other', '其他')]:
    data = stats[lang_key]
    hours = data['total_duration'] / 3600
    print(f"\n{lang_name}:")
    print(f"  檔案數: {data['count']}")
    print(f"  總時長: {data['total_duration']:.1f} 秒 = {hours:.2f} 小時")
    if data['count'] > 0 and data['count'] <= 10:
        print(f"  檔名範例:")
        for fn in data['files'][:10]:
            print(f"    - {fn}")

print("\n" + "="*70)
print(f"總檔案數: {len(all_files)}")
total_duration = sum(s['total_duration'] for s in stats.values())
print(f"總時長: {total_duration:.1f} 秒 = {total_duration/3600:.2f} 小時")
print("="*70)
