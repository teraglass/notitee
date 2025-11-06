from datetime import datetime, date, timedelta
import yfinance as yf
from module.slack import slackout_ma_stage, slackout_summary
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def analyze_ma_stage():
    """
    이동평균선 투자법 - 6단계 스테이지 분석
    단기(5일), 중기(20일), 장기(40일) 이동평균선 배열로 시장 국면 판단
    """
    try:
        # 1년간 데이터 다운로드 (40MA + 여유분)
        data = yf.download(
            "^GSPC", period="1y", interval="1d", progress=False, auto_adjust=True
        )

        if data.empty or len(data) < 40:
            return None

        close_prices = data["Close"].dropna()

        # 이동평균선 계산
        ma_5 = close_prices.rolling(window=5).mean()
        ma_20 = close_prices.rolling(window=20).mean()
        ma_40 = close_prices.rolling(window=40).mean()

        # 현재 값들
        current_price = float(close_prices.iloc[-1].item())
        current_ma5 = float(ma_5.iloc[-1].item())
        current_ma20 = float(ma_20.iloc[-1].item())
        current_ma40 = float(ma_40.iloc[-1].item())

        # 스테이지 판단
        stage, stage_name, trend_direction, market_psychology, strategy = (
            determine_stage(current_ma5, current_ma20, current_ma40)
        )

        # 크로스 신호 확인 (최근 3일 내)
        cross_events = check_recent_crosses(ma_5, ma_20, ma_40)

        return {
            "current_price": current_price,
            "ma_5": current_ma5,
            "ma_20": current_ma20,
            "ma_40": current_ma40,
            "stage": stage,
            "stage_name": stage_name,
            "trend_direction": trend_direction,
            "market_psychology": market_psychology,
            "strategy": strategy,
            "cross_events": cross_events,
        }

    except Exception as e:
        print(f"이동평균선 스테이지 분석 실패: {e}")
        return None


def determine_stage(ma5, ma20, ma40):
    """6단계 스테이지 판별"""

    # 스테이지 1: 단기 > 중기 > 장기 (정배열)
    if ma5 > ma20 > ma40:
        return (
            1,
            "제1스테이지 - 안정적 상승",
            "🚀 강력한 상승 추세",
            "💎 모든 투자자 수익권, 강력한 매수세",
            "🟢 적극적 매수 및 보유 - 이익 극대화 구간",
        )

    # 스테이지 2: 중기 > 단기 > 장기 (상승 둔화)
    elif ma20 > ma5 > ma40:
        return (
            2,
            "제2스테이지 - 상승 추세 둔화",
            "⚠️ 단기 조정 시작",
            "📉 단기 데드크로스 발생, 과열 조정",
            "🟡 매수 포지션 청산 고려 - 신규 매수 금물",
        )

    # 스테이지 3: 중기 > 장기 > 단기 (하락 전환 초기)
    elif ma20 > ma40 > ma5:
        return (
            3,
            "제3스테이지 - 하락 전환 초기",
            "📉 하락 추세 시작",
            "🔴 매도 세력 우위, 하락 에너지 강화",
            "🔴 매수 포지션 필수 청산 - 매도 준비",
        )

    # 스테이지 4: 장기 > 중기 > 단기 (역배열)
    elif ma40 > ma20 > ma5:
        return (
            4,
            "제4스테이지 - 안정적 하락",
            "💥 강력한 하락 추세",
            "😱 모든 투자자 손실권, 공포 심리 극대화",
            "🔴 매도 포지션 유지 - 하락 이익 극대화",
        )

    # 스테이지 5: 장기 > 단기 > 중기 (하락 둔화)
    elif ma40 > ma5 > ma20:
        return (
            5,
            "제5스테이지 - 하락 추세 둔화",
            "📈 바닥 다지기 시작",
            "💡 단기 골든크로스, 기술적 반등 시도",
            "🟡 매도 포지션 청산 고려 - 선발대 투입 검토",
        )

    # 스테이지 6: 단기 > 장기 > 중기 (상승 전환 초기)
    elif ma5 > ma40 > ma20:
        return (
            6,
            "제6스테이지 - 상승 전환 초기",
            "🌅 상승 추세 준비",
            "🎯 상승 에너지 축적, 희망의 신호",
            "🟢 매수 준비 - 제1스테이지 진입 확인 후 본격 매수",
        )

    # 예외 상황 (박스권 등)
    else:
        return (
            0,
            "박스권 - 추세 불분명",
            "🔄 횡보 또는 변동성 장세",
            "😐 방향성 부재, 혼조세",
            "⚫ 관망 - 명확한 추세 출현까지 대기",
        )


def check_recent_crosses(ma5, ma20, ma40, days=3):
    """최근 크로스 이벤트 확인"""
    cross_events = []

    try:
        # 최근 며칠간의 크로스 확인
        for i in range(-days, 0):
            if len(ma5) > abs(i) and len(ma20) > abs(i):
                # 5MA vs 20MA 크로스
                prev_5 = float(ma5.iloc[i - 1].item())
                prev_20 = float(ma20.iloc[i - 1].item())
                curr_5 = float(ma5.iloc[i].item())
                curr_20 = float(ma20.iloc[i].item())

                if prev_5 <= prev_20 and curr_5 > curr_20:
                    cross_events.append("🌟 5MA↗20MA 골든크로스 (단기 반등)")
                elif prev_5 >= prev_20 and curr_5 < curr_20:
                    cross_events.append("💀 5MA↘20MA 데드크로스 (단기 조정)")

                # 5MA vs 40MA 크로스
                if len(ma40) > abs(i):
                    prev_40 = float(ma40.iloc[i - 1].item())
                    curr_40 = float(ma40.iloc[i].item())

                    if prev_5 <= prev_40 and curr_5 > curr_40:
                        cross_events.append("⭐ 5MA↗40MA 돌파 (중요한 상승 신호)")
                    elif prev_5 >= prev_40 and curr_5 < curr_40:
                        cross_events.append("🔥 5MA↘40MA 하락 (중요한 하락 신호)")

                # 20MA vs 40MA 크로스 (가장 중요)
                if len(ma40) > abs(i):
                    if prev_20 <= prev_40 and curr_20 > curr_40:
                        cross_events.append("🚀 20MA↗40MA 돌파 - 스테이지 전환!")
                    elif prev_20 >= prev_40 and curr_20 < curr_40:
                        cross_events.append("💥 20MA↘40MA 하락 - 스테이지 전환!")

    except Exception as e:
        print(f"크로스 이벤트 확인 실패: {e}")

    return cross_events


def ma_stage_analysis_main():
    """이동평균선 스테이지 분석 메인 함수"""
    try:
        analysis = analyze_ma_stage()

        if not analysis:
            slackout_ma_stage(
                "⚠️ *이동평균선 스테이지 분석*\n데이터를 가져올 수 없습니다"
            )
            return

        # 크로스 이벤트 메시지
        cross_msg = ""
        if analysis["cross_events"]:
            cross_msg = "\n📊 *최근 크로스*: " + " | ".join(analysis["cross_events"])

        # 종합 리포트 생성
        report = f"""
📈 *이동평균선 스테이지 분석* 📈
- *현재가*: {analysis['current_price']:,.2f}
- *5일선*: {analysis['ma_5']:,.2f}
- *20일선*: {analysis['ma_20']:,.2f} 
- *40일선*: {analysis['ma_40']:,.2f}

🎯 *{analysis['stage_name']}*
{analysis['trend_direction']}
{analysis['market_psychology']}

💡 *투자 전략*: {analysis['strategy']}{cross_msg}
        """.strip()

        slackout_ma_stage(report)

        # 요약 정보 반환
        summary_data = f"MA단계: {analysis['stage_name']} | {analysis['strategy'].replace('*', '').replace('💡 투자 전략: ', '')}"
        print("✅ 이동평균선 스테이지 분석 완료")
        return summary_data

    except Exception as ex:
        slackout_ma_stage(f"⚠️ *이동평균선 스테이지 분석*\n예외 처리: {str(ex)}")
        print("✅ 이동평균선 스테이지 분석 완료 (오류)")
        return "MA단계: 분석 오류"


def get_current_stage_info():
    """현재 스테이지 정보만 간단히 반환 (다른 모듈에서 사용용)"""
    analysis = analyze_ma_stage()
    if analysis:
        return f"📊 *MA스테이지*: {analysis['stage_name']}"
    return "📊 *MA스테이지*: 정보없음"
