""" Clinical API resources"""

from typing import Optional

import requests

from framework.api.Base import BaseResource


class HomeResource(BaseResource):
    """ Home resource """
    name = 'home'

    def search_treatment_plans(self, clincheck_id: str) -> requests.Response:
        """
        Not in the blueprint at this moment.
        :param clincheck_id: ClinCheck ID also known as CCID.
        :return: Response object.
        """
        return self.api.client.get(f'treatment-plan-search?clincheckId={clincheck_id}').response


class DoctorResource(BaseResource):
    """ Doctor resource """
    name = 'doctor'

    def get_doctor_info(self, clinid: Optional[str] = None) -> requests.Response:
        """
        https://alignapi.cs1.aligntech.com/clinical-api/1.0/docs/api-blueprint.html#doctor-doctor-info-get
        :param clinid: Doctor's ID
        :return: Response object.
        """
        if not clinid:
            clinid = self.api.current_clinid

        return self.api.client.get(f'doctors/{clinid}').response

    def get_patients(self, clinid: Optional[str] = None) -> requests.Response:
        """
        https://alignapi.cs1.aligntech.com/clinical-api/1.0/docs/api-blueprint.html#doctor-doctor-patients
        :param clinid: Doctor's ID
        :return: Response object.
        """
        if not clinid:
            clinid = self.api.current_clinid

        return self.api.client.get(f'/doctors/{clinid}/patients').response

    def create_patient(self, given_name: str,
                       family_name: str,
                       birth_date: str,
                       gender: str,
                       zipcode: str,
                       clinid: Optional[str] = None) -> requests.Response:
        """
        https://alignapi.cs1.aligntech.com/clinical-api/1.0/docs/api-blueprint.html#doctor-doctor-patients-post
        :param given_name: Patient's name.
        :param family_name: Patient's surname
        :param birth_date:  Patient's birthdate in a format like '1990-01-01'
        :param gender:  Patient's gender, male or female
        :param zipcode: Patient's zipcode, 6 digits
        :param clinid: Doctor's ID
        :return: Response object.
        """
        if not clinid:
            clinid = self.api.current_clinid

        request_data = {"givenName": given_name,
                        "familyName": family_name,
                        "birthDate": birth_date,
                        "gender": gender,
                        "zipCode": zipcode}
        request_path = f'doctors/{clinid}/patients'

        return self.api.client.post(request_path, json=request_data).response


class TreatmentPlanResource(BaseResource):
    """ Treatment plan resource """
    name = 'treatment_plan'

    def get_treatment_plan(self, pid: str, treatment_plan_id: str) -> requests.Response:
        """
        https://alignapi.cs1.aligntech.com/clinical-api/1.0/docs/api-blueprint.html#treatment-plan-treatment-plan-get
        :param pid: Patient's ID
        :param treatment_plan_id: Treatment plan ID

        :return: Response object.
        """
        return self.api.client.get(
            f'patients/{pid}/treatment-plans/{treatment_plan_id}').response


class PatientResource(BaseResource):
    """ Patient resource """
    name = 'patient'

    def get_patient(self, pid: str) -> requests.Response:
        """
        https://alignapi.cs1.aligntech.com/clinical-api/1.0/docs/api-blueprint.html#patient-patient
        :param pid: Patient's ID
        :return: Response object.
        """
        return self.api.client.get(
            f'patients/{pid}').response
