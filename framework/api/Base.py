""" Base API wrapper """
from abc import ABC

from hyperclient.client import APIClient


class APIException(Exception):
    """ Base exception for all API errors """


class BaseAPI(ABC):
    """ Base class for API wrappers """
    config_section = None
    resources = None

    def __init__(self, config, creds=None, auth_client='default', jwt_token=None, jwt_auth=False):
        self._config = config
        self._creds = creds
        self._auth_client = auth_client
        self._client = None
        self.jwt_token = jwt_token
        self.jwt_auth = jwt_auth
        self.current_clinid = creds[0] if creds else None
        self._add_resources()

    @property
    def client(self):
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def _create_client(self):
        return APIClient(api_name=self.config_section,
                         verify_ssl=False,
                         user=self._creds,
                         config=self._config,
                         client=self._auth_client,
                         jwt_token=self.jwt_token,
                         jwt_auth=self.jwt_auth)

    def _add_resources(self):
        for resource in self.resources:
            setattr(self, resource.name, resource(self))

    def change_client(self, creds):
        self._creds = creds
        self._client = self._create_client()

    def __getattr__(self, name):
        raise APIException(f'Resource "{name}" is not defined')


class BaseResource:
    """ Base class for API resources """

    def __init__(self, api):
        self.api = api
