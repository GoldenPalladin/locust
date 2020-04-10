import logging
from locust.main import load_locustfile
from locust.util.timespan import parse_timespan
from framework.generator.sfx import SfxListener
from framework.generator.splunk import SplunkErrorListener
from framework.generator.debug import DebugListener
from config.test_config_reader import test_profile

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def update_dict_with(base: dict, new: dict) -> dict:
    """
    function for recursive update base dict (of dicts) with values from new dict
    :param base: dict to be updated
    :param new: dict with new values
    :return: updated base dict
    """
    if new and isinstance(new, dict):
        for k, v in new.items():
            if isinstance(base.get(k), dict) and isinstance(v, dict):
                update_dict_with(base.get(k), v)
            elif isinstance(base.get(k), dict) != isinstance(v, dict):
                continue
            else:
                base.update({k: v})
    return base


class Settings(object):
    """
    Class to manage extendable settings
    """
    def __init__(self, config=None):
        # DistributedLocustRunner options not included
        config = update_dict_with(test_profile['profile'], config)
        logger.info(f'Creating settings from config: {config}')
        self.runner = RunnerConfig(config['runner'])
        self.test = TestConfig(config['test'])
        self.logging = LoggingConfig(config['logging'])

    def __repr__(self):
        return f'Runner: {self.runner}\nTestConfig: {self.test}\nLogging: {self.logging}'


class RunnerConfig(object):
    def __init__(self, runner_config):
        self.num_clients = runner_config['clients']
        self.hatch_rate = runner_config['hatch_rate']
        self.stop_timeout = parse_timespan(runner_config['duration'])
        self.step_load = runner_config['step_load']
        self.step_duration = parse_timespan(runner_config['step_duration'])
        self.step_clients = runner_config['step_clients']
        self.reset_stats = False
        self.host = None

    def __repr__(self):
        return str(self.__dict__)


class TestConfig(object):
    def __init__(self, test_config):
        docstring, classes = load_locustfile(test_config['locustfile'])
        self.classes = [classes[n] for n in classes]
        self.debug = test_config['debug']

    def __repr__(self):
        return str(self.__dict__)


class LoggingConfig(object):
    def __init__(self, logging_config):
        def get_listener(name):
            listeners = dict({
                'Sfx': SfxListener,
                'Splunk': SplunkErrorListener,
                'Debug': DebugListener
            })
            listener = listeners.get(name)
            return listener() if listener else None
        self.loglevel = logging_config['loglevel']
        self.final_stats = logging_config['final_stats']
        self.listeners = [get_listener(name) for name in logging_config['listeners']]
        self.hyper_log_level = logging_config['hyperclient_console_log_level']

    def __repr__(self):
        return str(self.__dict__)


