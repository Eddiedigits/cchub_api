'''basic class to act as a client for the CCHUB Api'''

# https://{SERVER_ADDRESS}/api/v{VERSION}/{MODEL}/{NAME}.json?accessToken={ACCESS_TOKEN}&{OPTIONAL_PARAMS}
# Date Format: "yyyy-mm-dd hh:mm:ss", for example "2019-05-23 14:22:59"

from configparser import ConfigParser
from requests import Request, Session, RequestException
from requests.adapters import HTTPAdapter
from functools import partialmethod
from php import Php

def set_model_method(cls):
    verbs = ['get', 'post', 'put', 'delete']
    for model in cls.models:
        for verb in verbs:
            func_name = f'{verb}_{model}'
            setattr(cls, func_name, partialmethod(cls.model_func, model, verb, ))
    return cls

def set_get_all_method(cls):
    for model in cls.models:
        setattr(cls, f'get_all_{model}', partialmethod(cls.get_all, model))
    return cls

@set_get_all_method
@set_model_method
class CchubApiBaseClient:
    '''basic class to act as a client for the CCHUB Api
    it is expected that this Class will be extended with business logic
    for middleware purposes

    scope:
    handle auth, session and retry functionality
    provide basic methods for the api endpoints

    added dynamic methods:
    self.get_{model} 
        self.get_accounts() # get first page. default pagesize is 100
        self.get_accounts('name_4385245245') # get single item
    self.post_{model}(json={...}) # add single item
    self.put_{model}(cchub_uid, json={...}) # update single item
    self.get_all_{model} # get all items

    json: {
        'title': 'string',
        'database': {
            'title': 'string'
        },
        'customFields': {
            'MyCustomField': 'string'
        },
    }

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

    response.status_code: 200
    response.url: api_endpoint
    response.json(): {
        "error": [],
        "result": {
            "data": [
                {
                    "title": "string",
                    "database": {
                        "title": "string"
                    },
                    "customFields": {
                        "MyCustomField": "string"
                    },
                }
            ],
            "total": 0
        },
        
    }
    '''

    models = [
        'activities',
        'activitiesCall',
        'activitiesEmail',
        'activitiesWeb',
        'activitiesSms',
        'activitiesFbm',
        'activitiesIgdm',
        'activitiesWap',
        'activitiesVbr',
        'accounts',
        'contacts',
        'crmRecords',
        'crmDatabases',
        'campaignsRecords',
        'campaignsTypes',
        'databases',
        'groups',
        'pauses',
        'queues',
        'statuses',
        'templates',
        'tickets',
        'users',]

    def __init__(self, server_address, token, api_version='6'):
        self.base_url = f'{server_address}'
        self.access_token = token
        self.version_url = f'/api/v{api_version}'
        self.session = Session()
        adapter = HTTPAdapter(max_retries=3)
        self.session.mount(self.base_url, adapter)
        self.session.headers["Content-Type"]= "application/json"
        self.timeout = 10

    def model_func(self, model, verb, *args, **kwargs):
        '''simple get request for a model'''
        # cc.put_accounts('123', json={'customFields': {'business_name': 'test'}})
        # cc.get_accounts('123')
        # cc.get_accounts(params={'skip': 0, 'take': 20})
        uid = args[0] if args else None
        simulate = kwargs.pop('simulate', False)

        if uid:
            endpoint = f'{self.version_url}/{model}/{uid}.json'
        else:
            endpoint = f'{self.version_url}/{model}.json'

        verb_dict = {
            'get': self.get,
            'post': self.post,
            'put': self.put,
            'delete': self.delete,
        }
        if simulate:
            return self.simulate(endpoint, verb, **kwargs)
        else:
            return verb_dict[verb](endpoint, **kwargs)

    def _auth(self, params=None):
        '''add access token to params variable'''
        if params:
            params['accessToken'] = self.access_token
        else: 
            params = {'accessToken': self.access_token}
        return params
    
    def _make_request(self, method, endpoint, **kwargs):
        # prep vars
        params = kwargs.get('params', None)
        try:
            del kwargs['params']
        except KeyError:
            pass
        params=self._auth(params)
        param_string = Php.http_build_query(params)
        url = f'{self.base_url}{endpoint}?{param_string}'
        # prep request
        req = Request(
            method,
            url,
            # params=self._auth(params),
            **kwargs)
        prepped = req.prepare()
        
        try:
            response = self.session.send(prepped, timeout=self.timeout)
            # response.raise_for_status()  # Raise an exception for HTTP errors
            return response
        except RequestException as error:
            print(f"Error fetching data from the API: {error}")
            return None

    def get(self, endpoint, **kwargs):
        return self._make_request('GET', endpoint, **kwargs)

    def post(self, endpoint, **kwargs):
        return self._make_request('POST', endpoint, **kwargs)

    def put(self, endpoint, **kwargs):
        return self._make_request('PUT', endpoint, **kwargs)

    def delete(self, endpoint, **kwargs):
        return self._make_request('DELETE', endpoint, **kwargs)
    
    def simulate(self, endpoint, method, params=None, **kwargs):
        if params:
            params['_method'] = method.upper()
        else: 
            params = {'_method': method.upper()}
        return self._make_request('GET', endpoint, params=params, **kwargs)
    
    def get_all(self, model, **kwargs):
        """
        Retrieve data from an API with paging support.

        Parameters:
        - params (dict): Optional parameters to include in the API request.

        Returns:
        - list: A list of all items retrieved from the API.
        """
        all_data = {
            'result': {
                'data': [],
                'total': 0,
                },
            'error': [],
            'status_code': [],
        }
        position = 0

        # find the method to use
        do = f'get_{model}'
        if hasattr(self, do) and callable(func := getattr(self, do)):
            method = func
        else:
            raise Exception(f'no method for {do}')

        # Loop until all pages have been retrieved
        while True:
            # Set the page parameter in the request if provided
            try:
                params = kwargs['params']
            except KeyError:
                params = {}
            params['skip'] = position
            params['take'] = 100

            # Make the API request
            response = method(params=params)

            # Check for errors
            if response.status_code != 200:
                print(f"Error: Unable to retrieve data. Status code: {response.status_code}")
                break

            # Add the retrieved items to the result list
            all_data['status_code'].append(response.status_code)
            res = response.json()
            all_data['error'].append(res['error'])
            all_data['result']['data'].extend(res['result']['data'])
            # get total from first page
            if position == 0:
                all_data['result']['total'] = res['result']['total']

            # Check if there are more pages
            total = res['result']['total']
            pagesize = params['take']
            if total > position:
                position += pagesize
            else:
                break

        return all_data

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

    ccapi = CchubApiBaseClient(base_url, access_token, version)
