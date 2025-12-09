import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="寶可夢數據庫", layout="wide")
st.title("寶可夢戰鬥計算機")

# ==========================================
# 樣式設定函式 (字體加大至 28px、靠左對齊)
# ==========================================
def apply_style(df, float_cols=None):
    # 設定內容樣式
    properties = {
        'text-align': 'left',  
        'font-size': '28px',   # ★★★ 修改處：加大字體到 28px ★★★
        'padding': '12px 10px' # 增加一點內距讓表格不要太擠
    }
    styler = df.style.set_properties(**properties)
    
    # 設定表頭(標題)樣式
    styler = styler.set_table_styles([
        {'selector': 'th', 'props': [('text-align', 'left'), ('font-size', '28px'), ('padding-left', '10px')]}
    ])
    
    # 數值格式化
    if float_cols:
        for col, fmt in float_cols.items():
            if col in df.columns:
                styler = styler.format({col: fmt})     
    return styler

# ==========================================
# 讀取與切割資料
# ==========================================
def load_data_and_chart(filename):
    if not os.path.exists(filename):
        return None, None, f"❌ 找不到檔案：{filename}"

    try:
        df_raw = pd.read_excel(filename, header=None)
        
        split_col_idx = -1
        chart_header_row = 0
        for r in range(min(5, len(df_raw))):
            for c in range(len(df_raw.columns)):
                val = str(df_raw.iloc[r, c]).strip()
                if val == "攻/守" or (val == "一般" and c > 2):
                    split_col_idx = c
                    chart_header_row = r
                    break
            if split_col_idx != -1: break
        
        if split_col_idx == -1:
            return None, None, "⚠️ 無法自動偵測「屬性克制表」位置"

        df_data = pd.read_excel(filename, header=chart_header_row, usecols=range(0, split_col_idx))
        df_data = df_data.dropna(how='all')
        
        df_chart = pd.read_excel(filename, header=chart_header_row, usecols=range(split_col_idx, df_raw.shape[1]))
        df_chart = df_chart.set_index(df_chart.columns[0])
        
        return df_data, df_chart, None

    except Exception as e:
        return None, None, f"讀取錯誤: {str(e)}"

def get_multiplier(chart, atk_type, def_type1, def_type2=None):
    try:
        atk, d1 = str(atk_type).strip(), str(def_type1).strip()
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
tab1, tab2, tab3 = st.tabs(["🔥 1. 極巨攻擊輸出", "🛡️ 2. 極巨抗性防禦", "⚔️ 3. DPS計算"])

# -------------------------------------------------------------------------
# 功能 1：Att.xlsx
# -------------------------------------------------------------------------
with tab1:
    st.header("極巨對戰輸出計算")
    df_att, chart_att, err = load_data_and_chart("Att.xlsx")

    if err:
        st.error(err)
    elif df_att is not None:
        c1, c2 = st.columns(2)
        with c1:
            types = list(chart_att.columns)
            def_t1 = st.selectbox("防守方屬性 1", types, key="att_t1")
        with c2:
            def_t2 = st.selectbox("防守方屬性 2", ["無"] + types, key="att_t2")

        if st.button("計算輸出", key="btn_att"):
            df_att.columns = df_att.columns.str.strip()
            results = []
            
            try:
                for idx, row in df_att.iterrows():
                    name = row.get('寶可夢') or row.iloc[0]
                    atk_type = row.get('屬性')
                    stab = str(row.get('屬修', 'N')).upper()
                    base_atk = row.get('基礎攻擊', 0)
                    g_mode = str(row.get('超級巨/極巨', 'D')).upper()

                    if pd.isna(base_atk): continue

                    stab_bonus = 1.2 if 'Y' in stab else 1.0
                    move_power = 450 if 'G' in g_mode else 350
                    mult = get_multiplier(chart_att, atk_type, def_t1, def_t2)
                    final_dmg = base_atk * stab_bonus * move_power * mult
                    
                    results.append({
                        "寶可夢": name,
                        "屬性": atk_type,
                        "輸出": int(final_dmg)
                    })
                
                res_df = pd.DataFrame(results).sort_values(by="輸出", ascending=False)
                # 套用樣式 (大字體)
                styled_df = apply_style(res_df)
                st.dataframe(styled_df, use_container_width=True, hide_index=True)
                
            except Exception as e:
                st.error(f"計算錯誤: {e}")

# -------------------------------------------------------------------------
# 功能 2：Def.xlsx
# -------------------------------------------------------------------------
with tab2:
    st.header("極巨對戰防禦計算")
    df_def, chart_def, err = load_data_and_chart("Def.xlsx")

    if err:
        st.error(err)
    elif df_def is not None:
        atk_types = list(chart_def.index)
        user_atk = st.selectbox("對手 (攻擊方) 屬性", atk_types, key="def_atk")

        if st.button("計算防禦", key="btn_def"):
            df_def.columns = df_def.columns.str.strip()
            results = []
            
            try:
                for idx, row in df_def.iterrows():
                    name = row.get('寶可夢') or row.iloc[0]
                    my_t1 = row.get('屬性1') or row.get('屬性')
                    my_t2 = row.get('屬性2')
                    base_def = row.get('防禦', 0)
                    
                    if pd.isna(base_def): continue

                    dmg_mult = get_multiplier(chart_def, user_atk, my_t1, my_t2)
                    
                    if dmg_mult == 0:
                        final_def = 999999.9 
                    else:
                        final_def = base_def / dmg_mult

                    results.append({
                        "寶可夢": name,
                        "自身屬性": f"{my_t1}" + (f"/{my_t2}" if pd.notna(my_t2) and my_t2 != "無" else ""),
                        "防禦": final_def
                    })
                
                res_df = pd.DataFrame(results).sort_values(by="防禦", ascending=False)
                res_df = res_df[["寶可夢", "自身屬性", "防禦"]]
                # 套用樣式 (大字體)
                styled_df = apply_style(res_df, float_cols={'防禦': '{:.1f}'})
                st.dataframe(styled_df, use_container_width=True, hide_index=True)

            except Exception as e:
                st.error(f"計算錯誤: {e}")

# -------------------------------------------------------------------------
# 功能 3：DPS.xlsx (修改處：欄位順序調換、字體加大)
# -------------------------------------------------------------------------
with tab3:
    st.header("DPS 計算")
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
                    atk_type = row.get('屬性') or row.get('招式屬性')
                    if not atk_type:
                        for col in row.index:
                            if str(row[col]) in chart_dps.index:
                                atk_type = row[col]; break
                    
                    base_dps = row.get('DPS') or row.get('基礎DPS')
                    if pd.isna(base_dps) or not atk_type: continue
                    
                    mult = get_multiplier(chart_dps, atk_type, dps_t1, dps_t2)
                    final_dps = base_dps * mult
                    
                    results.append({
                        "寶可夢": name,
                        "屬性": atk_type,
                        "倍率": f"x{round(mult, 3)}", 
                        "DPS": final_dps
                    })
                
                res_df = pd.DataFrame(results).sort_values(by="DPS", ascending=False)
                
                # -------------------------------------------
                # ★★★ 修改處：重新排列欄位順序 ★★★
                # 順序變更為：屬性 -> 倍率 -> DPS -> 寶可夢
                # -------------------------------------------
                res_df = res_df[["屬性", "倍率", "DPS", "寶可夢"]]
                
                # 套用樣式 (大字體)
                styled_df = apply_style(res_df, float_cols={'DPS': '{:.2f}'})
                st.dataframe(styled_df, use_container_width=True, hide_index=True)
                
            except Exception as e:
                st.error(f"計算錯誤: {e}")