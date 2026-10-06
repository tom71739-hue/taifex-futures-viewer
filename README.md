# 台股期貨歷史資料查詢系統

用 Streamlit 做的台股個股期貨歷史資料查詢工具。可選期貨、選日期區間、選欄位，畫成線圖並附原始資料表。

資料為台期所公開市場資料（三大法人多空、現貨開收高低、未平倉量、前十大買賣等）。

## 本機執行

```bash
pip install -r requirements.txt
streamlit run app.py
```

瀏覽器會自動開啟（預設 http://localhost:8501）。

## 部署（Streamlit Community Cloud）

1. 到 https://share.streamlit.io 用 GitHub 登入
2. 選本 repo、主程式填 `app.py`
3. Deploy

## 資料

`taifex_data/` 內為各期貨 CSV，欄位包含：
`date, contract, long, short, ratio, spot_open, spot_close, spot_high, spot_low, open, close, buy_top10_all, sell_top10_all, market_oi`
