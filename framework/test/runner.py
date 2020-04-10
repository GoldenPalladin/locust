import re
import logging
from datetime import timedelta
from dataclasses import dataclass, asdict
from framework.test.stepload import StepLoad


logging.basicConfig()
logger = logging.getLogger(__name__)


def parse_timespan(time_str):
    """
    Parse a string representing a time span and return the number of seconds.
    Valid formats are: 20, 20s, 3m, 2h, 1h20m, 3h30m10s, etc.
    """
    if not time_str:
        raise ValueError("Invalid time span format")

    if re.match(r'^\d+$', time_str):
        # if an int is specified we assume they want seconds
        return int(time_str)

    timespan_regex = re.compile(r'((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?')
    parts = timespan_regex.match(time_str)
    if not parts:
        raise ValueError("Invalid time span format. Valid formats: 20, 20s, 3m, 2h, 1h20m, 3h30m10s, etc.")
    parts = parts.groupdict()
    time_params = {name: int(value) for name, value in parts.items() if value}
    if not time_params:
        raise ValueError("Invalid time span format. Valid formats: 20, 20s, 3m, 2h, 1h20m, 3h30m10s, etc.")
    return int(timedelta(**time_params).total_seconds())


def encode_timespan(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f'{h}h{m}m{s}s'


@dataclass
class Runner:
    clients: int
    hatch_rate: int
    duration: int
    step_load: bool = False
    step_duration: int = 0
    step_clients: int = 0

    @classmethod
    def from_config(cls, config: dict):
        logger.debug(f'Make runner from: {config}')
        return Runner(clients=config.get('clients', 0),
                      duration=parse_timespan(config.get('duration', '0s')),
                      hatch_rate=config.get('hatch_rate', 0),
                      step_load=config.get('step_load', False),
                      step_duration=parse_timespan(config.get('step_duration', '0s')),
                      step_clients=config.get('step_clients', 0))

    @property
    def step(self):
        return StepLoad(enabled=self.step_load,
                        duration=self.step_duration,
                        clients=self.step_clients)

    @step.setter
    def step(self, step: StepLoad):
        self.step_load = step.enabled
        self.step_duration = step.duration
        self.step_clients = step.clients

    def to_config(self):
        config = asdict(self)
        config['duration'] = encode_timespan(config['duration'])
        config['step_duration'] = encode_timespan(config['step_duration'])
        return config
