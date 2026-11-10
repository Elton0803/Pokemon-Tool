# Pokémon GO 攻守數據｜輸出防禦計算

[English](#english)

這是一個用 Python 和 Streamlit 製作的 Pokémon GO PVE 對戰計算工具。寶可夢計算器會依照對手的屬性、招式屬性與搭下的天氣加成，估算極巨對戰的輸出、坦度或團體戰的 DPS，方便挑選攻擊手與坦克。

## 功能

| 分頁 | 操作方式 | 顯示結果 |
| --- | --- | --- |
| 極巨攻擊 | 選擇對手的一至兩種屬性。 | 比較極巨招式的輸出，並顯示相較於榜首的強度百分比。 |
| 極巨防禦 | 選擇對手技能的**攻擊屬性**，可根據需求勾選「開三盾」。 | 根據防禦和血量數值及屬性倍率計算坦度排行。 |
| DPS計算 | 選擇對手的一至兩種屬性。 | 以基礎 DPS 乘上屬性倍率和天氣加成，依強度排序。 |
| 屬性克制 | 選擇對手的一至兩種屬性。 | 列出各攻擊屬性的倍率，由高到低排序。 |
| 團體戰輸出查詢 | 在搜尋欄填入對手寶可夢。 | 自動帶入對手屬性，依估算 DPS 列出前 50 名打手。 |

對手只有一種屬性時，第二屬性選「無」。右上角的「天氣加成」預設為「無」。選擇天氣後，符合該天氣的攻擊屬性會在極巨攻擊、DPS、屬性弱點計算器及團體戰排行套用 1.2 倍加成。

## 計算方式

- **極巨攻擊**：`攻擊 × 招式威力 × 屬修 × 屬性剋制倍率`。超極巨招式威力為 450，極巨招式威力為 350。符合天氣加成時，輸出再乘以 1.2。
- **極巨防禦**：`HP × 防禦 ÷ 屬性剋制倍率`。這裡的倍率是對手招式對我方寶可夢的屬性剋制倍率。

## 在電腦上執行

先安裝 Python 3 和 Git，接著在終端機執行：

```bash
git clone https://github.com/Elton0803/Pokemon-Tool.git
cd Pokemon-Tool
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

開啟終端機顯示的 Local URL（通常是 `http://localhost:8501`），即可切換分頁使用。第一次可以到「團體戰輸出查詢」選取「噴火龍」，查看程式帶入的火／飛行屬性和打手排行。

## 資料檔

| 檔案 | 用途 |
| --- | --- |
| [Att.xlsx](data/Att.xlsx) | 極巨攻擊資料及屬性倍率表。 |
| [Def.xlsx](data/Def.xlsx) | 極巨防禦資料及屬性倍率表。 |
| [DPS.xlsx](data/DPS.xlsx) | 基礎 DPS 及屬性倍率表，供 DPS 計算、弱點查詢與團體戰排行使用。 |
| [list.xlsx](data/list.xlsx) | 團體戰查詢使用的寶可夢名稱與屬性清單。 |
| [能量點.xlsx](data/能量點.xlsx) | 原本的完整版本工作簿，可根據需求修改自己的寶可夢體質。 |

[chart.png](chart.png) 是「屬性克制」分頁顯示的圖表。更新 Excel 資料後，請保留檔名、欄位名稱及屬性倍率表的位置，再重新執行程式。


---

## English

[繁體中文](#pokémon-go-攻守數據輸出防禦計算)

### Pokémon GO Attack and Defense Calculator

This Pokémon GO PvE battle calculator is built with Python and Streamlit. It uses the opponent’s types, move types, and current weather to estimate Max Battle damage output and durability or rank raid attackers by DPS.

### Features

| Tab | How to use it | Results |
| --- | --- | --- |
| Max Battle Attack (極巨攻擊) | Select one or two types for the opponent. | Compare Max Move damage output and see each result as a percentage of the highest output. |
| Max Battle Defense (極巨防禦) | Select the type of the opponent’s attack. Enable 「開三盾」 to include three Max Guards. | Rank Pokémon by durability using their HP, Defense, and the incoming type effectiveness multiplier. |
| DPS Calculator (DPS計算) | Select one or two types for the opponent. | Rank attackers by base DPS adjusted for type effectiveness and weather. |
| Type Effectiveness (屬性克制) | Select one or two types for the opponent. | See the multipliers for each attacking type, sorted from highest to lowest. |
| Raid Attacker Rankings (團體戰輸出查詢) | Search for the opposing Pokémon. | The calculator fills in the opponent’s types and lists the top 50 attackers by estimated DPS. |

For a single-type opponent, select 「無」 (None) for the second type. The weather setting in the upper right also defaults to 「無」. When you select a weather condition, moves of boosted types receive a 1.2× multiplier in Max Battle Attack, the DPS Calculator, the type weakness calculator, and the raid rankings.

### Formulas

- **Max Battle Attack** = `Attack × Move Power × STAB × Type Effectiveness Multiplier`. Gigantamax moves use 450 power and Dynamax moves use 350. When the move’s type is boosted by weather, multiply the result by 1.2. STAB is the same-type attack bonus.
- **Max Battle Defense** = `HP × Defense ÷ Type Effectiveness Multiplier`. Use the multiplier for the opponent’s move against your Pokémon’s type or types.

### Run Locally

Install Python 3 and Git, then run these commands in your terminal.

```bash
git clone https://github.com/Elton0803/Pokemon-Tool.git
cd Pokemon-Tool
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the local URL shown in the terminal, usually `http://localhost:8501`. To try the raid rankings, open 「團體戰輸出查詢」 and select Charizard (噴火龍). The calculator fills in Fire and Flying as its types and displays the attacker rankings.

### Data Files

| File | Purpose |
| --- | --- |
| [Att.xlsx](data/Att.xlsx) | Max Battle attack data and type multipliers. |
| [Def.xlsx](data/Def.xlsx) | Max Battle defense data and type multipliers. |
| [DPS.xlsx](data/DPS.xlsx) | Base DPS and type multipliers for the DPS calculator, type weakness lookup, and raid rankings. |
| [list.xlsx](data/list.xlsx) | Pokémon names and types for raid lookup. |
| [能量點.xlsx](data/能量點.xlsx) | Original full workbook. You can adjust your Pokémon’s stats in the workbook as needed. |

The Type Effectiveness tab displays [chart.png](chart.png). After updating the Excel data, keep the file names, column headers, and type multiplier table positions the same, then restart the app.
