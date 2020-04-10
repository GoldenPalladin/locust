from framework.api.Base import BaseResource

CALCULATIONS_PATH = 'calculations'


class Calculation(BaseResource):
    """
    https://alignapi.cs1.aligntech.com/tpcompute/v1/docs/api-blueprint.html#calculation-resource
    """
    name = 'calculation'

    def create(self, calculation_type, flow, clin_id, pid, so, voi, vpi, transaction_id, webhooks_box_url, eligible_products,
               calculation_request_id, prev_so, iid, tags, country_code, protocol_id, protocol_version_id):
        payload = {"type": calculation_type,
                   "flow": flow,
                   "webhooks": f'["{webhooks_box_url}"]',
                   "transactionId": transaction_id,
                   "clinId": clin_id,
                   "pid": pid,
                   "so": so,
                   "iid": iid,
                   "tags": tags,
                   "voi": voi,
                   "countryCode": country_code,
                   "eligibleProducts": eligible_products,
                   "calculationRequestId": calculation_request_id,
                   "prevSo": prev_so,
                   "vpi": vpi,
                   "protocolId": protocol_id,
                   "protocolVersionId": protocol_version_id,
                   }
        return self.api.client.post(CALCULATIONS_PATH, json=payload).response

    def get(self, calculation_id):
        request_path = f'{CALCULATIONS_PATH}/{calculation_id}'
        return self.api.client.get(request_path).response
