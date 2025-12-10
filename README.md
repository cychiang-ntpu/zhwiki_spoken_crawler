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

## 授權提醒

- 中文維基百科文字：CC BY-SA 4.0
- 有聲條目音訊：通常為 CC BY-SA / GFDL 等自由授權

若將資料或衍生作品（例如模型）公開或再散布，請務必遵守相應授權條款（包含署名與相同方式分享）。
