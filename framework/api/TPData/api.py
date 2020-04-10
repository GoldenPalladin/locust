""" TPData API wrapper """

from framework.api.Base import BaseAPI
from framework.api.TPData.resources import Treatment, TreatmentVariant, TreatmentVariantCheckout


class TPDataAPIClient(BaseAPI):
    config_section = 'tpdata_api'
    resources = (Treatment, TreatmentVariant, TreatmentVariantCheckout)

    def get_userinfo(self):
        return self.client.get('userinfo').response

    def get_home(self):
        return self.client.get('').response

    def healthcheck(self):
        return self.client.get('admin/healthcheck').response