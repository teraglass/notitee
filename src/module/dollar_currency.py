from datetime import datetime, date, timedelta
import pandas as pd
import yfinance as yf
import time

from module.slack import slackout_dollar, slackout_summary
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def dollar_currency_analysis():
    """Analyze dollar index and USD/KRW exchange rate"""

    start2 = str(date.today() - timedelta(days=365))
    end = str(date.today() + timedelta(days=1))

    # 데이터 다운로드
    usd_index_data = yf.download(
        ["DX=F"], start=start2, end=end, progress=False, auto_adjust=True
    )
    usd_krw_data = yf.download(
        ["USDKRW=X"], start=start2, end=end, progress=False, auto_adjust=True
    )

    # 데이터 유효성 검사
    if usd_index_data.empty or usd_krw_data.empty:
        slackout_dollar("⚠️ 데이터 다운로드 실패")
        exit(1)

    # NaN 값 제거
    usd_index_data = usd_index_data.dropna()
    usd_krw_data = usd_krw_data.dropna()

    if len(usd_index_data) < 10 or len(usd_krw_data) < 10:
        slackout_dollar("⚠️ 충분한 데이터가 없습니다")
        exit(1)

    # 현재 달러 인덱스 구하기
    today_usd_index = float(usd_index_data.iloc[-1, 3])  # Close column is index 3
    today_usd_index = round(today_usd_index, 2)

    # 1년 달러 인덱스 중앙값 구하기
    usd_index_median = float(usd_index_data.iloc[:, 3].median())
    usd_index_median = round(usd_index_median, 2)

    # 1년 환율 중앙값 구하기
    usd_krw_median = float(usd_krw_data.iloc[:, 3].median())
    usd_krw_median = round(usd_krw_median, 2)

    # 1년 달러 갭 지수 구하기 (NaN 처리 추가)
    usd_gap_ratio_mean = (
        (usd_index_data.iloc[:, 3] / usd_index_median - 1).mean()
    ) * 100

    try:
        usd_gap_ratio_mean = round(float(usd_gap_ratio_mean), 2)
    except (ValueError, TypeError):
        usd_gap_ratio_mean = 0.0

    # 현재 달러 갭 지수 구하기 (NaN 처리 추가)
    usd_gap_ratio = (today_usd_index / usd_index_median - 1) * 100
    try:
        usd_gap_ratio = round(float(usd_gap_ratio), 2)
    except (ValueError, TypeError):
        usd_gap_ratio = 0.0

    # 적정 원달러 환율 구하기 (NaN 처리 추가)
    usd_krw_estimate = usd_krw_median * (today_usd_index / usd_index_median)
    try:
        usd_krw_estimate = round(float(usd_krw_estimate), 2)
    except (ValueError, TypeError):
        usd_krw_estimate = 0.0

    # 현재 환율과 적정 환율 차이 (NaN 처리 추가)
    try:
        current_usd_krw = float(usd_krw_data.iloc[:, 3].iloc[-1])
        if usd_krw_estimate > 0:
            usd_gap_percentage = (current_usd_krw / usd_krw_estimate - 1) * 100
            usd_gap_percentage = round(float(usd_gap_percentage), 1)
        else:
            usd_gap_percentage = 0.0
    except (ValueError, TypeError, IndexError):
        current_usd_krw = 0.0
        usd_gap_percentage = 0.0

    # 투자 결정 로직
    if abs(usd_gap_percentage) < 0.1:  # 거의 0에 가까우면
        decision = "⚠️ 데이터 *오류* 가능성"
        decision_color = "⚠️"
    elif usd_gap_percentage > 5:
        decision = "*매도* (환율이 적정가보다 5% 이상 높음)"
        decision_color = "🔴"
    elif usd_gap_percentage < -5:
        decision = "*매수* (환율이 적정가보다 5% 이상 낮음)"
        decision_color = "🟢"
    else:
        decision = f"*관망* (갭: {usd_gap_percentage}%)"
        decision_color = "🟡"

    # 통합 달러환율 리포트 메시지 생성
    if usd_krw_estimate > 0:
        currency_report = f"""
💱 *달러환율 분석 리포트*
    - 현재 USD Index: {today_usd_index}
    - USD Index 중앙값: {usd_index_median}
    - 현재 원달러 환율: {current_usd_krw:.2f}원
    - *적정* 원달러 환율: {usd_krw_estimate}원
    - *환율 갭*: {usd_gap_percentage}%
{decision_color} *투자 결정*: {decision}"""
    else:
        currency_report = f"""
💱 *달러환율 분석 리포트*
    ⚠️ 적정 원달러 환율 계산 오류 발생
    - 현재 USD Index: {today_usd_index}
    - USD Index 중앙값: {usd_index_median}
    - 현재 원달러 환율: {current_usd_krw}원"""

    # 통합 메시지 전송
    slackout_dollar(currency_report)

    # 요약 정보 반환
    if usd_krw_estimate > 0:
        summary_data = f"달러: {current_usd_krw:.0f}원 ({usd_gap_percentage:+.1f}%) | {decision.split(' ')[0]}"
    else:
        summary_data = f"달러: {current_usd_krw:.0f}원 | 분석오류 ♦️"

    print("✅ 달러환율 분석 완료")
    return summary_data
