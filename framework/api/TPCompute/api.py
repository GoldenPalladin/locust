""" TPCompute API wrapper """

from framework.api.Base import BaseAPI
from framework.api.TPCompute.resources import Calculation


class TPComputeAPIClient(BaseAPI):
    config_section = 'tpcompute_api'
    resources = (Calculation,)

    def get_userinfo(self):
        return self.client.get('userinfo').response

    def get_home(self):
        return self.client.get('').response