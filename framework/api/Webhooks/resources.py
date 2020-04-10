from framework.api.Base import BaseResource

EXPIRATION_TIME = 3600

class Box(BaseResource):
    """
        Webhooks box
    """
    name: 'box'
    box_url = None

    def create(self, expiration_time=EXPIRATION_TIME):
        """

        :type expiration_time: box expiration time in seconds
        """
        payload: {
            "name": "expiration-time",
            "value": expiration_time
        }
        request_path = 'boxes'
        box = self.api.client.post(request_path, json=payload)
        self.box_url = f"{box.response.links.self}"
        return box.response

    def get_url(self, ):
        return self.box_url


class Hooks(BaseResource):
    """
        Webhooks collection
    """
    name = 'hooks'

    def get_hooks(self, box_url):
        request_path = f'/{box_url}/hooks'
        return self.api.client.get(request_path).response
