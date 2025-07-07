from PagerDutyAPI import PagerDutyAPI
from datetime import datetime, timedelta


if __name__ == "__main__":
    pd = PagerDutyAPI(api_token='u+HwZ8N2o6ch7RqkBaSg')
    user_id = pd.get_user_id_by_name("Assaf Mazal Tov")
    schedule_id = pd.get_schedule_id_by_name('BI Cross Schedule')
    start_time = "2024-01-02T09:00:00"
    end_datetime = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S") + timedelta(days=1)
    end_time = end_datetime.strftime("%Y-%m-%dT%H:%M:%S")
    # pd.create_shift(schedule_id, start_time, end_time, user_id)
    print(pd.get_user_for_shift(schedule_id, start_time, end_time))

