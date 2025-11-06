from datetime import datetime, date, timedelta
import yfinance as yf
from module.slack import slackout_sp500, slackout_summary

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


def get_advanced_ma_analysis():
    """Advanced S&P500 moving average analysis with Golden/Death Cross"""
    try:
        # 더 많은 데이터 다운로드 (50MA + 200MA + 여유분)
        data = yf.download("^GSPC", period="1y", interval="1d", progress=False, auto_adjust=True)
        
        if data.empty or len(data) < 200:
            return None
        
        close_prices = data["Close"].dropna()
        
        # 50일, 200일 이동평균 계산
        ma_50 = close_prices.rolling(window=50).mean()
        ma_200 = close_prices.rolling(window=200).mean()
        
        # 현재 값들
        current_price = float(close_prices.iloc[-1].item())
        current_ma50 = float(ma_50.iloc[-1].item())
        current_ma200 = float(ma_200.iloc[-1].item())
        
        # 골든크로스/데스크로스 체크 (최근 5일 내)
        cross_signal = None
        for i in range(-5, 0):
            if len(ma_50) > abs(i) and len(ma_200) > abs(i):
                prev_50 = float(ma_50.iloc[i-1].item())
                prev_200 = float(ma_200.iloc[i-1].item())
                curr_50 = float(ma_50.iloc[i].item())
                curr_200 = float(ma_200.iloc[i].item())
                
                # 골든 크로스 (50MA가 200MA를 상향 돌파)
                if prev_50 <= prev_200 and curr_50 > curr_200:
                    cross_signal = "golden"
                    break
                # 데스 크로스 (50MA가 200MA를 하향 돌파)  
                elif prev_50 >= prev_200 and curr_50 < curr_200:
                    cross_signal = "death"
                    break
        
        return {
            'current_price': current_price,
            'ma_50': current_ma50,
            'ma_200': current_ma200,
            'cross_signal': cross_signal,
            'data': close_prices
        }
        
    except Exception as e:
        print(f"고급 MA 분석 실패: {e}")
        return None


def analyze_support_resistance(price, ma200, historical_data):
    """Analyze 200MA as support/resistance level"""
    try:
        # 최근 30일간 200MA 근처에서의 반응 분석 (더 많은 데이터로 개선)
        recent_data = historical_data.tail(30)
        
        # 실제 200MA와 비교 (전달받은 ma200 값 사용)
        tolerance = 0.03  # ±3%로 관대하게 설정
        near_ma_touches = 0
        bounces = 0
        
        # 디버깅을 위한 정보
        touch_details = []
        
        for i in range(len(recent_data)-1):
            current_price = recent_data.iloc[i].item()
            next_price = recent_data.iloc[i+1].item()
            
            # 200MA와의 거리 계산 (퍼센트)
            price_diff = abs((current_price - ma200) / ma200)
            
            if price_diff <= tolerance:  # 200MA 근처 터치
                near_ma_touches += 1
                touch_details.append(f"{current_price:.2f} vs {ma200:.2f}")
                
                # 다음날 반등/반락 여부 확인
                if current_price < ma200 and next_price > current_price:
                    # 200MA 아래에서 반등
                    bounces += 1
                elif current_price > ma200 and next_price < current_price:
                    # 200MA 위에서 저항받아 하락 (이것도 200MA의 영향력)
                    bounces += 1
        
        # 지지/저항 강도 계산
        if near_ma_touches > 0:
            bounce_rate = bounces / near_ma_touches
            if bounce_rate >= 0.6:
                strength = "강력"
            elif bounce_rate >= 0.3:
                strength = "보통"
            else:
                strength = "약함"
        else:
            # 터치가 없을 때는 현재 위치와 추세 기반으로 평가
            current_diff = abs((price - ma200) / ma200)
            
            if current_diff <= 0.01:  # 1% 이내
                strength = "임계점"  # 200MA 바로 근처 - 중요한 변곡점
            elif current_diff <= 0.05:  # 5% 이내
                if price > ma200:
                    strength = "지지권"  # 200MA 위쪽 근처 - 지지 가능성
                else:
                    strength = "저항권"  # 200MA 아래쪽 근처 - 저항 가능성
            else:  # 5% 이상 떨어져 있음
                if price > ma200:
                    strength = "상승세"  # 200MA 훨씬 위 - 강한 상승 추세
                else:
                    strength = "하락세"  # 200MA 훨씬 아래 - 강한 하락 추세
            bounce_rate = 0
        
        return {
            'strength': strength,
            'bounce_rate': bounce_rate * 100,
            'touches': near_ma_touches
        }
        
    except Exception as e:
        print(f"지지/저항 분석 오류: {e}")
        return {'strength': '오류', 'bounce_rate': 0, 'touches': 0}


def snp500_200ma_main():
    try:
        # 고급 분석 실행
        analysis = get_advanced_ma_analysis()
        
        if not analysis:
            slackout_sp500("⚠️ *S&P500 분석 리포트*\n데이터를 가져올 수 없습니다")
            return
        
        current_price = analysis['current_price']
        ma_50 = analysis['ma_50'] 
        ma_200 = analysis['ma_200']
        cross_signal = analysis['cross_signal']
        
        # 200MA 대비 위치 분석
        diff_200 = ((current_price - ma_200) / ma_200) * 100
        diff_50 = ((current_price - ma_50) / ma_50) * 100
        
        # 지지/저항 분석
        support_analysis = analyze_support_resistance(current_price, ma_200, analysis['data'])
        
        # 투자 결정 로직 (Perplexity 기반)
        if cross_signal == "golden":
            decision = "🟢 *강력 매수* - 골든크로스 발생!"
            market_outlook = "📈 장기 상승 추세 시작 (통계적으로 70% 확률로 1년간 8.6% 상승)"
        elif cross_signal == "death":
            decision = "🔴 *매도* - 데스크로스 발생!"
            market_outlook = "� 장기 하락 추세 우려"
        elif diff_200 > 10:
            decision = "🚀 *매수* - 강세장"
            market_outlook = "🔥 200MA 대비 강한 상승 모멘텀"
        elif diff_200 > 0:
            decision = "🟡 *매수 고려* - 상승 추세"
            market_outlook = f"📊 200MA가 {support_analysis['strength']} 지지선 역할"
        elif diff_200 > -5:
            decision = "⚠️ *관망* - 중립 구간" 
            market_outlook = "🔍 200MA 근처에서 방향성 관찰 필요"
        elif diff_200 > -10:
            decision = "🔴 *매도* - 하락 추세"
            market_outlook = f"📉 200MA가 저항선으로 작용 중"
        else:
            decision = "💥 *매도* - 약세장"
            market_outlook = "❄️ 장기 하락 추세 지속"
        
        # 크로스 신호 메시지
        cross_msg = ""
        if cross_signal == "golden":
            cross_msg = "\n🌟 *골든크로스*: 50MA > 200MA 돌파! (강세 신호)"
        elif cross_signal == "death":
            cross_msg = "\n☠️ *데스크로스*: 50MA < 200MA 하락! (약세 신호)"
        elif ma_50 > ma_200:
            cross_msg = f"\n📈 50MA가 200MA 위 ({((ma_50/ma_200-1)*100):+.1f}%)"
        else:
            cross_msg = f"\n📉 50MA가 200MA 아래 ({((ma_50/ma_200-1)*100):+.1f}%)"
        
        # 지지/저항 표시 방식 개선
        if support_analysis['touches'] > 0:
            # 실제 터치가 있는 경우: 반등률 표시
            support_info = f"{support_analysis['strength']} ({support_analysis['bounce_rate']:.0f}% 반등률)"
        else:
            # 터치가 없는 경우: 위치 설명 표시
            position_desc = {
                "임계점": "200MA 임계점",
                "지지권": f"200MA 위 {diff_200:.1f}%",
                "저항권": f"200MA 아래 {abs(diff_200):.1f}%", 
                "상승세": f"200MA 훨씬 위 (+{diff_200:.1f}%)",
                "하락세": f"200MA 훨씬 아래 ({diff_200:.1f}%)"
            }.get(support_analysis['strength'], f"{diff_200:+.1f}%")
            
            support_info = f"{support_analysis['strength']} ({position_desc})"

        # 종합 리포트 생성
        report = f"""
🦖 *S&P 500 기술적 분석* 🦖
- *현재가*: {current_price:,.2f}
- *200일선*: {ma_200:,.2f} ({diff_200:+.1f}%)
- *50일선*: {ma_50:,.2f} ({diff_50:+.1f}%){cross_msg}

- *지지/저항*: {support_info}
{market_outlook}

💡 *투자 결정*: {decision}
        """.strip()
        
        slackout_sp500(report)
        
        # 요약 정보 반환
        summary_data = f"S&P500: {current_price:,.0f} ({diff_200:+.1f}%) | {decision.split(' - ')[0]} | {cross_signal if cross_signal else '크로스 없음'}"
        print("✅ S&P500 200MA 분석 완료")
        return summary_data
        
    except Exception as ex:
        slackout_sp500(f"⚠️ *S&P500 분석 리포트*\n오류: {str(ex)}")
        print("♦️ S&P500 200MA 분석 오류")
        return "♦️ S&P500: 분석 오류"