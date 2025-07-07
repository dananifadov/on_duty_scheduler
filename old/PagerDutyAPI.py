import requests


class PagerDutyAPI:
    def __init__(self, api_token):
        self.api_key = api_token
        self.base_url = 'https://api.pagerduty.com'
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Token token={self.api_key}'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.verify = False  # This is unverified HTTP request

    def __del__(self):
        self.session.close()

    def _get_entity_id_by_name(self, entity_type, name):
        url = f'{self.base_url}/{entity_type}'
        params = {'limit': 100}

        while True:
            response = self.session.get(url, params=params)
            if response.status_code == 200:
                entities_data = response.json()
                entities = entities_data[f'{entity_type}']
                for entity in entities:
                    if entity['name'] == name:
                        return entity['id']

                # Check if there are more pages
                if 'more' in entities_data and entities_data['more']:
                    params['offset'] = entities_data['offset'] + entities_data['limit']
                else:
                    print(f"No {entity_type} named {name}")
                    break
            else:
                print(f"Failed to get {entity_type}. Status code: {response.status_code}")
                return None

    def get_user_id_by_name(self, user_name):
        return self._get_entity_id_by_name('users', user_name)

    def get_team_id_by_name(self, team_name):
        return self._get_entity_id_by_name('teams', team_name)

    def get_schedule_id_by_name(self, schedule_name):
        return self._get_entity_id_by_name('schedules', schedule_name)

    def create_shift(self, schedule_id, start_time, end_time, user_id):
        url = f"{self.base_url}/schedules/{schedule_id}/overrides"
        overrides = [
            {
                "start": start_time,
                "end": end_time,
                "user": {
                    "id": user_id,
                    "type": "user_reference",
                },
            }
        ]
        response = self.session.post(url, json={"overrides": overrides})
        if 200 <= response.status_code <= 299:
            print("Shift created successfully.")
            return True
        else:
            print(f"Request status code: {response.status_code}. Error message: {response.text}")
            return False

    def get_user_for_shift(self, schedule_id, start_time, end_time):
        url = f'{self.base_url}/schedules/{schedule_id}/overrides'
        params = {
            'since': start_time,
            'until': end_time,
        }
        response = self.session.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if data['overrides']:
                return data['overrides'][0]['user']['summary']
            else:
                # If no shift is found within the time range, return None
                return None
        else:
            # Print an error message if the request was not successful
            print(f"Request status code: {response.status_code}. Error Message: {response.text}")
            return None
