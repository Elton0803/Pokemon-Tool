import streamlit as st
import pandas as pd
import os
import time

# 設定網頁標題與佈局 (initial_sidebar_state="collapsed" 預設收起側邊欄)
st.set_page_config(page_title="Pokémon GO攻守數據", layout="wide", initial_sidebar_state="collapsed")
st.title("Pokémon GO攻防計算")

# ==========================================
# 頂部：檔案管理 (取代原本的側邊欄)
# ==========================================
with st.expander("📁 資料來源管理 (點擊展開/收合)", expanded=False):
    st.info("若檔案有更新，請直接在此上傳新檔。")
    
    # 使用 4 欄排列上傳按鈕，節省空間
    uc1, uc2, uc3, uc4 = st.columns(4)
    with uc1: uploaded_att = st.file_uploader("上傳 Att.xlsx (攻擊)", type=['xlsx'])
    with uc2: uploaded_def = st.file_uploader("上傳 Def.xlsx (防禦)", type=['xlsx'])
    with uc3: uploaded_dps = st.file_uploader("上傳 DPS.xlsx (DPS)", type=['xlsx'])
    with uc4: uploaded_list = st.file_uploader("上傳 list.xlsx (搜尋清單)", type=['xlsx'])

    # 檔案狀態顯示
    def get_file_info(uploaded_file, local_filename):
        """判斷是使用上傳檔案還是本地檔案，並回傳物件與訊息"""
        if uploaded_file is not None:
            return uploaded_file, f"🟢 使用上傳的 {local_filename}"
        elif os.path.exists(local_filename):
            mod_time = os.path.getmtime(local_filename)
            time_str = time.strftime('%H:%M:%S', time.localtime(mod_time))
            return local_filename, f"🟠 本地檔 ({time_str})"
        else:
            return None, f"❌ 找不到 {local_filename}"

    file_att, msg_att = get_file_info(uploaded_att, "Att.xlsx")
    file_def, msg_def = get_file_info(uploaded_def, "Def.xlsx")
    file_dps, msg_dps = get_file_info(uploaded_dps, "DPS.xlsx")
    file_list, msg_list = get_file_info(uploaded_list, "list.xlsx")
    
    # 顯示狀態文字
    st.caption(f"{msg_att} | {msg_def} | {msg_dps} | {msg_list}")

    if st.button("🔄 清除快取並重整"):
        st.cache_data.clear()
        st.rerun()

# ==========================================
# 輔助函數：樣式與計算
# ==========================================
def apply_style(df, float_cols=None):
    properties = {'text-align': 'left', 'font-size': '28px', 'padding': '12px 10px'}
    styler = df.style.set_properties(**properties)
    styler = styler.set_table_styles([{'selector': 'th', 'props': [('text-align', 'left'), ('font-size', '28px'), ('padding-left', '10px')]}])
    if float_cols:
        for col, fmt in float_cols.items():
            if col in df.columns: styler = styler.format({col: fmt})      
    return styler

def load_data_and_chart(file_obj):
    """讀取複雜格式 (左資料、右圖表) 的 Excel"""
    if file_obj is None: return None, None, "❌ 未提供檔案"
    try:
        df_raw = pd.read_excel(file_obj, header=None, engine='openpyxl')
        split_col_idx = -1; chart_header_row = 0
        
        # 自動偵測分割點
        for r in range(min(5, len(df_raw))):
            for c in range(len(df_raw.columns)):
                val = str(df_raw.iloc[r, c]).strip()
                if val == "攻/守" or (val == "一般" and c > 2):
                    split_col_idx = c; chart_header_row = r; break
            if split_col_idx != -1: break
        
        if split_col_idx == -1: return None, None, "⚠️ 無法偵測屬性表位置"

        df_raw.columns = df_raw.iloc[chart_header_row]
        df_data = df_raw.iloc[chart_header_row+1:, :split_col_idx].copy().dropna(how='all')
        df_chart = df_raw.iloc[chart_header_row+1:, split_col_idx:].copy()
        
        if not df_chart.empty:
            df_chart = df_chart.set_index(df_chart.columns[0]).dropna(how='all')
            df_chart = df_chart[~df_chart.index.duplicated(keep='first')] # 去除重複索引
        return df_data, df_chart, None
    except Exception as e: return None, None, f"讀取錯誤: {str(e)}"

def load_simple_list(file_obj):
    """讀取簡單格式 (清單) 的 Excel"""
    if file_obj is None: return None, "❌ 未提供檔案"
    try:
        df = pd.read_excel(file_obj, engine='openpyxl')
        df.columns = df.columns.str.strip()
        df = df.dropna(how='all')
        return df, None
    except Exception as e: return None, f"讀取錯誤: {str(e)}"

def get_multiplier(chart, atk_type, def_type1, def_type2=None):
    """查詢屬性倍率"""
    try:
        atk = str(atk_type).strip(); d1 = str(def_type1).strip()
        if not atk or atk == "nan" or not d1 or d1 == "nan" or atk not in chart.index: return 1.0
        
        mult1 = float(chart.loc[atk, d1]) if d1 in chart.columns else 1.0
        mult2 = 1.0
        if def_type2 and str(def_type2) not in ["無", "nan", "None"]:
            d2 = str(def_type2).strip()
            if d2 in chart.columns: mult2 = float(chart.loc[atk, d2])
        return mult1 * mult2
    except: return 1.0

# ==========================================
# 程式啟動：讀取所有資料
# ==========================================
data_att, chart_att, err_att = load_data_and_chart(file_att)
data_def, chart_def, err_def = load_data_and_chart(file_def)
data_dps, chart_dps, err_dps = load_data_and_chart(file_dps)
data_list, err_list = load_simple_list(file_list)

# ==========================================
# 介面分頁
# ==========================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔥 1. 極巨攻擊", 
    "🛡️ 2. 極巨防禦", 
    "⚔️ 3. DPS計算", 
    "📊 4. 屬性克制", 
    "🔍 5. 團體戰打手查詢"
])

# -------------------------------------------------------------------------
# Tab 1: Att
# -------------------------------------------------------------------------
with tab1:
    st.header("極巨對戰輸出計算")
    if err_att: st.error(err_att)
    elif data_att is not None:
        c1, c2 = st.columns(2)
        with c1: def_t1 = st.selectbox("對手屬性 1", list(chart_att.columns), key="att_t1")
        with c2: def_t2 = st.selectbox("對手屬性 2", ["無"] + list(chart_att.columns), key="att_t2")
        
        data_att.columns = data_att.columns.str.strip()
        results = []
        try:
            for _, row in data_att.iterrows():
                name = row.get('寶可夢') or row.iloc[0]
                atk_t, base_atk = row.get('屬性'), row.get('基礎攻擊', 0)
                if pd.isna(base_atk): continue
                
                stab_bonus = 1.2 if 'Y' in str(row.get('屬修', 'N')).upper() else 1.0
                move_p = 450 if 'G' in str(row.get('超級巨/極巨', 'D')).upper() else 350
                mult = get_multiplier(chart_att, atk_t, def_t1, def_t2)
                
                results.append({
                    "寶可夢": name, "屬性": atk_t, 
                    "輸出": int(base_atk * stab_bonus * move_p * mult)
                })
            
            res_df = pd.DataFrame(results).sort_values("輸出", ascending=False)
            if not res_df.empty:
                res_df["強度%"] = (res_df["輸出"] / res_df["輸出"].max() * 100) if res_df["輸出"].max() > 0 else 0
            
            st.dataframe(apply_style(res_df, {'強度%': '{:.1f}%'}), use_container_width=True, hide_index=True)
        except Exception as e: st.error(f"計算錯誤: {e}")

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
# Tab 3: DPS
# -------------------------------------------------------------------------
with tab3:
    st.header("DPS計算 (自選屬性)")
    if err_dps: st.error(err_dps)
    elif data_dps is not None:
        c1, c2 = st.columns(2)
        with c1: dps_t1 = st.selectbox("對手屬性 1", list(chart_dps.columns), key="dps_t1")
        with c2: dps_t2 = st.selectbox("對手屬性 2", ["無"] + list(chart_dps.columns), key="dps_t2")
        
        data_dps.columns = data_dps.columns.str.strip()
        results = []
        try:
            for _, row in data_dps.iterrows():
                name = row.get('寶可夢') or row.iloc[0]
                atk_t = row.get('屬性') or row.get('招式屬性')
                if not atk_t: 
                    for col in row.index: 
                        if str(row[col]) in chart_dps.index: atk_t = row[col]; break
                
                base_dps = row.get('DPS') or row.get('基礎DPS')
                if pd.notna(base_dps) and atk_t:
                    mult = get_multiplier(chart_dps, atk_t, dps_t1, dps_t2)
                    results.append({"寶可夢": name, "屬性": atk_t, "DPS": base_dps * mult})
            
            res_df = pd.DataFrame(results).sort_values("DPS", ascending=False)
            st.dataframe(apply_style(res_df, {'DPS': '{:.2f}'}), use_container_width=True, hide_index=True)
        except Exception as e: st.error(f"計算錯誤: {e}")

# -------------------------------------------------------------------------
# Tab 4: Chart
# -------------------------------------------------------------------------
with tab4:
    st.header("屬性克制表")
    if os.path.exists("chart.png"): st.image("chart.png", use_container_width=True)
    elif os.path.exists("chart.jpg"): st.image("chart.jpg", use_container_width=True)
    
    st.divider(); st.subheader("屬性弱點計算器")
    if chart_dps is not None:
        c1, c2 = st.columns(2)
        with c1: chart_t1 = st.selectbox("防守屬性 1", list(chart_dps.columns), key="c_t1")
        with c2: chart_t2 = st.selectbox("防守屬性 2", ["無"] + list(chart_dps.columns), key="c_t2")
        
        chart_res = []
        for atk_t in chart_dps.index:
            if pd.isna(atk_t) or str(atk_t).strip() in ["","nan","攻/守"]: continue
            mult = get_multiplier(chart_dps, atk_t, chart_t1, chart_t2)
            chart_res.append({"屬性": str(atk_t), "倍率": f"x{round(mult, 3)}", "v": mult})
            
        res_df = pd.DataFrame(chart_res).sort_values("v", ascending=False)[["屬性","倍率"]]
        st.dataframe(apply_style(res_df), use_container_width=True, hide_index=True)

# -------------------------------------------------------------------------
# Tab 5: Search & DPS (極速優化版)
# -------------------------------------------------------------------------
with tab5:
    st.header("團體戰輸出排行")
    
    if err_list: st.error(f"無法讀取 list.xlsx: {err_list}")
    elif data_list is not None:
        col_name, col_t1, col_t2 = None, None, None
        for col in data_list.columns:
            if "名" in col: col_name = col
            elif "屬性" in col and ("1" in col or "一" in col): col_t1 = col
            elif "屬性" in col and ("2" in col or "二" in col): col_t2 = col
            
        if col_name and col_t1:
            poke_list = data_list[col_name].astype(str).unique().tolist()
            
            with st.container():
                target_poke = st.selectbox(
                    "請選擇對手寶可夢：", 
                    options=poke_list,
                    index=None, 
                    placeholder="請輸入寶可夢",
                )
            
            if target_poke:
                row = data_list[data_list[col_name] == target_poke].iloc[0]
                t1 = str(row[col_t1]).strip()
                t2 = str(row[col_t2]).strip() if col_t2 and pd.notna(row[col_t2]) else "無"
                if t2 == "nan": t2 = "無"
                
                c1, c2 = st.columns(2)
                with c1: st.info(f"對手屬性 1： **{t1}**")
                with c2: st.info(f"對手屬性 2： **{t2}**")
                
                if data_dps is not None and chart_dps is not None:
                    try:
                        # 優化版 DPS 計算
                        type_mult_map = {}
                        valid_types = [t for t in chart_dps.index if pd.notna(t) and str(t).strip() not in ["","nan","攻/守"]]
                        for atk_t in valid_types:
                            type_mult_map[str(atk_t)] = get_multiplier(chart_dps, atk_t, t1, t2)
                        
                        dps_df_calc = data_dps.copy()
                        type_col = None
                        possible_cols = ['屬性', '招式屬性', 'Type', 'Move Type']
                        for c in possible_cols:
                            if c in dps_df_calc.columns: type_col = c; break
                        
                        if type_col is None:
                            def find_type_in_row(r):
                                for c in r.index:
                                    if str(r[c]) in type_mult_map: return str(r[c])
                                return None
                            dps_df_calc['__CalcType__'] = dps_df_calc.apply(find_type_in_row, axis=1)
                            type_col = '__CalcType__'
                        
                        dps_df_calc['__Mult__'] = dps_df_calc[type_col].astype(str).map(type_mult_map).fillna(1.0)
                        dps_val_col = 'DPS' if 'DPS' in dps_df_calc.columns else ('基礎DPS' if '基礎DPS' in dps_df_calc.columns else None)
                        
                        if dps_val_col:
                            dps_df_calc['對戰DPS'] = dps_df_calc[dps_val_col] * dps_df_calc['__Mult__']
                            name_col = '寶可夢' if '寶可夢' in dps_df_calc.columns else dps_df_calc.columns[0]
                            final_show = dps_df_calc[[name_col, type_col, '對戰DPS', '__Mult__']].copy()
                            final_show.columns = ['寶可夢', '屬性', 'DPS', '倍率']
                            final_show = final_show.sort_values("DPS", ascending=False).head(50)
                            
                            st.subheader(f"⚔️ 針對「{target_poke}」的打手排行 ")
                            final_show['倍率'] = final_show['倍率'].apply(lambda x: f"x{round(x, 2)}")
                            st.dataframe(apply_style(final_show, {'DPS': '{:.2f}'}), use_container_width=True, hide_index=True)
                        else:
                            st.error("找不到 DPS 數值欄位")
                    except Exception as e:
                        st.error(f"DPS 計算發生錯誤: {e}")
                else:
                    st.warning("⚠️ 缺少 DPS.xlsx 或屬性表，無法計算。")
        else:
            st.error("list.xlsx 格式錯誤，找不到名稱或屬性欄位")