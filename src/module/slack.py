import slack_sdk
import sys, os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def slackout_summary(message: str):
    """Send summary message to main summary channel only (no individual channel)"""
    # Get environment variables
    slack_token = os.getenv("SLACK_TOKEN")
    slack_user_id = os.getenv("SLACK_USER_ID")

    if not slack_token:
        print("Error: SLACK_TOKEN environment variable not set")
        return None
    if not slack_user_id:
        print("Error: SLACK_USER_ID environment variable not set")
        return None

    current_time = get_data_freshness()
    client = slack_sdk.WebClient(token=slack_token)

    # 요약 채널에만 보냄 (개별 채널 전송 없음)
    summary_msg = f"📊 *일일 시장 요약* {current_time}\n{message}"
    summary_channel = "summary"
    response = client.chat_postMessage(channel=summary_channel, text=summary_msg)
    return response


def slackout(message: str, channel_tag: str, channel: str):
    """Send message to Slack with optional channel selection"""
    # Get environment variables
    slack_token = os.getenv("SLACK_TOKEN")
    slack_user_id = os.getenv("SLACK_USER_ID")

    if not slack_token:
        print("Error: SLACK_TOKEN environment variable not set")
        return None
    if not slack_user_id:
        print("Error: SLACK_USER_ID environment variable not set")
        return None

    current_time = get_data_freshness()
    client = slack_sdk.WebClient(token=slack_token)

    # 공통 포맷
    slack_msg = f"<{channel_tag}> {current_time} \n{message}"

    # 개별 채널에 보냄 (알림 음소거 상태)
    extra_channel = channel
    response = client.chat_postMessage(channel=extra_channel, text=slack_msg)
    return response


# 각 스크립트에 마지막 업데이트 시간 표시 추가
def get_data_freshness():
    from datetime import timezone, timedelta

    # KST는 UTC+9
    kst = timezone(timedelta(hours=9))
    current_time = datetime.now(kst)
    return current_time.strftime("%Y-%m-%d %H:%M:%S KST")


# === 0번 시리즈: 기본 지표/데이터 ===
def slackout_dollar(message: str):
    """Send message to dollar/currency channel"""
    return slackout(message, channel_tag="#C09PYLC5HHA", channel="0-currency")


def slackout_sp500(message: str):
    """Send message to S&P500 channel"""
    return slackout(message, channel_tag="#C09Q7T0TR25", channel="0-snp")


def slackout_feargreed(message: str):
    """Send message to Fear & Greed channel"""
    return slackout(message, channel_tag="#C09Q7SXFDHP", channel="0-feargreed")


def slackout_crypto(message: str):
    """Send message to crypto channel"""
    return slackout(message, channel_tag="#C09QTPVDGG6", channel="0-crypto")


def slackout_bonds(message: str):
    """Send message to bonds channel"""
    return slackout(message, channel_tag="#C09QPDBDMMH", channel="0-bonds")


def slackout_commodities(message: str):
    """Send message to commodities channel"""
    return slackout(message, channel_tag="#C09QVRFGS1G", channel="0-commodities")


# === 1번 시리즈: 차트/분석/API ===
def slackout_ma_stage(message: str):
    """Send message to MA Stage channel"""
    return slackout(message, channel_tag="#C09QT3GRDQD", channel="1-ma_stage")


def slackout_charts(message: str):
    """Send message to charts channel"""
    return slackout(message, channel_tag="#C01CHARTS01", channel="1-charts")


def slackout_api(message: str):
    """Send message to API channel"""
    return slackout(message, channel_tag="#C01API0001", channel="1-api")


def slackout_research(message: str):
    """Send message to research channel"""
    return slackout(message, channel_tag="#C01RSRCH01", channel="1-research")


def slackout_alerts(message: str):
    """Send message to alerts channel"""
    return slackout(message, channel_tag="#C01ALERT01", channel="1-alerts")
