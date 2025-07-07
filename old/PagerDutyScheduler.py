from datetime import datetime, timedelta

from PagerDutyAPI import PagerDutyAPI

class PagerDutyScheduler:
    def __init__(self, pd_schedule, employee_data, start_date, end_date, shift_switch_hour):
        self.pager_duty = PagerDutyAPI(api_token='u+HwZ8N2o6ch7RqkBaSg')  # TODO: this token is for Playtika. Don't publish it externally.
        self.pd_schedule_id = self.pager_duty.get_schedule_id_by_name(pd_schedule)
        self.shift_switch_hour = shift_switch_hour # shift_switch_hour is a number between 0-23
        self.start_date = start_date # start_date and end_date are datetime objects
        self.end_date = end_date
        self.schedule = self._initialize_empty_schedule(start_date, end_date) # schdule is a dictionary with dates as keys and names as values.
        self.users_data = self._read_employee_data(employee_data)
        self.constraints = self._initialize_constraints(start_date, end_date)
        # TODO: import holidays somehow for relevant countries.
        # TODO: allow the user to set double score for specific dates (like a company trip day)

    """returns a dictionary with keys for all dates between start and end"""
    def _initialize_empty_schedule(self, start_date, end_date):
        schedule = {}
        date = start_date
        while date <= end_date:
            schedule[date] = None
            date = date + timedelta(days=1)
        return schedule

    """reads off time from Teams into a dictionary or something. Need to think how to get that."""
    def _initialize_constraints(self, start_date, end_date):
        pass

    """reads the json with emploees data into a dictionary. The keys can be the user_ids from PagerDuty"""
    def _read_employee_data(self, employee_data):
        pass

    """does the algorithem and updates self.schedule and the score of each user in self.users_data"""
    def generate_schedule(self):
        pass

    def print_schedule(self):
        pass

    def print_scores(self):
        pass

    """reads into schedule the shifts that already exists in pager duty for that period.
    (I think no need to update scores in that case)"""
    def update_schedule_from_pager_duty(self):
        date = self.start_date
        while date <= self.end_date:
            self.schedule[date] = self.pager_duty.get_user_for_shift(self.pd_schedule_id, date, date + timedelta(days=1))
            date = date + timedelta(days=1)


    """allows to change manually a single shift in the schedule (and update scores)
    Override=True will allow to override off-time. Otherwise won't do the switch.
    Assuming a shift is 24hrs, we can use the "date" parameter and self.shift_switch_hour to create the start_time and 
    end_time in the correct format for PagerDutyAPI which is: "%Y-%m-%dT%H:%M:%SZ" 
    """
    def change_shift_in_schedule(self, date, employee_name, override=False):
        pass

    """Commit the entire schedule to pager duty"""
    def commit_schedule_to_pager_duty(self):
        for date in self.schedule.items():
            self.commit_shift_to_pager_duty(date)

    """Commit single shift from schedule into pager duty. Parameter date is datetime object"""
    def commit_shift_to_pager_duty(self, date):
        # assuming schedule is a dictionary with dates as keys and employees names as values.
        user_id = self.pager_duty.get_user_id_by_name(self.schedule[date])
        start_time = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S") + timedelta(hours=self.shift_switch_hour)
        end_time = start_time + timedelta(days=1)

        # Adding the shift to PagerDuty
        self.pager_duty.create_shift(self.pd_schedule_id, start_time, end_time, user_id)
