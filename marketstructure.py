"""
============================================================
 PROJECT 4 — MARKET STRUCTURE VISUALIZER
 pip install yfinance pandas plotly
 python market_structure.py
============================================================
CONCEPTS YOU WILL LEARN:
  - HH / HL / LH / LL — the 4 structure labels
  - How to determine trend direction from structure alone
  - Multi-Timeframe Analysis (MTF): Daily → Hourly
  - Premium vs Discount zones (ICT's PDA framework)
  - Fibonacci equilibrium (50%) as a buy/sell filter
  - Why you ONLY buy in discount and SELL in premium
  - How to export a shareable interactive HTML chart
============================================================
HOW TO READ THE OUTPUT CHART:
  HTF (top chart) = Daily candles — gives you the BIAS
  LTF (bottom)    = Hourly candles — gives you the ENTRY

  Structure labels:
    ● HH (green diamond) = Higher High   → bullish structure
    ● HL (blue  diamond) = Higher Low    → bullish structure  ← buy here
    ● LH (red   diamond) = Lower High    → bearish structure  ← sell here
    ● LL (orange diamond)= Lower Low     → bearish structure
============================================================
"""

import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings("ignore")


# ──────────────────────────────────────────────────────────
#  ★ EDIT THESE TO CHANGE PAIR / TIMEFRAMES
# ──────────────────────────────────────────────────────────

PAIR     = "EUR/USD"
SYMBOL   = "EURUSD=X"
HTF      = "1d"     # Higher timeframe (daily)  — for BIAS
LTF      = "1h"     # Lower  timeframe (hourly) — for ENTRY
HTF_DAYS = 180      # How many days of daily data
LTF_DAYS = 30       # How many days of hourly data
SWING_N  = 3        # Candles each side for swing detection


# ──────────────────────────────────────────────────────────
#  STEP 1 — FETCH DATA
# ──────────────────────────────────────────────────────────

def fetch(symbol: str, interval: str, days: int) -> pd.DataFrame:
    """Download OHLC data from Yahoo Finance (free)."""
    print(f"  Fetching {symbol} {interval} ({days}d)...", end=" ")
    t = yf.Ticker(symbol)
    df = t.history(
        start=datetime.now() - timedelta(days=days),
        end=datetime.now(),
        interval=interval,
    )
    if df.empty:
        print("NO DATA")
        return pd.DataFrame()
    df = df[["Open", "High", "Low", "Close"]].copy()
    df.columns = ["open", "high", "low", "close"]
    df.index = pd.to_datetime(df.index)
    df = df.dropna()
    print(f"{len(df)} candles ✓")
    return df


# ──────────────────────────────────────────────────────────
#  STEP 2 — FIND SWING HIGHS & LOWS
# ──────────────────────────────────────────────────────────

def find_swings(df: pd.DataFrame, n: int = 3) -> pd.DataFrame:
    """
    Detect swing highs (sh) and swing lows (sl).

    LEARNING NOTE:
      A swing high = local maximum (higher than n candles each side).
      A swing low  = local minimum (lower  than n candles each side).

      In ICT these are called "swing highs" and "swing lows" and they
      form the skeleton of all market structure analysis.
      Increasing n makes swings less frequent but more significant.
    """
    df = df.copy()
    df["sh"] = False
    df["sl"] = False
    for i in range(n, len(df) - n):
        wh = df["high"].iloc[i - n : i + n + 1]
        wl = df["low"].iloc[i - n : i + n + 1]
        if df["high"].iloc[i] == wh.max():
            df.loc[df.index[i], "sh"] = True
        if df["low"].iloc[i] == wl.min():
            df.loc[df.index[i], "sl"] = True
    return df


# ──────────────────────────────────────────────────────────
#  STEP 3 — LABEL STRUCTURE: HH / HL / LH / LL
# ──────────────────────────────────────────────────────────

def label_structure(df: pd.DataFrame) -> pd.DataFrame:
    """
    Label each swing as HH, HL, LH, or LL.

    LEARNING NOTE:
      HH  Higher High   — swing high ABOVE previous swing high
                          → buyers are gaining ground (BULLISH)

      HL  Higher Low    — swing low ABOVE previous swing low
                          → sellers can't push it down as far (BULLISH)
                          → This is the ENTRY point in an uptrend!

      LH  Lower High    — swing high BELOW previous swing high
                          → buyers can't push it up as far (BEARISH)
                          → This is the ENTRY point in a downtrend!

      LL  Lower Low     — swing low BELOW previous swing low
                          → sellers are gaining ground (BEARISH)

    MARKET PHASES:
      HH + HL series  = UPTREND  → buy the HL pullbacks
      LH + LL series  = DOWNTREND → sell the LH rallies
      Mixed / unclear = RANGE    → stay patient

    ICT RULE:
      Never trade AGAINST the HTF structure.
      If Daily shows HH+HL → only take LONG setups on LTF.
    """
    df = df.copy()
    df["label"]       = ""
    df["label_price"] = float("nan")

    prev_sh_val = None
    prev_sl_val = None

    for i in range(len(df)):
        if df["sh"].iloc[i]:
            val = df["high"].iloc[i]
            if prev_sh_val is not None:
                lbl = "HH" if val > prev_sh_val else "LH"
                df.loc[df.index[i], "label"]       = lbl
                df.loc[df.index[i], "label_price"] = val
            prev_sh_val = val

        if df["sl"].iloc[i]:
            val = df["low"].iloc[i]
            if prev_sl_val is not None:
                lbl = "HL" if val > prev_sl_val else "LL"
                df.loc[df.index[i], "label"]       = lbl
                df.loc[df.index[i], "label_price"] = val
            prev_sl_val = val

    return df


# ──────────────────────────────────────────────────────────
#  STEP 4 — DETERMINE MARKET BIAS
# ──────────────────────────────────────────────────────────

def get_bias(df: pd.DataFrame) -> tuple:
    """
    Determine the dominant bias from recent structure labels.

    LEARNING NOTE:
      We simply count recent bullish signals (HH, HL) vs bearish
      signals (LH, LL) in the last 10 labelled swings.

      bull > bear × 1.5  → BULLISH bias (strong enough to act on)
      bear > bull × 1.5  → BEARISH bias
      otherwise          → RANGING (sit on hands)
    """
    recent = df[df["label"] != ""].tail(10)
    bull = len(recent[recent["label"].isin(["HH", "HL"])])
    bear = len(recent[recent["label"].isin(["LH", "LL"])])

    if bull > bear * 1.5:
        return "BULLISH", bull, bear
    if bear > bull * 1.5:
        return "BEARISH", bull, bear
    return "RANGING", bull, bear


# ──────────────────────────────────────────────────────────
#  STEP 5 — PREMIUM / DISCOUNT ZONES (PDA)
# ──────────────────────────────────────────────────────────

def pda_zones(df: pd.DataFrame) -> dict:
    """
    Calculate Premium, Discount, and Equilibrium zones.

    LEARNING NOTE:
      ICT's PDA (Price Delivery Algorithm) framework:

        RANGE = recent swing high  →  recent swing low

        Equilibrium (EQ) = 50% of the range
          → This is the FAIR PRICE for both buyers and sellers

        PREMIUM ZONE = above EQ (above 50%)
          → Price is EXPENSIVE
          → Institutions look to SELL here
          → DO NOT buy in premium!

        DISCOUNT ZONE = below EQ (below 50%)
          → Price is CHEAP
          → Institutions look to BUY here
          → DO NOT sell in discount!

      Fibonacci levels within the range:
        0.0   = range low
        23.6% = shallow retracement
        38.2% = discount zone boundary (optimal entry zone)
        50.0% = equilibrium
        61.8% = premium zone boundary (optimal sell zone)
        78.6% = deep premium
        100%  = range high

      TRADING RULE:
        If HTF bias = BULLISH → wait for price to reach DISCOUNT
                                 → then look for OB/FVG entry on LTF
        If HTF bias = BEARISH → wait for price to reach PREMIUM
                                 → then look for OB/FVG entry on LTF
    """
    rng_high = df["high"].tail(40).max()
    rng_low  = df["low"].tail(40).min()
    span     = rng_high - rng_low
    eq       = (rng_high + rng_low) / 2
    price    = df["close"].iloc[-1]

    fibs = {
        "0.0%  (Low)":   rng_low,
        "23.6%":         rng_low + span * 0.236,
        "38.2% (Disc)":  rng_low + span * 0.382,
        "50.0% (EQ)":    eq,
        "61.8% (Prem)":  rng_low + span * 0.618,
        "78.6%":         rng_low + span * 0.786,
        "100%  (High)":  rng_high,
    }

    zone = "PREMIUM" if price > eq else "DISCOUNT"
    pct_from_low = (price - rng_low) / span * 100

    return {
        "high":         rng_high,
        "low":          rng_low,
        "eq":           eq,
        "zone":         zone,
        "pct_from_low": round(pct_from_low, 1),
        "fibs":         fibs,
    }


# ──────────────────────────────────────────────────────────
#  STEP 6 — BUILD INTERACTIVE PLOTLY CHART
# ──────────────────────────────────────────────────────────

def build_chart(htf: pd.DataFrame, ltf: pd.DataFrame,
                bias: str, pda: dict) -> go.Figure:
    """
    Create a two-panel interactive multi-timeframe chart.
    Top panel  = HTF (Daily) — for bias and big structure
    Bottom panel = LTF (Hourly) — for entry refinement
    """
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=False,
        vertical_spacing=0.07,
        row_heights=[0.55, 0.45],
        subplot_titles=[
            f"{PAIR} HTF ({HTF}) — Bias & Structure",
            f"{PAIR} LTF ({LTF}) — Entry Timeframe",
        ],
    )

    lbl_cfg = {
        "HH": {"color": "#00e5a0", "pos": "top center",    "y": lambda d: d["high"] * 1.0004},
        "HL": {"color": "#2d9cff", "pos": "bottom center", "y": lambda d: d["low"]  * 0.9996},
        "LH": {"color": "#ff4a6b", "pos": "top center",    "y": lambda d: d["high"] * 1.0004},
        "LL": {"color": "#d4a843", "pos": "bottom center", "y": lambda d: d["low"]  * 0.9996},
    }

    def add_candles(frame, row, name):
        fig.add_trace(
            go.Candlestick(
                x=frame.index,
                open=frame["open"], high=frame["high"],
                low=frame["low"],   close=frame["close"],
                name=name,
                increasing_line_color="#00e5a0",
                decreasing_line_color="#ff4a6b",
                increasing_fillcolor="rgba(0,229,160,.55)",
                decreasing_fillcolor="rgba(255,74,107,.55)",
            ),
            row=row, col=1,
        )

    def add_labels(frame, row, show_legend=True):
        for lbl, cfg in lbl_cfg.items():
            sub = frame[frame["label"] == lbl]
            if sub.empty:
                continue
            fig.add_trace(
                go.Scatter(
                    x=sub.index,
                    y=cfg["y"](sub),
                    mode="markers+text",
                    marker=dict(symbol="diamond", size=11 if row == 1 else 8,
                                color=cfg["color"]),
                    text=[lbl] * len(sub),
                    textposition=cfg["pos"],
                    textfont=dict(size=9 if row == 1 else 7, color=cfg["color"]),
                    name=lbl,
                    showlegend=show_legend,
                ),
                row=row, col=1,
            )

    # HTF
    add_candles(htf, 1, f"HTF ({HTF})")
    add_labels(htf, 1, show_legend=True)

    # PDA zones on HTF
    eq   = pda["eq"]
    high = pda["high"]
    low  = pda["low"]

    fig.add_hrect(y0=eq, y1=high,
                  fillcolor="rgba(255,74,107,.04)",
                  line=dict(color="rgba(255,74,107,.25)", width=1, dash="dot"),
                  annotation_text="PREMIUM", annotation_position="right",
                  annotation_font=dict(color="#ff4a6b", size=9), row=1, col=1)

    fig.add_hrect(y0=low, y1=eq,
                  fillcolor="rgba(0,229,160,.04)",
                  line=dict(color="rgba(0,229,160,.25)", width=1, dash="dot"),
                  annotation_text="DISCOUNT", annotation_position="right",
                  annotation_font=dict(color="#00e5a0", size=9), row=1, col=1)

    fig.add_hline(y=eq, line_dash="dash", line_color="#d4a843", line_width=1.5,
                  annotation_text=f"EQ {eq:.5f}",
                  annotation_font_color="#d4a843", row=1, col=1)

    # LTF
    add_candles(ltf, 2, f"LTF ({LTF})")
    add_labels(ltf, 2, show_legend=False)

    # Bias badge in title
    bias_color = "#00e5a0" if bias == "BULLISH" else ("#ff4a6b" if bias == "BEARISH" else "#304a61")
    zone_color = "#00e5a0" if pda["zone"] == "DISCOUNT" else "#ff4a6b"

    fig.update_layout(
        title=dict(
            text=(
                f"<b>{PAIR} Multi-Timeframe Structure</b>  "
                f"<span style='color:{bias_color}'>■ {bias}</span>  "
                f"<span style='color:{zone_color}'>■ {pda['zone']} ({pda['pct_from_low']}% from low)</span>"
            ),
            font=dict(color="#d4a843", size=14),
        ),
        paper_bgcolor="#020810",
        plot_bgcolor="#06101a",
        font=dict(family="monospace", color="#ccd8e8", size=10),
        xaxis_rangeslider_visible=False,
        xaxis2_rangeslider_visible=False,
        height=900,
        legend=dict(bgcolor="rgba(6,16,26,.85)", bordercolor="#0e2236"),
        margin=dict(r=120),
    )
    fig.update_xaxes(gridcolor="#0e2236")
    fig.update_yaxes(gridcolor="#0e2236")
    return fig


# ──────────────────────────────────────────────────────────
#  TERMINAL ANALYSIS REPORT
# ──────────────────────────────────────────────────────────

def print_report(htf: pd.DataFrame, ltf: pd.DataFrame, bias: str, pda: dict):
    htf_bias, hb, hbr = get_bias(htf)
    ltf_bias, lb, lbr = get_bias(ltf)
    price = htf["close"].iloc[-1]

    print(f"\n  {'='*52}")
    print(f"  MULTI-TIMEFRAME ANALYSIS — {PAIR}")
    print(f"  {'='*52}")
    print(f"  Current Price  : {price:.5f}")
    print(f"  HTF ({HTF}) Bias  : {htf_bias}  ({hb}↑ / {hbr}↓ signals)")
    print(f"  LTF ({LTF}) Bias  : {ltf_bias}  ({lb}↑ / {lbr}↓ signals)")
    print(f"  Zone           : {pda['zone']}  ({pda['pct_from_low']}% from range low)")
    print(f"  Equilibrium    : {pda['eq']:.5f}")
    print(f"  Range High     : {pda['high']:.5f}")
    print(f"  Range Low      : {pda['low']:.5f}")

    print(f"\n  FIBONACCI / PDA LEVELS:")
    for name, val in pda["fibs"].items():
        arrow = "  ◄ PRICE IS HERE" if abs(price - val) < (pda["high"] - pda["low"]) * 0.02 else ""
        print(f"    {name:20s}: {val:.5f}{arrow}")

    # Recent HTF structure
    recent = htf[htf["label"] != ""].tail(6)
    print(f"\n  RECENT HTF STRUCTURE EVENTS:")
    for idx, row in recent.iterrows():
        p = row["high"] if row["label"] in ["HH", "LH"] else row["low"]
        print(f"    {str(idx.date()):<12}  {row['label']:4}  {p:.5f}")

    # Trade guidance
    print(f"\n  ── TRADING GUIDANCE ──────────────────────────")
    if htf_bias == "BULLISH" and pda["zone"] == "DISCOUNT":
        print("  ✅ IDEAL LONG SETUP CONDITION MET")
        print("  • HTF bullish + Price in discount = highest probability")
        print("  • Look for LTF CHoCH → OB/FVG entry in London or NY KZ")
        print("  • Target: Previous swing high / BSL above")
    elif htf_bias == "BULLISH" and pda["zone"] == "PREMIUM":
        print("  🟡 BULLISH BIAS BUT PRICE IN PREMIUM")
        print("  • Wait for a pullback into discount zone")
        print("  • Do NOT chase — wait for HL to form at discount")
        print("  • Patience = edge in ICT trading")
    elif htf_bias == "BEARISH" and pda["zone"] == "PREMIUM":
        print("  ✅ IDEAL SHORT SETUP CONDITION MET")
        print("  • HTF bearish + Price in premium = highest probability")
        print("  • Look for LTF CHoCH → OB/FVG entry in London or NY KZ")
        print("  • Target: Previous swing low / SSL below")
    elif htf_bias == "BEARISH" and pda["zone"] == "DISCOUNT":
        print("  🟡 BEARISH BIAS BUT PRICE IN DISCOUNT")
        print("  • Wait for a rally into premium zone")
        print("  • Do NOT chase — wait for LH to form at premium")
    else:
        print("  ⚪ NO CLEAR BIAS — RANGING MARKET")
        print("  • Do NOT trade — wait for clear HH+HL or LH+LL series")
        print("  • Use this time to mark OBs and FVGs for when clarity comes")


# ──────────────────────────────────────────────────────────
#  MAIN
# ──────────────────────────────────────────────────────────

def main():
    print("\n" + "="*55)
    print("  MARKET STRUCTURE VISUALIZER")
    print(f"  {PAIR}  |  HTF: {HTF}  |  LTF: {LTF}")
    print("="*55 + "\n")

    # Fetch
    htf = fetch(SYMBOL, HTF, HTF_DAYS)
    ltf = fetch(SYMBOL, LTF, LTF_DAYS)
    if htf.empty or ltf.empty:
        print("  Failed to fetch data. Check internet connection.")
        return

    # Process HTF
    htf = find_swings(htf, n=SWING_N)
    htf = label_structure(htf)
    bias, _, _ = get_bias(htf)
    pda = pda_zones(htf)

    # Process LTF
    ltf = find_swings(ltf, n=SWING_N)
    ltf = label_structure(ltf)

    # Report
    print_report(htf, ltf, bias, pda)

    # Chart
    print(f"\n  Building chart...", end=" ")
    fig = build_chart(htf, ltf, bias, pda)
    fname = f"market_structure_{PAIR.replace('/','')}.html"
    fig.write_html(fname)
    print(f"saved → {fname}")

    print("\n  KEY RULES TO REMEMBER:")
    print("  1. HTF bias FIRST — never trade against the daily trend")
    print("  2. Only BUY in DISCOUNT (below EQ), only SELL in PREMIUM")
    print("  3. HL in uptrend  = best buy zone  (price pulled back)")
    print("  4. LH in downtrend = best sell zone (price rallied)")
    print("  5. Always align: HTF bias → LTF entry → Killzone timing\n")


if __name__ == "__main__":
    main()