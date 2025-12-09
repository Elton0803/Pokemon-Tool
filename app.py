import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="寶可夢極巨數據庫 (三檔版)", layout="wide")
st.title("寶可夢極巨戰鬥計算機")

# ==========================================
# 共用工具函數：切割數據與克制表
# ==========================================
def load_data_and_chart(filename):
    """
    讀取 Excel，自動將左邊的「數據區」和右邊的「屬性克制表」切分開來。
    回傳: (df_data, df_chart)
    """
    if not os.path.exists(filename):
        return None, None, f"❌ 找不到檔案：{filename}"

    try:
        # 1. 先讀取整張表 (假設 headers 在第一列或第二列)
        # 我們讀取前幾列來判斷哪裡是「攻/守」克制表的開始
        df_raw = pd.read_excel(filename, header=None)
        
        # 2. 尋找克制表的切分點
        # 邏輯：尋找包含 "攻/守" 或 "一般" (屬性開頭) 的欄位
        split_col_idx = -1
        chart_header_row = 0
        
        for r in range(min(5, len(df_raw))): # 掃描前5列
            for c in range(len(df_raw.columns)):
                val = str(df_raw.iloc[r, c]).strip()
                if val == "攻/守" or (val == "一般" and c > 2): # 簡單判斷
                    split_col_idx = c
                    chart_header_row = r
                    break
            if split_col_idx != -1:
                break
        
        if split_col_idx == -1:
            return None, None, "⚠️ 無法自動偵測「屬性克制表」的位置 (找不到 '攻/守' 關鍵字)"

        # 3. 切分資料
        # 左邊是數據 (Data)
        df_data = pd.read_excel(filename, header=chart_header_row, usecols=range(0, split_col_idx))
        df_data = df_data.dropna(how='all') # 刪除全空列

        # 右邊是克制表 (Chart)
        # 讀取從 split_col_idx 開始的所有欄位
        df_chart = pd.read_excel(filename, header=chart_header_row, usecols=range(split_col_idx, df_raw.shape[1]))
        df_chart = df_chart.set_index(df_chart.columns[0]) # 第一欄設為 Index (攻擊方屬性)
        
        return df_data, df_chart, None

    except Exception as e:
        return None, None, f"讀取錯誤: {str(e)}"

# 計算倍率函數
def get_multiplier(chart, atk_type, def_type1, def_type2=None):
    try:
        atk = str(atk_type).strip()
        d1 = str(def_type1).strip()
        
        if atk not in chart.index: return 1.0
        
        mult1 = float(chart.loc[atk, d1]) if d1 in chart.columns else 1.0
        mult2 = 1.0
        
        if def_type2 and str(def_type2) != "無":
            d2 = str(def_type2).strip()
            if d2 in chart.columns:
                mult2 = float(chart.loc[atk, d2])
                
        return mult1 * mult2
    except:
        return 1.0

# ==========================================
# APP 介面
# ==========================================
tab1, tab2, tab3 = st.tabs(["🔥 1. 攻擊輸出 (Att.xlsx)", "🛡️ 2. 防禦抗性 (Def.xlsx)", "⚔️ 3. DPS 計算 (DPS.xlsx)"])

# -------------------------------------------------------------------------
# 功能 1：使用 Att.xlsx
# 算法 = 基礎攻擊 * (屬修Y=1.2) * (極巨G=450, D=350) * 克制倍率
# -------------------------------------------------------------------------
with tab1:
    st.header("攻擊輸出計算機")
    df_att, chart_att, err = load_data_and_chart("Att.xlsx")

    if err:
        st.error(err)
    elif df_att is not None:
        # 介面
        c1, c2 = st.columns(2)
        with c1:
            # 取得防守屬性列表
            types = list(chart_att.columns)
            def_t1 = st.selectbox("防守方屬性 1", types, key="att_t1")
        with c2:
            def_t2 = st.selectbox("防守方屬性 2", ["無"] + types, key="att_t2")

        if st.button("計算輸出", key="btn_att"):
            # 準備欄位 (自動去除空白)
            df_att.columns = df_att.columns.str.strip()
            
            results = []
            
            # 確保欄位存在
            req_cols = ['寶可夢', '屬性', '屬修', '基礎攻擊', '超級巨/極巨']
            # 模糊搜尋欄位名稱 (避免 '寶可夢 ' 多空白)
            col_map = {k: k for k in df_att.columns} 
            
            try:
                for idx, row in df_att.iterrows():
                    # 讀取數值
                    name = row.get('寶可夢') or row.get(df_att.columns[0]) # 備用抓第一欄
                    atk_type = row.get('屬性')
                    stab_flag = str(row.get('屬修', 'N')).upper()
                    base_atk = row.get('基礎攻擊', 0)
                    g_mode = str(row.get('超級巨/極巨', 'D')).upper()

                    if pd.isna(base_atk): continue

                    # 1. 屬修加成
                    stab_bonus = 1.2 if 'Y' in stab_flag else 1.0
                    
                    # 2. 招式威力加成
                    move_power = 450 if 'G' in g_mode else 350
                    
                    # 3. 屬性克制倍率 (攻擊方=自身屬性, 防守方=使用者選擇)
                    type_mult = get_multiplier(chart_att, atk_type, def_t1, def_t2)
                    
                    # 4. 最終計算
                    final_dmg = base_atk * stab_bonus * move_power * type_mult
                    
                    results.append({
                        "寶可夢": name,
                        "屬性": atk_type,
                        "輸出": int(final_dmg),
                        "倍率": f"x{type_mult}"
                    })
                
                # 顯示結果
                res_df = pd.DataFrame(results).sort_values(by="輸出", ascending=False)
                st.dataframe(res_df, use_container_width=True)
                
            except Exception as e:
                st.error(f"計算過程發生錯誤，請檢查 Excel 欄位名稱是否正確: {e}")
                st.write("讀到的欄位:", list(df_att.columns))

# -------------------------------------------------------------------------
# 功能 2：使用 Def.xlsx
# 算法 = 防禦 / 屬性克制表的值
# -------------------------------------------------------------------------
with tab2:
    st.header("防禦抗性計算機")
    df_def, chart_def, err = load_data_and_chart("Def.xlsx")

    if err:
        st.error(err)
    elif df_def is not None:
        # 介面
        # 這次使用者是「攻擊方」，要選擇一個攻擊屬性
        # chart_def 的 index 應該是攻擊屬性
        atk_types = list(chart_def.index)
        user_atk = st.selectbox("對手 (攻擊方) 屬性", atk_types, key="def_atk")

        if st.button("計算防禦", key="btn_def"):
            df_def.columns = df_def.columns.str.strip()
            results = []
            
            try:
                for idx, row in df_def.iterrows():
                    # 欄位抓取
                    name = row.get('寶可夢') or row.iloc[0]
                    # 嘗試抓取屬性，若沒有則設為無
                    my_t1 = row.get('屬性1') or row.get('屬性')
                    my_t2 = row.get('屬性2')
                    base_def = row.get('防禦', 0)
                    
                    if pd.isna(base_def): continue

                    # 計算受傷倍率
                    # 這裡要查：攻擊方=user_atk, 防守方=my_t1 & my_t2
                    dmg_mult = get_multiplier(chart_def, user_atk, my_t1, my_t2)
                    
                    # 避免除以 0 (若免疫，倍率為 0，防禦趨近無限大)
                    if dmg_mult == 0:
                        final_def = 999999 # 代表無敵
                        desc = "免疫 (∞)"
                    else:
                        final_def = base_def / dmg_mult
                        desc = int(final_def)

                    results.append({
                        "寶可夢": name,
                        "自身屬性": f"{my_t1}" + (f"/{my_t2}" if pd.notna(my_t2) and my_t2 != "無" else ""),
                        "承受倍率": f"x{dmg_mult}",
                        "有效防禦": final_def, # 用於排序
                        "防禦 (顯示)": desc
                    })
                
                # 顯示結果 (由大排到小)
                res_df = pd.DataFrame(results).sort_values(by="有效防禦", ascending=False)
                # 整理顯示欄位
                st.dataframe(res_df[["寶可夢", "防禦 (顯示)", "自身屬性", "承受倍率"]], use_container_width=True)

            except Exception as e:
                st.error(f"計算錯誤: {e}")

# -------------------------------------------------------------------------
# 功能 3：使用 DPS.xlsx
# 算法 = DPS * 屬性克制表的值
# -------------------------------------------------------------------------
with tab3:
    st.header("DPS 輸出計算機")
    df_dps, chart_dps, err = load_data_and_chart("DPS.xlsx")

    if err:
        st.error(err)
    elif df_dps is not None:
        c1, c2 = st.columns(2)
        with c1:
            types = list(chart_dps.columns)
            dps_t1 = st.selectbox("防守方屬性 1", types, key="dps_t1")
        with c2:
            dps_t2 = st.selectbox("防守方屬性 2", ["無"] + types, key="dps_t2")

        if st.button("計算 DPS", key="btn_dps"):
            df_dps.columns = df_dps.columns.str.strip()
            results = []
            
            try:
                for idx, row in df_dps.iterrows():
                    name = row.get('寶可夢') or row.iloc[0]
                    # 需要找到自身的攻擊屬性
                    # 嘗試找 '屬性' 欄位，若無則嘗試找 '招式屬性'
                    atk_type = row.get('屬性') or row.get('招式屬性')
                    
                    # 如果真的找不到屬性欄位，嘗試用列表推導式找一定是屬性的欄位
                    if not atk_type:
                        for col in row.index:
                            if str(row[col]) in chart_dps.index:
                                atk_type = row[col]
                                break
                    
                    base_dps = row.get('DPS') or row.get('基礎DPS')
                    
                    if pd.isna(base_dps) or not atk_type: continue
                    
                    # 計算倍率
                    mult = get_multiplier(chart_dps, atk_type, dps_t1, dps_t2)
                    final_dps = base_dps * mult
                    
                    results.append({
                        "寶可夢": name,
                        "屬性": atk_type,
                        "DPS": round(final_dps, 2),
                        "倍率": f"x{mult}"
                    })
                
                res_df = pd.DataFrame(results).sort_values(by="DPS", ascending=False)
                st.dataframe(res_df, use_container_width=True)
                
            except Exception as e:
                st.error(f"計算錯誤: {e}")
                st.write("目前讀到的欄位:", list(df_dps.columns))