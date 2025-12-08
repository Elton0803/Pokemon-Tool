import streamlit as st
import pandas as pd
import os

# ==========================================
# 1. 讀取與設定資料 (這部分一定要在最上面！)
# ==========================================
st.set_page_config(page_title="寶可夢極巨數據庫", layout="wide")
st.title("寶可夢極巨戰鬥計算機")

# 檢查檔案是否存在，避免直接報錯
file_type_chart = "能量點.xlsx - 屬性克制表.csv"
file_data = "能量點.xlsx - 攻守數據.csv"

# 為了防止找不到變數，我們先給它初始值
df_type_chart = None
df_attackers = None
df_defenders = None

try:
    # 步驟 A: 讀取屬性克制表
    if not os.path.exists(file_type_chart):
        st.error(f"❌ 找不到檔案：{file_type_chart}。請確認檔案是否在同一個資料夾內。")
        st.stop() # 強制停止，不讓程式繼續往下跑
    
    # 設定 index_col=0 讓第一欄變成索引 (重要！)
    df_type_chart = pd.read_csv(file_type_chart, index_col=0)

    # 步驟 B: 讀取攻守數據
    if not os.path.exists(file_data):
        st.error(f"❌ 找不到檔案：{file_data}。請確認檔案是否在同一個資料夾內。")
        st.stop()

    df_data = pd.read_csv(file_data)
    
    # 步驟 C: 資料整理 (請確認這裡的欄位名稱跟您的 Excel 一樣)
    # 如果您的 Excel 欄位名稱不同，請修改引號內的文字
    
    # 整理攻擊手: 需有 '寶可夢', '屬性', '輸出'
    # 注意：這裡我用 .iloc 是為了避免欄位名稱打錯，直接抓第幾欄 (比較保險)
    # 假設攻擊手資料在 CSV 的右半邊 (請依實際情況調整)
    # 這裡示範：假設攻擊手名稱在第 10 欄(J欄), 屬性在 11 欄, 輸出在 13 欄 (請根據您的 CSV 調整數字)
    # 比較保險的做法是直接用您的欄位名稱，如下：
    
    # ★★★ 請檢查這裡的欄位名稱是否與 CSV 標題完全一致 ★★★
    # 根據您提供的檔案，攻擊手的欄位可能叫 '寶可夢.1', '屬性.1', '輸出'
    if '寶可夢.1' in df_data.columns:
        df_attackers = df_data[['寶可夢.1', '屬性.1', '輸出']].dropna()
        df_attackers.columns = ['寶可夢', '招式屬性', '輸出']
        # 簡單計算 DPS 作為示範
        df_attackers['DPS'] = df_attackers['輸出'] / 30 
    else:
        st.warning("⚠️ 找不到 '寶可夢.1' 欄位，請檢查 CSV 標題。目前先用假資料避免報錯。")
        # 建立假資料防止報錯
        df_attackers = pd.DataFrame({'寶可夢':['測試怪'], '招式屬性':['火'], '輸出':[100], 'DPS':[10]})

    # 整理防守者: 需有 '寶可夢', '屬性一', '屬性二', '抗性防禦'
    if '抗性防禦' in df_data.columns:
        df_defenders = df_data[['寶可夢', '屬性一', '屬性二', '抗性防禦']].dropna(subset=['寶可夢'])
    else:
        st.warning("⚠️ 找不到 '抗性防禦' 欄位。")
        df_defenders = pd.DataFrame()

except Exception as e:
    st.error(f"❌ 讀取資料發生未知錯誤：{e}")
    st.stop()

# ==========================================
# 2. 定義計算函數
# ==========================================
def get_effectiveness(move_type, def_type1, def_type2):
    """查詢屬性克制表，計算倍率"""
    try:
        # 確保查詢的屬性在表格內
        if move_type not in df_type_chart.index:
            return 1.0
        
        # 查屬性1
        mult1 = 1.0
        if def_type1 in df_type_chart.columns:
            mult1 = float(df_type_chart.loc[move_type, def_type1])
        
        # 查屬性2
        mult2 = 1.0
        if pd.notna(def_type2) and def_type2 != "無" and def_type2 in df_type_chart.columns:
            mult2 = float(df_type_chart.loc[move_type, def_type2])
            
        return mult1 * mult2
    except Exception as e:
        return 1.0 

# ==========================================
# 3. 建立 APP 介面
# ==========================================
tab1, tab2, tab3 = st.tabs(["⚔️ 1. 極巨傷害排名", "🛡️ 2. 抗性防禦排名", "⚡ 3. DPS 排名"])

# --- 功能 1：極巨傷害 (由大到小) ---
with tab1:
    st.subheader("針對「防守方」計算最大單發傷害")
    
    # 確保 df_type_chart 有資料再執行 UI
    if df_type_chart is not None:
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
        st.error("資料未載入，無法顯示選單。")

# --- 功能 2：抗性防禦 (由大到小) ---
with tab2:
    st.subheader("查詢特定屬性的寶可夢抗性排行")
    if df_type_chart is not None and not df_defenders.empty:
        target_attr = st.selectbox("選擇要查詢的屬性", df_type_chart.columns, key="t2_1")
        
        # 篩選
        mask = (df_defenders['屬性一'] == target_attr) | (df_defenders['屬性二'] == target_attr)
        filtered_def = df_defenders[mask].copy()
        filtered_def = filtered_def.sort_values(by="抗性防禦", ascending=False)
        
        st.write(f"屬性包含「{target_attr}」的寶可夢排名：")
        st.dataframe(filtered_def, use_container_width=True)

# --- 功能 3：DPS 排名 (由大到小) ---
with tab3:
    st.subheader("針對「防守方」計算最高 DPS")
    
    if df_type_chart is not None:
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