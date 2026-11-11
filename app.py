#Mega快龍=Mega魯魯米
from base64 import b64encode
from io import BytesIO
from pathlib import Path

import streamlit as st
import pandas as pd
from PIL import Image

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
ICON_DIR = APP_DIR / "icons"

# 設定網頁標題與佈局
st.set_page_config(page_title="Pokémon GO攻守數據", layout="wide", initial_sidebar_state="collapsed")
st.title("Pokémon GO攻守數據")

# ==========================================
# 天氣加成設定字典
# ==========================================
weather_boost = {
    "無": [],
    "晴朗": ["草", "火", "地面"],
    "雨天": ["水", "電", "蟲"],
    "多雲": ["一般", "岩石"],
    "陰天": ["妖精", "格鬥", "毒"],
    "強風": ["飛行", "龍", "超能力"],
    "下雪": ["冰", "鋼"],
    "起霧": ["惡", "幽靈"]
}

def get_weather_mult(atk_type, weather):
    """判斷該屬性在當下天氣是否有 1.2 倍加成"""
    if not atk_type or pd.isna(atk_type): return 1.0
    if str(atk_type).strip() in weather_boost.get(weather, []):
        return 1.2
    return 1.0

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

def clean_columns(df):
    """清除 DataFrame 中重複或無效的欄位名稱"""
    df.columns = [str(c).strip() if pd.notna(c) else f"未命名_{i}" for i, c in enumerate(df.columns)]
    return df.loc[:, ~df.columns.duplicated()].copy()

def load_data_and_chart(filename):
    path = DATA_DIR / filename
    if not path.is_file():
        return None, None, f"❌ 找不到檔案: data/{filename}"
    try:
        df_raw = pd.read_excel(path, header=None, engine='openpyxl')
        split_col_idx = -1; chart_header_row = 0
        for r in range(min(5, len(df_raw))):
            for c in range(len(df_raw.columns)):
                val = str(df_raw.iloc[r, c]).strip()
                if val == "攻/守" or (val == "一般" and c > 2):
                    split_col_idx = c; chart_header_row = r; break
            if split_col_idx != -1: break
        
        if split_col_idx == -1: return None, None, "⚠️ 無法偵測屬性表位置"

        df_raw.columns = df_raw.iloc[chart_header_row]
        df_raw = clean_columns(df_raw) # 過濾重複欄位
        
        df_data = df_raw.iloc[chart_header_row+1:, :split_col_idx].copy().dropna(how='all')
        df_chart = df_raw.iloc[chart_header_row+1:, split_col_idx:].copy()
        
        if not df_chart.empty:
            df_chart = df_chart.set_index(df_chart.columns[0]).dropna(how='all')
            df_chart = df_chart[~df_chart.index.duplicated(keep='first')]
        return df_data, df_chart, None
    except Exception as e: return None, None, f"讀取錯誤: {str(e)}"

def load_simple_list(filename):
    path = DATA_DIR / filename
    if not path.is_file():
        return None, f"❌ 找不到檔案: data/{filename}"
    try:
        df = pd.read_excel(path, engine='openpyxl')
        df = clean_columns(df)
        df = df.dropna(how='all')
        return df, None
    except Exception as e: return None, f"讀取錯誤: {str(e)}"

def get_multiplier(chart, atk_type, def_type1, def_type2=None):
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
# 程式啟動：讀取資料
# ==========================================
data_att, chart_att, err_att = load_data_and_chart("Att.xlsx")
data_def, chart_def, err_def = load_data_and_chart("Def.xlsx")
data_dps, chart_dps, err_dps = load_data_and_chart("DPS.xlsx")
data_list, err_list = load_simple_list("list.xlsx")

def apply_target_types(prefix, target_types):
    types = target_types.get(st.session_state[f"{prefix}_target"])
    if types is not None:
        st.session_state[f"{prefix}_t1"], st.session_state[f"{prefix}_t2"] = types


def clear_target(prefix):
    st.session_state[f"{prefix}_target"] = None


# ==========================================
# 全域 UI：天氣設定 (放置於分頁右上角)
# ==========================================
c_empty, c_weather = st.columns([5, 1])
with c_weather:
    current_weather = st.selectbox(
        "🌤️ 天氣加成", 
        ["無", "晴朗", "雨天", "多雲", "陰天", "強風", "下雪", "起霧"],
        index=0
    )

# ==========================================
# 介面分頁
# ==========================================
@st.cache_data(show_spinner=False)
def tab_label(label, icon_filename, *, trim_padding=False):
    try:
        with Image.open(ICON_DIR / icon_filename) as icon:
            thumbnail = icon.convert("RGBA")
            if trim_padding:
                alpha = thumbnail.getchannel("A")
                bounds = alpha.point(lambda value: 255 if value > 32 else 0).getbbox()
                if bounds:
                    left, top, right, bottom = bounds
                    margin = round(max(right - left, bottom - top) * 0.05)
                    thumbnail = thumbnail.crop(
                        (left - margin, top - margin, right + margin, bottom + margin)
                    )
            thumbnail.thumbnail((48, 48), Image.Resampling.LANCZOS)
            buffer = BytesIO()
            thumbnail.save(buffer, format="PNG")
    except OSError:
        return label

    encoded_icon = b64encode(buffer.getvalue()).decode("ascii")
    return f"![](data:image/png;base64,{encoded_icon}) {label}"


st.html("""
<style>
[data-testid="stTabs"] [role="tab"] [data-testid="stMarkdownContainer"] > p {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    font-size: 0.875rem;
}
[data-testid="stTabs"] [role="tab"] [data-testid="stMarkdownContainer"] > p > img {
    max-height: 1.125rem;
    width: auto;
}
@media (max-width: 600px) {
    [data-testid="stMainBlockContainer"] {
        padding-bottom: calc(8rem + 1.5 * env(safe-area-inset-bottom, 0px));
    }
    [data-testid="stTabs"] [role="tablist"] {
        position: fixed;
        inset: auto 0 0;
        transform: translateY(-50%);
        z-index: 10;
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.25rem;
        box-sizing: border-box;
        width: 100%;
        padding: 0.35rem 0.5rem calc(0.35rem + env(safe-area-inset-bottom, 0px));
        background: var(--background-color, Canvas);
        border-top: 1px solid color-mix(in srgb, currentColor 18%, transparent);
    }
    [data-testid="stTabs"] [role="tablist"] [role="tab"] {
        min-width: 0;
        min-height: 56px;
        justify-content: center;
        padding: 0.25rem 0;
        border-radius: 0.65rem;
    }
    [data-testid="stTabs"] [role="tab"] [data-testid="stMarkdownContainer"] > p {
        flex-direction: column;
        gap: 0.2rem;
        font-size: 0.75rem;
        white-space: nowrap;
    }
    [data-testid="stTabs"] [role="tab"] [data-testid="stMarkdownContainer"] > p > img {
        max-height: 1.5rem;
    }
    [data-testid="stTabs"] [role="tablist"] > :not([role="tab"]),
    [data-testid="stTabs"] [role="tab"] > .react-aria-SelectionIndicator {
        display: none;
    }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        background: color-mix(in srgb, currentColor 12%, transparent);
    }
}
</style>
""")

tab1, tab2, tab3, tab4 = st.tabs([
    tab_label("極巨攻擊", "max_attack-transparent.png"),
    tab_label("極巨防禦", "max_defense-transparent.png", trim_padding=True),
    tab_label("DPS", "raid-transparent.png"),
    tab_label("屬性克制", "type-transparent.png"),
])

# -------------------------------------------------------------------------
# Tab 1: Att
# -------------------------------------------------------------------------
with tab1:
    st.header("極巨對戰輸出計算")
    st.caption("輸出 = 攻擊 × 招式威力（超極巨 450、極巨 350）× 屬修 × 屬性剋制倍率 × 天氣倍率")
    if err_att: st.error(err_att)
    elif data_att is not None:
        attack_types = list(chart_att.columns)
        second_types = ["無"] + attack_types
        target_names = data_att["寶可夢"].dropna().astype(str).str.strip()
        target_names = target_names[target_names.ne("")].unique()

        # Att.xlsx 的「屬性」是攻擊招式屬性，對手屬性另查寶可夢資料。
        pokemon_types = {}
        for frame, columns in (
            (data_list, ["名稱", "屬性 1", "屬性 2"]),
            (data_def, ["寶可夢", "屬性一", "屬性二"]),
        ):
            if frame is not None and all(column in frame.columns for column in columns):
                for name, type1, type2 in frame[columns].dropna(subset=columns[:2]).itertuples(index=False, name=None):
                    type1 = str(type1).strip()
                    type2 = str(type2).strip() if pd.notna(type2) else "無"
                    if type1 in attack_types and type2 in second_types:
                        pokemon_types.setdefault(str(name).strip(), (type1, type2))

        target_types = {
            name: pokemon_types.get(name) or pokemon_types.get(name.removeprefix("超極巨"))
            for name in target_names
        }
        target = st.selectbox(
            "請選擇對手寶可夢",
            target_names,
            index=None,
            placeholder="搜尋極巨對戰對手，或直接選擇屬性",
            key="att_target",
            on_change=apply_target_types,
            args=("att", target_types),
        )
        if target is not None and target_types[target] is None:
            st.info("找不到這隻寶可夢的屬性，請用下方選單手動選擇。")

        c1, c2 = st.columns(2)
        with c1:
            def_t1 = st.selectbox("對手屬性 1", attack_types, key="att_t1", on_change=clear_target, args=("att",))
        with c2:
            def_t2 = st.selectbox("對手屬性 2", second_types, key="att_t2", on_change=clear_target, args=("att",))
        
        results = []
        try:
            for _, row in data_att.iterrows():
                name = row.get('寶可夢') or row.iloc[0]
                atk_t = row.get('屬性', row.get('屬性一'))
                raw_atk = row.get('基礎攻擊', 0)
                
                try:
                    base_atk = float(raw_atk)
                except:
                    continue
                    
                if pd.isna(base_atk) or base_atk <= 0: continue
                
                stab_bonus = 1.2 if 'Y' in str(row.get('屬修', 'N')).upper() else 1.0
                move_kind = row.get("超級巨/極巨", row.get("超極巨/極巨", "D"))
                move_p = 450 if str(move_kind).strip().upper() == "G" else 350
                
                mult = get_multiplier(chart_att, atk_t, def_t1, def_t2)
                w_mult = get_weather_mult(atk_t, current_weather)
                
                results.append({
                    "寶可夢": name, "屬性": atk_t, 
                    "輸出": int(base_atk * stab_bonus * move_p * mult * w_mult)
                })
            
            if results:
                res_df = pd.DataFrame(results).sort_values("輸出", ascending=False)
                res_df["強度%"] = (res_df["輸出"] / res_df["輸出"].max() * 100) if res_df["輸出"].max() > 0 else 0
                st.dataframe(apply_style(res_df, {'強度%': '{:.1f}%'}), use_container_width=True, hide_index=True)
        except Exception as e: st.error(f"計算錯誤: {e}")

# -------------------------------------------------------------------------
# Tab 2: Def (移除承受倍率欄位)
# -------------------------------------------------------------------------
with tab2:
    st.header("極巨對戰防禦計算")
    st.caption("坦度 = HP * 防禦 / 屬性剋制倍率")
    if err_def: st.error(err_def)
    elif data_def is not None:
        valid_atks = [t for t in chart_def.index if pd.notna(t) and str(t).strip() not in ["", "nan", "攻/守"]]
        
        c1, c2 = st.columns([1, 1])
        with c1:
            user_atk = st.selectbox("對手攻擊屬性", valid_atks, key="def_atk")
        with c2:
            st.markdown("<div style='margin-top: 35px;'></div>", unsafe_allow_html=True)
            use_shields = st.checkbox("開三盾", value=False)
        
        results = []
        try:
            for _, row in data_def.iterrows():
                name = row.get('寶可夢', row.iloc[0])
                t1 = row.get('屬性一', row.get('屬性1', row.get('屬性')))
                t2 = row.get('屬性二', row.get('屬性2'))
                
                if use_shields:
                    raw_stat = row.get('開三盾', 0)
                else:
                    raw_stat = row.get('基礎防禦', row.get('防禦', 0))
                    
                try:
                    base_stat = float(raw_stat)
                except (ValueError, TypeError):
                    continue
                if pd.isna(base_stat) or base_stat <= 0: continue
                
                # 原屬性克制倍率
                mult = get_multiplier(chart_def, user_atk, t1, t2)
                
                # 坦度計算
                final_def = 99999.0 if mult == 0 else base_stat / mult
                
                t2_str = f"/{t2}" if pd.notna(t2) and str(t2).strip() not in ["", "無", "nan", "None"] else ""
                
                results.append({
                    "寶可夢": name, 
                    "自身屬性": f"{t1}{t2_str}", 
                    "坦度": final_def
                })
            
            if results:
                res_df = pd.DataFrame(results).sort_values("坦度", ascending=False)
                st.dataframe(apply_style(res_df, {'坦度': '{:.1f}'}), use_container_width=True, hide_index=True)
            else:
                st.warning("沒有可計算的防禦資料，請檢查 Def.xlsx 中是否具有「基礎防禦」與「開三盾」欄位。")
        except Exception as e: st.error(f"防禦計算錯誤: {e}")

# -------------------------------------------------------------------------
# Tab 3: DPS
# -------------------------------------------------------------------------
with tab3:
    st.header("DPS")
    if err_dps: st.error(err_dps)
    elif data_dps is not None:
        dps_types = [type_name for type_name in chart_dps.columns if type_name != "無"]
        dps_second_types = ["無"] + dps_types
        raid_targets = {}
        if data_list is not None:
            name_col = next((col for col in data_list.columns if "名" in col), None)
            first_col = next((col for col in data_list.columns if "屬性" in col and ("1" in col or "一" in col)), None)
            second_col = next((col for col in data_list.columns if "屬性" in col and ("2" in col or "二" in col)), None)
            if name_col and first_col:
                for _, row in data_list.dropna(subset=[name_col, first_col]).iterrows():
                    name = str(row[name_col]).strip()
                    type1 = str(row[first_col]).strip()
                    raw_type2 = row.get(second_col)
                    type2 = str(raw_type2).strip() if pd.notna(raw_type2) else "無"
                    if name and type1 in dps_types and type2 in dps_second_types:
                        raid_targets.setdefault(name, (type1, type2))

        target_poke = st.selectbox(
            "請選擇團戰寶可夢",
            list(raid_targets),
            index=None,
            placeholder="搜尋團體戰對手，或直接選擇屬性",
            key="dps_target",
            on_change=apply_target_types,
            args=("dps", raid_targets),
        )
        if not raid_targets:
            st.info("目前無法搜尋寶可夢，請直接選擇對手屬性。")
        c1, c2 = st.columns(2)
        with c1:
            dps_t1 = st.selectbox("對手屬性 1", dps_types, key="dps_t1", on_change=clear_target, args=("dps",))
        with c2:
            dps_t2 = st.selectbox("對手屬性 2", dps_second_types, key="dps_t2", on_change=clear_target, args=("dps",))
        
        results = []
        try:
            for _, row in data_dps.iterrows():
                name = row.get('寶可夢') or row.iloc[0]
                atk_t = row.get('屬性', row.get('屬性一', row.get('招式屬性', row.get('Type', row.get('Move Type')))))
                if pd.isna(atk_t) or not atk_t:
                    for col in row.index: 
                        if str(row[col]) in chart_dps.index: atk_t = row[col]; break
                
                raw_dps = row.get('DPS') or row.get('基礎DPS')
                try:
                    base_dps = float(raw_dps)
                except:
                    continue
                    
                if pd.notna(base_dps) and base_dps > 0 and pd.notna(atk_t) and atk_t:
                    mult = get_multiplier(chart_dps, atk_t, dps_t1, dps_t2)
                    w_mult = get_weather_mult(atk_t, current_weather)
                    result = {"寶可夢": name, "屬性": atk_t, "DPS": base_dps * mult * w_mult}
                    if target_poke:
                        result["倍率"] = f"x{round(mult * w_mult, 2)}"
                    results.append(result)
            
            if results:
                res_df = pd.DataFrame(results).sort_values("DPS", ascending=False)
                if target_poke:
                    st.subheader(f"「{target_poke}」的打手排行（前 50 名）")
                    res_df = res_df.head(50)
                st.dataframe(apply_style(res_df, {'DPS': '{:.2f}'}), use_container_width=True, hide_index=True)
        except Exception as e: st.error(f"計算錯誤: {e}")

# -------------------------------------------------------------------------
# Tab 4: Chart
# -------------------------------------------------------------------------
with tab4:
    st.header("屬性克制表")
    if (APP_DIR / "chart.png").is_file(): st.image(APP_DIR / "chart.png", use_container_width=True)
    elif (APP_DIR / "chart.jpg").is_file(): st.image(APP_DIR / "chart.jpg", use_container_width=True)
    
    st.divider(); st.subheader("屬性弱點計算器")
    if chart_dps is not None:
        c1, c2 = st.columns(2)
        with c1: chart_t1 = st.selectbox("防守屬性 1", list(chart_dps.columns), key="c_t1")
        with c2: chart_t2 = st.selectbox("防守屬性 2", ["無"] + list(chart_dps.columns), key="c_t2")
        
        chart_res = []
        for atk_t in chart_dps.index:
            if pd.isna(atk_t) or str(atk_t).strip() in ["","nan","攻/守"]: continue
            
            mult = get_multiplier(chart_dps, atk_t, chart_t1, chart_t2)
            w_mult = get_weather_mult(atk_t, current_weather)
            final_mult = mult * w_mult
            
            chart_res.append({"屬性": str(atk_t), "倍率": f"x{round(final_mult, 3)}", "v": final_mult})
            
        res_df = pd.DataFrame(chart_res).sort_values("v", ascending=False)[["屬性","倍率"]]
        st.dataframe(apply_style(res_df), use_container_width=True, hide_index=True)
