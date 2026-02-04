# app.py — BOLVA CEO 动态经营看板（2025）
# 风格：奶油象牙渐变 + 香槟金 + 玻璃拟态（接近参考图）
# 功能：季度切换Q1~Q4、Top8产品贡献、购货单位&业务员年度分析、平台费用指标、洞察popover、营销费率模拟
#
# 运行：
#   python -m pip install -U streamlit plotly pandas openpyxl numpy
#   python -m streamlit run app.py

import os
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re

def is_cloud() -> bool:
    return bool(os.environ.get("STREAMLIT_SERVER_PORT") or os.environ.get("STREAMLIT_CLOUD"))

def load_all_dashboard_data(used_file, fp=None):
    """
    统一收口：一站式读取所有看板数据
    """
    results = {}
    
    # 1. 年度利润
    try:
        results["annual_profit"] = read_annual_profit(used_file, fp=fp)
    except Exception as e:
        st.error(f"读取《年度利润》失败：{e}")
        st.stop()

    # 2. 银行余额
    try:
        results["cash_cny"] = read_bank_balance_cny(used_file, fp=fp)
    except Exception:
        results["cash_cny"] = 0.0

    # 3. 销售数据
    try:
        results["sales"] = read_sales(used_file, fp=fp)
    except Exception as e:
        st.error(f"读取《销售数据》失败：{e}")
        st.stop()

    # 4. 平台费用
    try:
        results["platform"] = read_platform_selling_exp(used_file, fp=fp)
    except Exception as e:
        st.warning(f"读取《平台 销售费用比》失败：{e}（费用分析页将不可用）")
        results["platform"] = pd.DataFrame()

    # 5. 运营费用
    try:
        results["opex_df"] = read_opex(used_file, fp=fp)
    except Exception as e:
        results["opex_df"] = pd.DataFrame()
        
    return results

# -----------------------------
# 页面工具
# -----------------------------
# -----------------------------
# 页面配置
# -----------------------------
st.set_page_config(page_title="BOLVA CEO 动态经营看板（2025）", layout="wide", initial_sidebar_state="expanded")

TEMPLATE = "ggplot2"
CHARCOAL = "#1f1f1f"
GOLD = "#c9a66b"

# -----------------------------
# UI 主题（奶油金玻璃拟态）
# -----------------------------
def inject_css():
    st.markdown(
        """
        <style>
          :root{
            --bg1:#f3efe8;
            --bg2:#e9e1d3;
            --card:rgba(255,255,255,.68);
            --card2:rgba(247,242,234,.64);
            --ink:#1f1f1f;
            --muted:rgba(0,0,0,.58);
            --gold:#c9a66b;
            --border:rgba(40,40,40,.10);
            --shadow:0 14px 40px rgba(0,0,0,.10);
            --shadow2:0 10px 26px rgba(0,0,0,.08);
            --radius:18px;
          }

          .stApp{
            background: radial-gradient(1200px 700px at 35% 10%, #ffffff 0%, var(--bg1) 40%, var(--bg2) 100%);
            color: var(--ink);
            font-family: "Helvetica Neue", Helvetica, Arial, system-ui, -apple-system, Segoe UI, Roboto;
          }

          .h1{
            font-weight: 900; letter-spacing:.6px;
            font-size: 28px; margin: 0 0 4px 0;
          }
          .sub{
            color: var(--muted); font-size: .92rem; margin: 0 0 14px 0;
          }
          .badge{
            display:inline-block; padding:4px 12px; border-radius:999px;
            background: rgba(201,166,107,.14);
            border: 1px solid rgba(201,166,107,.40);
            color: var(--ink); font-size:.82rem; margin-left:10px;
          }

          .panel{
            background: linear-gradient(180deg, var(--card) 0%, var(--card2) 100%);
            border: 1px solid rgba(60,60,60,.08);
            border-radius: 20px;
            box-shadow: var(--shadow);
            padding: 12px 14px 14px 14px;
          }

          .kpi{
            background: linear-gradient(180deg, rgba(255,255,255,.72) 0%, rgba(247,242,234,.70) 100%);
            border: 1px solid rgba(60,60,60,.10);
            border-radius: var(--radius);
            box-shadow: var(--shadow2);
            padding: 14px 16px 12px 16px;
          }
          .kpi .label{
            font-size: 12px; color: var(--muted); letter-spacing:.5px;
            display:flex; align-items:center; justify-content:space-between;
          }
          .kpi .value{
            font-size: 34px; font-weight: 900; margin-top: 6px;
          }
          .kpi .delta{
            margin-top: 2px; font-size: 12px; color: rgba(0,0,0,.50);
          }
          .kpi .icon{
            width:28px; height:28px; border-radius:10px;
            background: rgba(0,0,0,.06);
            display:flex; align-items:center; justify-content:center;
          }

          .tip{
            margin-left:6px; font-size:.86rem; color: rgba(0,0,0,.55);
            cursor: help;
          }

          /* tabs 更精致 */
          [data-baseweb="tab-list"] button{
            border-radius: 999px !important;
            padding: 8px 14px !important;
          }

          /* popover 按钮更像奶油金控件 */
          button[kind="secondary"]{
            border-radius: 999px !important;
            border: 1px solid rgba(201,166,107,.35) !important;
            background: rgba(255,255,255,.55) !important;
          }

          /* Multiselect Tag 样式覆盖 (去除默认红/蓝色，改为奶油金) */
          span[data-baseweb="tag"] {
            background-color: rgba(201,166,107,0.15) !important;
            border: 1px solid rgba(201,166,107,0.40) !important;
            color: var(--ink) !important;
            border-radius: 999px !important;
          }
          /* Tag 中的关闭 X 颜色 */
          span[data-baseweb="tag"] span {
            color: var(--ink) !important;
          }

          section[data-testid="stSidebar"]{
            background: rgba(255,255,255,.55);
            border-right: 1px solid rgba(60,60,60,.08);
          }

          @keyframes pulse {
            0% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.05); opacity: 0.8; }
            100% { transform: scale(1); opacity: 1; }
          }
          .pulse-badge {
            animation: pulse 2s infinite ease-in-out;
            background: #c9a66b; color: white; padding: 2px 10px; border-radius: 20px; font-size: 0.8em;
          }

          @media (max-width: 768px){
            .block-container{ padding: 1rem .9rem !important; }
            .kpi .value{ font-size: 30px; }
          }
        </style>
        """,
        unsafe_allow_html=True
    )

def apply_plot_style(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        template=TEMPLATE,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=CHARCOAL, family="Helvetica Neue, Helvetica, Arial, system-ui"),
        margin=dict(l=18, r=18, t=58, b=18),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(0,0,0,0.06)", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(0,0,0,0.06)", zeroline=False)
    return fig

# -----------------------------
# 工具：格式化
# -----------------------------
def fmt_money(x): 
    return f"¥{x:,.2f}"
def fmt_m(x):
    return f"¥{x:,.2f}M"
def fmt_pct(x):
    return f"{x*100:.1f}%"

def safe_div(a, b):
    b = np.where(b == 0, np.nan, b)
    return a / b

# -----------------------------
# 工具：列名健壮匹配
# -----------------------------
def norm_col(s: str) -> str:
    return str(s).strip().replace("（", "(").replace("）", ")").replace(" ", "").lower()

def pick_col(cols, candidates):
    norm_map = {norm_col(c): c for c in cols}
    for cand in candidates:
        k = norm_col(cand)
        if k in norm_map:
            return norm_map[k]
    # 模糊包含匹配
    for cand in candidates:
        kc = norm_col(cand)
        for nk, orig in norm_map.items():
            if kc in nk or nk in kc:
                return orig
    return None

# -----------------------------
# 核心取数工具：缓存与指纹
# -----------------------------
def file_fingerprint(path: str) -> str:
    """用 文件大小+修改时间 作为轻量指纹，驱动缓存失效"""
    try:
        stat = os.stat(path)
        return f"{stat.st_mtime_ns}_{stat.st_size}"
    except:
        return "none"

# -----------------------------
# Excel 读取
# -----------------------------
@st.cache_data(show_spinner=False)
def read_annual_profit(excel_file, fp=None) -> pd.DataFrame:
    if hasattr(excel_file, "seek"): excel_file.seek(0)
    raw = pd.read_excel(excel_file, sheet_name="年度利润")
    headers = raw.iloc[1].tolist()
    df = raw.iloc[2:].copy()
    df.columns = headers

    mcol = pick_col(df.columns, ["月份", "month"])
    sales_col = pick_col(df.columns, ["销售额", "营收", "revenue"])
    gm_col = pick_col(df.columns, ["毛利率", "grossmargin", "gm"])
    np_col = pick_col(df.columns, ["净利润", "netprofit"])
    npr_col = pick_col(df.columns, ["净利率", "netmargin"])

    if mcol is None or sales_col is None:
        raise ValueError("《年度利润》缺少关键列：月份 / 销售额(营收)")

    # ---- 日期兼容：字符串 + Excel序列号 ----
    # 尝试解析为数值（Excel序列号）
    df[mcol+"_num"] = pd.to_numeric(df[mcol], errors="coerce")
    
    # 尝试解析为字符串并提取YYYY-MM
    def try_parse_date(x):
        s = str(x).strip()
        # 匹配 2025-01
        m = re.search(r"(\d{4})[-/年](\d{1,2})", s)
        if m:
            return f"{m.group(1)}-{int(m.group(2)):02d}"
        return None

    df[mcol+"_str"] = df[mcol].apply(try_parse_date)

    # 优先用数值解析（如果不为空）
    mask_num = df[mcol+"_num"].notna()
    if mask_num.any():
        s_num = pd.to_datetime(df.loc[mask_num, mcol+"_num"], unit="D", origin="1899-12-30", errors="coerce")
        df.loc[mask_num, mcol+"_str"] = s_num.dt.to_period("M").astype(str)

    df["月份"] = df[mcol+"_str"]
    df = df[df["月份"].notna()].copy()

    out = pd.DataFrame({"月份": df["月份"], "销售额": df[sales_col]})
    if gm_col: out["毛利率"] = df[gm_col]
    if np_col: out["净利润"] = df[np_col]
    if npr_col: out["净利率"] = df[npr_col]
    return out.reset_index(drop=True)

@st.cache_data(show_spinner=False)
@st.cache_data(show_spinner=False)
def read_bank_balance_cny(excel_file, fp=None) -> float:
    if hasattr(excel_file, "seek"): excel_file.seek(0)
    bb = pd.read_excel(excel_file, sheet_name="银行余额")
    cny_col = pick_col(bb.columns, ["本位币(CNY)", "本位币", "cny"])
    if cny_col is None:
        return 0.0
    bb[cny_col] = pd.to_numeric(bb[cny_col], errors="coerce").fillna(0.0)
    return float(bb[cny_col].sum())

def parse_month_key(v):
    # 支持：2025-01月 / 2025年7月 / 2025/01 / 2025-01
    s = str(v).strip()
    s = s.replace("年", "-").replace("月", "").replace("/", "-")
    # 处理 "2025-01" / "2025-1"
    import re
    m = re.search(r"(\d{4})-(\d{1,2})", s)
    if m:
        y, mm = m.group(1), int(m.group(2))
        return f"{y}-{mm:02d}"
    # 处理 excel 序列号兜底
    try:
        x = float(s)
        dt = pd.to_datetime(x, unit="D", origin="1899-12-30", errors="coerce")
        if pd.notna(dt):
            return dt.to_period("M").strftime("%Y-%m")
    except:
        pass
    return None

def render_insight_module(title, insight_list):
    """
    渲染统一的洞察区块
    insight_list: list of dicts [{"headline": "结论", "detail": "详细建议/口径"}]
    """
    if not insight_list:
        return
    st.markdown(f"**💡 {title}｜洞察与建议**")
    for item in insight_list:
        c1, c2 = st.columns([0.92, 0.08])
        with c1:
            st.markdown(f"• {item['headline']}")
        with c2:
            with st.popover("ⓘ", use_container_width=True):
                st.markdown(item['detail'])

def render_data_insufficient(section_name, missing_fields):
    """
    数据不足时的统一提示
    """
    st.warning(f"⚠️ {section_name}：数据不足，无法生成洞察")
    st.caption(f"需要补齐字段/数据源：{', '.join(missing_fields)}")

def is_channel_token(x: str) -> bool:
    t = str(x).strip().lower()
    return any(k in t for k in ["tiktok", "amazon", "shopify", "juvera", "亚马逊"])


def map_channel(x: str) -> str:
    t = str(x).strip().lower()
    if "juvera" in t: return "Juvera"
    if "tiktok" in t: return "TikTok-US" if "us" in t else "TikTok-UK"
    if "amazon" in t or "亚马逊" in t:
        return "亚马逊-US" if ("us" in t or "美国" in t) else "亚马逊-UK"
    if "shopify" in t: return "Shopify"
    return "其他"


@st.cache_data(show_spinner=False)
def read_sales(excel_file, fp=None):
    if hasattr(excel_file, "seek"): excel_file.seek(0)
    s = pd.read_excel(excel_file, sheet_name="销售数据")

    date_col = pick_col(s.columns, ["日期"])
    b_col    = pick_col(s.columns, ["购货单位"])
    prod_col = pick_col(s.columns, ["产品名称"])
    rev_col  = pick_col(s.columns, ["销售收入", "收入", "revenue"])
    cost_col = pick_col(s.columns, ["销售成本", "成本", "cost"])
    margin_col = pick_col(s.columns, ["销售毛利", "毛利", "margin"])
    rep_col  = pick_col(s.columns, ["业务员"])
    chan_col = pick_col(s.columns, ["渠道", "channel"])

    if date_col is None or b_col is None or prod_col is None or rev_col is None:
        raise ValueError("《销售数据》缺少关键列：日期/购货单位/产品名称/销售收入")

    s["月份"] = s[date_col].apply(parse_month_key)
    s = s[s["月份"].notna()].copy()

    s[rev_col] = pd.to_numeric(s[rev_col], errors="coerce").fillna(0.0)
    if cost_col:
        s[cost_col] = pd.to_numeric(s[cost_col], errors="coerce").fillna(0.0)
    
    if margin_col:
        s["销售毛利"] = pd.to_numeric(s[margin_col], errors="coerce").fillna(0.0)
    elif cost_col:
        s["销售毛利"] = s[rev_col] - s[cost_col]
    else:
        s["销售毛利"] = 0.0

    s[prod_col] = s[prod_col].astype(str).str.strip()
    s[b_col]    = s[b_col].astype(str).str.strip()

    # 渠道：映射出的平台名稱 (Amazon, TikTok...) -> 用於趨勢圖和「客戶」頁面的主渠道分析
    s["渠道_mapped"] = s[b_col].apply(map_channel)
    
    # 业务类型：Excel 裡原始的 "渠道" 列內容 (B2B/B2C) -> 用於彙總卡片
    if chan_col:
        s["业务类型"] = s[chan_col].astype(str).str.strip()
    else:
        s["业务类型"] = s["渠道_mapped"] # 回退方案

    # 客户：直接输出购货单位名字
    out = pd.DataFrame({
        "月份": s["月份"],
        "渠道": s["渠道_mapped"],
        "业务类型": s["业务类型"],
        "购货单位": s[b_col],
        "产品名称": s[prod_col],
        "销售收入": s[rev_col],
        "销售毛利": s["销售毛利"]
    })

    if cost_col:
        out["销售成本"] = s[cost_col]
    else:
        out["销售成本"] = np.nan

    if rep_col:
        s["业务员_clean"] = s[rep_col].astype(str).str.strip()
    else:
        s["业务员_clean"] = "Unknown"

    if rep_col:
        out["业务员"] = s["业务员_clean"]
    else:
        out["业务员"] = np.nan

    return out

@st.cache_data(show_spinner=False)
def read_platform_selling_exp(excel_file, fp=None) -> pd.DataFrame:
    if hasattr(excel_file, "seek"): excel_file.seek(0)
    pf = pd.ExcelFile(excel_file)
    raw = pd.read_excel(excel_file, sheet_name="平台 销售费用比")
    header = raw.iloc[0].tolist()
    df = raw.iloc[1:].copy()
    df.columns = header

    platform_col = pick_col(df.columns, ["平台"])
    channel_col  = pick_col(df.columns, ["渠道"])
    sales_col    = pick_col(df.columns, ["销售收入", "营收"])
    ads_col      = pick_col(df.columns, ["广告费(CNY)", "广告费（CNY）", "广告费cny", "广告费"])
    ship_col     = pick_col(df.columns, ["物流费(CNY)", "物流费（CNY）", "物流费"])
    comm_col     = pick_col(df.columns, ["佣金(CNY)", "佣金（CNY）", "佣金"])
    disc_col     = pick_col(df.columns, ["销售折扣/补贴", "折扣/补贴", "折扣补贴"])
    total_col    = pick_col(df.columns, ["总销售费用", "销售费用合计", "总费用"])

    if platform_col is None or sales_col is None or total_col is None:
        raise ValueError("《平台 销售费用比》缺少关键列：平台 / 销售收入 / 总销售费用")

    out = pd.DataFrame({
        "平台": df[platform_col].astype(str).str.strip(),
        "渠道": df[channel_col].astype(str).str.strip() if channel_col else "",
        "销售收入": pd.to_numeric(df[sales_col], errors="coerce").fillna(0.0),
        "广告费": pd.to_numeric(df[ads_col], errors="coerce").fillna(0.0) if ads_col else 0.0,
        "物流费": pd.to_numeric(df[ship_col], errors="coerce").fillna(0.0) if ship_col else 0.0,
        "佣金": pd.to_numeric(df[comm_col], errors="coerce").fillna(0.0) if comm_col else 0.0,
        "销售折扣/补贴": pd.to_numeric(df[disc_col], errors="coerce").fillna(0.0) if disc_col else 0.0,
        "总销售费用": pd.to_numeric(df[total_col], errors="coerce").fillna(0.0),
    })
    out = out[out["平台"] != "合计"].copy()

    # 指标
    out["广告费率"] = safe_div(out["广告费"], out["销售收入"])
    out["物流费率"] = safe_div(out["物流费"], out["销售收入"])
    out["佣金率"] = safe_div(out["佣金"], out["销售收入"])
    out["折扣/补贴率"] = safe_div(out["销售折扣/补贴"], out["销售收入"])
    out["总销售费用率"] = safe_div(out["总销售费用"], out["销售收入"])
    out["ROAS"] = safe_div(out["销售收入"], out["广告费"])

    out["广告占比"] = safe_div(out["广告费"], out["总销售费用"])
    out["物流占比"] = safe_div(out["物流费"], out["总销售费用"])
    out["佣金占比"] = safe_div(out["佣金"], out["总销售费用"])
    out["折扣占比"] = safe_div(out["销售折扣/补贴"], out["总销售费用"])

    out["贡献利润"] = out["销售收入"] - out["总销售费用"]
    out["贡献利润率"] = safe_div(out["贡献利润"], out["销售收入"])

    out["净收入"] = out["销售收入"] + out["销售折扣/补贴"]
    out["净收入口径总费用率"] = safe_div(out["总销售费用"], out["净收入"])

    return out.reset_index(drop=True)

import datetime

def _clean(s):
    return str(s).strip().replace(" ", "").replace("\u3000", "")

def _to_number(x):
    return pd.to_numeric(str(x).replace(",", "").strip(), errors="coerce")

def _parse_month_key(v):
    # 支持：2025年1月 / 2025年01月 / 2025-01 / 2025/01
    s = str(v).strip()
    s = s.replace("年", "-").replace("月", "").replace("/", "-")
    m = re.search(r"(\d{4})-(\d{1,2})", s)
    if not m:
        return None
    y, mm = int(m.group(1)), int(m.group(2))
    return f"{y}-{mm:02d}"

@st.cache_data(show_spinner=False)
def read_opex(excel_file, fp=None):
    """
    在整个Excel里自动寻找“日期+金额”表头的sheet，并读取为 月份-运营费用 数据。
    """
    if hasattr(excel_file, "seek"): excel_file.seek(0)
    xf = pd.ExcelFile(excel_file)

    for sh in xf.sheet_names:
        # 只看前10行（足够定位表头）
        raw = pd.read_excel(xf, sheet_name=sh, header=None, nrows=10).fillna("")
        # 扫描“日期/金额”所在行
        header_row = None
        for i in range(len(raw)):
            row = [_clean(x) for x in raw.iloc[i].tolist()]
            if ("日期" in row) and ("金额" in row):
                header_row = i
                break
        if header_row is None:
            continue

        # 找到后，重新从该sheet完整读取
        full = pd.read_excel(xf, sheet_name=sh, header=None)
        cols = [_clean(x) for x in full.iloc[header_row].tolist()]
        df = full.iloc[header_row+1:].copy()
        df.columns = cols

        if "日期" not in df.columns or "金额" not in df.columns:
            continue

        df = df[["日期", "金额"]].copy()
        df["金额"] = df["金额"].apply(_to_number)
        df = df[df["金额"].notna()].copy()

        df["月份"] = df["日期"].apply(_parse_month_key)
        df = df[df["月份"].notna()].copy()

        out = df.groupby("月份", as_index=False)["金额"].sum()
        out = out.rename(columns={"金额": "运营费用"}).sort_values("月份")

        # ✅ 只要找到一个非空结果就返回（默认认为它就是运营费用表）
        if not out.empty:
            return out

    # 全都没找到
    return pd.DataFrame()

# -----------------------------
# 业务逻辑：季度筛选
# -----------------------------
def quarter_filter_month_str(df: pd.DataFrame, quarter: str, month_col: str = "月份") -> pd.DataFrame:
    if quarter == "全年":
        return df
    qmap = {
        "Q1": ["2025-01", "2025-02", "2025-03"],
        "Q2": ["2025-04", "2025-05", "2025-06"],
        "Q3": ["2025-07", "2025-08", "2025-09"],
        "Q4": ["2025-10", "2025-11", "2025-12"],
    }
    return df[df[month_col].isin(qmap[quarter])].copy()

# -----------------------------
# 组件：KPI 卡
# -----------------------------
def kpi_card(label, value, yoy_text="", icon="◼", help_text=""):
    title_attr = f'title="{help_text}"' if help_text else ""
    st.markdown(
        f"""
        <div class="kpi" {title_attr}>
          <div class="label">
            <div>{label}</div>
            <div class="icon">{icon}</div>
          </div>
          <div class="value">{value}</div>
          <div class="delta">{yoy_text}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# -----------------------------
# 图表：营收 & 净利率（双轴）+ 2026预测
# -----------------------------
def rev_np_forecast_chart(df_profit: pd.DataFrame, df_forecast: pd.DataFrame = None) -> go.Figure:
    # 2025 data
    x = list(df_profit["月份"])
    rev_m = list(df_profit["销售额"] / 1_000_000.0)
    # 改为净利率
    np_margin = list(df_profit["净利率"]) if "净利率" in df_profit.columns else [np.nan]*len(df_profit)

    # 2026 forecast data (append if exists)
    if df_forecast is not None and not df_forecast.empty:
        x += list(df_forecast["月份"])
        rev_m += list(df_forecast["销售额"] / 1_000_000.0)
        # 假设预测年份净利率保持 2025 平均水平
        avg_np = df_profit["净利率"].mean() if "净利率" in df_profit.columns else 0.0
        np_margin += [avg_np] * len(df_forecast)

    # 简单排序：确保X轴是按时间顺序
    # 构造成 DF 排序后再拆回
    tmp = pd.DataFrame({"x": x, "rev": rev_m, "np": np_margin})
    tmp["x"] = tmp["x"].astype(str)
    tmp = tmp.sort_values("x")
    
    x = list(tmp["x"])
    rev_m = list(tmp["rev"])
    np_margin = list(tmp["np"])

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Bar: 营收
    #区分颜色：实际 vs 预测
    colors = ["rgba(31,31,31,0.18)"] * len(df_profit)
    if df_forecast is not None and not df_forecast.empty:
        colors += ["rgba(201,166,107,0.3)"] * len(df_forecast)

    fig.add_trace(go.Bar(
        x=x, y=rev_m, name="营收（M CNY）",
        marker=dict(color=colors),
        hovertemplate="月份：%{x}<br>营收：¥%{y:,.2f}M<extra></extra>",
    ), secondary_y=False)

    # Line: 净利率
    fig.add_trace(go.Scatter(
        x=x, y=np_margin, name="净利率",
        mode="lines+markers",
        line=dict(color=GOLD, width=3),
        marker=dict(size=8, color=GOLD),
        hovertemplate="月份：%{x}<br>净利率：%{y:.1%}<extra></extra>",
    ), secondary_y=True)

    # 简化标题，遵循原本风格
    title_suffix = " & 2026 Forecast" if (df_forecast is not None and not df_forecast.empty) else ""
    fig.update_layout(title=f"Revenue Trend & Net Margin (2025{title_suffix})", height=420)
    # 强制使用 categorical 轴，避免日期自动识别导致 add_vline 的 index 失效（出现1970）
    fig.update_xaxes(type="category")
    
    fig.update_yaxes(title_text="营收（M CNY）", secondary_y=False)
    fig.update_yaxes(title_text="净利率（%）", tickformat=".1%", secondary_y=True)

    # 预测分别线
    if df_forecast is not None and not df_forecast.empty:
        fig.add_vline(x=len(df_profit)-0.5, line_width=1, line_dash="dash", line_color="rgba(0,0,0,0.2)")
        fig.add_annotation(x=len(df_profit), y=max(rev_m)*0.95, text="2026 Forecast", showarrow=False, xanchor="left")

    return apply_plot_style(fig)

# -----------------------------
# 图表：渠道趋势（按季度筛选）
# -----------------------------
def channel_trend_chart(sales: pd.DataFrame, channel: str, quarter: str) -> go.Figure:
    m = sales.groupby(["月份", "渠道"], as_index=False)["销售收入"].sum()
    m = m[m["渠道"] == channel].copy()
    m = quarter_filter_month_str(m, quarter, "月份")
    m["营收_M"] = m["销售收入"] / 1_000_000.0

    fig = px.line(m, x="月份", y="营收_M", title=f"{channel}｜月度趋势（{quarter}）", markers=True, template=TEMPLATE)
    fig.update_traces(
        line=dict(color=GOLD, width=3),
        marker=dict(size=8, color=GOLD),
        hovertemplate="月份：%{x}<br>营收：¥%{y:,.2f}M<extra></extra>",
    )
    fig.update_layout(height=360)
    fig.update_yaxes(title_text="营收（M CNY）")
    fig.update_xaxes(title_text="")
    return apply_plot_style(fig)

# -----------------------------
# 产品贡献：Top8 + Others（横向条形）
# -----------------------------
def top_products(sales: pd.DataFrame, topn: int = 5) -> pd.DataFrame:
    g = sales.groupby("产品名称", as_index=False)["销售收入"].sum().sort_values("销售收入", ascending=False)
    top = g.head(topn).copy()
    others = g.iloc[topn:]["销售收入"].sum()
    if others > 0:
        top = pd.concat([top, pd.DataFrame([{"产品名称": "Others", "销售收入": others}])], ignore_index=True)
    top["占比"] = top["销售收入"] / top["销售收入"].sum()
    return top

def product_bar_chart(top_df: pd.DataFrame) -> go.Figure:
    d = top_df.copy().sort_values("销售收入", ascending=True)
    fig = px.bar(
        d, x="销售收入", y="产品名称", orientation="h",
        title="Top8 Product Contribution (2025)",
        template=TEMPLATE,
        text=d["占比"].map(lambda x: f"{x*100:.1f}%")
    )
    fig.update_traces(
        marker=dict(color="rgba(201,166,107,0.55)", line=dict(color="rgba(0,0,0,0.14)", width=1)),
        textposition="outside",
        hovertemplate="SKU：%{y}<br>营收：¥%{x:,.0f}<extra></extra>",
    )
    fig.update_layout(height=340)
    fig.update_xaxes(title_text="")
    fig.update_yaxes(title_text="")
    return apply_plot_style(fig)

# -----------------------------
# 客户&业务员：Top10
# -----------------------------
def top_customers(sales: pd.DataFrame, topn: int = 10, sort_by: str = "销售收入") -> pd.DataFrame:
    # 1. 基础聚合
    g = sales.groupby("购货单位", as_index=False).agg({
        "销售收入": "sum",
        "销售毛利": "sum",
        "业务类型": lambda x: x.mode()[0] if not x.mode().empty else "B2B"
    })
    
    # 2. 计算毛利率
    g["毛利率"] = safe_div(g["销售毛利"], g["销售收入"])
    
    # 3. 确定主渠道
    def get_main_channel(cust_name):
        c_data = sales[sales["购货单位"] == cust_name]
        c_grp = c_data.groupby("渠道")["销售收入"].sum().sort_values(ascending=False)
        if c_grp.empty: return "未知"
        top_chan = c_grp.index[0]
        top_rev = c_grp.iloc[0]
        total_rev = c_grp.sum()
        if total_rev > 0 and (top_rev / total_rev) < 0.6:
            return "Multi"
        return top_chan

    g["渠道"] = g["购货单位"].apply(get_main_channel)
    
    # 4. 排序并取 TopN
    g = g.sort_values(sort_by, ascending=False).head(topn).reset_index(drop=True)
    g.index = g.index + 1
    
    # 5. 计算累计占比（基于当前 TopN 还是 全局？）
    # 用户要求：累计占比（收入）和 累计占比（毛利）
    total_rev_all = sales["销售收入"].sum()
    total_gp_all = sales["销售毛利"].sum()
    
    g["占比(收入)"] = g["销售收入"] / total_rev_all if total_rev_all else 0.0
    g["累计占比(收入)"] = g["占比(收入)"].cumsum()
    
    g["占比(毛利)"] = g["销售毛利"] / total_gp_all if total_gp_all else 0.0
    g["累计占比(毛利)"] = g["占比(毛利)"].cumsum()
    
    return g

def customer_pareto_chart(cust_df: pd.DataFrame) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # 柱状图：销售收入
    fig.add_trace(go.Bar(
        x=cust_df["购货单位"], y=cust_df["销售收入"], name="销售收入",
        marker=dict(color="rgba(31,31,31,0.18)"),
        hovertemplate="客户：%{x}<br>收入：¥%{y:,.0f}<extra></extra>"
    ), secondary_y=False)
    
    # 折线1：累计收入占比
    fig.add_trace(go.Scatter(
        x=cust_df["购货单位"], y=cust_df["累计占比(收入)"], name="累计收入占比",
        mode="lines+markers", line=dict(color=GOLD, width=3), marker=dict(size=7, color=GOLD),
        hovertemplate="客户：%{x}<br>累计收入占比：%{y:.1%}<extra></extra>"
    ), secondary_y=True)
    
    # 折线2：累计毛利占比
    fig.add_trace(go.Scatter(
        x=cust_df["购货单位"], y=cust_df["累计占比(毛利)"], name="累计毛利占比",
        mode="lines+markers", line=dict(color="#8d7b68", width=2, dash="dot"), marker=dict(size=5, color="#8d7b68"),
        hovertemplate="客户：%{x}<br>累计毛利占比：%{y:.1%}<extra></extra>"
    ), secondary_y=True)
    
    fig.update_layout(title="客户帕累托（Revenue & Margin Concentration）", height=450)
    fig.update_yaxes(title_text="销售收入（CNY）", secondary_y=False)
    fig.update_yaxes(title_text="累计占比", tickformat=".0%", secondary_y=True, range=[0, 1.1])
    return apply_plot_style(fig)

def customer_efficiency_matrix(sales: pd.DataFrame, top_cust_names: list) -> go.Figure:
    # 仅针对 Top10 客户
    d = sales[sales["购货单位"].isin(top_cust_names)].groupby("购货单位", as_index=False).agg({
        "销售收入": "sum",
        "销售毛利": "sum",
        "业务类型": lambda x: x.mode()[0] if not x.mode().empty else "B2B"
    })
    d["毛利率"] = safe_div(d["销售毛利"], d["销售收入"])
    
    fig = px.scatter(
        d, x="销售收入", y="毛利率", size="销售毛利", color="业务类型",
        hover_name="购货单位", title="客户效率矩阵（Revenue vs Margin %）",
        labels={"销售收入": "销售收入", "毛利率": "毛利率", "销售毛利": "毛利额", "业务类型": "类型"},
        template=TEMPLATE,
        size_max=40
    )
    fig.update_traces(marker=dict(opacity=0.8, line=dict(width=1, color="White")))
    fig.update_yaxes(tickformat=".1%")
    fig.update_layout(
        height=480,
        margin=dict(t=50, b=80),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5
        )
    )
    return apply_plot_style(fig)

def customer_channel_dist_chart(sales: pd.DataFrame, top_cust_names: list) -> go.Figure:
    # Top10 客户按 业务类型 (B2B/B2C) 堆叠
    d = sales[sales["购货单位"].isin(top_cust_names)].groupby(["购货单位", "业务类型"], as_index=False)["销售收入"].sum()
    
    fig = px.bar(
        d, x="购货单位", y="销售收入", color="业务类型",
        title="Top10 客户｜业务类型分布结构",
        labels={"销售收入": "销售收入", "购货单位": "客户", "业务类型": "类型"},
        template=TEMPLATE,
        barmode="stack"
    )
    fig.update_layout(height=450)
    return apply_plot_style(fig)

def top_salesreps(sales: pd.DataFrame, topn: int = 10) -> pd.DataFrame:
    if "业务员" not in sales.columns or sales["业务员"].isna().all():
        return pd.DataFrame()
    g = sales.dropna(subset=["业务员"]).groupby("业务员", as_index=False).agg({
        "销售收入": "sum",
        "销售毛利": "sum"
    })
    g = g.sort_values("销售收入", ascending=False).head(topn).reset_index(drop=True)
    g.index = g.index + 1
    total = sales["销售收入"].sum()
    g["占比"] = g["销售收入"] / total if total else 0.0
    g["毛利率"] = safe_div(g["销售毛利"], g["销售收入"])
    return g

# -----------------------------
# 平台费用：图表
# -----------------------------
def platform_charts(df: pd.DataFrame) -> tuple[go.Figure, go.Figure]:
    d = df.sort_values("总销售费用率", ascending=False).copy()

    # 珠光轻奢配色方案：浅珍珠金、柔和香槟、亮象牙、雾面灰金、清透白
    # 使用带有透明度的 RGBA 或更亮的 Hex 模拟珠光感
    LUX_PALETTE = [
        "rgba(201,166,107,0.7)", # 核心香槟金 (珠光感)
        "rgba(230,213,184,0.6)", # 浅珍珠白
        "rgba(168,142,110,0.5)", # 柔和古铜
        "rgba(141,123,104,0.4)", # 雾面灰金
        "rgba(191,174,153,0.3)"  # 半透浅灰
    ]

    fig1 = px.bar(d, x="平台", y="总销售费用率", title="各平台｜总销售费用率（年度）", template=TEMPLATE)
    fig1.update_traces(
        marker_color="rgba(201,166,107,0.8)",  # 更明亮的珠光金
        marker_line_color="rgba(201,166,107,1)",
        marker_line_width=1,
        hovertemplate="平台：%{x}<br>总销售费用率：%{y:.1%}<extra></extra>"
    )
    fig1.update_yaxes(tickformat=".0%")
    fig1.update_layout(height=340)
    fig1 = apply_plot_style(fig1)

    # 100%结构堆叠（折扣用绝对值）
    dd = d.copy()
    dd["折扣/补贴(绝对值)"] = dd["折扣/补贴率"].abs()
    
    # 定义堆叠顺序和对应的轻奢配色
    stacks = ["广告费率", "物流费率", "佣金率", "折扣/补贴(绝对值)"]
    stack_labels = ["广告费", "物流费", "佣金", "折扣/补贴"]
    
    fig2 = go.Figure()
    for i, col in enumerate(stacks):
        fig2.add_trace(go.Bar(
            name=stack_labels[i],
            x=dd["平台"],
            y=dd[col],
            marker_color=LUX_PALETTE[i % len(LUX_PALETTE)],
            hovertemplate=f"{stack_labels[i]}占比：" + "%{y:.1%}<extra></extra>"
        ))
    
    fig2.update_layout(
        barmode='stack',
        title="各平台｜销售费用结构（100%堆叠, 年度）",
        template=TEMPLATE,
        height=360,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(tickformat=".0%")
    )
    fig2 = apply_plot_style(fig2)

    return fig1, fig2
    dd["折扣绝对值"] = dd["销售折扣/补贴"].abs()
    denom = (dd["广告费"] + dd["物流费"] + dd["佣金"] + dd["折扣绝对值"]).replace(0, np.nan)
    dd["广告结构"] = dd["广告费"] / denom
    dd["物流结构"] = dd["物流费"] / denom
    dd["佣金结构"] = dd["佣金"] / denom
    dd["折扣结构"] = dd["折扣绝对值"] / denom

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(name="广告费", x=dd["平台"], y=dd["广告结构"]))
    fig2.add_trace(go.Bar(name="物流费", x=dd["平台"], y=dd["物流结构"]))
    fig2.add_trace(go.Bar(name="佣金", x=dd["平台"], y=dd["佣金结构"]))
    fig2.add_trace(go.Bar(name="折扣/补贴(绝对值)", x=dd["平台"], y=dd["折扣结构"]))
    fig2.update_layout(barmode="stack", title="各平台｜销售费用结构（100%堆叠，年度）", height=360, template=TEMPLATE)
    fig2.update_yaxes(tickformat=".0%")
    fig2 = apply_plot_style(fig2)

    return fig1, fig2

# -----------------------------
# 动态洞察逻辑生成器
# -----------------------------
def get_revenue_trend_insights(profit_q, df_forecast, quarter, forecast_mode):
    if profit_q.empty:
        return [{"headline": "数据缺失：营收趋势无法分析", "detail": "口径：年度利润表<br>缺损字段：月份, 销售额"}]
    
    total_25 = profit_q["销售额"].sum()
    avg_25 = profit_q["销售额"].mean()
    
    res = []
    res.append({
        "headline": f"{quarter} 营收表现平稳，月均贡献约 {fmt_money(avg_25)}",
        "detail": f"**口径**：管理会计口径（不含税/本位币 CNY）<br>**关键数字**：{quarter} 合计营收 {fmt_money(total_25)}。<br>**建议动作**：关注月度波动率，若波动超过 20%，建议启动渠道库存盘点。"
    })
    
    if df_forecast is not None and not df_forecast.empty:
        total_26 = df_forecast["销售额"].sum()
        delta = total_26 - total_25
        res.append({
            "headline": f"2026 {forecast_mode} 情景下，预计增量营收 {fmt_money(delta)}",
            "detail": f"**口径**：2026 预测模型（基于 {forecast_mode} 乘数）<br>**关键数字**：预测年度总营收 {fmt_money(total_26)}。<br>**建议动作**：根据预测增量提前锁定核心 SKU 产能，防止旺季断货。"
        })
    return res

def get_channel_trend_insights(sales_q, channel):
    if sales_q.empty:
        return [{"headline": "数据不足", "detail": "缺损字段：销售数据/渠道"}]
    
    c_data = sales_q[sales_q["渠道"] == channel]
    if c_data.empty:
        return [{"headline": f"渠道 {channel} 暂无数据", "detail": "请检查销售明细中是否有该渠道匹配。"}]
        
    c_rev = c_data["销售收入"].sum()
    total_rev = sales_q["销售收入"].sum()
    share = c_rev / total_rev if total_rev else 0
    
    res = []
    res.append({
        "headline": f"{channel} 贡献占比为 {share:.1%}，属核心经营渠道",
        "detail": f"**口径**：销售明细实时汇总<br>**关键数字**：该渠道营收额 {fmt_money(c_rev)}。<br>**建议动作**：维持当前投放力度，并监控獲客成本 (CAC) 变动。"
    })
    return res

def get_product_insights(top_products_df, total_rev):
    if top_products_df.empty: return []
    
    top1 = top_products_df.iloc[0]
    top1_share = top1["销售收入"] / total_rev if total_rev else 0
    
    res = []
    res.append({
        "headline": f"头号产品 {top1['产品名称']} 贡献率达 {top1_share:.1%}",
        "detail": f"**口径**：产品 SKU 汇总<br>**关键数字**：Top 1 营收 {fmt_money(top1['销售收入'])}。<br>**建议动作**：针对 Top 产品实施“防守型”库存策略，至少保持 30 天安全周转量。"
    })
    return res

def get_opex_insights(opex_df):
    if opex_df.empty:
        return [{"headline": "运营费用数据欠缺", "detail": "建议补齐《运营费用》表中的“日期”与“金额”字段。"}]
    
    total = opex_df["运营费用"].sum()
    max_m = opex_df.loc[opex_df["运营费用"].idxmin(), "月份"] # 误用了 idxmin 找最高? 修正为 idxmax
    max_m = opex_df.loc[opex_df["运营费用"].idxmax(), "月份"]
    
    return [{
        "headline": f"年度运营费用总支出 {fmt_money(total)}",
        "detail": f"**口径**：费用报表汇总（本位币 CNY）<br>**关键数字**：单月最高支出出现在 {max_m}。<br>**建议动作**：对固定支出进行常态化对标，寻找 5%-10% 的优化空间。"
    }]

def get_platform_grid_insights(df):
    if df.empty: return []
    
    best_roas = df.sort_values("ROAS", ascending=False).iloc[0]
    worst_margin = df.sort_values("贡献利润率", ascending=True).iloc[0]
    
    return [
        {
            "headline": f"投放效率冠軍：{best_roas['平台']}，ROAS 达到 {best_roas['ROAS']:.2f}",
            "detail": f"**口径**：平台费用表实时计算<br>**建议动作**：建议将低效平台的预算向 {best_roas['平台']} 倾斜。"
        },
        {
            "headline": f"边际贡献预警：{worst_margin['平台']} 利润率仅 {worst_margin['贡献利润率']:.1%}",
            "detail": f"**口径**：(收入 - 销售费用) / 收入（不含 COGS）<br>**建议动作**：检查该平台的佣金与物流扣费，确认是否存在计费异常。"
        }
    ]

def get_customer_decision_insights(cust, sales_q):
    if cust.empty: return []
    
    top1 = cust.iloc[0]
    top1_gp = top1["销售收入"] * top1["毛利率"]
    
    return [
        {
            "headline": f"客户集中度分析：Top 1 占据 {top1['占比(收入)']:.1%} 营收份额",
            "detail": f"**口径**：客户/购货单位维度<br>**建议动作**：单一客户占比过高存在违约风险，建议多元化获客途径。"
        },
        {
            "headline": f"利潤贡献分析：{top1['购货单位']} 為核心利潤引擎",
            "detail": f"**关键数字**：预估毛利贡献 {fmt_money(top1['销售毛利'])}。<br>**建议动作**：加强與重要客戶的賬期合作，提高資金週轉率。"
        }
    ]

def get_salesrep_insights(reps_df):
    if reps_df.empty:
        return [{"headline": "业务员数据缺失", "detail": "缺损字段：销售数据/业务员。请确保原始表中存在该列。"}]
    
    top1 = reps_df.iloc[0]
    best_margin = reps_df.sort_values("毛利率", ascending=False).iloc[0]
    
    res = []
    res.append({
        "headline": f"销售冠軍：{top1['业务员']}，贡献率 {top1['占比']:.1%}",
        "detail": f"**口径**：按业务员字段汇总銷售收入<br>**建议动作**：总结 Top 1 的拓客话术与资源配置，向全组推广。"
    })
    res.append({
        "headline": f"利潤标兵：{best_margin['业务员']}，毛利率高达 {best_margin['毛利率']:.1%}",
        "detail": f"**口径**：销售毛利 / 销售收入<br>**建议动作**：分析其成交的产品组合，评估是否具备高客单价/高溢价商品的销售基因。"
    })
    return res

# -----------------------------
# 战略指南针 (Executive Summary)
# -----------------------------
def get_executive_summary(annual_profit, sales, platform):
    if annual_profit.empty or sales.empty:
        return "数据正在加载中..."
    
    total_rev = annual_profit["销售额"].sum()
    last_month = annual_profit.iloc[-1]
    
    # 状态判定
    momentum = "稳健"
    if last_month["销售额"] > annual_profit["销售额"].mean() * 1.2:
        momentum = "强劲增长"
    elif last_month["销售额"] < annual_profit["销售额"].mean() * 0.8:
        momentum = "需关注波动"
        
    summary = f"**經營現狀**：2025 全年營收已達成 {fmt_money(total_rev)}，當前增長趨勢**{momentum}**。 "
    
    if not platform.empty:
        avg_roas = platform["ROAS"].mean()
        summary += f"全渠道平均 ROAS 維持在 **{avg_roas:.2f}**，投放效率良好。 "
        
    summary += "建議關注 Q4 旺季庫存周轉及 2026 預測性備貨。"
    return summary

def render_strategic_header(annual_profit, sales, platform):
    """
    渲染 CEO 战略看板头部：包含数据鲜度、战略摘要
    """
    if annual_profit.empty:
        return
    
    last_data_month = annual_profit["月份"].max()
    summary_text = get_executive_summary(annual_profit, sales, platform)
    
    st.markdown(f"""
    <div style="background: rgba(255, 255, 255, 0.4); backdrop-filter: blur(10px); 
                border-radius: 12px; padding: 15px; border: 1px solid rgba(201, 166, 107, 0.3);
                margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <div style="font-weight: bold; color: #8d7b68; font-size: 1.1em;">🧭 戰略指南針 (Executive Summary)</div>
            <div class="pulse-badge">
                數據更新至：{last_data_month}
            </div>
        </div>
        <div style="color: #555; line-height: 1.6; font-size: 0.95em;">
            {summary_text}
        </div>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------
# 战略行动清单 (Bottom Actions)
# -----------------------------
def render_final_action_checklist():
    with st.container():
        st.markdown("---")
        st.markdown("### 🎯 戰略行動與清單 (CEO Roadmap)")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.checkbox("核對核心渠道 (Amazon/TikTok) 預算遷移執行率", value=False)
            st.checkbox("啟動 Top 10 客戶 Q1 年度返利談判", value=False)
        with c2:
            st.checkbox("審核 2026 備貨計劃（進取型情景下的資金佔用）", value=False)
            st.checkbox("優化低毛利（<15%）客戶的服務成本結構", value=False)
        with c3:
            st.checkbox("評估銷售團隊績效獎金與毛利掛鉤方案", value=False)
            st.caption("✨ 提示：點擊核取方塊可記錄臨時決策思路。")

# -----------------------------
# 辅助处理
# -----------------------------

def rYG(value, green_cond, yellow_cond):
    if pd.isna(value):
        return "—"
    if green_cond(value): return "🟢"
    if yellow_cond(value): return "🟡"
    return "🔴"

# -----------------------------
# 主程序
# -----------------------------
def main():
    inject_css()

    # 侧边栏：强制刷新 & 数据源
    with st.sidebar:
        st.markdown("## 系统控制")
        if st.button("🔄 强制刷新取数", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
            
        st.markdown("---")
        st.markdown("## 数据源")
        # 更新为用户提供的最新确切路径
        default_path = r"D:\财务工作\09-财务报表\2025年\季度、年度报表\2025年度报表\2025年全年.xlsx"
        excel_path = st.sidebar.text_input("本地Excel路径（优先）", value=default_path)
        upload = st.sidebar.file_uploader("或上传 2025年全年.xlsx", type=["xlsx"])

    # 尝试读取数据
    used = None
    fp = None
    if excel_path and os.path.exists(excel_path):
        used = excel_path
        fp = file_fingerprint(excel_path)
    elif upload is not None:
        used = upload
        # 上传文件对象本身作为缓存 key，此处 fp 可留空或用 object id
    else:
        st.warning("未找到本地路径文件，也未上传Excel。请检查路径或上传文件。")
        st.stop()

    # 统一读取
    data = load_all_dashboard_data(used, fp=fp)
    annual_profit = data["annual_profit"]
    cash_cny = data["cash_cny"]
    sales = data["sales"]
    platform = data["platform"]
    opex_df = data["opex_df"]

    # 侧边栏：交互控件
    st.sidebar.markdown("## 交互控制")
    quarter = st.sidebar.selectbox("营收&毛利率趋势（2025）查看区间", ["全年", "Q1", "Q2", "Q3", "Q4"], index=0)
    
    # 2026 预测设置 (Moved up to group with Main Chart Interval)
    forecast_mode = st.sidebar.radio("2026年 销售收入预测", ["悲观 (-10%)", "保守 (+10%)", "基准 (+30%)", "进取 (+50%)"], index=2)
    st.sidebar.markdown("""
    <div style="font-size:12px; color:gray; line-height:1.4; margin-bottom:12px;">
    • <b>悲观</b> (-10%): 假设营收同比下降 10%<br>
    • <b>保守</b> (+10%): 假设营收同比增长 10%<br>
    • <b>基准</b> (+30%): 假设营收同比增长 30%<br>
    • <b>进取</b> (+50%): 假设营收同比增长 50%
    </div>
    """, unsafe_allow_html=True)

    channel = st.sidebar.selectbox("核心渠道趋势", ["亚马逊-US", "TikTok-US", "Juvera", "Shopify", "其他"], index=0)
    marketing_delta = st.sidebar.slider("营销费用率变化（预测年度利润）", -10.0, 10.0, 0.0, 0.5) / 100.0

    st.sidebar.caption("说明：净利润动态模拟 = 基准净利润 −（年度营收 × 营销费率变化）")


    # KPI（年度）
    total_rev = float(annual_profit["销售额"].sum())
    total_np = float(annual_profit["净利润"].sum()) if "净利润" in annual_profit.columns else np.nan
    base_margin = (total_np / total_rev) if total_rev and not np.isnan(total_np) else np.nan

    dyn_np = total_np - (total_rev * marketing_delta) if not np.isnan(total_np) else np.nan
    dyn_margin = (dyn_np / total_rev) if total_rev and not np.isnan(dyn_np) else np.nan

    # 标题
    st.markdown(
        f"""
        <div class="h1">BOLVA CEO 經營決策控制艙 — 2025 <span class="badge">Strategic AI Console</span></div>
        """,
        unsafe_allow_html=True
    )
    
    # 顶部战略指南针 (New)
    render_strategic_header(annual_profit, sales, platform)

    tab1, tab2, tab3 = st.tabs(["经营总览", "费用分析", "客户&业务员分析"])

    # -------------------------
    # Tab1：经营总览
    # -------------------------
    with tab1:
        # KPI 四卡
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            kpi_card("REVENUE", fmt_m(total_rev/1_000_000.0), "", "📈", "年度营收（年度利润表汇总）")
        with c2:
            delta_np_m = (dyn_np - total_np)/1_000_000.0 if not np.isnan(dyn_np) and not np.isnan(total_np) else np.nan
            kpi_card("NET PROFIT", fmt_m(dyn_np/1_000_000.0) if not np.isnan(dyn_np) else "—",
                     f"Δ {fmt_m(delta_np_m)}" if not np.isnan(delta_np_m) else "", "💰", "净利润动态模拟（营销费率滑块）")
        with c3:
            kpi_card("CASH", fmt_m(cash_cny/1_000_000.0), "", "🏦", "银行余额（本位币汇总）")
        with c4:
            kpi_card("MARGIN", fmt_pct(dyn_margin) if not np.isnan(dyn_margin) else "—",
                     f"基准 {fmt_pct(base_margin)}" if not np.isnan(base_margin) else "", "％", "净利率（动态）")

        st.write("")

        st.write("")

        st.write("")

        # 图表布局：左（营收&毛利率 + 渠道趋势）右（Top8产品贡献 + 月度快照）
        left, right = st.columns([1.55, 1.0])

        # 季度过滤
        profit_q = quarter_filter_month_str(annual_profit, quarter, "月份")

        with left:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            
            # 2026 预测数据生成 + 交互控制更新
            df_forecast_2026 = None
            if forecast_mode != "不预测":
                # 简单的 multiplier
                multipliers = {"悲观 (-10%)": 0.9, "保守 (+10%)": 1.1, "基准 (+30%)": 1.3, "进取 (+50%)": 1.5}
                rate = multipliers.get(forecast_mode, 1.0)
                
                # 生成 2026 全年 (基于 2025 每月 * rate) -> 保持季节性
                df_full_2026 = annual_profit[["月份", "销售额"]].copy()
                df_full_2026["销售额"] = df_full_2026["销售额"] * rate
                
                # 月份 +1 年
                def add_one_year(m_str):
                    # 假设格式 YYYY-MM
                    try:
                        y, m = m_str.split("-")
                        return f"{int(y)+1}-{int(m):02d}"
                    except:
                        return m_str
                
                df_full_2026["月份"] = df_full_2026["月份"].apply(add_one_year)
                
                # ✅ 关键交互：2026数据也跟随“查看区间”筛选
                if quarter == "全年":
                    df_forecast_2026 = df_full_2026
                else:
                    # 复用筛选函数逻辑（Q1筛选会找 2025-01..03，这里需要转换一下思路）
                    # quarter_filter_month_str 里面用的是 hardcode 的 "2025-01"
                    # 所以如果直接传 2026的月份进去，会筛选不到。
                    
                    # 修正策略：
                    # 1. 先把 annual_profit (2025) 筛选出对应季度 profit_q
                    # 2. 基于 profit_q 直接生成 2026 预测
                    
                    # 重新基于 profit_q 生成
                    df_forecast_2026 = profit_q[["月份", "销售额"]].copy()
                    df_forecast_2026["销售额"] = df_forecast_2026["销售额"] * rate
                    df_forecast_2026["月份"] = df_forecast_2026["月份"].apply(add_one_year)

            st.plotly_chart(rev_np_forecast_chart(profit_q, df_forecast_2026), use_container_width=True)
            render_insight_module("营收与预测", get_revenue_trend_insights(profit_q, df_forecast_2026, quarter, forecast_mode))
            st.markdown("</div>", unsafe_allow_html=True)

            st.write("")
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.plotly_chart(channel_trend_chart(sales, channel, quarter), use_container_width=True)
            sales_q = quarter_filter_month_str(sales, quarter, "月份")
            render_insight_module("渠道趋势", get_channel_trend_insights(sales_q, channel))
            st.markdown("</div>", unsafe_allow_html=True)

        with right:
            Top8 = top_products(sales, topn=8)

            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.plotly_chart(product_bar_chart(Top8), use_container_width=True)
            render_insight_module("产品贡献", get_product_insights(Top8, sales_q["销售收入"].sum()))
            st.caption("口径：销售数据按产品名称汇总（Top8 + Others）。悬停条形可查看金额。")
            st.markdown("</div>", unsafe_allow_html=True)

            st.write("")
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.subheader("月度快照（年度利润）")
            snap = profit_q.copy()
            snap["销售额"] = snap["销售额"].map(lambda x: f"¥{x/1_000_000:,.2f}M")
            if "毛利率" in snap.columns: snap["毛利率"] = snap["毛利率"].map(lambda x: f"{x*100:.1f}%" if pd.notnull(x) else "")
            if "净利润" in snap.columns: snap["净利润"] = snap["净利润"].map(lambda x: f"¥{x/1_000_000:,.2f}M" if pd.notnull(x) else "")
            if "净利率" in snap.columns: snap["净利率"] = snap["净利率"].map(lambda x: f"{x*100:.1f}%" if pd.notnull(x) else "")
            st.dataframe(snap, use_container_width=True, height=280)
            st.markdown("</div>", unsafe_allow_html=True)

    # -------------------------
    # Tab2：费用分析
    # -------------------------
    with tab2:

        if platform.empty:
            st.info("未读取到《平台 销售费用比》，请检查工作表名称/表头列名。")
        else:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.subheader("各平台｜年度费用指标（自动计算）")

            col_a, col_b, col_c = st.columns([1.4, 1.2, 1.4])
            with col_a:
                # 平台筛选：改为下拉单选 (Selectbox)
                all_platforms = ["全部平台"] + sorted(platform["平台"].unique().tolist())
                selected_platform = st.selectbox("平台筛选", all_platforms, index=0)
                
                # 兼容原有逻辑：platforms 需为列表
                if selected_platform == "全部平台":
                     platforms = sorted(platform["平台"].unique().tolist())
                else:
                     platforms = [selected_platform]
            with col_b:
                sort_by = st.selectbox("排序方式", ["总销售费用率", "ROAS", "贡献利润率"], index=0)
            with col_c:
                st.markdown(
                    "<span title='总费用率>55%红；45-55黄；<45绿'>ⓘ 总费用率阈值</span> ｜ "
                    "<span title='ROAS<3红；3-5黄；>5绿'>ⓘ ROAS阈值</span> ｜ "
                    "<span title='物流费率>25%红'>ⓘ 物流费率阈值</span>",
                    unsafe_allow_html=True
                )

            d = platform.copy()
            if platforms:
                d = d[d["平台"].isin(platforms)].copy()

            # 红黄绿灯号
            d["总费用灯"] = d["总销售费用率"].apply(lambda v: rYG(v, lambda x: x < 0.45, lambda x: 0.45 <= x <= 0.55))
            d["ROAS灯"] = d["ROAS"].apply(lambda v: rYG(v, lambda x: x > 5, lambda x: 3 <= x <= 5))
            d["物流灯"] = d["物流费率"].apply(lambda v: rYG(v, lambda x: x < 0.15, lambda x: 0.15 <= x <= 0.25))

            # 排序
            if sort_by in ["ROAS", "贡献利润率"]:
                d = d.sort_values(sort_by, ascending=False)
            else:
                d = d.sort_values(sort_by, ascending=False)

            show_cols = [
                "平台","渠道","销售收入","总销售费用","总销售费用率","ROAS","贡献利润率",
                "广告费率","物流费率","佣金率","折扣/补贴率",
                "总费用灯","ROAS灯","物流灯"
            ]
            show = d[show_cols].copy()

            # 格式化
            for c in ["销售收入","总销售费用"]:
                show[c] = show[c].map(fmt_money)
            for c in ["总销售费用率","贡献利润率","广告费率","物流费率","佣金率","折扣/补贴率"]:
                show[c] = show[c].map(lambda x: f"{x*100:.1f}%" if pd.notnull(x) else "")
            show["ROAS"] = show["ROAS"].map(lambda x: f"{x:,.2f}" if pd.notnull(x) else "")

            st.dataframe(show, use_container_width=True, height=360)
            st.markdown("</div>", unsafe_allow_html=True)

            st.write("")
            fig1, fig2 = platform_charts(d)
            l, r = st.columns([1.3, 1.0])
            with l:
                st.markdown('<div class="panel">', unsafe_allow_html=True)
                st.plotly_chart(fig1, use_container_width=True)
                render_insight_module("平台费用效率", get_platform_grid_insights(d))
                st.markdown("</div>", unsafe_allow_html=True)

                st.write("")
                st.markdown('<div class="panel">', unsafe_allow_html=True)
                st.plotly_chart(fig2, use_container_width=True)
                render_insight_module("费用结构洞察", [
                    {"headline": "关注高占比物流费率", "detail": "若物流费率高于 25%，建议检查超重/超尺寸计费是否准确。"},
                    {"headline": "佣金结构对标", "detail": "对标各平台佣金政策，评估是否可以通过调整 SKU 组合降低整体扣费率。"}
                ])
                st.markdown("</div>", unsafe_allow_html=True)

            with r:
                st.markdown('<div class="panel">', unsafe_allow_html=True)
                st.subheader("单个平台快照（点击ⓘ）")
                psel = st.selectbox("选择平台", d["平台"].tolist(), index=0)
                row = d[d["平台"] == psel].iloc[0]

                m1, m2, m3 = st.columns(3)
                with m1:
                    st.metric("总销售费用率", f"{row['总销售费用率']*100:.1f}%")
                with m2:
                    st.metric("ROAS", f"{row['ROAS']:.2f}" if pd.notnull(row["ROAS"]) else "—")
                with m3:
                    st.metric("贡献利润率", f"{row['贡献利润率']*100:.1f}%")

                with st.popover("ⓘ 指标解释"):
                    st.write("- 总销售费用率 = 总销售费用 / 销售收入")
                    st.write("- ROAS = 销售收入 / 广告费")
                    st.write("- 贡献利润率 = (销售收入 - 总销售费用) / 销售收入（仅扣销售费用，不含COGS）")

                comp = pd.DataFrame({
                    "费用项":["广告费","物流费","佣金","折扣/补贴"],
                    "金额":[row["广告费"], row["物流费"], row["佣金"], row["销售折扣/补贴"]],
                })
                fig = px.bar(comp, x="费用项", y="金额", title=f"{psel}｜费用构成（金额）", template=TEMPLATE)
                fig.update_traces(
                    marker_color="rgba(201,166,107,0.8)", # 珠光香槟金
                    marker_line_color="rgba(201,166,107,1)",
                    marker_line_width=1,
                    hovertemplate="费用项：%{x}<br>金额：¥%{y:,.2f}<extra></extra>"
                )
                fig.update_layout(height=300)
                st.plotly_chart(apply_plot_style(fig), use_container_width=True)
                render_insight_module(f"{psel} 深度诊断", [
                    {"headline": "费用平衡性检查", "detail": "检查当前广告费与销量的弹性关系，若广告增长快于销量，建议降低非核心词竞价。"}
                ])
                st.markdown("</div>", unsafe_allow_html=True)
        if opex_df.empty:
            st.info("💡 未读取到有效的运营费用数据（请检查《运营费用》表中的“日期”与“金额”列）。")
        else:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.subheader("年度运营费用分析")

            # 简单 KPI
            total_opex = opex_df["运营费用"].sum()
            c_op1, c_op2 = st.columns([1, 3])
            with c_op1:
                st.metric("年度运营费用合计", fmt_money(total_opex))
            with c_op2:
                fig_opex = px.bar(opex_df, x="月份", y="运营费用", title="运营费用｜月度趋势", template=TEMPLATE)
                fig_opex.update_traces(marker_color="rgba(201,166,107,0.6)", hovertemplate="月份：%{x}<br>费用：¥%{y:,.2f}<extra></extra>")
                fig_opex.update_layout(height=260, margin=dict(t=30, b=0))
                st.plotly_chart(apply_plot_style(fig_opex), use_container_width=True)
                render_insight_module("运营费用", get_opex_insights(opex_df))
            st.markdown("</div>", unsafe_allow_html=True)
            st.write("")
            
    # -------------------------
    # Tab3：客户&业务员分析
    # -------------------------
    with tab3:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.subheader("客户年度经营洞察（Top10决策视图）")
        
        # 核心筛选过滤
        sales_q = quarter_filter_month_str(sales, quarter, "月份")
        
        # B2B / B2C 总收入汇总 (基于业务类型列)
        b2b_rev = sales_q[sales_q["业务类型"].str.upper() == "B2B"]["销售收入"].sum()
        b2c_rev = sales_q[sales_q["业务类型"].str.upper() == "B2C"]["销售收入"].sum()
        
        c_k1, c_k2, c_k3 = st.columns([1, 1, 2])
        with c_k1:
            kpi_card("B2B 总收入", fmt_money(b2b_rev), "", "🏢", "筛选区间内 B2B 渠道销售额总計")
        with c_k2:
            kpi_card("B2C 总收入", fmt_money(b2c_rev), "", "🛒", "筛选区间内 B2C 渠道销售額總計")
        with c_k3:
            st.write("")

        col_ctrl1, col_ctrl2 = st.columns([1, 2])
        with col_ctrl1:
            sort_by = st.radio("Top10 排序依据", ["销售收入", "销售毛利"], index=0, horizontal=True)
        with col_ctrl2:
            st.caption("✨ 提示：主渠道显示为 Multi 表示该客户在单一渠道占比低于 60%。")

        cust = top_customers(sales_q, topn=10, sort_by=sort_by)

        if cust.empty:
            st.warning("当前筛选条件下未发现有效的销售记录。")
        else:
            # 数据美化展示
            cust_show = cust.copy()
            cust_show["销售收入"] = cust_show["销售收入"].map(fmt_money)
            cust_show["销售毛利"] = cust_show["销售毛利"].map(fmt_money)
            cust_show["毛利率"] = cust_show["毛利率"].map(lambda x: f"{x*100:.1f}%")
            cust_show["累计占比(收入)"] = cust_show["累计占比(收入)"].map(lambda x: f"{x*100:.1f}%")
            cust_show["累计占比(毛利)"] = cust_show["累计占比(毛利)"].map(lambda x: f"{x*100:.1f}%")
            
            st.dataframe(cust_show[["购货单位", "业务类型", "销售收入", "销售毛利", "毛利率", "累计占比(收入)", "累计占比(毛利)"]].rename(columns={"业务类型": "渠道"}), 
                         use_container_width=True, height=340)

            st.write("")
            
            # 图表：帕累托 + 效率矩阵
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(customer_pareto_chart(cust), use_container_width=True)
            with c2:
                st.plotly_chart(customer_efficiency_matrix(sales_q, cust["购货单位"].tolist()), use_container_width=True)
            
            st.write("")
            st.plotly_chart(customer_channel_dist_chart(sales_q, cust["购货单位"].tolist()), use_container_width=True)

            # 统一洞察模块
            render_insight_module("客户经营", get_customer_decision_insights(cust, sales_q))

        st.markdown("</div>", unsafe_allow_html=True)

        st.write("")

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.subheader("业务员｜年度销售分析")

        repN = 10
        reps = top_salesreps(sales, topn=repN)

        if reps.empty:
            st.warning("未检测到《销售数据》中的“业务员/销售员”列（或全为空）。如需该模块，请在销售数据表中加入“业务员”列。")
        else:
            reps_show = reps.copy()
            reps_show["销售收入"] = reps_show["销售收入"].map(fmt_money)
            reps_show["销售毛利"] = reps_show["销售毛利"].map(fmt_money)
            reps_show["占比"] = reps_show["占比"].map(lambda x: f"{x*100:.1f}%")
            reps_show["毛利率"] = reps_show["毛利率"].map(lambda x: f"{x*100:.1f}%")
            
            st.dataframe(reps_show[["业务员", "销售收入", "销售毛利", "毛利率", "占比"]], use_container_width=True, height=320)

            fig = px.bar(reps, x="业务员", y="销售收入", title="业务员年度销售额（Top10）", template=TEMPLATE)
            fig.update_traces(hovertemplate="业务员：%{x}<br>销售收入：¥%{y:,.2f}<extra></extra>")
            fig.update_layout(height=380)
            st.plotly_chart(apply_plot_style(fig), use_container_width=True)
            render_insight_module("业务员绩效", get_salesrep_insights(reps))

        st.markdown("</div>", unsafe_allow_html=True)

    # 底部战略行动建议 (New Grand Finale)
    render_final_action_checklist()

    st.caption("© BOLVA — CEO Strategic Console (2025) | Data-Driven Decision Engine | Cream Gold Lux Edition")

if __name__ == "__main__":
    main()
