from datetime import datetime, date, timedelta
import pytz
us_time = datetime.now(pytz.timezone('America/New_York'))           # 미국 서머타임인지 확인하는 로직
# pytz의 timezone 매써드를 이용하여 'New_York'의 현지시간을 가져와 datetime.now로 us time 변수 할당
diff_hour = us_time.utcoffset().total_seconds()/60/60
# us_현지시각와 utcoffset method를 이용해 UTC 현지 시간과 시간 차이를 계산함          # 써머타임시 -4.0 임

us_summertime = False
if diff_hour == -4.0:
    us_summertime = True
# us_summetime 체크 Flag를 생성하고 UTC와 Newyork의 시차가 4시간인 경우 해당 Flag를 True 변경

if us_summertime == True:
    pass
    # slackOut('미국 써머타임 중!')       # Slack Alarm
    # doSomthingWithRPA()                # RPA 시간대 변경