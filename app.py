import streamlit as st
import pandas as pd
import os

# ==========================================
# 1. 設定與讀取 Excel
# ==========================================
st.set_page_config(page_title="寶可夢極巨數據庫", layout="wide")
st.title("寶可夢極巨戰鬥計算機")

# 檔名設定
excel_file = "Pokemon.xlsx"
SHEET_TYPE = "屬性克制表"
SHEET_DATA = "攻守數據"

# 初始化
df_type_chart = None
df_attackers = None
df_defenders = None

try:
    # --- 檢查檔案 ---
    if not os.path.exists(excel_file):
        st.error(f"❌ 找不到檔案：{excel_file}")
        st.stop()

    # --- A. 讀取屬性克制表 ---
    try:
        df_type_chart = pd.read_excel(excel_file, sheet_name=SHEET_TYPE, index_col=0)
    except:
        st.error(f"❌ 讀取 '{SHEET_TYPE}' 分頁失敗。")
        st.stop()

    # --- B. 讀取攻守數據 (關鍵修改處) ---
    try:
        # ★★★ 修正：header=1 代表讀取 Excel 的「第二行」作為標題 ★★★
        df_data = pd.read_excel(excel_file, sheet_name=SHEET_DATA, header=1)
        
        # 清除欄位名稱的多餘空白
        df_data.columns = df_data.columns.str.strip()
        
    except:
        st.error(f"❌ 讀取 '{SHEET_DATA}' 分頁失敗。")
        st.stop()
    
    # --- C. 智能抓取資料 (解決欄位找不到的問題) ---
    
    # 1. 抓取攻擊手資料
    # 邏輯：只要該行有「輸出」數值，就是攻擊手資料
    if '輸出' in df_data.columns:
        # 找出跟「輸出」同一組的「寶可夢」和「屬性」
        # 通常 Pandas 會把重複的欄位命名為 寶可夢, 寶可夢.1, 寶可夢.2
        # 我們直接透過欄位位置來抓比較保險
        
        # 找到 '輸出' 這一欄的位置索引
        out_col_idx = df_data.columns.get_loc('輸出')
        
        # 假設結構是：寶可夢(idx-5) ... 屬性(idx-4) ... 輸出(idx)
        # 根據您的檔案結構，往左推算
        # 讓我們嘗試用欄位名稱抓取最靠近的屬性與寶可夢
        
        # 建立一個暫存表，只保留有「輸出」的列
        temp_atk = df_data[df_data['輸出'].notna()].copy()
        
        # 嘗試抓取對應欄位 (這裡使用您的檔案常見結構)
        # 如果 '屬性' 欄位有重複，Pandas 會命名為 '屬性', '屬性.1'
        col_atk = '寶可夢.1' if '寶可夢.1' in df_data.columns else '寶可夢'
        col_type = '屬性.1' if '屬性.1' in df_data.columns else '屬性'
        
        # 如果找不到 .1，就試試看直接找名稱
        if col_atk not in df_data.columns: 
             # 備案：直接用 iloc 抓取 '輸出' 左邊的欄位
             # 這是一個猜測，但通常有效
             col_atk = df_data.columns[out_col_idx - 5] # 往左5格通常是名稱
        
        try:
            df_attackers = temp_atk[[col_atk, col_type, '輸出']].copy()
            df_attackers.columns = ['寶可夢', '招式屬性', '輸出']
            df_attackers['DPS'] = df_attackers['輸出'] / 30 # 預設 DPS
        except:
            st.warning("⚠️ 雖然找到了 '輸出'，但在對應寶可夢名稱時遇到困難。")
            df_attackers = pd.DataFrame()
    else:
        st.error("❌ 依然找不到 '輸出' 欄位。請確認 Excel '攻守數據' 分頁的第二列是否有 '輸出' 這個詞。")
        st.write("目前讀到的欄位有：", list(df_data.columns)) # 顯示除錯資訊
        df_attackers = pd.DataFrame()

    # 2. 抓取防守者資料
    # 邏輯：只要該行有「抗性防禦」數值
    if '抗性防禦' in df_data.columns:
        temp_def = df_data[df_data['抗性防禦'].notna()].copy()
        
        # 防守者的寶可夢名稱通常在抗性防禦的左邊
        def_col_idx = df_data.columns.get_loc('抗性防禦')
        col_def_name = df_data.columns[def_col_idx - 1] # 往左1格是寶可夢
        
        # 屬性通常在更左邊，或者這張表可能沒有屬性欄位？
        # 根據您的截圖，防守排行似乎是單獨的表
        # 我們先只抓名稱和數值，屬性用 '屬性克制表' 來反查，或是抓左邊的欄位
        
        try:
            # 嘗試抓取屬性，若無則顯示 N/A
            cols_to_fetch = [col_def_name, '抗性防禦']
            if '屬性一' in df_data.columns: cols_to_fetch.append('屬性一')
            if '屬性二' in df_data.columns: cols_to_fetch.append('屬性二')
                
            df_defenders = temp_def[cols_to_fetch].copy()
            
            # 標準化欄位名稱
            rename_dict = {col_def_name: '寶可夢', '抗性防禦': '抗性防禦'}
            if '屬性一' in cols_to_fetch: rename_dict['屬性一'] = '屬性一'
            if '屬性二' in cols_to_fetch: rename_dict['屬性二'] = '屬性二'
            
            df_defenders = df_defenders.rename(columns=rename_dict)
            
            # 補屬性 (如果 Excel 裡防守表沒有屬性欄位)
            if '屬性一' not in df_defenders.columns:
                df_defenders['屬性一'] = '未知'
                df_defenders['屬性二'] = '無'
                
        except Exception as e:
            st.warning(f"⚠️ 抓取防守數據時出錯: {e}")
            df_defenders = pd.DataFrame()
    else:
        st.warning("⚠️ 找不到 '抗性防禦' 欄位。")
        df_defenders = pd.DataFrame()

except Exception as e:
    st.error(f"❌ 發生未預期的錯誤：{e}")
    st.stop()

# ==========================================
# 2. 定義計算函數
# ==========================================
def get_effectiveness(move_type, def_type1, def_type2):
    try:
        if df_type_chart is None or move_type not in df_type_chart.index:
            return 1.0
        mult1 = float(df_type_chart.loc[move_type, def_type1]) if def_type1 in df_type_chart.columns else 1.0
        mult2 = float(df_type_chart.loc[move_type, def_type2]) if pd.notna(def_type2) and def_type2 != "無" and def_type2 in df_type_chart.columns else 1.0
        return mult1 * mult2
    except:
        return 1.0 

# ==========================================
# 3. 建立 APP 介面
# ==========================================
tab1, tab2, tab3 = st.tabs(["⚔️ 1. 極巨傷害排名", "🛡️ 2. 抗性防禦排名", "⚡ 3. DPS 排名"])

# 分頁 1: 傷害計算
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
                results.append({
                    "寶可夢": row['寶可夢'],
                    "招式屬性": m_type,
                    "屬性倍率": f"x{multiplier:.2f}",
                    "最終傷害": int(base_dmg * multiplier)
                })
            st.dataframe(pd.DataFrame(results).sort_values(by="最終傷害", ascending=False), use_container_width=True)
    else:
        st.warning("攻擊數據載入失敗，請檢查 Excel 格式。")

# 分頁 2: 抗性排行
with tab2:
    st.subheader("查詢特定屬性的寶可夢抗性排行")
    if df_type_chart is not None and not df_defenders.empty:
        target_attr = st.selectbox("選擇要查詢的屬性", df_type_chart.columns, key="t2_1")
        
        # 篩選邏輯
        mask = (df_defenders['屬性一'] == target_attr) | (df_defenders['屬性二'] == target_attr)
        res = df_defenders[mask].sort_values(by="抗性防禦", ascending=False)
        
        st.write(f"屬性包含「{target_attr}」的寶可夢排名：")
        st.dataframe(res, use_container_width=True)
    else:
        st.warning("防守數據載入失敗，請檢查 Excel 格式。")

# 分頁 3: DPS
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
                dps_results.append({
                    "寶可夢": row['寶可夢'],
                    "招式屬性": m_type,
                    "屬性倍率": f"x{multiplier:.2f}",
                    "最終 DPS": round(base_dps * multiplier, 2)
                })
            st.dataframe(pd.DataFrame(dps_results).sort_values(by="最終 DPS", ascending=False), use_container_width=True)