from datetime import datetime, date, timedelta
import yfinance as yf
from module.slack import slackout_sp500

import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_sp500_200ma(ticker="^GSPC"):
    """Get S&P500 200-day moving average"""
    try:
        # Download ~300 trading days to ensure we have 200 days
        data = yf.download(
            ticker, period="300d", interval="1d", progress=False, auto_adjust=True
        )
        if data.empty:
            raise RuntimeError("Failed to download S&P500 data")

        # Use Close price for calculation
        close_prices = data["Close"].dropna()
        if len(close_prices) < 200:
            raise RuntimeError(
                f"Not enough data to compute 200-day MA; got {len(close_prices)} rows"
            )

        # Calculate 200-day moving average (fix FutureWarning)
        ma200 = close_prices.tail(200).mean().item()

        # Get current price (most recent) - use .item() to avoid FutureWarning
        current_price = close_prices.iloc[-1]
        if hasattr(current_price, "item"):
            current_price = current_price.item()

        latest_date = close_prices.index[-1].strftime("%Y-%m-%d")

        return round(ma200, 2), round(current_price, 2), latest_date
    except Exception as e:
        print(f"Error getting S&P500 data: {e}")
        return None, None, None


def analyze_sp500_trend(current_price, ma200):
    """Analyze S&P500 trend relative to 200MA"""
    if not current_price or not ma200:
        return "⚠️ 데이터 오류"

    percentage_diff = ((current_price - ma200) / ma200) * 100

    if percentage_diff > 5:
        return (
            f"🚀 강세장 - 현재가가 200일 이평선보다 {percentage_diff:.1f}% 높음 - 매수"
        )
    elif percentage_diff > 0:
        return f"📈 상승 추세 - 현재가가 200일 이평선보다 {percentage_diff:.1f}% 높음 - 매수 고려"
    elif percentage_diff > -5:
        return f"📉 하락 추세 - 현재가가 200일 이평선보다 {abs(percentage_diff):.1f}% 낮음 - 매도"
    else:
        return f"💥 약세장 - 현재가가 200일 이평선보다 {abs(percentage_diff):.1f}% 낮음 - 매도"


def snp500_200ma_main():
    try:
        ma200, current_price, date = get_sp500_200ma()

        if ma200 and current_price:
            # Calculate percentage difference
            percentage_diff = ((current_price - ma200) / ma200) * 100

            # Determine investment decision and color
            if percentage_diff > 5:
                decision = f"*매수* - 강세장 ({percentage_diff:.1f}% 상승)"
                decision_color = "🟢"
            elif percentage_diff > 0:
                decision = f"*매수 고려* - 상승 추세 ({percentage_diff:.1f}% 상승)"
                decision_color = "🟡"
            elif percentage_diff > -5:
                decision = f"*매도* - 하락 추세 ({abs(percentage_diff):.1f}% 하락)"
                decision_color = "🔴"
            else:
                decision = f"*매도* - 약세장 ({abs(percentage_diff):.1f}% 하락)"
                decision_color = "💥"

            # Create consolidated S&P500 report
            sp500_report = f"""
🦖 *S&P500 분석 리포트*
    - 현재가: {current_price}
    - 200일 이평선: {ma200}
    - 차이율: {percentage_diff:+.1f}%
    - 기준일: {date}
{decision_color} *투자 결정*: {decision}"""

            slackout_sp500(sp500_report)
        else:
            slackout_sp500("⚠️ *S&P500 분석 리포트*\n데이터를 가져올 수 없습니다")

    except Exception as ex:
        slackout_sp500(f"⚠️ *S&P500 분석 리포트*\n예외 처리: {str(ex)}")
