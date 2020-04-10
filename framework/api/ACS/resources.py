import urllib

from framework.api.Base import BaseResource

BASE_URL = 'assets'


class Asset(BaseResource):
    """
    https://alignapi.cs1.aligntech.com/acs/v1/docs/api-blueprint.html#asset-resources-asset
    """
    name = 'asset'

    def create(self, iid, category, access_policy, tags, country_code):
        payload = {
            "iid": iid,
            "category": category,
            "accessPolicy": access_policy,
            "tags": tags,
            "countryCode": country_code
        }
        request_path = f'{BASE_URL}/{iid}'
        return self.api.client.post(request_path, json=payload).response

    def get_asset(self, iid, asset_id):
        request_path = f'{BASE_URL}/{iid}/{asset_id}'
        return self.api.client.get(request_path).response

    def find(self, iid, category, tags):
        qs = {}
        if category:
            qs['category'] = category
        if tags:
            qs['tags'] = tags
        query_string = urllib.urlencode(qs)
        request_path = f'{BASE_URL}/{iid}?{query_string}'
        return self.api.client.get(request_path, content_type='application/x-www-form-urlencoded').response


class Revision(BaseResource):
    """
    asset revision
    https://alignapi.cs1.aligntech.com/acs/v1/docs/api-blueprint.html#revision-resources
    """
    name = 'revision'

    def create(self, asset_id, iid, tags):
        payload = {
            "tags": tags
        }
        request_path = f'{BASE_URL}/{iid}/{asset_id}/r'
        return self.api.client.post(request_path, json=payload).response

    def upload_content(self, iid, asset_id, revision_id, file, content_type):
        request_path = f'{BASE_URL}/{iid}/{asset_id}/r/{revision_id}/content'
        return self.api.client.put(request_path, data=file, content_type=content_type).response


class Patient(BaseResource):
    """
    acs patient
    """
    name = 'patient'

    def create(self):
        return
