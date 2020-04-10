""" Webhooks API wrapper """

from framework.api.Base import BaseAPI
from framework.api.Webhooks.resources import Box, Hooks


class HooksClient(BaseAPI):
    config_section = 'webhooks'
    resources = (Box, Hooks)

    def get_home(self):
        return self.client.get('').response

    def get_box_url(self):
        box = Box().create()
        return box.get_url()