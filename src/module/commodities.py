from datetime import datetime, date, timedelta
import pandas as pd
import yfinance as yf
import time

from module.slack import slackout_commodities, slackout_summary
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def analyze_commodity(ticker, name, emoji, unit="$"):
    """Analyze individual commodity"""
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

        # 과거 가격들
        price_1d = float(data.iloc[-2, 3]) if len(data) >= 2 else current_price
        price_7d = float(data.iloc[-8, 3]) if len(data) >= 8 else current_price
        price_30d = float(data.iloc[-31, 3]) if len(data) >= 31 else current_price
        price_1y_ago = float(data.iloc[0, 3])

        # 변화율 계산
        change_1d = ((current_price - price_1d) / price_1d) * 100
        change_7d = ((current_price - price_7d) / price_7d) * 100
        change_30d = ((current_price - price_30d) / price_30d) * 100
        change_1y = ((current_price - price_1y_ago) / price_1y_ago) * 100

        # 52주 고점/저점
        high_52w = float(data["Close"].max().item())
        low_52w = float(data["Close"].min().item())

        # 현재 위치 (52주 고점 대비)
        position_from_high = ((current_price - high_52w) / high_52w) * 100

        # 트렌드 판단
        if change_7d > 3:
            trend_emoji = "🚀"  # 강한 상승
        elif change_7d > 0:
            trend_emoji = "📈"  # 상승
        elif change_7d < -3:
            trend_emoji = "💥"  # 강한 하락
        else:
            trend_emoji = "📉"  # 하락

        # 20일 이동평균 계산
        ma_20_series = data["Close"].rolling(window=20).mean()
        ma_20 = (
            float(ma_20_series.iloc[-1].item())
            if not ma_20_series.empty
            else current_price
        )

        # NaN 체크 후 비교
        if pd.isna(ma_20):
            ma_20 = current_price
            ma_signal = "정보없음"
            ma_emoji = "⚫"
        else:
            ma_signal = "위" if current_price > ma_20 else "아래"
            ma_emoji = "🟢" if current_price > ma_20 else "🔴"

        message = f"""
{emoji} *{name}* {trend_emoji}
💰 현재가: {unit}{current_price:,.2f}
- 변화율: 1D {change_1d:+.1f}% | 7D {change_7d:+.1f}% | 30D {change_30d:+.1f}% | 1Y {change_1y:+.1f}%
- 52주 고점 대비: {position_from_high:+.1f}%
- 20MA: {ma_emoji} 20일선 {ma_signal} ({unit}{ma_20:,.2f})
- 52주 범위: {unit}{low_52w:,.2f} - {unit}{high_52w:,.2f}
        """.strip()

        return message

    except Exception as e:
        return f"⚠️ {name} 분석 중 오류 발생: {str(e)}"


def get_commodity_sentiment():
    """Analyze overall commodity market sentiment"""
    try:
        # DJP (원자재 ETF)를 통한 전체 원자재 시장 분석
        djp_data = yf.download(
            "DJP",
            start=str(date.today() - timedelta(days=30)),
            end=str(date.today() + timedelta(days=1)),
            progress=False,
            auto_adjust=True,
        )

        if not djp_data.empty:
            current = float(djp_data.iloc[-1, 3])
            month_ago = float(djp_data.iloc[0, 3]) if len(djp_data) > 1 else current
            change = ((current - month_ago) / month_ago) * 100

            if change > 5:
                sentiment = "🟢 강세 (원자재 슈퍼사이클 신호?)"
            elif change > 0:
                sentiment = "🟡 약한 상승세"
            elif change < -5:
                sentiment = "🔴 약세 (디플레이션 우려)"
            else:
                sentiment = "⚫ 보합세"

            return f"🌍 *원자재 시장 전체*: {sentiment} ({change:+.1f}%)"

    except Exception as e:
        print(f"원자재 시장 심리 분석 실패: {e}")

    return "🌍 *원자재 시장 전체*: 데이터 없음"


def analyze_dxy_impact():
    """Analyze DXY (Dollar Index) impact on commodities"""
    try:
        # 달러 인덱스 (DXY) 분석
        dxy_data = yf.download(
            "DX=F",
            start=str(date.today() - timedelta(days=7)),
            end=str(date.today() + timedelta(days=1)),
            progress=False,
            auto_adjust=True,
        )

        if not dxy_data.empty:
            current_dxy = float(dxy_data.iloc[-1, 3])
            week_ago_dxy = (
                float(dxy_data.iloc[0, 3]) if len(dxy_data) > 1 else current_dxy
            )
            dxy_change = ((current_dxy - week_ago_dxy) / week_ago_dxy) * 100

            if dxy_change > 1:
                impact = "🔴 달러 강세 → 원자재 압박"
            elif dxy_change < -1:
                impact = "🟢 달러 약세 → 원자재 호재"
            else:
                impact = "🟡 달러 안정 → 중립적 영향"

            return (
                f"💵 *DXY 영향*: {impact} (DXY: {current_dxy:.1f}, {dxy_change:+.1f}%)"
            )

    except Exception as e:
        print(f"DXY 영향 분석 실패: {e}")

    return "💵 *DXY 영향*: 데이터 없음"


def analyze_inflation_signals():
    """
    Analyze inflation/deflation signals based on key commodities
    Based on CRB index methodology and central bank monitoring practices
    """
    try:
        # 핵심 인플레이션 지표 원자재들 (30일 변화율)
        period_days = 30
        start_date = str(date.today() - timedelta(days=period_days))
        end_date = str(date.today() + timedelta(days=1))

        # 에너지: 원유 (가장 중요한 인플레이션 지표)
        oil_data = yf.download(
            "CL=F", start=start_date, end=end_date, progress=False, auto_adjust=True
        )

        # 산업금속: 구리 (경기 선행지표 "Dr. Copper")
        copper_data = yf.download(
            "HG=F", start=start_date, end=end_date, progress=False, auto_adjust=True
        )

        # 농산물: 밀 (식품 인플레이션 대표)
        wheat_data = yf.download(
            "ZW=F", start=start_date, end=end_date, progress=False, auto_adjust=True
        )

        signals = []
        weight_total = 0
        weighted_change = 0

        # 원유 분석 (가중치 50% - 가장 중요)
        if not oil_data.empty and len(oil_data) > 1:
            oil_change = (
                (oil_data.iloc[-1, 3] - oil_data.iloc[0, 3]) / oil_data.iloc[0, 3]
            ) * 100
            weighted_change += oil_change * 0.5
            weight_total += 0.5
            signals.append(f"🛢️ 원유: {oil_change:+.1f}%")

        # 구리 분석 (가중치 30% - 산업 수요 반영)
        if not copper_data.empty and len(copper_data) > 1:
            copper_change = (
                (copper_data.iloc[-1, 3] - copper_data.iloc[0, 3])
                / copper_data.iloc[0, 3]
            ) * 100
            weighted_change += copper_change * 0.3
            weight_total += 0.3
            signals.append(f"🔶 구리: {copper_change:+.1f}%")

        # 밀 분석 (가중치 20% - 식품 인플레이션)
        if not wheat_data.empty and len(wheat_data) > 1:
            wheat_change = (
                (wheat_data.iloc[-1, 3] - wheat_data.iloc[0, 3]) / wheat_data.iloc[0, 3]
            ) * 100
            weighted_change += wheat_change * 0.2
            weight_total += 0.2
            signals.append(f"🌾 밀: {wheat_change:+.1f}%")

        if weight_total == 0:
            return "⚠️ *인플레이션 신호*: 데이터 없음"

        # 가중평균 계산
        avg_change = weighted_change / weight_total

        # 인플레이션/디플레이션 신호 판단 (CRB 기준)
        if avg_change > 8:
            signal = "🚨 *강한 인플레이션 압박* (코스트푸시형)"
            emoji = "🔥"
        elif avg_change > 3:
            signal = "⚠️ *인플레이션 주의* (상승 압력)"
            emoji = "📈"
        elif avg_change < -8:
            signal = "❄️ *디플레이션 우려* (원자재 급락)"
            emoji = "📉"
        elif avg_change < -3:
            signal = "😐 *디플레이션 압력* (하락세)"
            emoji = "⬇️"
        else:
            signal = "📊 *인플레이션 안정* (정상 범위)"
            emoji = "✅"

        # 결과 메시지
        signal_detail = " | ".join(signals)
        result = f"""
{emoji} *인플레이션 신호* ({period_days}일 기준)
{signal}
📊 가중평균: {avg_change:+.1f}% | {signal_detail}
        """.strip()

        return result

    except Exception as e:
        print(f"인플레이션 신호 분석 실패: {e}")
        return "⚠️ *인플레이션 신호*: 분석 실패"


def commodities_main():
    """Main function for commodities analysis"""

    # 분석할 원자재들
    commodities = [
        ("GC=F", "금 (Gold)", "🥇", "$"),
        ("CL=F", "원유 (WTI Crude)", "🛢️", "$"),
        ("HG=F", "구리 (Copper)", "🔶", "$"),
        ("ZW=F", "밀 (Wheat)", "🌾", "$"),
    ]

    messages = []

    # 제목 메시지
    title_message = "🏗️ *원자재 시장 분석* 🏗️"
    messages.append(title_message)

    # 전체 시장 심리
    sentiment = get_commodity_sentiment()
    messages.append(sentiment)

    # 달러 영향 분석
    dxy_impact = analyze_dxy_impact()
    messages.append(dxy_impact)

    # 각 원자재 분석
    for ticker, name, emoji, unit in commodities:
        analysis = analyze_commodity(ticker, name, emoji, unit)
        messages.append(analysis)
        time.sleep(1)  # API 호출 제한 고려

    # 핵심 인플레이션 지표 분석 (CRB 지수 기반)
    inflation_analysis = analyze_inflation_signals()
    if inflation_analysis:
        messages.append(inflation_analysis)

    # 종합 메시지 전송
    final_message = "\n\n".join(messages)
    slackout_commodities(final_message)

    # 요약 정보 반환
    try:
        # 금 가격으로 대표 요약 (1주일 변화율 포함)
        gold_data = yf.download(
            "GC=F",
            start=str(date.today() - timedelta(days=10)),  # 1주일 + 여유분
            end=str(date.today() + timedelta(days=1)),
            progress=False,
            auto_adjust=True,
        )
        if not gold_data.empty and len(gold_data) >= 2:
            current_gold = float(gold_data.iloc[-1, 3])
            # 1주일 전 가격 (7영업일 전, 최소 2일 전)
            week_ago_gold = (
                float(gold_data.iloc[-8, 3])
                if len(gold_data) >= 8
                else float(gold_data.iloc[0, 3])
            )

            # 1주일 변화율 계산
            week_change = ((current_gold - week_ago_gold) / week_ago_gold) * 100

            # 상승/하락 이모지
            trend_emoji = "📈" if week_change >= 0 else "📉"

            summary_data = (
                f"원자재: 금 ${current_gold:.0f} ({week_change:+.1f}% {trend_emoji})"
            )
        else:
            summary_data = "원자재: 데이터 부족"
    except Exception as e:
        print(f"원자재 요약 오류: {e}")
        summary_data = "원자재: 시장 분석 오류"

    print("✅ 원자재 분석 완료")
    return summary_data
