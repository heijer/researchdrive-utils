import logging
import requests
import json
import pandas


class ResearchDrive:
    """
    A wrapper for interacting with the SURF Research Drive API.

    This class provides methods to among others list project folders
    and create new project folders.

    Attributes:
        url (str): The base URL of the Research Drive API. https://<institute>.data.surfsara.nl/dashboard/api/
        headers (dict): Headers for API requests, including the authorization token.
        dry_run (bool): If True, POST methods will return payload in logging instead of making API calls.
    """
    url = None
    headers = {}
    dry_run = False

    def __init__(self, url=None, token=None):
        """
        initialise ResearchDrive class
        :param url: API url https://<environment_domain>/dashboard/api/
        :param token: API access token
        """
        self.url = url
        self.headers = {'Authorization': 'Bearer {}'.format(token),
                        'Accept-Language': 'en',
                        'Content-Type': 'application/json',
                        'accept': 'application/json'}

    def get(self, request='me', params=None):
        """
        get call to Research Drive API
        :param request: request string (excluding https://<environment_domain>/dashboard/api/)
        :param params: dictionary with params to parse
        :return: json object (if http status code == 200, None otherwise)
        """
        if params is None:
            params = {}
        url = self.url + request

        try:
            r = requests.get(url,
                             headers=self.headers,
                             params=params,
                             )
        except:
            logging.error('GET request to {} does not give valid response'.format(url))
            return None

        if r.status_code == 200:
            json_text = r.text
            data = json.loads(json_text)
            return data
        else:
            logging.error('GET request to {} gives status code {}\n{}'.format(url, r.status_code, r.text))
            return None

    def get_many(self, request='account', per_page=50, params=None):
        """
        series of get calls to Research Drive API
        :param request: request string (excluding https://<environment_domain>/dashboard/api/)
        :param per_page: number of records per page
        :param params: dictionary with params to parse
        :return: json object (if http status code == 200, None otherwise)
        """
        if params is None:
            params = {}
        params['per_page'] = per_page
        data = []
        current_page = 0
        last_page = 1

        while last_page > current_page:
            params['page'] = current_page + 1
            # get next page
            data.append(self.get(request=request, params=params))
            # read meta information
            current_page = data[-1]['meta']['current_page']
            last_page = data[-1]['meta']['last_page']

        return data

    def post(self, request='', payload=None):
        """
        post call to Research Drive API
        :param request: request string (excluding https://<environment_domain>/dashboard/api/)
        :param payload: payload dictionary
        :return: json object (if http status code == 200, None otherwise)
        """
        if payload is None:
            payload = {}
        url = self.url + request

        if self.dry_run:
            logging.info('Dry run, returning payload of POST request')
            return payload

        try:
            r = requests.post(url,
                             headers=self.headers,
                             data=json.dumps(payload),
                             )
        except:
            logging.error('POST request to {} does not give valid response'.format(url))
            return None

        if r.status_code == 200:
            json_text = r.text
            data = json.loads(json_text)
            return data
        else:
            logging.error('POST request to {} gives status code {}\n{}'.format(url, r.status_code, r.text))
            return None

    def create_folder(self, name, description='', owner=None, contract=None, quotum=10):
        """
        create Research Drive project folder
        :param name: name of project folder
        :param description: description of project folder (optional)
        :param owner: owner of project folder; will default to "me" being the user owning the API access token
        :param contract:
        :param quotum: storage quotum in GB (integer)
        :return:
        """
        if owner is None:
            me_df = self.get_me()
            owner_username = me_df.username.values[0]
        else:
            accounts_df = self.get_accounts()
            if type(owner) == type({}):
                idx = (accounts_df[list(owner)] == pandas.Series(owner)).all(axis=1)
            else:
                idx = accounts_df.username == owner

            if accounts_df.loc[idx].shape[0] == 1:
                owner_username = accounts_df.loc[idx].username.values[0]
            else:
                logging.error('{} usernames found matching "{}"'.format(accounts_df.loc[idx].shape[0], owner))
                return {}

        contracts = self.get_contracts()
        if contract is None:
            if contracts.shape[0] == 1:
                contract_id = contracts.id.values[0]
                logging.debug('No contract specified, default to the only available contract: {}'.format(contract_id))
            else:
                option_str = '; '.join(['{} ({})'.format(id, contract_id) for id,contract_id in contracts[['id', 'contract_id']].values.tolist()])
                logging.error('No contract specified, {} options available. Choose from: {}'.format(contracts.shape[0],
                                                                                                    option_str))
                return {}
        else:
            if type(contract) == type({}):
                idx = (contracts[list(contract)] == pandas.Series(contract)).all(axis=1)
            elif type(contract) == type(10):
                idx = contracts.id == contract
            elif type(contract) == type(''):
                idx = contracts.contract_id == contract
            else:
                logging.error('contract of type "{}" not recognized'.format(type(contract)))
                return {}

            if contracts.loc[idx].shape[0] == 1:
                contract_id = contracts.loc[idx].id.values[0]
            else:
                logging.error('{} contracts found that match "{}"'.format(contracts.loc[idx].shape[0], contract))
                return {}

        projectfolders_df = self.get_projectfolders()
        if name in projectfolders_df.name.values:
            logging.error('Project folder with name "{}" already exists'.format(name))
            return {}

        payload = {
                "name": name,
                "account": {
                  "id": owner_username
                },
                "description": description.strip(),
                "contract": {
                  "id": int(contract_id)
                },
                "quotum": int(quotum)
              }

        data = self.post(request='functional-account', payload=payload)

        return data

    def get_contracts(self):
        """
        get available contracts
        :return: dataframe with contracts
        """
        contracts_df = pandas.json_normalize(self.get(request='contract')['data'])
        return contracts_df

    def get_accounts(self):
        """
        get available accounts
        :return: dataframe with accounts
        """
        accounts_df = pandas.concat([pandas.json_normalize(d['data']) for d in self.get_many(request='account')])
        return accounts_df

    def get_me(self):
        """
        get information about current user
        :return: dataframe with user information
        """
        me_df = pandas.json_normalize(self.get(request='me')['data'])
        return me_df

    def get_projectfolders(self):
        """
        get available project folders
        :return: dataframe with project folders
        """
        projectfolders_df = pandas.concat([pandas.json_normalize(d['data']) for d in self.get_many(request='functional-account')])
        return projectfolders_df