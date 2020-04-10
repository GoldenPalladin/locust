import random

from locust import between, task, Locust, TaskSet

from framework.generator.asserter import LocustAsserter
from framework.generator.rps import TaskSetRPS
from framework.generator.expected import ExpectedResponse
from framework.api.ACS.api import ACSAPIClient
from config.test_config_reader import env_config, datapool
from framework.generator.helpers import CsvData


class ACSAPILocust(Locust):
    """
    Here we define Locust client for ACS
    """

    def __init__(self):
        super().__init__()
        self.client = ACSAPIClient(config=env_config,
                                   jwt_auth=True,
                                   jwt_token=datapool['AUTH_HEADER_VALUE'])


class GetAssetThreadGroup(TaskSetRPS):
    """
    Task set to create and get assets
    """
    min_wait = 0
    max_wait = 0

    def __init__(self, *args, **kwargs):
        super(GetAssetThreadGroup, self).__init__(*args, **kwargs)
        self.def_exp = ExpectedResponse()
        self.generated_assets = CsvData(file_path='tests/ACS/users-assets-revs.csv',
                                        fieldnames=['iid', 'asset_id', '3', '4', '5'])

    @task
    def get_asset(self):
        self.keep_rps_at(50)
        asset_json_response = ExpectedResponse(json={'class': ['Asset']})
        asset_data = self.generated_assets.get_rand_item()
        with LocustAsserter(expected=asset_json_response, name='Get asset',
                            interrupt_flow=True) as transaction:
            transaction.response = self.client.asset.get_asset(iid=asset_data['iid'],
                                                               asset_id=asset_data['asset_id'])


class CreateAssetThreadGroup(TaskSetRPS):
    """
    Task set to create and get assets
    """
    min_wait = 0
    max_wait = 0

    def __init__(self, *args, **kwargs):
        super(CreateAssetThreadGroup, self).__init__(*args, **kwargs)
        self.def_exp = ExpectedResponse()

    @task
    def create_asset(self):
        self.keep_rps_at(10)
        payload = {
            "iid": f'ids:{random.randint(0, 999999999):09}',
            "category": "xray:full-mouth",
            "access_policy": "allowAll",
            "tags": ['locust_test_tags'],
            "country_code": "US"
        }
        asset_properties = payload.copy()
        asset_properties.pop('iid')
        individual_assets = {'class': ['Asset'], 'properties': asset_properties}
        create_assets_response = ExpectedResponse(json=individual_assets)
        with LocustAsserter(expected=create_assets_response, name='Create asset') as transaction:
            transaction.response = self.client.asset.create(**payload)


class Test(TaskSet):

    tasks = {CreateAssetThreadGroup: 1, GetAssetThreadGroup: 1}


class TPComputeAPIUser(ACSAPILocust):
    """
    Here we define user with tasks to execute
    """
    task_set = Test
    wait_time = between(0.1, 0.2)
