""" ACS API wrapper """

from framework.api.Base import BaseAPI
from framework.api.ACS.resources import Asset


class MockHealthcheck(object):

    @property
    def ok(self):
        return True

    @staticmethod
    def json():
        return {'properties': {'systemName': 'acs-meta', 'buildInfo': {'appVersion': '1.25.0-ci.52'}}}


class ACSAPIClient(BaseAPI):
    config_section = 'acs_api'
    resources = (Asset,)

    def get_userinfo(self):
        return self.client.get('userinfo').response

    def get_home(self):
        return self.client.get('').response

    def healthcheck(self):
        return self.client.get('admin/healthcheck').response

