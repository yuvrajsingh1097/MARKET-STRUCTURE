HH / HL / LH / LL — the 4 structure labels
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




HH (green diamond) = Higher High   → bullish structure
    ● HL (blue  diamond) = Higher Low    → bullish structure  ← buy here
    ● LH (red   diamond) = Lower High    → bearish structure  ← sell here
    ● LL (orange diamond)= Lower Low     → bearish structure





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













Label each swing as HH, HL, LH, or LL.
 
    
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
