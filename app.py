# -*- coding: utf-8 -*-
"""
台股期貨歷史資料查詢系統（部署版）
- 從同層 taifex_data 的 CSV 讀取各期貨歷史資料
- 使用者用下拉選單選期貨、選日期區間、選要畫的欄位
- 以線圖呈現，並附原始資料表格
資料為公開市場資料，程式僅讀取不修改。
"""
import os
import glob
import pandas as pd
import streamlit as st

# ---- 資料夾位置（與本檔同層的 taifex_data）----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "taifex_data")

# 可畫的數值欄位 → 顯示名稱
NUMERIC_FIELDS = {
    "spot_close": "現貨收盤價",
    "spot_open": "現貨開盤價",
    "spot_high": "現貨最高價",
    "spot_low": "現貨最低價",
    "long": "三大法人多單",
    "short": "三大法人空單",
    "market_oi": "全市場未平倉量",
    "buy_top10_all": "前十大買方",
    "sell_top10_all": "前十大賣方",
}

st.set_page_config(page_title="台股期貨歷史資料查詢", page_icon="📈", layout="wide")
st.title("📈 台股期貨歷史資料查詢系統")
st.caption("資料來源：台期所公開市場資料")


@st.cache_data(show_spinner=False)
def list_contracts():
    """列出 taifex_data 內所有期貨（依檔名）。"""
    if not os.path.isdir(DATA_DIR):
        return []
    files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    names = sorted(os.path.splitext(os.path.basename(f))[0] for f in files)
    return names


@st.cache_data(show_spinner=False)
def load_contract(name):
    """讀取單一期貨 CSV，date 轉為日期並排序。"""
    path = os.path.join(DATA_DIR, name + ".csv")
    df = pd.read_csv(path)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"]).sort_values("date")
    for col in NUMERIC_FIELDS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


contracts = list_contracts()

if not contracts:
    st.error(f"找不到資料。預期資料夾：{DATA_DIR}")
    st.stop()

# ---- 側邊欄：選期貨、日期、欄位 ----
st.sidebar.header("查詢條件")
contract = st.sidebar.selectbox("選擇期貨", contracts,
                                index=contracts.index("台積電期貨") if "台積電期貨" in contracts else 0)

df = load_contract(contract)

if df.empty or "date" not in df.columns:
    st.warning("這個期貨沒有可用的資料。")
    st.stop()

min_d = df["date"].min().date()
max_d = df["date"].max().date()
date_range = st.sidebar.date_input("日期區間", value=(min_d, max_d),
                                   min_value=min_d, max_value=max_d)

if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_d, end_d = date_range
else:
    start_d, end_d = min_d, max_d

available_fields = {k: v for k, v in NUMERIC_FIELDS.items() if k in df.columns and df[k].notna().any()}
label_to_col = {v: k for k, v in available_fields.items()}

default_label = available_fields.get("spot_close", list(available_fields.values())[0] if available_fields else None)
chosen_labels = st.sidebar.multiselect(
    "要畫的資料", list(label_to_col.keys()),
    default=[default_label] if default_label else []
)

mask = (df["date"].dt.date >= start_d) & (df["date"].dt.date <= end_d)
view = df.loc[mask].copy()

st.subheader(f"{contract}")
c1, c2, c3 = st.columns(3)
c1.metric("資料筆數", len(view))
c2.metric("起始日", str(start_d))
c3.metric("結束日", str(end_d))

if not chosen_labels:
    st.info("請在左側至少選一個「要畫的資料」。")
    st.stop()

chosen_cols = [label_to_col[l] for l in chosen_labels]

chart_df = view.set_index("date")[chosen_cols].rename(columns={k: available_fields[k] for k in chosen_cols})
st.line_chart(chart_df)

with st.expander("查看原始資料表格"):
    show_cols = ["date"] + chosen_cols
    table = view[show_cols].rename(columns={**{"date": "日期"}, **{k: available_fields[k] for k in chosen_cols}})
    st.dataframe(table, use_container_width=True, hide_index=True)

    csv_bytes = table.to_csv(index=False).encode("utf-8-sig")
    st.download_button("下載目前區間 CSV", data=csv_bytes,
                       file_name=f"{contract}_{start_d}_{end_d}.csv", mime="text/csv")
