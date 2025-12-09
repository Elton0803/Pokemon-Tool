import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="寶可夢數據計算機 (三合一版)", layout="wide")
st.title("寶可夢數據計算機 📊")
st.caption("支援 Att.xlsx, Def.xlsx, DPS.xlsx 獨立運算")

# ==========================================
# 共用函數：讀取屬性克制表 (Type Chart)
# ==========================================
def load_type_chart(df, sheet_name):
    """
    嘗試從 Dataframe 中尋找屬性克制表矩陣。
    通常特徵是：第一列或某列包含 '一般', '火', '水'...
    """
    try:
        # 尋找包含 "一般" 的那一列作為標題列 (Header)
        # 我們掃描前 10 列
        header_idx = -1
        for i, row in df.head(10).iterrows():
            # 轉成字串並檢查是否包含關鍵屬性
            row_str = row.astype(str).values
            if "一般" in row_str and "火" in row_str:
                header_idx = i
                break
        
        if header_idx != -1:
            # 重讀一次，以這一列為 header
            # 注意：這裡假設克制表在右側，我們需要把這一列當成 columns
            # 簡單起見，我們直接切分 DataFrame
            
            # 抓取該列作為欄位名稱
            new_columns = df.iloc[header_idx]
            # 建立新的 DF，從下一列開始
            chart_df = df.iloc[header_idx+1:].copy()
            chart_df.columns = new_columns
            
            # 設定 Index：通常第一欄是攻擊方屬性
            # 我們尋找欄位名稱是 "攻/守" 或 "屬性" 或 NaN 的第一欄
            # 這裡假設克制表的 Index 在該區域的第一欄
            
            # 嘗試找到 "一般" 所在的欄位索引，從那裡開始切
            start_col = -1
            for idx, col in enumerate(chart_df.columns):
                if str(col).strip() == "一般":
                    start_col = idx
                    break
            
            if start_col > 0:
                # 設定索引為 "一般" 前面的那一欄 (通常是攻擊方屬性)
                chart_df = chart_df.set_index(chart_df.columns[start_col-1])
                # 只保留屬性欄位
                valid_types = ["一般", "火", "水", "草", "電", "冰", "格鬥", "毒", "地面", "飛行", "超能力", "蟲", "岩石", "幽靈", "龍", "惡", "鋼", "妖精"]
                # 過濾欄位
                cols_to_keep = [c for c in chart_df.columns if str(c).strip() in valid_types]
                chart_df = chart_df[cols_to_keep]
                
                # 轉成數字，非數字補 1.0
                chart_df = chart_df.apply(pd.to_numeric, errors='coerce').fillna(1.0)
                return chart_df
                
    except Exception as e:
        st.error(f"解析屬性表失敗: {e}")
    
    return None

def get_multiplier(chart, atk_type, def_type1, def_type2):
    if chart is None: return 1.0
    atk = str(atk_type).strip()
    mult = 1.0
    
    # 對第一屬性
    if atk in chart.index and def_type1 in chart.columns:
        mult *= chart.loc[atk, def_type1]
    
    # 對第二屬性
    if pd.notna(def_type2) and def_type2 in chart.columns and def_type2 != "無":
        mult *= chart.loc[atk, def_type2]
        
    return mult

# ==========================================
# 介面分頁
# ==========================================
tab1, tab2, tab3 = st.tabs(["⚔️ 1. 攻擊計算 (Att)", "🛡️ 2. 防禦計算 (Def)", "⚡ 3. DPS 計算 (DPS)"])

# ==========================================
# 功能 1：Att.xlsx
# ==========================================
with tab1:
    st.header("1. 攻擊輸出計算")
    file_att = "Att.xlsx"
    
    if os.path.exists(file_att):
        try:
            # 讀取整個表
            df_att_raw = pd.read_excel(file_att, header=None) # 先不設 header，手動抓
            
            # 解析屬性表 (從右邊抓)
            chart_att = load_type_chart(df_att_raw, "Att")
            
            if chart_att is not None:
                # 介面：選擇防守方屬性
                c1, c2 = st.columns(2)
                types = list(chart_att.columns)
                def1 = c1.selectbox("防守屬性 1", types, key="att_d1")
                def2 = c2.selectbox("防守屬性 2", ["無"] + types, key="att_d2")
                
                # 側邊欄設定：攻擊數據欄位
                st.sidebar.markdown("---")
                st.sidebar.subheader("⚔️ Att.xlsx 欄位設定")
                
                # 嘗試讀取資料部分 (假設在左邊)
                # 我們讓使用者指定 Header 所在的列 (通常是第1列)
                header_row = st.sidebar.number_input("Att 資料標題在第幾列? (0表示第一列)", min_value=0, value=0, key="att_h_row")
                df_att_data = pd.read_excel(file_att, header=header_row)
                cols = list(df_att_data.columns)
                
                col_name = st.sidebar.selectbox("寶可夢名稱", cols, index=0 if len(cols)>0 else 0, key="att_c1")
                col_type = st.sidebar.selectbox("屬性", cols, index=1 if len(cols)>1 else 0, key="att_c2")
                col_stab = st.sidebar.selectbox("屬修 (Y/N)", cols, index=2 if len(cols)>2 else 0, key="att_c3")
                col_base = st.sidebar.selectbox("基礎攻擊", cols, index=3 if len(cols)>3 else 0, key="att_c4")
                col_giga = st.sidebar.selectbox("超級巨/極巨 (G/D)", cols, index=4 if len(cols)>4 else 0, key="att_c5")
                
                if st.button("計算攻擊輸出", key="btn_att"):
                    results = []
                    # 清洗數據
                    clean_data = df_att_data[[col_name, col_type, col_stab, col_base, col_giga]].dropna()
                    
                    for idx, row in clean_data.iterrows():
                        p_name = row[col_name]
                        p_type = row[col_type]
                        p_stab = str(row[col_stab]).strip().upper()
                        p_base = float(row[col_base]) if pd.notna(row[col_base]) else 0
                        p_giga = str(row[col_giga]).strip().upper()
                        
                        # 公式：基礎攻擊 * 屬修 * 極巨倍率 * 克制倍率
                        
                        # 1. 屬修
                        mult_stab = 1.2 if p_stab == 'Y' else 1.0
                        
                        # 2. 極巨倍率
                        mult_giga = 1.0
                        if 'G' in p_giga: mult_giga = 450
                        elif 'D' in p_giga: mult_giga = 350
                        else: mult_giga = 350 # 預設
                        
                        # 3. 克制倍率
                        mult_type = get_multiplier(chart_att, p_type, def1, def2)
                        
                        final_dmg = p_base * mult_stab * mult_giga * mult_type
                        
                        results.append({
                            "寶可夢": p_name,
                            "屬性": p_type,
                            "基礎": p_base,
                            "屬修": p_stab,
                            "極巨": p_giga,
                            "克制": f"x{mult_type:.2f}",
                            "輸出": int(final_dmg)
                        })
                    
                    res_df = pd.DataFrame(results).sort_values(by="輸出", ascending=False)
                    st.dataframe(res_df[[ "寶可夢", "屬性", "輸出", "克制", "基礎", "屬修", "極巨"]], use_container_width=True)
            else:
                st.error("無法在 Att.xlsx 中找到屬性克制表，請確認格式。")
        except Exception as e:
            st.error(f"讀取 Att.xlsx 錯誤: {e}")
    else:
        st.warning("找不到 Att.xlsx")

# ==========================================
# 功能 2：Def.xlsx
# ==========================================
with tab2:
    st.header("2. 防禦數值計算")
    file_def = "Def.xlsx"
    
    if os.path.exists(file_def):
        try:
            df_def_raw = pd.read_excel(file_def, header=None)
            chart_def = load_type_chart(df_def_raw, "Def")
            
            if chart_def is not None:
                # 介面：選擇攻擊方屬性
                types = list(chart_def.columns)
                atk_type = st.selectbox("攻擊方屬性", types, key="def_a1")
                
                # 側邊欄設定
                st.sidebar.markdown("---")
                st.sidebar.subheader("🛡️ Def.xlsx 欄位設定")
                header_row_def = st.sidebar.number_input("Def 資料標題在第幾列?", min_value=0, value=0, key="def_h_row")
                df_def_data = pd.read_excel(file_def, header=header_row_def)
                cols = list(df_def_data.columns)
                
                col_d_name = st.sidebar.selectbox("寶可夢名稱", cols, index=0, key="def_c1")
                col_d_t1 = st.sidebar.selectbox("屬性1", cols, index=1 if len(cols)>1 else 0, key="def_c2")
                col_d_t2 = st.sidebar.selectbox("屬性2", cols, index=2 if len(cols)>2 else 0, key="def_c3")
                col_d_val = st.sidebar.selectbox("防禦數值", cols, index=3 if len(cols)>3 else 0, key="def_c4")
                
                if st.button("計算防禦", key="btn_def"):
                    results = []
                    clean_data = df_def_data[[col_d_name, col_d_t1, col_d_val]].dropna() # t2 可空
                    
                    for idx, row in clean_data.iterrows():
                        p_name = row[col_d_name]
                        p_t1 = row[col_d_t1]
                        p_t2 = df_def_data.loc[idx, col_d_t2] # 獨立抓避免 dropna 掉單屬性
                        p_val = float(row[col_d_val])
                        
                        # 公式：防禦 * 屬性克制表的值
                        # 注意：這裡是指「攻擊方 vs 該寶可夢」的倍率
                        
                        # 查表: 攻擊方 vs 屬性1
                        m1 = 1.0
                        if atk_type in chart_def.index and p_t1 in chart_def.columns:
                            m1 = chart_def.loc[atk_type, p_t1]
                            
                        # 查表: 攻擊方 vs 屬性2
                        m2 = 1.0
                        if pd.notna(p_t2) and p_t2 in chart_def.columns and p_t2 != "無":
                            m2 = chart_def.loc[atk_type, p_t2]
                        
                        total_mult = m1 * m2
                        final_def = p_val * total_mult
                        
                        results.append({
                            "寶可夢": p_name,
                            "屬性1": p_t1,
                            "屬性2": p_t2 if pd.notna(p_t2) else "無",
                            "原始防禦": p_val,
                            "克制倍率": f"x{total_mult:.2f}",
                            "防禦": final_def # 根據您的公式 (防禦 * 克制值)
                        })
                        
                    res_df = pd.DataFrame(results).sort_values(by="防禦", ascending=False)
                    st.dataframe(res_df[["寶可夢", "防禦", "屬性1", "屬性2", "原始防禦", "克制倍率"]], use_container_width=True)
            else:
                st.error("無法在 Def.xlsx 中找到屬性克制表。")
        except Exception as e:
            st.error(f"讀取 Def.xlsx 錯誤: {e}")
    else:
        st.warning("找不到 Def.xlsx")

# ==========================================
# 功能 3：DPS.xlsx
# ==========================================
with tab3:
    st.header("3. DPS 計算")
    file_dps = "DPS.xlsx"
    
    if os.path.exists(file_dps):
        try:
            df_dps_raw = pd.read_excel(file_dps, header=None)
            chart_dps = load_type_chart(df_dps_raw, "DPS")
            
            if chart_dps is not None:
                c1, c2 = st.columns(2)
                types = list(chart_dps.columns)
                def1 = c1.selectbox("防守屬性 1", types, key="dps_d1")
                def2 = c2.selectbox("防守屬性 2", ["無"] + types, key="dps_d2")
                
                # 側邊欄
                st.sidebar.markdown("---")
                st.sidebar.subheader("⚡ DPS.xlsx 欄位設定")
                header_row_dps = st.sidebar.number_input("DPS 資料標題在第幾列?", min_value=0, value=0, key="dps_h_row")
                df_dps_data = pd.read_excel(file_dps, header=header_row_dps)
                cols = list(df_dps_data.columns)
                
                col_dps_name = st.sidebar.selectbox("寶可夢名稱", cols, index=0, key="dps_c1")
                col_dps_type = st.sidebar.selectbox("屬性", cols, index=1 if len(cols)>1 else 0, key="dps_c2")
                col_dps_val = st.sidebar.selectbox("DPS 數值", cols, index=2 if len(cols)>2 else 0, key="dps_c3")
                
                if st.button("計算 DPS", key="btn_dps"):
                    results = []
                    clean_data = df_dps_data[[col_dps_name, col_dps_type, col_dps_val]].dropna()
                    
                    for idx, row in clean_data.iterrows():
                        p_name = row[col_dps_name]
                        p_type = row[col_dps_type]
                        p_dps = float(row[col_dps_val])
                        
                        # 公式：DPS * 屬性克制表的值
                        mult = get_multiplier(chart_dps, p_type, def1, def2)
                        final_dps = p_dps * mult
                        
                        results.append({
                            "寶可夢": p_name,
                            "屬性": p_type,
                            "原始DPS": p_dps,
                            "克制倍率": f"x{mult:.2f}",
                            "DPS": final_dps
                        })
                    
                    res_df = pd.DataFrame(results).sort_values(by="DPS", ascending=False)
                    st.dataframe(res_df[["寶可夢", "屬性", "DPS", "原始DPS", "克制倍率"]], use_container_width=True)
            else:
                st.error("無法在 DPS.xlsx 中找到屬性克制表。")
        except Exception as e:
            st.error(f"讀取 DPS.xlsx 錯誤: {e}")
    else:
        st.warning("找不到 DPS.xlsx")