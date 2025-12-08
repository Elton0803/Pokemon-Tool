import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="寶可夢極巨數據庫", layout="wide")
st.title("寶可夢極巨戰鬥計算機 (校正版)")

# 檔名設定
excel_file = "Pokemon.xlsx"
SHEET_TYPE = "屬性克制表"
SHEET_DATA = "攻守數據"

# 初始化
df_type_chart = None
df_raw_data = None # 這是原始讀進來的亂亂的資料
df_attackers = pd.DataFrame()
df_defenders = pd.DataFrame()

# ==========================================
# 1. 讀取資料
# ==========================================
try:
    if not os.path.exists(excel_file):
        st.error(f"❌ 找不到檔案：{excel_file}")
        st.stop()

    # 讀取屬性表
    try:
        df_type_chart = pd.read_excel(excel_file, sheet_name=SHEET_TYPE, index_col=0)
    except:
        st.error("❌ 屬性克制表讀取失敗")
        st.stop()

    # 讀取攻守數據 (讀取前 2 列作為混合標題，以便我們辨識)
    try:
        # header=1 代表我們跳過第一行分類，直接讀第二行標題
        df_raw_data = pd.read_excel(excel_file, sheet_name=SHEET_DATA, header=1)
        # 把欄位名稱變成清單，方便選擇
        all_columns = list(df_raw_data.columns)
    except:
        st.error("❌ 攻守數據讀取失敗")
        st.stop()

except Exception as e:
    st.error(f"❌ 發生錯誤：{e}")
    st.stop()

# ==========================================
# 2. 側邊欄：欄位校正區 (這是修正數據錯誤的關鍵！)
# ==========================================
st.sidebar.header("🛠️ 數據欄位校正")
st.sidebar.info("請在此處選擇正確的 Excel 欄位，以確保數據正確。")

# --- 設定攻擊手資料來源 ---
st.sidebar.subheader("1. 設定「攻擊」數據來源")
# 預設嘗試抓取可能的欄位名稱
def get_index(options, key_part):
    for i, opt in enumerate(options):
        if key_part in str(opt): return i
    return 0

# 讓使用者選擇欄位
col_atk_name = st.sidebar.selectbox("寶可夢名稱 (攻擊方)", all_columns, index=get_index(all_columns, "寶可夢.1"), key="s1")
col_atk_type = st.sidebar.selectbox("招式屬性", all_columns, index=get_index(all_columns, "屬性.1"), key="s2")
col_atk_dmg = st.sidebar.selectbox("輸出數值 (傷害)", all_columns, index=get_index(all_columns, "輸出"), key="s3")

# 是否有 DPS 欄位？
use_dps = st.sidebar.checkbox("我有 DPS 欄位", value=False)
col_atk_dps = None
if use_dps:
    col_atk_dps = st.sidebar.selectbox("DPS 數值", all_columns, key="s4")

# 即時整理攻擊數據
try:
    cols_to_keep = [col_atk_name, col_atk_type, col_atk_dmg]
    if use_dps and col_atk_dps:
        cols_to_keep.append(col_atk_dps)
    
    # 清洗數據
    df_attackers = df_raw_data[cols_to_keep].dropna().copy()
    
    # 重新命名
    rename_dict = {col_atk_name: '寶可夢', col_atk_type: '招式屬性', col_atk_dmg: '輸出'}
    if use_dps:
        rename_dict[col_atk_dps] = 'DPS'
    
    df_attackers = df_attackers.rename(columns=rename_dict)
    
    # 如果沒有選 DPS，就用輸出簡單算一個參考值，避免程式報錯
    if 'DPS' not in df_attackers.columns:
        df_attackers['DPS'] = df_attackers['輸出'] / 30 
        
except Exception as e:
    st.sidebar.error(f"攻擊數據解析錯誤: {e}")

# --- 設定防守者資料來源 ---
st.sidebar.markdown("---")
st.sidebar.subheader("2. 設定「防守」數據來源")
st.sidebar.caption("因為您的防守表是分開的，請選擇其中一組做為代表，或選擇包含「抗性防禦」的那一欄")

col_def_name = st.sidebar.selectbox("寶可夢名稱 (防守方)", all_columns, index=0, key="d1")
col_def_val = st.sidebar.selectbox("抗性防禦數值", all_columns, index=get_index(all_columns, "抗性防禦"), key="d2")

# 嘗試抓取屬性 (如果沒有就顯示無)
col_def_t1 = st.sidebar.selectbox("防守屬性 1 (選填)", ["(無)"] + all_columns, index=0, key="d3")
col_def_t2 = st.sidebar.selectbox("防守屬性 2 (選填)", ["(無)"] + all_columns, index=0, key="d4")

try:
    cols_def = [col_def_name, col_def_val]
    if col_def_t1 != "(無)": cols_def.append(col_def_t1)
    if col_def_t2 != "(無)": cols_def.append(col_def_t2)
    
    df_defenders = df_raw_data[cols_def].dropna(subset=[col_def_name, col_def_val]).copy()
    
    rename_def = {col_def_name: '寶可夢', col_def_val: '抗性防禦'}
    if col_def_t1 != "(無)": rename_def[col_def_t1] = '屬性一'
    if col_def_t2 != "(無)": rename_def[col_def_t2] = '屬性二'
    
    df_defenders = df_defenders.rename(columns=rename_def)
    
    # 補空值
    if '屬性一' not in df_defenders.columns: df_defenders['屬性一'] = '未知'
    if '屬性二' not in df_defenders.columns: df_defenders['屬性二'] = '無'
    
except Exception as e:
    st.sidebar.error(f"防守數據解析錯誤: {e}")


# ==========================================
# 3. 計算函數
# ==========================================
def get_effectiveness(move_type, def_type1, def_type2):
    try:
        if df_type_chart is None: return 1.0
        # 修正: 確保屬性名稱完全匹配 (去除空白)
        move_type = str(move_type).strip()
        def_type1 = str(def_type1).strip()
        
        mult1 = float(df_type_chart.loc[move_type, def_type1]) if move_type in df_type_chart.index and def_type1 in df_type_chart.columns else 1.0
        
        mult2 = 1.0
        if pd.notna(def_type2) and str(def_type2) != "無":
             dt2 = str(def_type2).strip()
             if dt2 in df_type_chart.columns:
                 mult2 = float(df_type_chart.loc[move_type, dt2])
            
        return mult1 * mult2
    except:
        return 1.0

# ==========================================
# 4. 主畫面顯示
# ==========================================

# 顯示目前的數據樣本，讓使用者確認
with st.expander("🔎 點此檢查目前讀取到的數據是否正確"):
    c1, c2 = st.columns(2)
    with c1:
        st.write("**目前設定的攻擊手資料 (前5筆):**")
        st.dataframe(df_attackers.head())
    with c2:
        st.write("**目前設定的防守者資料 (前5筆):**")
        st.dataframe(df_defenders.head())

tab1, tab2, tab3 = st.tabs(["⚔️ 1. 極巨傷害排名", "🛡️ 2. 抗性防禦排名", "⚡ 3. DPS 排名"])

# --- TAB 1: 傷害計算 ---
with tab1:
    if df_type_chart is not None and not df_attackers.empty:
        st.subheader("傷害計算器")
        c1, c2 = st.columns(2)
        with c1:
            def_t1 = st.selectbox("防守方屬性 1", df_type_chart.columns, key="t1_1")
        with c2:
            options = ["無"] + list(df_type_chart.columns)
            def_t2 = st.selectbox("防守方屬性 2", options, key="t1_2")

        if st.button("計算傷害排名", key="btn1"):
            results = []
            for idx, row in df_attackers.iterrows():
                m_type = row['招式屬性']
                base_dmg = row['輸出']
                multiplier = get_effectiveness(m_type, def_t1, def_t2)
                
                results.append({
                    "寶可夢": row['寶可夢'],
                    "招式屬性": m_type,
                    "屬性倍率": f"x{multiplier:.2f}",
                    "最終傷害": int(base_dmg * multiplier)
                })
            
            final_df = pd.DataFrame(results).sort_values(by="最終傷害", ascending=False)
            st.dataframe(final_df, use_container_width=True)
    else:
        st.warning("⚠️ 請先在左側邊欄設定正確的攻擊數據欄位。")

# --- TAB 2: 抗性排行 ---
with tab2:
    if not df_defenders.empty:
        st.subheader("防守排行")
        target_attr = st.selectbox("選擇要查詢的屬性 (需確認防守表有屬性欄位)", df_type_chart.columns, key="t2_1")
        
        # 篩選
        mask = (df_defenders['屬性一'] == target_attr) | (df_defenders['屬性二'] == target_attr)
        res = df_defenders[mask].sort_values(by="抗性防禦", ascending=False)
        st.dataframe(res, use_container_width=True)
    else:
        st.warning("⚠️ 請先在左側邊欄設定正確的防守數據欄位。")

# --- TAB 3: DPS ---
with tab3:
    if not df_attackers.empty:
        st.subheader("DPS 計算器")
        c1, c2 = st.columns(2)
        with c1:
            def_dps_t1 = st.selectbox("防守方屬性 1", df_type_chart.columns, key="t3_1")
        with c2:
            options_dps = ["無"] + list(df_type_chart.columns)
            def_dps_t2 = st.selectbox("防守方屬性 2", options_dps, key="t3_2")

        if st.button("計算 DPS 排名", key="btn3"):
            dps_results = []
            for idx, row in df_attackers.iterrows():
                m_type = row['招式屬性']
                base_dps = row['DPS']
                multiplier = get_effectiveness(m_type, def_dps_t1, def_dps_t2)
                
                dps_results.append({
                    "寶可夢": row['寶可夢'],
                    "招式屬性": m_type,
                    "屬性倍率": f"x{multiplier:.2f}",
                    "最終 DPS": round(base_dps * multiplier, 2)
                })
            
            final_dps_df = pd.DataFrame(dps_results).sort_values(by="最終 DPS", ascending=False)
            st.dataframe(final_dps_df, use_container_width=True)