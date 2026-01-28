# Chinese Wikipedia Spoken Articles Crawler

這個小工具會：
1. 透過 MediaWiki API 取得中文維基百科 `Category:有声条目` 裡所有有聲條目。
2. 對每個條目：
   - 抓純文字 extract （存成 `transcript.txt`）
   - 從 wikitext 解析對應的有聲檔名（`Zh-xxx.ogg`）
   - 從 Wikimedia Commons 下載 OGG 音訊檔
3. 結果會存成：

```text
data/
  條目標題1/
    transcript.txt
    Zh-xxx-part_1.ogg
    Zh-xxx-part_2.ogg
  條目標題2/
    ...
```

## 使用方法

1. 安裝相依套件：

   ```bash
   pip install requests
   ```

2. 執行爬蟲：

   ```bash
   python crawl_spoken_zhwiki.py
   ```

3. 執行完成後，可在 `data/` 目錄查看每個條目的文字與音訊檔。

## 其他工具

### 音訊分析工具

**analyze_audio.py** - 完整版音訊分析（需要安裝 ffprobe）

分析所有已下載音檔的時長和語言分類：

```bash
python analyze_audio.py
```

功能：
- 使用 ffprobe 取得每個音檔的實際時長
- 根據檔名自動分類語言（國語/粵語/英文/其他）
- 統計各語言的檔案數量和總時長
- 顯示檔名範例

**analyze_audio_simple.py** - 快速版音訊分析（不需要 ffprobe）

不需要額外工具，快速分析音檔：

```bash
python analyze_audio_simple.py
```

功能：
- 根據檔名分類語言
- 統計檔案數量和總大小
- 基於檔案大小預估時長（假設 OGG 平均品質約 0.5 MB/分鐘）

### 測試工具

**test_audio_parsing.py** - 測試音檔解析功能

測試從維基百科條目中解析音檔名稱的功能：

```bash
python test_audio_parsing.py
```

可以修改腳本中的 `test_titles` 列表來測試不同的條目。

**test_download_one.py** - 測試單個檔案下載

測試從 Wikimedia Commons 下載單個音檔：

```bash
python test_download_one.py
```

下載的檔案會存放在 `test_download/` 目錄中。可以修改腳本中的 `test_file` 變數來下載不同的檔案。

## 授權提醒

- 中文維基百科文字：CC BY-SA 4.0
- 有聲條目音訊：通常為 CC BY-SA / GFDL 等自由授權

若將資料或衍生作品（例如模型）公開或再散布，請務必遵守相應授權條款（包含署名與相同方式分享）。
