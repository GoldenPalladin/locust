import re
import json
from requests import Response
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

"""
Class to handle Expected response parameter and compare with actual
"""


class ExpectedResponse(object):
    def __init__(self, code=200, text=None, headers=None, json: dict = None):
        self._code = code
        self._text = text
        self._headers = headers
        self._json = json
        if headers and not (isinstance(headers, str) or isinstance(headers, dict)):
            raise TypeError('Headers are expected to be string (keys lookup) or dictionary (key=value lookup)')

    @property
    def code(self):
        return self._code

    @property
    def text(self):
        return self._text

    @property
    def headers(self):
        return self._headers

    @property
    def json(self):
        return self._json

    def __eq__(self, other):
        if issubclass(type(other), Response):
            if self.code:
                code = getattr(other, 'status_code', None)
                if self.code != code:
                    logger.info(f'Expected response code {self.code}, but got {code}')
                    return False
            if self.text:
                text = getattr(other, 'text', None)
                if self.text not in text:
                    logger.info(f'Expected response text to contain {self.text}, but got {text}')
                    return False
            if self.headers:
                headers = getattr(other, 'headers', None)
                contains_headers = (isinstance(self.headers, str) and self.headers in headers.keys()) \
                    or (isinstance(self.headers, dict) and contains(headers, self.headers))
                if not contains_headers:
                    logger.info(f'Expected response headers to contain {self.headers}, but got {headers}')
                    return False
            if self.json:
                json = other.json()
                if not contains(json, self.json):
                    logger.info(f'Expected response json to contain {self.json}, but got {json}')
                    return False
        else:
            logger.error(f'{other} is not a Response subclass.')
            return False
        return True

    def __repr__(self):
        return str(self.__dict__)


def rextract_data(resp: Response, reg_exp: str = None, json_item: str = None, headers_key: str = None) -> str:
    """
    function to extract data by regexp
    :param resp: response object
    :param reg_exp: regexp pattern to search
    :param json_item: dot-separated string to drill into json dict, like 'properties.id'
    :param headers_key: header key to look in
    :return:
    """
    if resp:
        text = resp.headers.get(headers_key, None) if headers_key else resp.text
        if json_item and not headers_key:
            text = json.loads(text)
            for k in json_item.split('.'):
                text = text[k]
        if text and reg_exp:
            pattern = re.compile(reg_exp)
            return pattern.search(text).group(0)
        elif text:
            return text
    return ''


def contains(super_dict: dict, sub_dict:dict) -> bool:
    """
    function checks if sub_dict is contained in super_dict.
    Used for json 'contains' checks
    Snake_case from sub_dict is transmitted to camelCase (of json) from super_dict
    :param super_dict:
    :param sub_dict:
    :return:
    """
    def snake_to_camel(name: str) -> str:
        words = name.split('_')
        if len(words) == 1:
            return name
        first_word = words.pop(0)
        words = [word.capitalize() for word in words]
        words.insert(0, first_word)
        return "".join(words)

    for k, v in sub_dict.items():
        super_node = super_dict.get(snake_to_camel(k))
        if not super_node \
                or type(super_node) != type(v) \
                or isinstance(super_node, dict) and not contains(super_node, v) \
                or isinstance(super_node, list) and sorted(super_node) != sorted(v) \
                or not isinstance(super_node, (list, dict)) and super_node != v:
            return False
    return True