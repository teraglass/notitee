import slack_sdk
import sys, os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


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
    slack_msg = f"<{channel_tag}> {current_time} {message}"

    # 모음 채널에 한번 보냄
    notitee_slack_msg = f"<@{slack_user_id}> {slack_msg}"
    main_channel = "notitee_msg"
    response = client.chat_postMessage(channel=main_channel, text=notitee_slack_msg)

    # 개별 채널에도 보냄 (알림 음소거 상태)
    extra_channel = channel
    response = client.chat_postMessage(channel=extra_channel, text=slack_msg)
    return response


# Convenience functions for specific channels
def slackout_dollar(message: str):
    """Send message to dollar/currency channel"""
    return slackout(message, channel_tag="#C09PYLC5HHA", channel="0-currency")


def slackout_sp500(message: str):
    """Send message to S&P500 channel"""
    return slackout(message, channel_tag="#C09Q7T0TR25", channel="0-snp")


def slackout_feargreed(message: str):
    """Send message to Fear & Greed channel"""
    return slackout(message, channel_tag="#C09Q7SXFDHP", channel="0-feargreed")


# 각 스크립트에 마지막 업데이트 시간 표시 추가
def get_data_freshness():
    from datetime import timezone, timedelta

    # KST는 UTC+9
    kst = timezone(timedelta(hours=9))
    current_time = datetime.now(kst)
    return current_time.strftime("%Y-%m-%d %H:%M:%S KST")
