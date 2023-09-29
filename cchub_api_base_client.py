'''basic class to act as a client for the CCHUB Api'''

# https://{SERVER_ADDRESS}/api/v{VERSION}/{MODEL}/{NAME}.json?accessToken={ACCESS_TOKEN}&{OPTIONAL_PARAMS}
# Date Format: "yyyy-mm-dd hh:mm:ss", for example "2019-05-23 14:22:59"

from configparser import ConfigParser
from requests import Request, Session, RequestException
from requests.adapters import HTTPAdapter

class CchubApiBaseClient:
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
    def __init__(self, server_address, api_version, token):
        self.base_url = f'{server_address}'
        self.version_url = f'/api/v{api_version}'
        self.access_token = token
        self.session = Session()
        adapter = HTTPAdapter(max_retries=3)
        self.session.mount(self.base_url, adapter)
        self.timeout = 10

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
            response = self.session.send(prepped, timeout=self.timeout)
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response
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

# Example interpreter usage:
# file = open('cchub_api_base_client.py')
# exec(file.read())
if __name__ == "__main__":
    from pprint import PrettyPrinter
    pp = PrettyPrinter()
    config = ConfigParser()
    config.read('config.ini')
    base_url = config['API']['SERVER_ADDRESS']
    version = config['API']['VERSION']
    access_token = config['API']['ACCESS_TOKEN']

    ccapi = CchubApiBaseClient(base_url, version, access_token)
