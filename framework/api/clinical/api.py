""" Clinical API wrapper """
import requests

from framework.api.Base import BaseAPI
from framework.api.clinical.resources import (DoctorResource,
                                              HomeResource,
                                              PatientResource,
                                              TreatmentPlanResource)


class ClinicalAPI(BaseAPI):
    config_section = 'clinical_api'
    resources = (DoctorResource, HomeResource, PatientResource, TreatmentPlanResource)

    def get_userinfo(self) -> requests.Response:
        return self.client.get('userinfo').response

    def get_home(self) -> requests.Response:
        return self.client.get('').response
