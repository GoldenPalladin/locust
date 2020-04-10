import time
import sys
from locust import events
from framework.generator.exceptions import FlowException
from framework.generator.expected import ExpectedResponse
from requests import Response
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def current_millis():
    return int(round(time.time() * 1000))


class LocustAsserter(object):
    """
    Class to implement context locust response time measuring,
    response assertion and events logging
    Note 'name' parameter -- by default it uses name of the task function
    IMPORTANT: to make it work you should return response to LocustAsserter.response property
    """
    def __init__(self,
                 name: str = sys._getframe(1).f_code.co_name,
                 expected: ExpectedResponse = None,
                 interrupt_flow: bool = False,
                 skip_transaction: bool = False):
        self.__name = name
        self.__transaction = {'request_type': 'https',
                              'name': name,
                              'response_length': 0}
        self.__expected = expected
        self.__interrupt_flow = interrupt_flow
        self.__skip_transaction = skip_transaction

    def __enter__(self):
        self.__start = current_millis()
        self.response: Response = None
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = int(current_millis() - self.__start)
        self.__transaction.update({'response_time': duration})
        exception = None
        # estimating response
        if self.response:
            success, msg = self.is_response_succeeded()
        else:
            success, msg = False, 'Got no response'
        logger.debug(f'Result: {success}, {msg}')

        # defining exception reason
        if not success:
            exception = exc_val if exc_val else FlowException(msg)
            self.__transaction.update({'exception': exception})
            logger.error(f'{self.__name} Asserter: Got exception {exception}')

        # posting __transaction results
        if not self.__skip_transaction:
            if success:
                self.__transaction['response_length'] = len(self.response.content)
                events.request_success.fire(**self.__transaction)
            else:
                events.request_failure.fire(**self.__transaction)

        # interrupting flow if required
        if self.__interrupt_flow and exception:
            if exc_val:
                return True
            else:
                raise exception
        else:
            return True

    def is_response_succeeded(self) -> tuple:
        if self.__expected:
            if self.__expected == self.response:
                return True, 'Response match to expected'
            else:
                return False, f'{self.__name}'
        else:
            return True, 'Nothing was expected'

