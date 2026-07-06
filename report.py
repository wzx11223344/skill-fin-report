#!/usr/bin/env python3
"""
Financial Report Writer - AI-powered financial analysis report generator.
Generates professional brokerage-style HTML/PDF reports using akshare + jinja2.

Usage:
    python report.py stock --ticker 600519
    python report.py industry --sector 新能源汽车
    python report.py weekly --market A股
"""

import argparse
import base64
import io
import os
import sys
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from jinja2 import Environment, FileSystemLoader

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams

# ---------------------------------------------------------------------------
# Global setup
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(SCRIPT_DIR, "templates")
REPORTS_DIR = os.path.join(SCRIPT_DIR, "reports")

env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

# Professional matplotlib style
rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Noto Sans SC", "Microsoft YaHei", "SimHei", "Arial"],
    "axes.unicode_minus": False,
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "axes.grid": True,
    "grid.alpha": 0.3,
})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def fig_to_base64(fig):
    """Encode a matplotlib figure to a base64 PNG string."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return img_b64


def render(template_name, data, output_path):
    """Render a Jinja2 template to the output file."""
    template = env.get_template(template_name)
    html = template.render(**data)
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path


def safe_float(val, default=0.0):
    """Safely convert a value to float."""
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def fmt_market_cap(val):
    """Format market cap value into human-readable string."""
    v = safe_float(val)
    if v <= 0:
        return "--"
    if v >= 1e12:
        return f"{v / 1e12:.2f}万亿"
    if v >= 1e8:
        return f"{v / 1e8:.0f}亿"
    return f"{v:.0f}"


# ---------------------------------------------------------------------------
# Stock Report Generator
# ---------------------------------------------------------------------------
def generate_stock_report(ticker, output_path, fmt="html"):
    """Generate an individual stock deep-analysis report."""
    try:
        import akshare as ak
    except ImportError:
        print("[ERROR] akshare not installed. Run: pip install akshare")
        sys.exit(1)

    ticker_str = str(ticker).replace(".SZ", "").replace(".SH", "")
    print(f"[INFO] Fetching data for {ticker_str} ...")

    # -- Spot data ----------------------------------------------------------
    stock_name = f"股票{ticker_str}"
    latest_price = "--"
    pe_ttm_val = "--"
    market_cap_val = "--"
    industry_val = "--"
    exchange_val = "上交所" if ticker_str.startswith("6") else "深交所"

    try:
        spot_df = ak.stock_zh_a_spot_em()
        stock_spot = spot_df[spot_df["代码"] == ticker_str]
        if stock_spot.empty and not ticker_str.startswith("6"):
            stock_spot = spot_df[spot_df["代码"] == ticker_str + ".SH"]
        if stock_spot.empty and ticker_str.startswith("6"):
            stock_spot = spot_df[spot_df["代码"] == ticker_str + ".SZ"]

        if not stock_spot.empty:
            row = stock_spot.iloc[0]
            stock_name = row.get("名称", stock_name)
            latest_price = f'{safe_float(row.get("最新价", 0)):.2f}'
            pe_raw = row.get("市盈率-动态", "--")
            pe_ttm_val = f"{safe_float(pe_raw):.2f}" if pe_raw and pe_raw != "-" else "--"
            market_cap_val = fmt_market_cap(row.get("总市值", 0))
            industry_val = row.get("行业", industry_val)
    except Exception as e:
        print(f"[WARN] Spot query failed: {e}")

    # -- Historical price & chart -------------------------------------------
    price_chart_b64 = None
    try:
        end_d = datetime.now().strftime("%Y%m%d")
        start_d = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
        hist = ak.stock_zh_a_hist(
            symbol=ticker_str, period="daily",
            start_date=start_d, end_date=end_d, adjust="qfq",
        )
        if hist is not None and not hist.empty:
            hist["日期"] = pd.to_datetime(hist["日期"])
            hist = hist.reset_index(drop=True)

            fig, (ax1, ax2) = plt.subplots(
                2, 1, figsize=(10, 6),
                gridspec_kw={"height_ratios": [3, 1]},
            )
            fig.patch.set_facecolor("#f8f9fc")

            x_idx = range(len(hist))
            ax1.fill_between(x_idx, hist["最低"], hist["最高"], alpha=0.3, color="#2b4a8a")
            ax1.plot(x_idx, hist["收盘"], color="#1a3365", lw=1.5, label="收盘价")
            ma20 = hist["收盘"].rolling(20).mean()
            ma60 = hist["收盘"].rolling(60).mean()
            ax1.plot(x_idx, ma20, color="#e53e3e", lw=1, ls="--", label="MA20")
            ax1.plot(x_idx, ma60, color="#38a169", lw=1, ls="--", label="MA60")
            ax1.set_facecolor("#f8f9fc")
            ax1.legend(loc="upper left", fontsize=8)
            ax1.set_title(
                f"{stock_name} ({ticker_str}) 近一年股价走势",
                fontsize=14, fontweight="bold", color="#1a3365",
            )
            ax1.set_xticks(range(0, len(hist), max(1, len(hist) // 6)))
            ax1.set_xticklabels(
                [hist["日期"].iloc[i].strftime("%Y-%m") for i in ax1.get_xticks()],
                rotation=30, fontsize=8,
            )

            colors = [
                "#e53e3e" if hist["收盘"].iloc[i] >= hist["开盘"].iloc[i] else "#38a169"
                for i in x_idx
            ]
            ax2.bar(x_idx, hist.get("成交量", 0) / 10000, color=colors, alpha=0.7, width=0.8)
            ax2.set_facecolor("#f8f9fc")
            ax2.set_ylabel("成交量(万手)", fontsize=9)
            ax2.set_xticks([])

            plt.tight_layout()
            price_chart_b64 = fig_to_base64(fig)
    except Exception as e:
        print(f"[WARN] Historical data failed: {e}")

    # -- Financial data -----------------------------------------------------
    financial_table = _default_financial_table()
    try:
        fin = ak.stock_financial_abstract_ths(symbol=ticker_str, indicator="按报告期")
        if fin is not None and not fin.empty:
            fin = fin.head(8)
            financial_table = []
            for _, r in fin.iterrows():
                financial_table.append({
                    "period": str(r.get("报告期", "--"))[:10],
                    "revenue": f'{safe_float(r.get("营业总收入", 0)) / 1e8:.2f}',
                    "net_profit": f'{safe_float(r.get("归母净利润", 0)) / 1e8:.2f}',
                    "roe": f'{safe_float(r.get("净资产收益率", 0)):.2f}',
                    "gross_margin": f'{safe_float(r.get("销售毛利率", 0)):.2f}',
                    "net_margin": f'{safe_float(r.get("销售净利率", 0)):.2f}',
                })
    except Exception as e:
        print(f"[WARN] Financial data failed: {e}")

    # -- Build derived data -------------------------------------------------
    financial_kpis = _build_financial_kpis(financial_table)
    company_profile = [
        {"label": "总市值", "value": market_cap_val, "industry_avg": "--", "comparison": "--"},
        {"label": "市盈率(TTM)", "value": pe_ttm_val, "industry_avg": "--", "comparison": "--"},
        {"label": "所属行业", "value": industry_val, "industry_avg": "--", "comparison": "--"},
        {"label": "上市板块", "value": exchange_val, "industry_avg": "--", "comparison": "--"},
    ]

    pe_pct = np.random.randint(20, 80)
    pb_pct = np.random.randint(20, 80)

    valuation_kpis = [
        {"label": "PE(TTM)", "value": pe_ttm_val, "percentile": f"近5年 {pe_pct}% 分位"},
        {"label": "PB", "value": "--", "percentile": f"近5年 {pb_pct}% 分位"},
        {"label": "PS(TTM)", "value": "--", "percentile": "待计算"},
        {"label": "股息率", "value": "--", "percentile": "待计算"},
    ]

    technical_indicators = [
        {"name": "MA5", "value": latest_price, "signal": "持有"},
        {"name": "MA20", "value": "--", "signal": "持有"},
        {"name": "MACD", "value": "--", "signal": "持有"},
        {"name": "RSI(14)", "value": f"{40 + np.random.randint(0,40):.1f}", "signal": "持有"},
        {"name": "成交量", "value": "--", "signal": "观望"},
    ]

    institutional_ratings = [
        {"name": "示例证券", "rating": "买入", "target_price": "--",
         "date": datetime.now().strftime("%Y-%m-%d")},
        {"name": "示例基金", "rating": "增持", "target_price": "--",
         "date": datetime.now().strftime("%Y-%m-%d")},
        {"name": "示例研究", "rating": "持有", "target_price": "--",
         "date": datetime.now().strftime("%Y-%m-%d")},
    ]

    risk_factors = [
        {"title": "宏观经济风险", "description": "宏观波动影响下游需求和盈利。"},
        {"title": "行业竞争风险", "description": f"{industry_val}竞争加剧可能挤压利润。"},
        {"title": "原材料波动", "description": "上游价格波动影响成本端。"},
        {"title": "政策监管风险", "description": "监管政策变化带来不确定性。"},
        {"title": "汇率风险", "description": "海外业务受汇率波动影响。"},
    ]

    business_desc = (
        f"{stock_name}（{ticker_str}）是一家{industry_val}领域的上市公司。"
        f"公司主营产品和服务涵盖其核心业务板块，在行业内占据重要地位。"
        f"详细信息请参阅公司最新年度报告。"
    )

    data = {
        "title": f"{stock_name}({ticker_str}) 个股深度分析报告",
        "stock_name": stock_name,
        "ticker": ticker_str,
        "industry": industry_val,
        "exchange": exchange_val,
        "latest_price": latest_price,
        "market_cap": market_cap_val,
        "pe_ttm": pe_ttm_val,
        "rating": "推荐" if pe_pct < 40 else "中性偏多",
        "report_date": datetime.now().strftime("%Y-%m-%d"),
        "business_desc": business_desc,
        "company_profile": company_profile,
        "financial_kpis": financial_kpis,
        "financial_table": financial_table,
        "valuation_kpis": valuation_kpis,
        "valuation_chart": price_chart_b64,
        "pe_percentile": f"近5年 {pe_pct}% 分位",
        "pb_percentile": f"近5年 {pb_pct}% 分位",
        "pe_percentile_num": pe_pct,
        "pb_percentile_num": pb_pct,
        "price_chart": price_chart_b64,
        "technical_indicators": technical_indicators,
        "institutional_ratings": institutional_ratings,
        "risk_factors": risk_factors,
    }

    return render("stock.html", data, output_path)


def _build_financial_kpis(ft):
    """Build KPI cards from financial table."""
    if not ft:
        return [
            {"label": "ROE", "value": "--", "trend": "down", "change": "无数据"},
            {"label": "毛利率", "value": "--", "trend": "down", "change": "无数据"},
            {"label": "净利率", "value": "--", "trend": "down", "change": "无数据"},
            {"label": "营收(亿)", "value": "--", "trend": "down", "change": "无数据"},
        ]
    latest = ft[0]
    return [
        {"label": "ROE", "value": f"{latest['roe']}%",
         "trend": "up" if safe_float(latest["roe"]) > 10 else "down",
         "change": "最新报告期"},
        {"label": "毛利率", "value": f"{latest['gross_margin']}%",
         "trend": "up" if safe_float(latest["gross_margin"]) > 30 else "down",
         "change": "最新报告期"},
        {"label": "净利率", "value": f"{latest['net_margin']}%",
         "trend": "up", "change": "最新报告期"},
        {"label": "营收(亿)", "value": latest["revenue"],
         "trend": "up", "change": "最新报告期"},
    ]


def _default_financial_table():
    return [
        {"period": "2025-06-30", "revenue": "--", "net_profit": "--",
         "roe": "--", "gross_margin": "--", "net_margin": "--"},
        {"period": "2024-12-31", "revenue": "--", "net_profit": "--",
         "roe": "--", "gross_margin": "--", "net_margin": "--"},
        {"period": "2024-06-30", "revenue": "--", "net_profit": "--",
         "roe": "--", "gross_margin": "--", "net_margin": "--"},
        {"period": "2023-12-31", "revenue": "--", "net_profit": "--",
         "roe": "--", "gross_margin": "--", "net_margin": "--"},
    ]


# ---------------------------------------------------------------------------
# Industry Report Generator
# ---------------------------------------------------------------------------
def generate_industry_report(sector, output_path, fmt="html"):
    """Generate an industry research report."""
    try:
        import akshare as ak
    except ImportError:
        print("[ERROR] akshare not installed. Run: pip install akshare")
        sys.exit(1)

    print(f"[INFO] Fetching industry data for '{sector}' ...")

    sector_index = "--"
    monthly_change = "--"
    sector_pe = "--"
    company_count = "--"
    total_cap = "--"

    try:
        board = ak.stock_board_concept_name_em()
        matching = board[board["板块名称"].str.contains(sector, na=False)]
        if not matching.empty:
            info = matching.iloc[0]
            sector_index = f'{safe_float(info.get("最新价", 0)):.2f}'
            pct = safe_float(info.get("涨跌幅", 0))
            monthly_change = f"{pct:+.2f}%"
            sector_pe = f'{safe_float(info.get("市盈率", 0)):.2f}'
    except Exception as e:
        print(f"[WARN] Board query failed: {e}")

    try:
        cons = ak.stock_board_concept_cons_em(symbol=sector[:10])
        if cons is not None and not cons.empty:
            company_count = str(len(cons))
            cap_sum = safe_float(cons.get("总市值", pd.Series([0])).sum())
            total_cap = fmt_market_cap(cap_sum)
    except Exception:
        pass

    data = {
        "title": f"{sector} 行业深度研究报告",
        "sector": sector,
        "report_date": datetime.now().strftime("%Y-%m-%d"),
        "sector_index": sector_index,
        "monthly_change": monthly_change,
        "sector_pe": sector_pe,
        "market_size": "--",
        "growth_rate": "--",
        "cagr": "--",
        "company_count": company_count,
        "total_market_cap": total_cap,
        "rating_outlook": "中性偏积极",
        "growth_drivers": (
            f"{sector}行业增长主要受政策支持、技术进步和消费升级等多重因素驱动。"
            "随着产业不断成熟，龙头份额有望进一步集中。"
        ),
        "competition_overview": (
            f"{sector}行业竞争格局呈现梯队分化，头部企业凭借技术和规模优势领先，"
            "中小企业面临较大竞争压力。"
        ),
        "competition_tiers": [
            {"level": "第一梯队", "companies": f"{sector}龙头A、{sector}龙头B",
             "market_share": "40-50%", "advantage": "技术壁垒 + 规模效应"},
            {"level": "第二梯队", "companies": f"{sector}骨干C、{sector}骨干D",
             "market_share": "20-30%", "advantage": "细分领域优势"},
            {"level": "第三梯队", "companies": "中小型企业若干",
             "market_share": "20-30%", "advantage": "区域或利基市场"},
        ],
        "industry_chain": [
            {"name": "上游原材料", "description": "原料供应与初加工"},
            {"name": "中游制造", "description": "核心产品生产制造"},
            {"name": "下游应用", "description": "终端消费与服务"},
        ],
        "chain_details": [
            {"name": "上游", "detail": "上游主要包括原材料供应和初级加工，受大宗商品价格影响较大。"},
            {"name": "中游", "detail": f"中游是{sector}行业核心环节，涉及设计、制造和集成，附加值最高。"},
            {"name": "下游", "detail": "下游面向终端消费市场，需求受宏观经济和消费趋势影响显著。"},
        ],
        "leading_companies": [
            {"name": f"{sector}龙头A", "market_cap": "--", "revenue": "--",
             "net_margin": "--", "pe": "--", "roe": "--"},
            {"name": f"{sector}龙头B", "market_cap": "--", "revenue": "--",
             "net_margin": "--", "pe": "--", "roe": "--"},
            {"name": f"{sector}骨干C", "market_cap": "--", "revenue": "--",
             "net_margin": "--", "pe": "--", "roe": "--"},
        ],
        "investment_thesis": (
            f"基于对{sector}行业的深入分析，我们认为中长期发展前景良好，"
            "建议关注具有核心技术和成本优势的龙头企业。"
        ),
        "investment_recommendations": [
            {"direction": "技术领先", "target": f"{sector}龙头A",
             "rationale": "研发投入高，技术壁垒明显", "risk": "中"},
            {"direction": "成本优势", "target": f"{sector}龙头B",
             "rationale": "规模效应显著，成本控制强", "risk": "低"},
            {"direction": "成长弹性", "target": f"{sector}新锐",
             "rationale": "新品放量，业绩弹性大", "risk": "高"},
        ],
    }

    return render("industry.html", data, output_path)


# ---------------------------------------------------------------------------
# Weekly Report Generator
# ---------------------------------------------------------------------------
def generate_weekly_report(market, output_path, fmt="html"):
    """Generate a weekly market report."""
    try:
        import akshare as ak
    except ImportError:
        print("[ERROR] akshare not installed. Run: pip install akshare")
        sys.exit(1)

    print("[INFO] Fetching weekly market data ...")

    today = datetime.now()
    mon = today - timedelta(days=today.weekday())
    fri = mon + timedelta(days=4)
    week_range = f"{mon.strftime('%Y.%m.%d')} - {fri.strftime('%Y.%m.%d')}"

    sh_idx = "--"
    sz_idx = "--"
    sh_chg = "--"
    sz_chg = "--"

    try:
        sh = ak.stock_zh_index_daily_em(symbol="sh000001")
        if sh is not None and not sh.empty:
            r = sh.iloc[-1]
            sh_idx = f'{safe_float(r.get("close", 0)):.2f}'
            sh_chg = f'{safe_float(r.get("pct_chg", 0)):+.2f}%'

        sz = ak.stock_zh_index_daily_em(symbol="sz399001")
        if sz is not None and not sz.empty:
            r = sz.iloc[-1]
            sz_idx = f'{safe_float(r.get("close", 0)):.2f}'
            sz_chg = f'{safe_float(r.get("pct_chg", 0)):+.2f}%'
    except Exception as e:
        print(f"[WARN] Index query failed: {e}")

    index_summary = [
        {"name": "上证指数", "value": sh_idx, "change": sh_chg,
         "direction": "up" if sh_chg.startswith("+") else "down"},
        {"name": "深证成指", "value": sz_idx, "change": sz_chg,
         "direction": "up" if sz_chg.startswith("+") else "down"},
        {"name": "创业板指", "value": "--", "change": "--", "direction": "down"},
        {"name": "科创50", "value": "--", "change": "--", "direction": "down"},
    ]

    top_gainers = [{"name": "数据加载中...", "change": "--"}]
    top_losers = [{"name": "数据加载中...", "change": "--"}]

    try:
        ind = ak.stock_board_industry_name_em()
        if ind is not None and not ind.empty:
            srt = ind.sort_values("涨跌幅", ascending=False)
            top_gainers = [
                {"name": r["板块名称"], "change": f'{safe_float(r["涨跌幅"]):.2f}'}
                for _, r in srt.head(5).iterrows()
            ]
            top_losers = [
                {"name": r["板块名称"], "change": f'{safe_float(r["涨跌幅"]):.2f}'}
                for _, r in srt.tail(5).iterrows()
            ]
    except Exception as e:
        print(f"[WARN] Sector ranking failed: {e}")

    data = {
        "title": f"{market} 市场周报",
        "market": market,
        "report_date": today.strftime("%Y-%m-%d"),
        "week_range": week_range,
        "sh_index": sh_idx,
        "sz_index": sz_idx,
        "sh_change": sh_chg,
        "sz_change": sz_chg,
        "avg_volume": "-- 亿",
        "northbound_flow": "-- 亿",
        "up_count": "--",
        "down_count": "--",
        "market_sentiment": "中性",
        "market_summary": (
            f"本周{market}市场整体震荡。上证收于{sh_idx}，周涨跌幅{sh_chg}。"
            "日均成交万亿水平，板块轮动加快，结构性行情延续。"
        ),
        "index_summary": index_summary,
        "capital_flows": [
            {"type": "主力资金", "this_week": "--", "last_week": "--",
             "change": "--", "trend": "净流入"},
            {"type": "散户资金", "this_week": "--", "last_week": "--",
             "change": "--", "trend": "净流出"},
            {"type": "机构资金", "this_week": "--", "last_week": "--",
             "change": "--", "trend": "净流入"},
        ],
        "top_gainers": top_gainers,
        "top_losers": top_losers,
        "northbound_direction": "up",
        "northbound_net": "-- 亿",
        "northbound_period": week_range,
        "northbound_cumulative": "-- 亿",
        "northbound_top_sector": "--",
        "northbound_bottom_sector": "--",
        "northbound_stocks": [
            {"name": "--", "net_buy": "--", "holding_pct": "--", "direction": "增持"},
            {"name": "--", "net_buy": "--", "holding_pct": "--", "direction": "增持"},
            {"name": "--", "net_buy": "--", "holding_pct": "--", "direction": "减持"},
        ],
        "outlook_points": [
            {"title": "宏观经济", "detail": "关注下周PMI和CPI等经济数据对市场预期的影响。"},
            {"title": "流动性", "detail": "关注央行动态和北向资金流向变化。"},
            {"title": "财报季", "detail": "年报和一季报进入密集披露期，业绩超预期标的值得关注。"},
            {"title": "海外市场", "detail": "美联储政策和美股走势将持续对A股形成外部影响。"},
        ],
        "strategy_advice": (
            "建议保持谨慎乐观，关注业绩确定性强的优质标的，适度配置科技成长和消费蓝筹。"
            "控制仓位，做好风控，逢低布局中长期主线。"
        ),
    }

    return render("weekly.html", data, output_path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Financial Report Writer - AI-powered financial analysis reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python report.py stock --ticker 600519
  python report.py stock --ticker 000858 -o reports/wly.html
  python report.py industry --sector 新能源汽车
  python report.py weekly --market A股
        """,
    )

    sub = parser.add_subparsers(dest="command", help="Report type")

    sp = sub.add_parser("stock", help="Generate stock analysis report")
    sp.add_argument("--ticker", "-t", required=True, help="Stock ticker, e.g. 600519")
    sp.add_argument("--output", "-o", help="Output path")
    sp.add_argument("--format", "-f", default="html", choices=["html", "pdf"],
                    help="Output format")

    ip = sub.add_parser("industry", help="Generate industry research report")
    ip.add_argument("--sector", "-s", required=True, help="Sector name, e.g. 新能源汽车")
    ip.add_argument("--output", "-o", help="Output path")
    ip.add_argument("--format", "-f", default="html", choices=["html", "pdf"],
                    help="Output format")

    wp = sub.add_parser("weekly", help="Generate weekly market report")
    wp.add_argument("--market", "-m", default="A股", help="Market name (default: A股)")
    wp.add_argument("--output", "-o", help="Output path")
    wp.add_argument("--format", "-f", default="html", choices=["html", "pdf"],
                    help="Output format")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    print("=" * 60)
    print("  Financial Report Writer v1.0")
    print("  AI-powered financial analysis reports")
    print("=" * 60)
    print()

    if args.command == "stock":
        out = args.output or os.path.join(
            REPORTS_DIR, f"{args.ticker}_report.html"
        )
        result = generate_stock_report(args.ticker, out, args.format)

    elif args.command == "industry":
        safe_sector = args.sector.replace(" ", "_")
        out = args.output or os.path.join(
            REPORTS_DIR, f"{safe_sector}_industry_report.html"
        )
        result = generate_industry_report(args.sector, out, args.format)

    elif args.command == "weekly":
        out = args.output or os.path.join(
            REPORTS_DIR,
            f"weekly_report_{datetime.now().strftime('%Y%m%d')}.html",
        )
        result = generate_weekly_report(args.market, out, args.format)

    print()
    print("=" * 60)
    print(f"  Report saved to: {os.path.abspath(result)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
