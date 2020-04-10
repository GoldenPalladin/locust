from locust import between, seq_task, TaskSequence, Locust

from framework.generator.asserter import LocustAsserter
from framework.generator.expected import ExpectedResponse, rextract_data
from framework.api.TPData.api import TPDataAPIClient
from framework.generator.helpers import make_file_with_size
from config.test_config_reader import env_config, test_profile, datapool

TREATMENT_ID = None


class TPDataAPILocust(Locust):
    """
    Here ve define Locust client for TPData
    """
    def __init__(self):
        super().__init__()
        self.client = TPDataAPIClient(config=env_config,
                                      creds=env_config.auto_system)


class CheckTreatmentVariants(TaskSequence):
    """
    Task sequence to form Create treatment variants transaction
    Autosystem creates treatment variants
    """
    min_wait = 0
    max_wait = 0

    def __init__(self, *args, **kwargs):
        super(CheckTreatmentVariants, self).__init__(*args, **kwargs)
        self.treatment_id = None
        self.def_exp = ExpectedResponse()

    @seq_task(1)
    def get_autosystem_home(self):
        self.client.change_client(creds=env_config.auto_system)
        exp = ExpectedResponse(text='AutoSystemHome')
        with LocustAsserter(expected=exp, name='Get autosystem home') as transaction:
            transaction.response = self.client.get_home()

    @seq_task(2)
    def get_treatment(self):
        patient = datapool['patient']
        payload = {"clin_id": patient['CLIN_ID'],
                   "pid": patient['PID'],
                   "so": patient['SO'],
                   "voi": patient['VOI'],
                   "vpi": 1,
                   "treat_save_id": "058d053e-9a74-42bf-831d-785bd42467b5",
                   "max_plan_number": test_profile['profile']['PLANNUMBER_COUNT']}

        with LocustAsserter(expected=self.def_exp,
                            name='Create Treatment',
                            interrupt_flow=True) as transaction:
            transaction.response = self.client.treatment.create(**payload)

        self.treatment_id = rextract_data(resp=transaction.response,
                                          json_item='properties.id')
        exp = ExpectedResponse(text='Treatment')
        with LocustAsserter(expected=exp,
                            name='Get created treatment') as transaction:
            transaction.response = self.client.treatment.get(self.treatment_id)

    @seq_task(3)
    def create_new_treatment_variant(self):
        adf = make_file_with_size('adf.adf', datapool['adf_filesize'])
        wcc = make_file_with_size('wcc.wcc', datapool['wcc_filesize'])
        treatment_variant_file = make_file_with_size('treatment-data.xml', datapool['treatment_data_filesize'])
        for i in range(int(test_profile['profile']['PLANNUMBER_COUNT'])):
            tvd = {'planNumber': i, 'tags': {'collection': 'tags'}}
            with LocustAsserter(expected=self.def_exp,
                                name='Create treatment variant') as transaction:
                transaction.response = self.client\
                    .treatment_variant\
                    .create(treatment_id=self.treatment_id,
                            treatment_variant_data=tvd,
                            adf=adf,
                            wcc=wcc)

            exp = ExpectedResponse(text='TreatmentVariant')
            with LocustAsserter(expected=exp,
                                name='Get treatment variant') as transaction:
                transaction.response = self.client\
                    .treatment_variant\
                    .get(treatment_id=self.treatment_id,
                         plan_number=i)

            with LocustAsserter(expected=self.def_exp,
                                name='Create checkout') as transaction:
                transaction.response = self.client\
                    .treatment_variant_checkout\
                    .create_update(treatment_id=self.treatment_id,
                                   plan_number=i,
                                   uploaded_file=treatment_variant_file)

    @seq_task(4)
    def get_doctor_home(self):
        self.client.change_client(creds=env_config.us_doctor)
        exp = ExpectedResponse(text='DoctorHome')
        with LocustAsserter(expected=exp, name='Get doctor home') as transaction:
            transaction.response = self.client.get_home()

"""
    @seq_task(5)
    def post_new_revision(self):
        #  loop = ${REVISIONS_COUNT}
        #  authorization = Bearer ${ACCESS_TOKEN_DOCTOR
        #  url = f'{base}/tpdata/v1/treatments/${mtpId}/variants/${planNumber}/revisions'
        #  FileWriter f = new FileWriter("/Users/stolstikov/Desktop/loadtest/revision-${__threadNum}.csv",true);
        #  String s = "{\"name\": \"performance case\"}";
        #  response.code = 201
        #  revision_id = re.search(r'Location.*revisions/(.+)', response.header,
        #  default = NOT EXTRACTED, group_number = 1)
        pass
"""


class TPDataAPIUser(TPDataAPILocust):
    """
    Here we define user with tasks to execute
    """
    task_set = CheckTreatmentVariants
    wait_time = between(0.1, 0.2)

