#Mega快龍=Mega魯魯米
import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Pokémon GO攻守數據", layout="wide")
st.title("Pokémon GO攻防計算")

if st.sidebar.button("🔄 重新讀取 Excel 資料"):
    st.cache_data.clear()
    st.rerun()

def apply_style(df, float_cols=None):
    properties = {
        'text-align': 'left',  
        'font-size': '28px',   
        'padding': '12px 10px' 
    }
    styler = df.style.set_properties(**properties)
    
    styler = styler.set_table_styles([
        {'selector': 'th', 'props': [('text-align', 'left'), ('font-size', '28px'), ('padding-left', '10px')]}
    ])
    
    if float_cols:
        for col, fmt in float_cols.items():
            if col in df.columns:
                styler = styler.format({col: fmt})      
    return styler

# ==========================================
# 資料讀取 (包含去除重複索引修復)
# ==========================================
#@st.cache_data  # 加入快取，讓切換 Tab 時不用重新讀檔，速度更快
def load_data_and_chart(filename):
    if not os.path.exists(filename):
        return None, None, f"❌ 找不到檔案：{filename}"

    try:
        df_raw = pd.read_excel(filename, header=None)
        
        split_col_idx = -1
        chart_header_row = 0
        
        # 自動偵測分割點
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

        # 左邊數據
        df_data = pd.read_excel(filename, header=chart_header_row, usecols=range(0, split_col_idx))
        df_data = df_data.dropna(how='all')

        # 右邊圖表
        df_chart = pd.read_excel(filename, header=chart_header_row, usecols=range(split_col_idx, df_raw.shape[1]))
        df_chart = df_chart.set_index(df_chart.columns[0])
        df_chart = df_chart.dropna(how='all')
        
        # [修復] 去除重複索引，避免 lookup 錯誤
        df_chart = df_chart[~df_chart.index.duplicated(keep='first')]

        return df_data, df_chart, None

    except Exception as e:
        return None, None, f"讀取錯誤: {str(e)}"

def get_multiplier(chart, atk_type, def_type1, def_type2=None):
    try:
        atk = str(atk_type).strip()
        d1 = str(def_type1).strip()
        
        if not atk or atk == "nan": return 1.0
        if not d1 or d1 == "nan": return 1.0
        
        if atk not in chart.index: return 1.0
        
        mult1 = float(chart.loc[atk, d1]) if d1 in chart.columns else 1.0
        
        mult2 = 1.0
        if def_type2 and str(def_type2) not in ["無", "nan", "None"]:
            d2 = str(def_type2).strip()
            if d2 in chart.columns:
                mult2 = float(chart.loc[atk, d2])
                
        return mult1 * mult2
    except Exception:
        return 1.0

# ==========================================
# 介面邏輯
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["🔥 1. 極巨攻擊輸出", "🛡️ 2. 極巨對戰防禦", "⚔️ 3. DPS計算", "📊 4. 屬性克制表"])

# -------------------------------------------------------------------------
# Tab 1: Att.xlsx
# -------------------------------------------------------------------------
with tab1:
    st.header("極巨對戰輸出計算")
    st.caption("數值計算說明：輸出 = 攻擊 * 屬修 * 350(極巨) or 450(超極巨)")
    df_att, chart_att, err = load_data_and_chart("Att.xlsx")

    if err:
        st.error(err)
    elif df_att is not None:
        c1, c2 = st.columns(2)
        with c1:
            types = list(chart_att.columns)
            def_t1 = st.selectbox("對手(防守方)屬性 1", types, key="att_t1")
        with c2:
            def_t2 = st.selectbox("對手(防守方)屬性 2", ["無"] + types, key="att_t2")

        # --- 自動計算區 ---
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
            
            if not res_df.empty:
                max_dmg = res_df["輸出"].max()
                res_df["強度%"] = (res_df["輸出"] / max_dmg * 100) if max_dmg > 0 else 0.0

            styled_df = apply_style(res_df, float_cols={'強度%': '{:.1f}%'})
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
            
        except Exception as e:
            st.error(f"計算錯誤: {e}")

# -------------------------------------------------------------------------
# Tab 2: Def.xlsx (自動更新 + 修正防禦邏輯)
# -------------------------------------------------------------------------
with tab2:
    st.header("極巨對戰防禦計算")
    st.caption("數值計算說明：坦度 = HP * 防禦 / 屬性剋制倍率")
    
    df_def, chart_def, err = load_data_and_chart("Def.xlsx")

    if err:
        st.error(err)
    elif df_def is not None:
        atk_types = list(chart_def.index)
        valid_atk_types = [t for t in atk_types if pd.notna(t) and str(t).strip() not in ["", "nan", "攻/守"]]
        
        user_atk = st.selectbox("對手 (攻擊方) 屬性", valid_atk_types, key="def_atk")

        # --- 自動計算區 ---
        df_def.columns = df_def.columns.str.strip()
        results = []
        
        try:
            for idx, row in df_def.iterrows():
                name = row.get('寶可夢') or row.iloc[0]
                my_t1 = row.get('屬性1') or row.get('屬性') or row.get('屬性一')
                my_t2 = row.get('屬性2') or row.get('屬性二')
                
                base_def = row.get('基礎防禦') or row.get('防禦', 0)
                
                if pd.isna(base_def): continue

                dmg_mult = get_multiplier(chart_def, user_atk, my_t1, my_t2)
                
                if dmg_mult == 0:

                    final_def = 999.9 
                    dmg_mult_str = "免疫 (x0)"
                else:
                    
                    final_def = base_def / dmg_mult
                    dmg_mult_str = f"x{round(dmg_mult, 2)}"

                results.append({
                    "寶可夢": name,
                    "自身屬性": f"{my_t1}" + (f"/{my_t2}" if pd.notna(my_t2) and str(my_t2) != "無" else ""),
                    "承受倍率": dmg_mult_str,
                    "坦度": final_def
                })
            
            res_df = pd.DataFrame(results).sort_values(by="坦度", ascending=False)
            
            res_df = res_df[["寶可夢", "自身屬性", "坦度"]]
            
            styled_df = apply_style(res_df, float_cols={'坦度': '{:.1f}'})
            st.dataframe(styled_df, use_container_width=True, hide_index=True)

        except Exception as e:
            st.error(f"計算錯誤: {e}")

# -------------------------------------------------------------------------
# Tab 3: DPS.xlsx
# -------------------------------------------------------------------------
with tab3:
    st.header("DPS計算")
    df_dps, chart_dps, err = load_data_and_chart("DPS.xlsx")

    if err:
        st.error(err)
    elif df_dps is not None:
        c1, c2 = st.columns(2)
        with c1:
            types = list(chart_dps.columns)
            dps_t1 = st.selectbox("對手(防守方)屬性 1", types, key="dps_t1")
        with c2:
            dps_t2 = st.selectbox("對手(防守方)屬性 2", ["無"] + types, key="dps_t2")

        # --- 自動計算區 ---
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
                    "DPS": final_dps
                })
            
            res_df = pd.DataFrame(results).sort_values(by="DPS", ascending=False)
            res_df = res_df[["寶可夢", "屬性", "DPS"]]
            styled_df = apply_style(res_df, float_cols={'DPS': '{:.2f}'})
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
            
        except Exception as e:
            st.error(f"計算錯誤: {e}")

# -------------------------------------------------------------------------
# Tab 4: 屬性表
# -------------------------------------------------------------------------
with tab4:
    st.header("屬性克制表")

    chart_img_path = "chart.png"
    if os.path.exists(chart_img_path):
        st.image(chart_img_path, caption="屬性克制表", use_container_width=True)
    elif os.path.exists("chart.jpg"):
        st.image("chart.jpg", caption="屬性克制表", use_container_width=True)
    
    st.divider() 
    st.subheader("屬性弱點計算器")

    if 'chart_dps' not in locals() or chart_dps is None:
        _, chart_dps, err = load_data_and_chart("DPS.xlsx")
    
    if chart_dps is not None:
        c1, c2 = st.columns(2)
        with c1:
            types = list(chart_dps.columns)
            chart_t1 = st.selectbox("防守方屬性 1", types, key="chart_t1")
        with c2:
            chart_t2 = st.selectbox("防守方屬性 2", ["無"] + types, key="chart_t2")
            
        # --- 自動計算區 ---
        chart_results = []
        
        for atk_type in chart_dps.index:
            if pd.isna(atk_type): continue
            atk_str = str(atk_type).strip()
            if atk_str in ["", "nan", "攻/守", "無", "DPS", "寶可夢"]: continue
            
            mult = get_multiplier(chart_dps, atk_type, chart_t1, chart_t2)

            chart_results.append({
                "屬性": atk_str,
                "倍率": f"x{round(mult, 3)}", 
                "數值倍率": mult 
            })
        
        res_chart = pd.DataFrame(chart_results).sort_values(by="數值倍率", ascending=False)
        res_chart = res_chart[["屬性", "倍率"]] 
        
        styled_chart = apply_style(res_chart)
        st.dataframe(styled_chart, use_container_width=True, hide_index=True)
    else:
        st.error("無法讀取屬性克制表")