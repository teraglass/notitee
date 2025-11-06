from datetime import datetime, date, timedelta
import math

import pandas as pd
import fear_and_greed
import yfinance as yf
from module.slack import slackout_feargreed
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_fear_and_greed():
    fg = fear_and_greed.get()
    fg_score = float(fg[0])
    fg_score = round(fg_score, 2)
    fg_status = fg[1]
    fg_date = fg[2]
    fg_date = fg_date.strftime("%Y-%m-%d %H:%M:%S")
    return (fg_score, fg_status, fg_date)


def buy_stock(ticker):
    slackout_feargreed("🟢 Buy signal - Fear & Greed below 35")
    # slackout("🟢 #feargreed Buy signal - Fear & Greed below 35")


def sell_stock(ticker):
    slackout_feargreed("🔴 Sell signal - Fear & Greed above 80")
    # slackout("🔴 #feargreed Sell signal - Fear & Greed above 80")


def cnn_fear_greed_main():
    sell_score = 80
    buy_score = 35

    try:
        fg_score, fg_status, fg_date = get_fear_and_greed()
        fg_status = fg_status.upper()
        if fg_score < 25:
            emoji = "😱"  # Extreme Fear
        elif fg_score < 45:
            emoji = "😰"  # Fear
        elif fg_score < 55:
            emoji = "😐"  # Neutral
        elif fg_score < 75:
            emoji = "😎"  # Greed
        else:
            emoji = "🤑"  # Extreme Greed

        # Determine investment decision
        if fg_score > sell_score:
            decision = "*매도* (F&G 지수 80 이상)"
            decision_color = "🔴"
        elif fg_score < buy_score:
            decision = "*매수* (F&G 지수 35 이하)"
            decision_color = "🟢"
        else:
            decision = "*관망* (중립 구간)"
            decision_color = "🟡"

        # Create consolidated Fear & Greed report
        feargreed_report = f"""
🍅 *CNN Fear & Greed 분석 리포트*
    - 업데이트: {fg_date} UTC
    - 현재 지수: {fg_score} {emoji}
    - 상태: *{fg_status}*
    - *매수* 기준: {buy_score} 이하
    - *매도* 기준: {sell_score} 이상
{decision_color} *투자 결정*: {decision}"""

        slackout_feargreed(feargreed_report)

        # 요약 정보 반환
        summary_data = f"공포탐욕: {fg_score} ({fg_status}) | {decision.split(' ')[0]}"
        print("✅ CNN Fear & Greed 분석 완료")
        return summary_data

    except Exception as ex:
        slackout_feargreed(f"⚠️ *CNN Fear & Greed 분석 리포트*\n예외 처리: {str(ex)}")
        print("✅ CNN Fear & Greed 분석 오류")
        return "공포탐욕: 분석 오류"
