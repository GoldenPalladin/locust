from framework.api.Base import BaseResource
import json


class Treatment(BaseResource):
    """
    https://alignapi.cs1.aligntech.com/tpdata/v1/docs/api-blueprint.html#treatment-resource
    """
    name = 'treatment'

    def create(self, clin_id, pid, so, voi, treat_save_id, max_plan_number, vpi):
        payload = {"clinId": clin_id,
                   "pid": pid,
                   "so": so,
                   "vOI": voi,
                   "vPI": vpi,
                   "treatSaveId": treat_save_id,
                   "maxPlanNumber": max_plan_number}
        request_path = f'treatments'
        return self.api.client.post(request_path, json=payload).response

    def get(self, treatment_id):
        request_path = f'treatments/{treatment_id}'
        return self.api.client.get(request_path).response


class TreatmentVariant(BaseResource):
    name = 'treatment_variant'

    def create(self, treatment_id, treatment_variant_data, adf, wcc):
        """
        https://alignapi.cs1.aligntech.com/tpdata/v1/docs/api-blueprint.html#treatment-variant-resource-treatment-variant-put
        :param treatment_id:
        :param treatment_variant_data: json
        :param adf: file path
        :param wcc: file path
        :return:
        """
        request_path = f'treatments/{treatment_id}/variants'
        multiple_files = {
            'treatmentVariantData': (None, json.dumps(treatment_variant_data), 'application/json'),
            'adfFile': ('adf.adf', open(adf, 'rb'), 'application/octet-stream'),
            'wccFile': ('wcc.wcc', open(wcc, 'rb'), 'application/octet-stream')
        }
        return self.api.client.put(url=request_path,
                                   files=multiple_files).response

    def get(self, treatment_id, plan_number):
        request_path = f'treatments/{treatment_id}/variants/{plan_number}'
        return self.api.client.get(request_path).response


class TreatmentVariantCheckout(BaseResource):
    """
    https://alignapi.cs1.aligntech.com/tpdata/v1/docs/api-blueprint.html#treatment-variant-checkout-resource
    """
    name = 'treatment_variant_checkout'

    def create_update(self, treatment_id, plan_number, uploaded_file, checkout_data=None):
        """
        https://alignapi.cs1.aligntech.com/tpdata/v1/docs/api-blueprint.html#treatment-variant-checkout-resource-treatment-variant-checkout-put
        :param treatment_id:
        :param plan_number:
        :param checkout_data: json or NOne to create default
        :param uploaded_file: file path
        :return:
        """
        checkout_data = checkout_data if checkout_data else {
            "partNumber": 1,
            "treatmentType": "iGO20",
            "ipr": "DoNotPerformAnyIPR",
            "teethDeniedForAttachments": [1, 3, 5],
            "archesToTreat": "upper",
            "lowerStages": 1,
            "upperStages": 1
        }
        request_path = f'treatments/{treatment_id}/variants/{plan_number}/checkout'
        multiple_files = {
            'checkoutData': (None, json.dumps(checkout_data), 'application/json'),
            'uploadedFile': ('treatment-data.xml', open(uploaded_file, 'rb'), 'application/octet-stream')
        }
        return self.api.client.put(url=request_path,
                                   files=multiple_files).response


