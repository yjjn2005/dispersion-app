#!/usr/bin/env python3
"""
GitHub Actions에서 실행 — 관심종목 시세·히스토리 수집 후 data.json 저장
"""
import json, time, datetime, pathlib, sys
try:
    import yfinance as yf
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance", "-q"])
    import yfinance as yf

# ── 수집 대상 (index.html DEFAULT_WATCHLIST 와 동기화 유지) ──
TICKERS = [
    ("005930.KS", "삼성전자"),
    ("000660.KS", "SK하이닉스"),
    ("006800.KS", "미래에셋증권"),
    ("005380.KS", "현대차"),
    ("010120.KS", "LS일렉트릭"),
    ("018290.KQ", "브이티"),
    ("034020.KS", "두산에너빌리티"),
    ("373220.KS", "LG에너지솔루션"),
    ("329180.KS", "HD현대중공업"),
    ("108490.KQ", "로보티즈"),
    ("277810.KQ", "레인보우로보틱스"),
    ("278470.KS", "에이피알"),
    ("9984.T",    "소프트뱅크"),
    ("NVDA",      "엔비디아"),
    ("CRCL",      "서클"),
    ("IONQ",      "아이온큐"),
    ("TWST",      "트위스트 바이오"),
    ("CRSP",      "크리스퍼 테라퓨틱스"),
    ("SCHD",      "SCHD"),
    ("^KS11",     "코스피"),
    ("^KQ11",     "코스닥"),
    ("^IXIC",     "나스닥 종합"),
    ("^GSPC",     "S&P 500"),
    ("^DJI",      "다우존스"),
    ("^SOX",      "필라델피아 반도체"),
    ("KORU",      "KORU"),
]

def fetch_one(ticker, name):
    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period="1y", interval="1d", auto_adjust=True)
        if hist.empty or len(hist) < 60:
            return {"error": f"히스토리 부족 ({len(hist)}일)"}

        closes = [round(float(v), 4) if v == v else None for v in hist["Close"].tolist()]
        dates  = [d.strftime("%m/%d") for d in hist.index]

        # 현재가: 마지막 종가 사용 (regularMarketPrice 폴백)
        price = closes[-1]
        try:
            info = tk.fast_info
            lp = getattr(info, "last_price", None)
            if lp and lp == lp:
                price = round(float(lp), 4)
        except Exception:
            pass

        currency = "KRW"
        try:
            currency = tk.fast_info.currency or "KRW"
        except Exception:
            if ticker.endswith(".T"):
                currency = "JPY"
            elif not (ticker.endswith(".KS") or ticker.endswith(".KQ") or ticker.startswith("^KS") or ticker.startswith("^KQ")):
                currency = "USD"

        return {
            "price": price,
            "currency": currency,
            "closes": closes,
            "dates": dates,
            "source": "야후",
        }
    except Exception as e:
        return {"error": str(e)}

def main():
    stocks = {}
    for ticker, name in TICKERS:
        print(f"  [{ticker}] {name} ...", end=" ", flush=True)
        result = fetch_one(ticker, name)
        stocks[ticker] = result
        status = "✓" if "price" in result else f"✗ {result.get('error','')}"
        print(status)
        time.sleep(0.3)  # 야후 rate-limit 회피

    kst = datetime.timezone(datetime.timedelta(hours=9))
    out = {
        "updated": datetime.datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S KST"),
        "stocks": stocks,
    }
    out_path = pathlib.Path(__file__).parent / "data.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    ok  = sum(1 for v in stocks.values() if "price" in v)
    err = sum(1 for v in stocks.values() if "error" in v)
    print(f"\n완료: {ok}개 성공 / {err}개 실패 → data.json 저장")

if __name__ == "__main__":
    main()
