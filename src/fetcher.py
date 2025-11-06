from module.dollar_currency import dollar_currency_analysis
from module.cnn_fear_greed import cnn_fear_greed_main
from module.snp500_200ma import snp500_200ma_main
from module.crypto_analysis import crypto_analysis_main
from module.bond_yields import bond_yields_main
from module.commodities import commodities_main
from module.ma_stage_analysis import ma_stage_analysis_main
from module.slack import slackout_summary
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    print("✨ 일일 시장 분석 시작...")

    # 각 모듈 실행하고 요약 데이터 수집
    summaries = []

    # 달러/환율 분석
    try:
        dollar_summary = dollar_currency_analysis()
        if dollar_summary:
            summaries.append(dollar_summary)
    except Exception as e:
        summaries.append("달러: 분석 오류")
        print(f"♦️ 달러 분석 오류: {e}")

    # CNN 공포탐욕지수
    try:
        feargreed_summary = cnn_fear_greed_main()
        summaries.append(feargreed_summary)
    except Exception as e:
        summaries.append("공포탐욕: 분석 오류")
        print(f"♦️ 공포탐욕 분석 오류: {e}")

    # S&P 500 분석
    try:
        sp500_summary = snp500_200ma_main()
        summaries.append(sp500_summary)
    except Exception as e:
        summaries.append("S&P500: 분석 오류")
        print(f"♦️ S&P500 분석 오류: {e}")

    # 암호화폐 분석
    try:
        crypto_summary = crypto_analysis_main()
        summaries.append(crypto_summary)
    except Exception as e:
        summaries.append("암호화폐: 분석 오류")
        print(f"♦️ 암호화폐 분석 오류: {e}")

    # 채권 분석
    try:
        bond_summary = bond_yields_main()
        summaries.append(bond_summary)
    except Exception as e:
        summaries.append("채권: 분석 오류")
        print(f"♦️ 채권 분석 오류: {e}")

    # 원자재 분석
    try:
        commodity_summary = commodities_main()
        summaries.append(commodity_summary)
    except Exception as e:
        summaries.append("원자재: 분석 오류")
        print(f"♦️ 원자재 분석 오류: {e}")

    # MA 단계 분석
    try:
        ma_summary = ma_stage_analysis_main()
        summaries.append(ma_summary)
    except Exception as e:
        summaries.append("MA단계: 분석 오류")
        print(f"♦️ MA단계 분석 오류: {e}")

    # 종합 요약 메시지 전송
    final_summary = "\n".join([f"• {summary}" for summary in summaries])
    slackout_summary(final_summary)

    print("✅ 일일 시장 분석 완료!")


if __name__ == "__main__":
    main()
