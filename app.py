#Mega快龍=Mega嚕嚕米
import streamlit as st
import pandas as pd
import os
import time

st.set_page_config(page_title="Pokémon GO攻守數據", layout="wide")
st.title("Pokémon GO攻防計算")

# ==========================================
# 側邊欄：檔案管理與上傳
# ==========================================
st.sidebar.header("📁 資料來源管理")
st.sidebar.info("如果您修改了 Excel 但網頁沒變，請直接在這裡上傳剛改好的檔案！")

# 建立上傳器
uploaded_att = st.sidebar.file_uploader("上傳 Att.xlsx (攻擊)", type=['xlsx'])
uploaded_def = st.sidebar.file_uploader("上傳 Def.xlsx (防禦)", type=['xlsx'])
uploaded_dps = st.sidebar.file_uploader("上傳 DPS.xlsx (DPS)", type=['xlsx'])

st.sidebar.markdown("---")
st.sidebar.caption("目前檔案狀態：")

def get_file_info(uploaded_file, local_filename):
    """判斷是使用上傳檔案還是本地檔案，並回傳訊息與檔案物件"""
    if uploaded_file is not None:
        return uploaded_file, f"🟢 使用上傳的 {local_filename}"
    elif os.path.exists(local_filename):
        mod_time = os.path.getmtime(local_filename)
        time_str = time.strftime('%H:%M:%S', time.localtime(mod_time))
        return local_filename, f"🟠 本地檔 ({time_str} 更新)"
    else:
        return None, f"❌ 找不到 {local_filename}"

# 取得最終要讀取的檔案來源
file_att, msg_att = get_file_info(uploaded_att, "Att.xlsx")
file_def, msg_def = get_file_info(uploaded_def, "Def.xlsx")
file_dps, msg_dps = get_file_info(uploaded_dps, "DPS.xlsx")

# 顯示狀態在側邊欄
st.sidebar.text(msg_att)
st.sidebar.text(msg_def)
st.sidebar.text(msg_dps)

if st.sidebar.button("🔄 強制重新整理頁面"):
    st.cache_data.clear()
    st.rerun()

# ==========================================
# 樣式設定
# ==========================================
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
# 資料讀取函數
# ==========================================
def load_data_and_chart(file_obj):
    if file_obj is None:
        return None, None, "❌ 未提供檔案"

    try:
        # 讀取 Excel (支援上傳物件或路徑字串)
        df_raw = pd.read_excel(file_obj, header=None, engine='openpyxl')
        
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
            return None, None, "⚠️ 無法偵測屬性表位置"

        # 重新讀取資料部分
        # 為了避免指針問題，如果傳入的是 UploadedFile，要 seek(0) 或是直接用 raw data 切割
        # 簡單作法：直接用剛剛讀進來的 df_raw 做切割，不再 read_excel 兩次
        
        # 設定欄位名稱
        df_raw.columns = df_raw.iloc[chart_header_row]
        
        # 切割 DataFrames
        df_data = df_raw.iloc[chart_header_row+1:, :split_col_idx].copy()
        df_chart = df_raw.iloc[chart_header_row+1:, split_col_idx:].copy()
        
        # 清理資料
        df_data = df_data.dropna(how='all')
        
        # 清理圖表
        if not df_chart.empty:
            df_chart = df_chart.set_index(df_chart.columns[0])
            df_chart = df_chart.dropna(how='all')
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
# 讀取資料 (使用側邊欄決定的來源)
# ==========================================
data_att, chart_att, err_att = load_data_and_chart(file_att)
data_def, chart_def, err_def = load_data_and_chart(file_def)
data_dps, chart_dps, err_dps = load_data_and_chart(file_dps)

# ==========================================
# 介面分頁
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["🔥 1. 極巨攻擊輸出", "🛡️ 2. 極巨對戰防禦", "⚔️ 3. DPS計算", "📊 4. 屬性克制表"])

# -------------------------------------------------------------------------
# Tab 1: Att
# -------------------------------------------------------------------------
with tab1:
    st.header("極巨對戰輸出計算")
    if err_att:
        st.error(f"檔案讀取失敗: {err_att}")
    elif data_att is not None:
        c1, c2 = st.columns(2)
        with c1:
            types = list(chart_att.columns)
            def_t1 = st.selectbox("對手(防守方)屬性 1", types, key="att_t1")
        with c2:
            def_t2 = st.selectbox("對手(防守方)屬性 2", ["無"] + types, key="att_t2")

        data_att.columns = data_att.columns.str.strip()
        results = []
        try:
            for idx, row in data_att.iterrows():
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
                
                results.append({"寶可夢": name, "屬性": atk_type, "輸出": int(final_dmg)})
            
            res_df = pd.DataFrame(results).sort_values(by="輸出", ascending=False)
            if not res_df.empty:
                max_dmg = res_df["輸出"].max()
                res_df["強度%"] = (res_df["輸出"] / max_dmg * 100) if max_dmg > 0 else 0.0

            st.dataframe(apply_style(res_df, float_cols={'強度%': '{:.1f}%'}), use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"計算錯誤: {e}")

# -------------------------------------------------------------------------
# Tab 2: Def
# -------------------------------------------------------------------------
with tab2:
    st.header("極巨對戰防禦計算")
    if err_def:
        st.error(f"檔案讀取失敗: {err_def}")
    elif data_def is not None:
        atk_types = list(chart_def.index)
        valid_atk_types = [t for t in atk_types if pd.notna(t) and str(t).strip() not in ["", "nan", "攻/守"]]
        user_atk = st.selectbox("對手 (攻擊方) 屬性", valid_atk_types, key="def_atk")

        data_def.columns = data_def.columns.str.strip()
        results = []
        try:
            for idx, row in data_def.iterrows():
                name = row.get('寶可夢') or row.iloc[0]
                my_t1 = row.get('屬性1') or row.get('屬性') or row.get('屬性一')
                my_t2 = row.get('屬性2') or row.get('屬性二')
                base_def = row.get('基礎防禦') or row.get('防禦', 0)
                
                if pd.isna(base_def): continue
                dmg_mult = get_multiplier(chart_def, user_atk, my_t1, my_t2)
                
                if dmg_mult == 0:
                    final_def = 999.9; dmg_mult_str = "免疫 (x0)"
                else:
                    final_def = base_def / dmg_mult; dmg_mult_str = f"x{round(dmg_mult, 2)}"

                results.append({
                    "寶可夢": name,
                    "自身屬性": f"{my_t1}" + (f"/{my_t2}" if pd.notna(my_t2) and str(my_t2) != "無" else ""),
                    "承受倍率": dmg_mult_str,
                    "坦度": final_def
                })
            
            res_df = pd.DataFrame(results).sort_values(by="坦度", ascending=False)
            res_df = res_df[["寶可夢", "自身屬性", "承受倍率", "坦度"]]
            st.dataframe(apply_style(res_df, float_cols={'坦度': '{:.1f}'}), use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"計算錯誤: {e}")

# -------------------------------------------------------------------------
# Tab 3: DPS
# -------------------------------------------------------------------------
with tab3:
    st.header("DPS計算")
    if err_dps:
        st.error(f"檔案讀取失敗: {err_dps}")
    elif data_dps is not None:
        c1, c2 = st.columns(2)
        with c1:
            types = list(chart_dps.columns)
            dps_t1 = st.selectbox("對手(防守方)屬性 1", types, key="dps_t1")
        with c2:
            dps_t2 = st.selectbox("對手(防守方)屬性 2", ["無"] + types, key="dps_t2")

        data_dps.columns = data_dps.columns.str.strip()
        results = []
        try:
            for idx, row in data_dps.iterrows():
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
                results.append({"寶可夢": name, "屬性": atk_type, "DPS": final_dps})
            
            res_df = pd.DataFrame(results).sort_values(by="DPS", ascending=False)
            res_df = res_df[["寶可夢", "屬性", "DPS"]]
            st.dataframe(apply_style(res_df, float_cols={'DPS': '{:.2f}'}), use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"計算錯誤: {e}")

# -------------------------------------------------------------------------
# Tab 4: 克制表
# -------------------------------------------------------------------------
with tab4:
    st.header("屬性克制表")
    if os.path.exists("chart.png"):
        st.image("chart.png", caption="屬性克制表", use_container_width=True)
    elif os.path.exists("chart.jpg"):
        st.image("chart.jpg", caption="屬性克制表", use_container_width=True)
    
    st.divider() 
    st.subheader("屬性弱點計算器")
    if chart_dps is not None:
        c1, c2 = st.columns(2)
        with c1:
            types = list(chart_dps.columns)
            chart_t1 = st.selectbox("防守方屬性 1", types, key="chart_t1")
        with c2:
            chart_t2 = st.selectbox("防守方屬性 2", ["無"] + types, key="chart_t2")
            
        chart_results = []
        for atk_type in chart_dps.index:
            if pd.isna(atk_type): continue
            atk_str = str(atk_type).strip()
            if atk_str in ["", "nan", "攻/守", "無", "DPS", "寶可夢"]: continue
            
            mult = get_multiplier(chart_dps, atk_type, chart_t1, chart_t2)
            chart_results.append({"屬性": atk_str, "倍率": f"x{round(mult, 3)}", "數值倍率": mult})
        
        res_chart = pd.DataFrame(chart_results).sort_values(by="數值倍率", ascending=False)
        res_chart = res_chart[["屬性", "倍率"]] 
        st.dataframe(apply_style(res_chart), use_container_width=True, hide_index=True)
    else:
        st.error("無法讀取屬性克制表，請來信eltons0803@gmail.com")