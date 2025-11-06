from datetime import datetime, date, timedelta
import pandas as pd
import yfinance as yf
import time

from module.slack import slackout_bonds, slackout_summary
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def analyze_bond_yield(ticker, name, emoji):
    """Analyze bond yield data"""
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

        # 현재 수익률
        current_yield = float(data.iloc[-1, 3])  # Close price

        # 과거 수익률들
        yield_1d = float(data.iloc[-2, 3]) if len(data) >= 2 else current_yield
        yield_7d = float(data.iloc[-8, 3]) if len(data) >= 8 else current_yield
        yield_30d = float(data.iloc[-31, 3]) if len(data) >= 31 else current_yield
        yield_1y_ago = float(data.iloc[0, 3])

        # 변화량 계산 (basis points)
        change_1d = (current_yield - yield_1d) * 100
        change_7d = (current_yield - yield_7d) * 100
        change_30d = (current_yield - yield_30d) * 100
        change_1y = (current_yield - yield_1y_ago) * 100

        # 52주 고점/저점
        high_52w = float(data["Close"].max().item())
        low_52w = float(data["Close"].min().item())

        # 트렌드 판단
        trend_emoji = "⬆️" if change_7d > 10 else "⬇️" if change_7d < -10 else "➡️"

        # 수익률 레벨 판단
        if current_yield >= 5.0:
            level_emoji = "🔴"  # 높음
            level_desc = "높음"
        elif current_yield >= 4.0:
            level_emoji = "🟡"  # 보통
            level_desc = "보통"
        else:
            level_emoji = "🟢"  # 낮음
            level_desc = "낮음"

        message = f"""
{emoji} *{name}* {trend_emoji}
- 현재 수익률: {current_yield:.2f}% {level_emoji} ({level_desc})
- 변화량 (bp): 1D {change_1d:+.0f} | 7D {change_7d:+.0f} | 30D {change_30d:+.0f} | 1Y {change_1y:+.0f}
- 52주 범위: {low_52w:.2f}% - {high_52w:.2f}%
        """.strip()

        return message

    except Exception as e:
        return f"⚠️ {name} 분석 중 오류 발생: {str(e)}"


def calculate_yield_curve_spread():
    """Calculate yield curve spreads"""
    try:
        # 2년, 10년 국채 수익률
        tickers = ["^TNX", "^FVX"]  # 10년, 5년 (2년 대신)

        end_date = str(date.today() + timedelta(days=1))
        start_date = str(date.today() - timedelta(days=30))

        data_10y = yf.download(
            "^TNX", start=start_date, end=end_date, progress=False, auto_adjust=True
        )
        data_5y = yf.download(
            "^FVX", start=start_date, end=end_date, progress=False, auto_adjust=True
        )

        if not data_10y.empty and not data_5y.empty:
            current_10y = float(data_10y.iloc[-1, 3])
            current_5y = float(data_5y.iloc[-1, 3])

            # 10Y-5Y 스프레드
            spread = current_10y - current_5y

            # 역전 여부 판단
            if spread < 0:
                spread_status = "🔴 역전 (Inverted)"
            elif spread < 0.5:
                spread_status = "🟡 평탄화 (Flattening)"
            else:
                spread_status = "🟢 정상 (Normal)"

            return f"📊 10Y-5Y 스프레드: {spread:.2f}bp {spread_status}"

    except Exception as e:
        print(f"수익률 곡선 계산 실패: {e}")

    return "⚠️ 수익률 곡선 데이터 없음"


def bond_yields_main():
    """Main function for bond yield analysis"""

    # 분석할 채권들
    bonds = [
        ("^TNX", "미국 10년 국채", "🇺🇸"),
        ("^FVX", "미국 5년 국채", "🇺🇸"),
        ("^IRX", "미국 3개월 국채", "🇺🇸"),
        ("^TYX", "미국 30년 국채", "🇺🇸"),
    ]

    messages = []

    # 제목 메시지
    title_message = "📊 *채권 수익률 분석* 📊"
    messages.append(title_message)

    # 수익률 곡선 스프레드
    spread_message = calculate_yield_curve_spread()
    messages.append(spread_message)

    # 각 채권 분석
    for ticker, name, emoji in bonds:
        analysis = analyze_bond_yield(ticker, name, emoji)
        messages.append(analysis)
        time.sleep(1)  # API 호출 제한 고려

    # Fed 금리 정책 힌트
    try:
        # 10년 국채 수익률로 정책 힌트
        data = yf.download(
            "^TNX",
            start=str(date.today() - timedelta(days=7)),
            end=str(date.today() + timedelta(days=1)),
            progress=False,
            auto_adjust=True,
        )
        if not data.empty:
            current_10y = float(data.iloc[-1, 3])
            week_ago_10y = float(data.iloc[0, 3]) if len(data) > 1 else current_10y
            change_week = current_10y - week_ago_10y

            if change_week > 0.2:
                policy_hint = "💡 *수익률 상승 → 인플레이션 우려 또는 긴축 기대*"
            elif change_week < -0.2:
                policy_hint = "💡 *수익률 하락 → 경기 둔화 우려 또는 완화 기대*"
            else:
                policy_hint = "💡 *수익률 안정 → 정책 기대감 제한적*"

            messages.append(policy_hint)

    except Exception:
        pass

    # 종합 메시지 전송
    final_message = "\n\n".join(messages)
    slackout_bonds(final_message)

    # 요약 정보 반환
    try:
        data_10y = yf.download(
            "^TNX",
            start=str(date.today() - timedelta(days=2)),
            end=str(date.today() + timedelta(days=1)),
            progress=False,
            auto_adjust=True,
        )
        if not data_10y.empty:
            current_10y = float(data_10y.iloc[-1, 3])
            summary_data = f"채권: 10Y {current_10y:.2f}%"
        else:
            summary_data = "채권: 수익률 분석 오류 ♦️"
    except:
        summary_data = "채권: 수익률 분석 오류 ♦️"

    print("✅ 채권 수익률 분석 완료")
    return summary_data
