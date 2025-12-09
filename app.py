import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="寶可夢極巨數據庫", layout="wide")
st.title("寶可夢極巨戰鬥計算機 (指定欄位版)")

# 檔名設定
excel_file = "Pokemon.xlsx"
SHEET_TYPE = "屬性克制表"
SHEET_DATA = "攻守數據"

# ==========================================
# 0. 核心：讀取屬性克制表 (用於計算倍率)
# ==========================================
# 我們需要這張表來算出 "屬性變更" 後的結果
df_type_chart = None
try:
    if os.path.exists(excel_file):
        # 假設克制表矩陣在 A1 開始的區域，直接讀取
        # index_col=0 代表第一欄是攻擊方屬性
        df_type_chart = pd.read_excel(excel_file, sheet_name=SHEET_TYPE, index_col=0)
    else:
        st.error(f"❌ 找不到檔案：{excel_file}")
        st.stop()
except:
    st.error("❌ 讀取「屬性克制表」失敗，請檢查工作表名稱。")
    st.stop()

# 定義計算倍率的函數
def get_multiplier(atk_type, def_type1, def_type2):
    try:
        if df_type_chart is None: return 1.0
        # 去除空白並轉字串
        atk_type = str(atk_type).strip()
        def_type1 = str(def_type1).strip()
        
        # 查表
        m1 = float(df_type_chart.loc[atk_type, def_type1]) if (atk_type in df_type_chart.index and def_type1 in df_type_chart.columns) else 1.0
        
        m2 = 1.0
        if pd.notna(def_type2) and str(def_type2) != "無":
             dt2 = str(def_type2).strip()
             if dt2 in df_type_chart.columns:
                 m2 = float(df_type_chart.loc[atk_type, dt2])
        return m1 * m2
    except:
        return 1.0

# ==========================================
# APP 介面
# ==========================================
tab1, tab2, tab3 = st.tabs(["功能 1 (輸出排序)", "功能 2 (抗性防禦)", "功能 3 (DPS排序)"])

# ==========================================
# 功能 1：讀取 J, K, O 欄 (J2:J21, K2:K21, O2:O21)
# ==========================================
with tab1:
    st.header("功能 1：選擇防守方屬性，輸出由大排到小")
    st.caption("讀取資料來源：Pokemon.xlsx [攻守數據] 工作表 (J, K, O 欄)")

    # 1. 介面：選擇屬性 (模擬變更 L1, M1)
    c1, c2 = st.columns(2)
    with c1:
        def_t1 = st.selectbox("防守方屬性 1 (變更 L1)", df_type_chart.columns, key="f1_t1")
    with c2:
        options = ["無"] + list(df_type_chart.columns)
        def_t2 = st.selectbox("防守方屬性 2 (變更 M1)", options, key="f1_t2")

    # 2. 讀取資料 (J, K, O 欄)
    # Pandas 的 usecols 接受 "J,K,O" 這種寫法，非常方便
    try:
        # header=1 代表 Excel 的第 2 列是標題 (因為資料是從 J2 開始) -> 實際上 Python index 從 0 開始，所以 Row 1 是 header
        # 根據您的描述，J1, K1, O1 應該是標題，J2 開始是數據
        df_f1 = pd.read_excel(excel_file, sheet_name=SHEET_DATA, usecols="J,K,O")
        
        # 重新命名欄位以利程式識別 (依序是 J, K, O)
        df_f1.columns = ["寶可夢", "招式屬性", "基礎輸出"]
        
        # 清除空值 (只讀取有數據的部分)
        df_f1 = df_f1.dropna()

        # 3. 計算與排序
        if st.button("計算並排序", key="btn_f1"):
            results = []
            for idx, row in df_f1.iterrows():
                # 取得數據
                p_name = row["寶可夢"]
                p_type = row["招式屬性"]
                base_dmg = row["基礎輸出"]

                # 計算倍率
                mult = get_multiplier(p_type, def_t1, def_t2)
                final_dmg = base_dmg * mult

                results.append({
                    "寶可夢": p_name,
                    "屬性": p_type,
                    "基礎輸出": base_dmg,
                    "倍率": f"x{mult}",
                    "最終輸出": int(final_dmg)
                })
            
            # 轉成 DataFrame 並由大排到小
            res_df = pd.DataFrame(results).sort_values(by="最終輸出", ascending=False)
            st.dataframe(res_df, use_container_width=True)

    except Exception as e:
        st.error(f"讀取 J,K,O 欄位失敗：{e}")

# ==========================================
# 功能 2：讀取 A, B 欄 (模擬變更 A1)
# ==========================================
with tab2:
    st.header("功能 2：選擇守方屬性，抗性防禦由大排到小")
    st.caption("讀取資料來源：Pokemon.xlsx [攻守數據] 工作表")
    
    # 邏輯說明：
    # 由於 Python 不能真的去改 Excel 的 A1 讓 Excel 自己跑 filter，
    # 我們必須去讀取 Excel 裡「所有的防守排行資料」，然後幫您抓出您要的那一欄。
    
    target_attr = st.selectbox("選擇守方屬性 (變更 A1)", df_type_chart.columns, key="f2_t1")

    try:
        # 讀取整個工作表的前幾列，用來找屬性在哪裡
        # header=0 (第一列) 通常是分類 (如: 格鬥, 地面...)
        # header=1 (第二列) 通常是標題 (如: 寶可夢, 抗性防禦...)
        df_all = pd.read_excel(excel_file, sheet_name=SHEET_DATA, header=0) # 讀取第一列分類
        
        # 尋找使用者選的屬性在哪一欄 (例如 "格鬥" 在第 A 欄)
        found_col_index = -1
        
        # 掃描第一列的所有標題
        for idx, col_name in enumerate(df_all.columns):
            if str(col_name).strip() == target_attr:
                found_col_index = idx
                break
        
        if found_col_index != -1:
            # 找到了！讀取這一欄(寶可夢) 和 右邊那一欄(數值)
            # 使用 usecols 讀取特定兩欄
            df_f2 = pd.read_excel(excel_file, sheet_name=SHEET_DATA, header=1, usecols=[found_col_index, found_col_index+1])
            
            # 重新命名 (因為抓進來的標題可能是 '寶可夢.1' 之類的)
            df_f2.columns = ["寶可夢", "抗性防禦"]
            
            # 排序：抗性防禦由大排到小
            df_f2 = df_f2.sort_values(by="抗性防禦", ascending=False).dropna()
            
            st.write(f"顯示 **{target_attr}** 屬性的排名：")
            st.dataframe(df_f2, use_container_width=True)
        else:
            st.warning(f"在工作表的第一列找不到「{target_attr}」這個分類。請確認 Excel 格式。")
            # 備用方案：如果真的只是要讀 A, B 欄 (不論 A1 選什麼)
            if st.checkbox("強制讀取 A, B 欄 (不搜尋屬性)"):
                df_force = pd.read_excel(excel_file, sheet_name=SHEET_DATA, usecols="A,B", header=1)
                df_force.columns = ["寶可夢", "抗性防禦"]
                st.dataframe(df_force.sort_values(by="抗性防禦", ascending=False))

    except Exception as e:
        st.error(f"讀取資料失敗：{e}")

# ==========================================
# 功能 3：讀取 V, W, X, Y 欄 (V2:Y19)
# ==========================================
with tab3:
    st.header("功能 3：選擇防守方屬性，DPS 由大排到小")
    st.caption("讀取資料來源：Pokemon.xlsx [屬性克制表] 工作表 (V, W, Y 欄)")

    # 1. 介面 (模擬變更 V1, W1)
    c1, c2 = st.columns(2)
    with c1:
        dps_t1 = st.selectbox("防守方屬性 1 (變更 V1)", df_type_chart.columns, key="f3_t1")
    with c2:
        opt_dps = ["無"] + list(df_type_chart.columns)
        dps_t2 = st.selectbox("防守方屬性 2 (變更 W1)", opt_dps, key="f3_t2")

    # 2. 讀取資料 (V, W, Y 欄)
    # 假設 V=寶可夢, W=屬性, X=?, Y=DPS
    try:
        # V 是第 22 欄 (Excel), W=23, Y=25. Python index 分別是 21, 22, 24
        # 使用 usecols="V,W,Y" 最準確
        df_f3 = pd.read_excel(excel_file, sheet_name=SHEET_TYPE, usecols="V,W,Y")
        
        # 假設第一列 (Row 1) 是標題
        df_f3.columns = ["寶可夢", "招式屬性", "基礎DPS"]
        df_f3 = df_f3.dropna()

        if st.button("計算 DPS 排名", key="btn_f3"):
            dps_results = []
            for idx, row in df_f3.iterrows():
                p_name = row["寶可夢"]
                p_type = row["招式屬性"]
                base_dps = row["基礎DPS"]

                # 計算倍率
                mult = get_multiplier(p_type, dps_t1, dps_t2)
                final_dps = base_dps * mult

                dps_results.append({
                    "寶可夢": p_name,
                    "屬性": p_type,
                    "基礎DPS": base_dps,
                    "倍率": f"x{mult}",
                    "最終DPS": final_dps
                })

            # 轉 DataFrame 並排序
            res_dps = pd.DataFrame(dps_results).sort_values(by="最終DPS", ascending=False)
            st.dataframe(res_dps, use_container_width=True)

    except Exception as e:
        st.error(f"讀取 V,W,Y 欄位失敗：{e}")