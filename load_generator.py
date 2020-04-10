import logging
from framework.generator.launcher import LoadTestLauncher
from framework.settings import Settings
from framework.test.serialization import native_object_encoded

logging.basicConfig(level=logging.INFO)


def start(event=None, context=None):
    """
    Lambda load test entry point to start configured load test
    :param event: dict to override test settings from profile.yml
    :param context:
    :return:
    """
    stats = None  # Locust stats object
    try:
        test = LoadTestLauncher(settings=Settings(config=event))
        logging.info(f'Starting test with settings {event}')
        stats = test.start_test()
    except Exception as e:
        logging.exception(f'Test start exception {e}')
    return native_object_encoded(stats)


if __name__ == '__main__':
    start()

