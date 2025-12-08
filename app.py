import streamlit as st
import pandas as pd
import os

# ==========================================
# 1. 設定與讀取 Excel
# ==========================================
st.set_page_config(page_title="寶可夢極巨數據庫", layout="wide")
st.title("寶可夢極巨戰鬥計算機")

# ★★★ 設定您的 Excel 檔名 ★★★
excel_file = "Pokemon.xlsx"

# 初始化變數
df_type_chart = None
df_attackers = None
df_defenders = None

# 定義分頁名稱 (必須跟您 Excel 下方的分頁名稱一模一樣)
SHEET_TYPE = "屬性克制表"
SHEET_DATA = "攻守數據"

try:
    # 檢查檔案是否存在
    if not os.path.exists(excel_file):
        st.error(f"❌ 找不到檔案：{excel_file}")
        st.warning("👉 請確認您已將 '能量點.xlsx' 改名為 'Pokemon.xlsx' 並放在同一個資料夾。")
        st.stop()

    # --- A. 讀取屬性克制表 ---
    try:
        # index_col=0 代表第一欄是標題
        df_type_chart = pd.read_excel(excel_file, sheet_name=SHEET_TYPE, index_col=0)
    except ValueError:
        st.error(f"❌ 找不到分頁：'{SHEET_TYPE}'。請確認 Excel 內的分頁名稱是否正確。")
        st.stop()

    # --- B. 讀取攻守數據 ---
    try:
        df_data = pd.read_excel(excel_file, sheet_name=SHEET_DATA)
    except ValueError:
        st.error(f"❌ 找不到分頁：'{SHEET_DATA}'。請確認 Excel 內的分頁名稱是否正確。")
        st.stop()
    
    # --- C. 資料整理 (欄位對應) ---
    # 1. 整理攻擊手 (尋找關鍵欄位)
    # 我們嘗試用關鍵字搜尋欄位，避免名稱有些微差異
    cols = df_data.columns
    
    # 找攻擊手欄位 (通常包含 '寶可夢' 和 '輸出')
    # 這裡假設右邊那區的寶可夢欄位可能叫 '寶可夢.1' 或是重複的名稱
    col_atk_name = '寶可夢.1' if '寶可夢.1' in cols else '寶可夢'
    col_atk_dmg = '輸出'
    col_atk_type = '屬性.1' if '屬性.1' in cols else '屬性'

    if col_atk_dmg in cols:
        df_attackers = df_data[[col_atk_name, col_atk_type, col_atk_dmg]].dropna()
        df_attackers.columns = ['寶可夢', '招式屬性', '輸出']
        # 自動計算 DPS (假設攻速或簡單除法，此處僅為排名參考)
        df_attackers['DPS'] = df_attackers['輸出'] / 30 
    else:
        st.warning(f"⚠️ 找不到 '輸出' 欄位。")
        df_attackers = pd.DataFrame()

    # 2. 整理防守者 (需有: 抗性防禦)
    if '抗性防禦' in cols:
        # 這裡需要注意：前面的 '寶可夢' 欄位可能是左邊那區的
        col_def_name = '寶可夢' 
        df_defenders = df_data[[col_def_name, '屬性一', '屬性二', '抗性防禦']].dropna(subset=[col_def_name])
    else:
        st.warning("⚠️ 找不到 '抗性防禦' 欄位。")
        df_defenders = pd.DataFrame()

except Exception as e:
    st.error(f"❌ 讀取 Excel 發生錯誤：{e}")
    st.info("💡 提示：請確認您的 requirements.txt 裡面有包含 'openpyxl'")
    st.stop()

# ==========================================
# 2. 定義計算函數
# ==========================================
def get_effectiveness(move_type, def_type1, def_type2):
    try:
        if df_type_chart is None or move_type not in df_type_chart.index:
            return 1.0
        
        mult1 = 1.0
        if def_type1 in df_type_chart.columns:
            mult1 = float(df_type_chart.loc[move_type, def_type1])
        
        mult2 = 1.0
        # 判斷屬性2是否存在且有效
        if pd.notna(def_type2) and def_type2 != "無" and def_type2 in df_type_chart.columns:
            mult2 = float(df_type_chart.loc[move_type, def_type2])
            
        return mult1 * mult2
    except:
        return 1.0 

# ==========================================
# 3. 建立 APP 介面
# ==========================================
tab1, tab2, tab3 = st.tabs(["⚔️ 1. 極巨傷害排名", "🛡️ 2. 抗性防禦排名", "⚡ 3. DPS 排名"])

# 分頁 1
with tab1:
    st.subheader("針對「防守方」計算最大單發傷害")
    if df_type_chart is not None and not df_attackers.empty:
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
                final_dmg = base_dmg * multiplier
                results.append({
                    "寶可夢": row['寶可夢'],
                    "招式屬性": m_type,
                    "屬性倍率": f"x{multiplier:.2f}",
                    "最終傷害": int(final_dmg)
                })
            res_df = pd.DataFrame(results).sort_values(by="最終傷害", ascending=False)
            st.dataframe(res_df, use_container_width=True)
    else:
        st.info("資料載入中...")

# 分頁 2
with tab2:
    st.subheader("查詢特定屬性的寶可夢抗性排行")
    if df_type_chart is not None and not df_defenders.empty:
        target_attr = st.selectbox("選擇要查詢的屬性", df_type_chart.columns, key="t2_1")
        mask = (df_defenders['屬性一'] == target_attr) | (df_defenders['屬性二'] == target_attr)
        filtered_def = df_defenders[mask].copy().sort_values(by="抗性防禦", ascending=False)
        st.write(f"屬性包含「{target_attr}」的寶可夢排名：")
        st.dataframe(filtered_def[['寶可夢', '屬性一', '屬性二', '抗性防禦']], use_container_width=True)

# 分頁 3
with tab3:
    st.subheader("針對「防守方」計算最高 DPS")
    if df_type_chart is not None and not df_attackers.empty:
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
                final_dps = base_dps * multiplier
                dps_results.append({
                    "寶可夢": row['寶可夢'],
                    "招式屬性": m_type,
                    "屬性倍率": f"x{multiplier:.2f}",
                    "最終 DPS": round(final_dps, 2)
                })
            res_dps_df = pd.DataFrame(dps_results).sort_values(by="最終 DPS", ascending=False)
            st.dataframe(res_dps_df, use_container_width=True)