'''basic class to act as a client for the CCHUB Api'''

# https://{SERVER_ADDRESS}/api/v{VERSION}/{MODEL}/{NAME}.json?accessToken={ACCESS_TOKEN}&{OPTIONAL_PARAMS}
# Date Format: "yyyy-mm-dd hh:mm:ss", for example "2019-05-23 14:22:59"

from requests import Request, Session, RequestException
from configparser import ConfigParser

class CchubApiClient:
    '''basic class to act as a client for the CCHUB Api
    it is expected that this Class will be extended with business logic
    for middleware purposes

    scope:
    handle auth, session and retry functionality

    params:
    {
        'skip': 0, # offset
        'take': 20, # pagesize
        'sort': [
		    {"field":"firstname", "dir":"desc"},
		    {"field":"lastname", "dir":"asc"}
        ], # custom field example: "field": "customFields.telefon"
        "filter": {
		    "field": "firstname",
		    "operator": "eq", # various operators available
		    "value": "John"
	    }, # filter can be a list of filter dicts
        "fields": [
            "firstname",
            "lastname",
            "account.title"
	    ], # limit the fields which are returned

    }
    '''
    def __init__(self, server_address, version, token):
        self.base_url = f'{server_address}'
        self.version_url = f'/api/v{version}'
        self.access_token = token
        self.session = Session()

    def _auth(self, params=None):
        '''add access token to params variable'''
        if params:
            params['accessToken'] = self.access_token
        else: 
            params = {'accessToken': self.access_token}
        return params
    
    def _make_request(self, method, endpoint, params=None, data=None):
        
        url = f'{self.base_url}{endpoint}'
        req = Request(
            method,
            url,
            params=self._auth(params),
            data=data)
        prepped = req.prepare()
        
        try:
            response = self.session.send(prepped, timeout=10)
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response.json()  # Assuming the API returns JSON data
        except RequestException as error:
            print(f"Error fetching data from the API: {error}")
            return None

    def get(self, endpoint, params=None):
        return self._make_request('GET', endpoint, params=params)

    def post(self, endpoint, data=None):
        return self._make_request('POST', endpoint, data=data)

    def put(self, endpoint, data=None):
        return self._make_request('PUT', endpoint, data=data)

    def delete(self, endpoint):
        return self._make_request('DELETE', endpoint)
    
    def simulate(self, endpoint, method, params=None):
        if params:
            params['_method'] = method.upper()
        else: 
            params = {'_method': method.upper()}
        return self._make_request('GET', endpoint, params=params)

# Example usage:
# file = open('cchub_api_client.py')
# exec(file.read())
if __name__ == "__main__":
    from pprint import PrettyPrinter
    pp = PrettyPrinter()
    config = ConfigParser()
    config.read('config.ini')
    base_url = config['API']['SERVER_ADDRESS']
    version = config['API']['VERSION']
    access_token = config['API']['ACCESS_TOKEN']

    ccapi = CchubApiClient(base_url, version, access_token)

    # # Example dynamic endpoint access:
    # customers_data = api_client.get('customers')
    # orders_data = api_client.get('orders')
    # # You can use api_client.post(), api_client.put(), and api_client.delete() similarly.

    # if customers_data:
    #     for customer in customers_data:
    #         print(customer)

    # if orders_data:
    #     for order in orders_data:
    #         print(order)
