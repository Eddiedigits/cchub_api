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
    """
    A basic class to act as a client for the CCHUB API.

    This class is expected to be extended with business logic for middleware purposes.

    Scope:
    - Handles authentication, session, and retry functionality.
    - Provides basic methods for the API endpoints.

    Added dynamic methods:
    - self.get_{model}
        - self.get_accounts()  # get first page. Default pagesize is 100
        - self.get_accounts('name_4385245245')  # get single item
    - self.post_{model}(json={...})  # add single item
    - self.put_{model}(cchub_uid, json={...})  # update single item
    - self.get_all_{model}  # get all items

    JSON structure:
    {
        'title': 'string',
        'database': {
            'title': 'string'
        },
        'customFields': {
            'MyCustomField': 'string'
        },
    }

    Parameters:
    - json (dict): The JSON data to be sent in the request body.

    Params:
    {
        'skip': 0,  # offset
        'take': 20,  # pagesize
        'sort': [
            {"field": "firstname", "dir": "desc"},
            {"field": "lastname", "dir": "asc"}
        ],  # custom field example: "field": "customFields.telefon"
        "filter": {
            "field": "firstname",
            "operator": "eq",  # various operators available
            "value": "John"
        },  # filter can be a list of filter dicts
        "fields": [
            "firstname",
            "lastname",
            "account.title"
        ],  # limit the fields which are returned
    }

    Response structure:
    {
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
    """
    # There are dynamic methods for each model
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
        'users',
    ]

    def __init__(self, server_address, token, api_version='6'):
        """
        Initialize the CchubApiBaseClient.

        Parameters:
        - server_address (str): The address of the CCHUB server.
        - token (str): The access token for authentication.
        - api_version (str): The version of the API to use (default is '6').
        """
        self.base_url = f'{server_address}'
        self.access_token = token
        self.version_url = f'/api/v{api_version}'
        self.session = Session()
        adapter = HTTPAdapter(max_retries=3)
        self.session.mount(self.base_url, adapter)
        self.session.headers["Content-Type"] = "application/json"
        self.timeout = 10

    def model_func(self, model, verb, *args, **kwargs):
            """
            Perform a HTTP request for a model using the specified verb.

            This function is used by the decorator to dynamically create methods for HTTP verbs for each model.
            For example, `self.get_activities()` or `self.post_account(json)`.

            Parameters:
            - model (str): The name of the model.
            - verb (str): The HTTP verb to use for the request.
            - args: Positional arguments for the request.
            - kwargs: Keyword arguments for the request.

            Returns:
            - object: The response object.

            Raises:
            - KeyError: If the specified verb is not supported.

            """
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
        """
        Add the access token to the params variable.

        Parameters:
        - params (dict): The parameters to be sent in the request.

        Returns:
        - dict: The updated parameters with the access token.
        """
        if params:
            params['accessToken'] = self.access_token
        else:
            params = {'accessToken': self.access_token}
        return params

    def _make_request(self, method, endpoint, **kwargs):
        """
        Make a request to the API.

        Parameters:
        - method (str): The HTTP method to use for the request.
        - endpoint (str): The API endpoint to send the request to.
        - kwargs: Keyword arguments for the request.

        Returns:
        - object: The response object.
        """
        params = kwargs.get('params', None)
        try:
            del kwargs['params']
        except KeyError:
            pass
        params = self._auth(params)
        param_string = Php.http_build_query(params)
        url = f'{self.base_url}{endpoint}?{param_string}'
        req = Request(
            method,
            url,
            **kwargs)
        prepped = req.prepare()

        try:
            response = self.session.send(prepped, timeout=self.timeout)
            return response
        except RequestException as error:
            print(f"Error fetching data from the API: {error}")
            return None

    def get(self, endpoint, **kwargs):
        """
        Perform a GET request.

        Parameters:
        - endpoint (str): The API endpoint to send the request to.
        - kwargs: Keyword arguments for the request.

        Returns:
        - object: The response object.
        """
        return self._make_request('GET', endpoint, **kwargs)

    def post(self, endpoint, **kwargs):
        """
        Perform a POST request.

        Parameters:
        - endpoint (str): The API endpoint to send the request to.
        - kwargs: Keyword arguments for the request.

        Returns:
        - object: The response object.
        """
        return self._make_request('POST', endpoint, **kwargs)

    def put(self, endpoint, **kwargs):
        """
        Perform a PUT request.

        Parameters:
        - endpoint (str): The API endpoint to send the request to.
        - kwargs: Keyword arguments for the request.

        Returns:
        - object: The response object.
        """
        return self._make_request('PUT', endpoint, **kwargs)

    def delete(self, endpoint, **kwargs):
        """
        Perform a DELETE request.

        Parameters:
        - endpoint (str): The API endpoint to send the request to.
        - kwargs: Keyword arguments for the request.

        Returns:
        - object: The response object.
        """
        return self._make_request('DELETE', endpoint, **kwargs)

    def simulate(self, endpoint, method, params=None, **kwargs):
        """
        Simulate a request.

        Parameters:
        - endpoint (str): The API endpoint to send the request to.
        - method (str): The HTTP method to use for the request.
        - params (dict): The parameters to be sent in the request.
        - kwargs: Keyword arguments for the request.

        Returns:
        - object: The response object.
        """
        if params:
            params['_method'] = method.upper()
        else:
            params = {'_method': method.upper()}
        return self._make_request('GET', endpoint, params=params, **kwargs)

    def get_all(self, model, **kwargs):
        """
        Retrieve data from the API with paging support.

        Parameters:
        - model (str): The name of the model.
        - kwargs: Keyword arguments for the request.

        Returns:
        - dict: A dictionary containing the retrieved data.
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

        # Find the method to use
        do = f'get_{model}'
        if hasattr(self, do) and callable(func := getattr(self, do)):
            method = func
        else:
            raise Exception(f'No method for {do}')

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
            # Get total from the first page
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