# CCHUB Api
Basic api client for the Daktela/CCHUB api v6

Handles auth, session, retry. Import and extend for custom middleware development.

Api Docs
https://customer.daktela.com/apihelp/v6/global/general-information

    basic class to act as a client for the CCHUB Api
    it is expected that this Class will be extended with business logic
    for middleware purposes

    scope:
    handle auth, session and retry functionality
    provide basic methods for the api endpoints

    # with dynamic methods:
    self.get_{model} 
        self.get_accounts() # get first page. default pagesize is 100
        self.get_accounts('name_4385245245') # get single item
    self.post_{model}(json={...}) # add single item
    self.put_{model}(cchub_uid, json={...}) # update single item
    self.get_all_{model} # get all items

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
        'campaignsRecords',
        'campaignsTypes',
        'groups',
        'pauses',
        'queues',
        'statuses',
        'templates',
        'tickets',
        'users',]

    # sending data to the server. This does not need to be converted to json
    # just send the object. self.post_account(json=dict(...))
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
