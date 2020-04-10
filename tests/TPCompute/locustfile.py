import time

from locust import between, seq_task, TaskSequence, Locust

from framework.generator.asserter import LocustAsserter
from framework.generator.expected import ExpectedResponse, rextract_data
from framework.api.TPCompute.api import TPComputeAPIClient
from framework.api.ACS.api import ACSAPIClient
from framework.api.Protocol.api import ProtocolAPIClient
from framework.api.Webhooks.api import HooksClient
from config.test_config_reader import env_config, common_config, datapool
from generator.helpers import read_file_from_path

CALCULATION_ID = None
CALCULATION_SUCCESS_STATUS = 'COMPLETED'
CALCULATION_SUCCESS_WAIT_INTERVAL_SEC = 300
CALCULATION_SUCCESS_WAIT_TIMEOUT_MIN = 50


class TPComputeAPILocust(Locust):
    """
    Here we define Locust client for TPCompute
    """

    def __init__(self):
        super().__init__()
        self.client = TPComputeAPIClient(config=env_config,
                                         creds=env_config.auto_system)
        self.acs_client = ACSAPIClient(config=env_config,
                                       creds=env_config.cs_admin)
        self.protocol_client = ProtocolAPIClient(config=env_config,
                                                 creds=env_config.cs_admin)
        self.webhook_client = HooksClient(config=common_config)


class CheckSuggestiveCalculation(TaskSequence):
    """
    Task sequence to form Create suggestive flow calculation
    Autosystem creates treatment variants
    """
    min_wait = 0
    max_wait = 0

    def __init__(self, *args, **kwargs):
        super(CheckSuggestiveCalculation, self).__init__(*args, **kwargs)
        self.calculation_id = None
        self.calculation_status = None
        self.webhooks_box_url = None
        self.protocol_id = None
        self.protocol_version_id = None
        self.patient = datapool['patient']
        self.def_exp = ExpectedResponse()

    @seq_task(1)
    def get_acs_home(self):
        self.acs_client.change_client(creds=env_config.cs_admin)
        with LocustAsserter(expected=self.def_exp, name='Get acs admin home',
                            interrupt_flow=True) as transaction:
            transaction.response = self.client.get_home()

    @seq_task(2)
    def create_3d_cut_asset(self):
        payload = {
            "iid": self.patient['IID'],
            "category": "3d:cut",
            "accessPolicy": "invisalign-internal",
            "tags": f"[\"so={self.patient['SO']}\"]",
            "countryCode": self.patient['COUNTRY_CODE']
        }
        with LocustAsserter(expected=self.def_exp, name='Create 3d cut asset',
                            interrupt_flow=True) as transaction:
            transaction.response = self.client.asset.create(**payload)

        asset_id = rextract_data(resp=transaction.response,
                                 json_item='properties.id')
        rev_payload = {
            "tags": f"[\"so={self.patient['SO']}\"]"
        }
        with LocustAsserter(expected=self.def_exp,
                            name='Create 3d cut asset revision',
                            interrupt_flow=True) as transaction:
            transaction.response = self.acs_client.revision.create(asset_id, self.patient['IID'], rev_payload)

        revision_id = rextract_data(resp=transaction.response,
                                    json_item='properties.id')

        content_type = "application/octet-stream"
        cut_file = read_file_from_path('3d-cut-suggestive.adf', 'tests/tpcompute/suggestive_flow')
        with LocustAsserter(expected=self.def_exp,
                            name='Upload 3d cut asset revision content',
                            interrupt_flow=True) as transaction:
            transaction.response = self.acs_client.revision.upload_content(asset_id, revision_id, cut_file,
                                                                           content_type)

    @seq_task(3)
    def create_3d_cut_painted_asset(self):
        payload = {
            "iid": self.patient['IID'],
            "category": "3d:cut-painted",
            "accessPolicy": "invisalign-internal",
            "tags": f"[\"so={self.patient['SO']}\"]",
            "countryCode": self.patient['COUNTRY_CODE']
        }

        with LocustAsserter(expected=self.def_exp, name='Create 3d cut painted asset',
                            interrupt_flow=True) as transaction:
            transaction.response = self.client.asset.create(**payload)

        asset_id = rextract_data(resp=transaction.response,
                                 json_item='properties.id')
        rev_payload = {
            "tags": self.patient['TAGS'],
        }
        with LocustAsserter(expected=self.def_exp,
                            name='Create 3d cut painted asset revision',
                            interrupt_flow=True) as transaction:
            transaction.response = self.acs_client.revision.create(asset_id, rev_payload)

        revision_id = rextract_data(resp=transaction.response,
                                    json_item='properties.id')

        content_type = "application/octet-stream"
        cut_painted_file = read_file_from_path('3d-cut-painted-suggestive.adf', 'tests/tpcompute/suggestive_flow')
        with LocustAsserter(expected=self.def_exp,
                            name='Upload 3d cut painted asset revision content',
                            interrupt_flow=True) as transaction:
            transaction.response = self.acs_client.revision.upload_content(asset_id, revision_id, cut_painted_file,
                                                                           content_type)

    @seq_task(4)
    def create_xml_prescription_asset(self):
        payload = {
            "iid": self.patient['IID'],
            "category": "xml:prescription",
            "accessPolicy": "invisalign-internal",
            "tags": f"[\"so={self.patient['SO']}\"]",
            "countryCode": self.patient['COUNTRY_CODE']
        }
        with LocustAsserter(expected=self.def_exp, name='Create XML prescription asset',
                            interrupt_flow=True) as transaction:
            transaction.response = self.client.asset.create(**payload)

        asset_id = rextract_data(resp=transaction.response,
                                 json_item='properties.id')
        rev_payload = {
            "tags": self.patient['TAGS'],
        }
        with LocustAsserter(expected=self.def_exp,
                            name='Create XML prescription asset revision',
                            interrupt_flow=True) as transaction:
            transaction.response = self.acs_client.revision.create(asset_id, rev_payload)

        revision_id = rextract_data(resp=transaction.response,
                                    json_item='properties.id')

        content_type = "application/octet-stream"
        cut_painted_file = read_file_from_path('CD-suggestive.xml', 'tests/tpcompute/suggestive_flow')
        with LocustAsserter(expected=self.def_exp,
                            name='Upload XML prescription asset revision content',
                            interrupt_flow=True) as transaction:
            transaction.response = self.acs_client.revision.upload_content(asset_id, revision_id, cut_painted_file,
                                                                           content_type)

    @seq_task(5)
    def get_protocol_home(self):
        self.protocol_client.change_client(creds=env_config.cs_admin)
        with LocustAsserter(expected=self.def_exp, name='Get protocol api admin home',
                            interrupt_flow=True) as transaction:
            transaction.response = self.client.get_home()

    @seq_task(6)
    def create_protocol(self):
        payload = {
            "clinId": self.patient['CLIN_ID']
        }
        with LocustAsserter(expected=self.def_exp, name='Create protocol',
                            interrupt_flow=True) as transaction:
            transaction.response = self.client.protocol.create(**payload)
        self.protocol_id = rextract_data(resp=transaction.response,
                                         json_item='properties.id')

    @seq_task(7)
    def create_protocol_version(self):
        payload = {
            "name": "Dr. Galler standard protocol",
            "description": "New Dr. Galler's protocol",
            "script": "protocol DoctorProtocol {}"
        }
        with LocustAsserter(expected=self.def_exp, name='Create version',
                            interrupt_flow=True) as transaction:
            transaction.response = self.client.version.create(self.protocol_id, **payload)
        self.protocol_version_id = rextract_data(resp=transaction.response,
                                                 json_item='properties.id')

    @seq_task(8)
    def publish_protocol_version(self):
        with LocustAsserter(expected=self.def_exp, name='Publish version',
                            interrupt_flow=True) as transaction:
            transaction.response = self.client.version.publish(self.protocol_id, self.protocol_version_id)

    @seq_task(9)
    def get_tpcompute_home(self):
        self.client.change_client(creds=env_config.auto_system)
        with LocustAsserter(expected=self.def_exp, name='Get autosystem home',
                            interrupt_flow=True) as transaction:
            transaction.response = self.client.get_home()

    @seq_task(10)
    def create_new_suggestive_calculation(self):
        self.webhooks_box_url = f"{common_config.hook_servers.hooks_test_api.gateway}{self.webhook_client.get_box_url()}"
        payload = {"type": "INITIAL",
                   "flow": "SUGGESTIVE",
                   "webhooks": f'["{self.webhooks_box_url}"]',
                   "transactionId": '058d053e-9a74-42bf-831d-785bd42467b4',
                   "clinId": self.patient['CLIN_ID'],
                   "iid": self.patient['IID'],
                   "tags": self.patient['TAGS'],
                   "protocolId": self.protocol_id,
                   "protocolVersionId": self.protocol_version_id,
                   }
        with LocustAsserter(expected=self.def_exp,
                            name='Create Suggestive Calculation',
                            interrupt_flow=True) as transaction:
            transaction.response = self.client.calculation.create(**payload)

        self.calculation_id = rextract_data(resp=transaction.response,
                                            json_item='properties.id')
        exp = ExpectedResponse(text='Calculation')
        with LocustAsserter(expected=exp,
                            name='Get created calculation') as transaction:
            transaction.response = self.client.calculation.get(self.calculation_id)

    @seq_task(11)
    def wait_for_calculation_success_status(self):
        timeout = 60 * CALCULATION_SUCCESS_WAIT_TIMEOUT_MIN
        time_started = time.time()
        while time.time() < time_started + timeout:
            with LocustAsserter(expected=self.def_exp,
                                name='Get created calculation') as transaction:
                transaction.response = self.client.calculation.get(self.calculation_id)
            calculation_status = rextract_data(resp=transaction.response,
                                               json_item='properties.status')
            if calculation_status == CALCULATION_SUCCESS_STATUS:
                self.calculation_status = calculation_status
                return
            else:
                time.sleep(CALCULATION_SUCCESS_WAIT_INTERVAL_SEC)

    @seq_task(12)
    def check_calculation_status(self):
        with LocustAsserter(expected=self.def_exp,
                            name='Check calculation status',
                            interrupt_flow=True) as transaction:
            transaction.response = self.client.calculation.get(self.calculation_id)
            calculation_status = rextract_data(resp=transaction.response,
                                               json_item='properties.status')
            assert calculation_status == CALCULATION_SUCCESS_STATUS,\
                "Calculation success status check failed"

    @seq_task(12)
    def check_webhook_event(self):
        with LocustAsserter(expected=self.def_exp,
                            name='Check webhooks resource',
                            interrupt_flow=True) as transaction:
            transaction.response = self.webhooks_client.get_hooks(self.webhooks_box_url)

        events_total = rextract_data(resp=transaction.response,
                                     json_item='properties.total')
        assert events_total == 1, f"Webhook events count check failed"

    @seq_task(13)
    def check_3d_treatment_asset(self):
        payload = {
            "category": "3d:treatment",
            "tags": self.patient['TAGS']
        }
        with LocustAsserter(expected=self.def_exp, name='Find 3d treatment asset',
                            interrupt_flow=True) as transaction:
            transaction.response = self.client.asset.find(**payload)
        assets_total = rextract_data(resp=transaction.response,
                                     json_item='properties.total')
        assert assets_total == 1, f"ACS treatment asset check failed"


class TPComputeAPIUser(TPComputeAPILocust):
    """
    Here we define user with tasks to execute
    """
    task_set = CheckSuggestiveCalculation
    wait_time = between(0.1, 0.2)
