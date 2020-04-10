""" Protocol API wrapper """

from framework.api.Base import BaseAPI
from framework.api.Protocol.resources import Protocol, Version


class ProtocolAPIClient(BaseAPI):
    config_section = 'protocol_api'
    resources = (Protocol, Version)

    def get_userinfo(self):
        return self.client.get('userinfo').response

    def get_home(self):
        return self.client.get('').response