from framework.api.Base import BaseResource

BASE_PATH = 'protocols'


class Protocol(BaseResource):
    """
    https://alignapi.alta-sqa1.aligntech.com/protocol/v1/docs/api-blueprint.html#protocols-resource
    """
    name = 'protocol'

    def create(self, clin_id):
        payload = {
            "clinId": clin_id
        }
        return self.api.client.post(BASE_PATH, json=payload).response

    def get(self, protocol_id):
        request_path = f'{BASE_PATH}/{protocol_id}'
        return self.api.client.get(request_path).response


class Version(BaseResource):
    """
    https://alignapi.alta-sqa1.aligntech.com/protocol/v1/docs/api-blueprint.html#version-resource
    """
    name = 'protocol_version'

    def create(self, protocol_id, name, description, script):
        payload = {
            "name": name,
            "description": description,
            "script": script
        }
        request_path = f'{BASE_PATH}/{protocol_id}/versions'
        return self.api.client.post(request_path, json=payload).response

    def get(self, protocol_id, protocol_version):
        request_path = f'{BASE_PATH}/{protocol_id}/versions/{protocol_version}'
        return self.api.client.get(request_path).response

    def publish(self, protocol_id, version_id):
        request_path = f'{BASE_PATH}/{protocol_id}/versions/{version_id}?action=publish'
        return self.api.client.put(request_path).response

