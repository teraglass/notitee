from datetime import datetime, date, timedelta
import pandas as pd
import yfinance as yf
import time

from module.slack import slackout_crypto, slackout_summary
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def analyze_crypto_asset(ticker, name, emoji):
    """Analyze individual crypto asset"""
    try:
        # 1년간 데이터 다운로드
        start_date = str(date.today() - timedelta(days=365))
        end_date = str(date.today() + timedelta(days=1))

        data = yf.download(
            ticker, start=start_date, end=end_date, progress=False, auto_adjust=True
        )

        if data.empty:
            return f"⚠️ {name} 데이터를 가져올 수 없습니다."

        data = data.dropna()

        if len(data) < 10:
            return f"⚠️ {name} 충분한 데이터가 없습니다."

        # 현재 가격
        current_price = float(data.iloc[-1, 3])  # Close price

        # 1일, 7일, 30일 전 가격
        price_1d = float(data.iloc[-2, 3]) if len(data) >= 2 else current_price
        price_7d = float(data.iloc[-8, 3]) if len(data) >= 8 else current_price
        price_30d = float(data.iloc[-31, 3]) if len(data) >= 31 else current_price

        # 변화율 계산
        change_1d = ((current_price - price_1d) / price_1d) * 100
        change_7d = ((current_price - price_7d) / price_7d) * 100
        change_30d = ((current_price - price_30d) / price_30d) * 100

        # 52주 고점/저점
        high_52w = float(data.iloc[:, 3].max())
        low_52w = float(data.iloc[:, 3].min())

        # 현재 위치 (52주 고점 대비)
        position_from_high = ((current_price - high_52w) / high_52w) * 100

        # RSI 계산 (14일)
        rsi = calculate_rsi(data["Close"], 14)

        # 이모지 선택
        trend_emoji = "🟢" if change_7d > 0 else "🔴"

        # RSI 상태 판단
        if rsi > 70:
            rsi_status = "(과매수)"
        elif rsi < 30:
            rsi_status = "(과매도)"
        else:
            rsi_status = ""

        # 메시지 포맷
        message = f"""
{emoji} *{name}* {trend_emoji}
🪙 현재가: ${current_price:,.2f}
- 변화율: 1D {change_1d:+.1f}% | 7D {change_7d:+.1f}% | 30D {change_30d:+.1f}%
- 52주 고점 대비: {position_from_high:+.1f}%
- RSI(14): {rsi:.1f} {rsi_status}
- 52주 범위: ${low_52w:,.2f} - ${high_52w:,.2f}
        """.strip()

        return message

    except Exception as e:
        return f"⚠️ {name} 분석 중 오류 발생: {str(e)}"


def calculate_rsi(prices, period=14):
    """Calculate RSI (Relative Strength Index)"""
    try:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        # RSI 계산을 위한 시리즈 생성
        rsi = pd.Series(index=prices.index, dtype=float)
        for i in range(len(prices)):
            avg_gain = gain.iloc[i]
            avg_loss = loss.iloc[i]
            if pd.isna(avg_gain) or pd.isna(avg_loss):
                rsi.iloc[i] = float('nan')
            elif avg_loss == 0 and avg_gain == 0:
                rsi.iloc[i] = 50.0
            elif avg_loss == 0:
                rsi.iloc[i] = 100.0
            elif avg_gain == 0:
                rsi.iloc[i] = 0.0
            else:
                rs = avg_gain / avg_loss
                rsi.iloc[i] = 100 - (100 / (1 + rs))

        # 마지막 값을 float로 변환, NaN이면 50 반환
        rsi_value = float(rsi.iloc[-1])
        return rsi_value if not pd.isna(rsi_value) else 50.0

    except Exception:
        return 50.0  # 계산 실패시 중립값 반환


def get_crypto_fear_greed():
    """Get crypto fear & greed index from alternative.me API"""
    import requests

    try:
        url = "https://api.alternative.me/fng/"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data["data"]:
                fng_data = data["data"][0]
                return {
                    "value": int(fng_data["value"]),
                    "classification": fng_data["value_classification"],
                    "timestamp": fng_data["timestamp"],
                }
    except Exception as e:
        print(f"암호화폐 공포탐욕지수 가져오기 실패: {e}")

    return None


def crypto_analysis_main():
    """Main function for crypto analysis"""

    # 분석할 암호화폐들
    cryptos = [
        ("BTC-USD", "Bitcoin", "₿"),
        ("ETH-USD", "Ethereum", "⟠"),
        ("SOL-USD", "Solana", "◎"),
    ]

    messages = []

    # 암호화폐 공포탐욕지수
    crypto_fng = get_crypto_fear_greed()
    if crypto_fng:
        fng_emoji = {
            "Extreme Fear": "😱",
            "Fear": "😰",
            "Neutral": "😐",
            "Greed": "😎",
            "Extreme Greed": "🤑",
        }.get(crypto_fng["classification"], "😐")

        fng_message = f"""
🔥 *Crypto Fear & Greed Index* {fng_emoji}
- *지수*: {crypto_fng['value']}/100 ({crypto_fng['classification']})
        """.strip()
        messages.append(fng_message)

    # 각 암호화폐 분석
    for ticker, name, emoji in cryptos:
        analysis = analyze_crypto_asset(ticker, name, emoji)
        messages.append(analysis)
        time.sleep(1)  # API 호출 제한 고려

    # 종합 메시지 전송
    final_message = "\n\n".join(messages)
    slackout_crypto(final_message)

    # 요약 정보 반환
    if crypto_fng:
        fng_value = crypto_fng["value"]

        # FNG 지수에 따른 투자 결정
        if fng_value <= 24:
            decision = "💚 매수"  # Extreme Fear
        elif fng_value <= 44:
            decision = "🟢 매수고려"  # Fear
        elif fng_value <= 55:
            decision = "🟡 관망"  # Neutral
        elif fng_value <= 75:
            decision = "🟠 매도고려"  # Greed
        else:
            decision = "🔴 매도"  # Extreme Greed

        fng_summary = f"FNG:{fng_value}"
        summary_data = f"암호화폐: BTC 추세 분석 | {fng_summary} | {decision}"
    else:
        summary_data = f"♦️ 암호화폐: BTC 추세 분석 | FNG:N/A | 데이터없음"
    print("✅ 암호화폐 분석 완료")
    return summary_data
