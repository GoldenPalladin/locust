import logging
from typing import List
from framework.test.stepload import StepLoad
from framework.test.llp import LoadLevelPoint, are_aligned
from framework.test.runner import Runner

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

LlpList = List[LoadLevelPoint]


class Interval(object):
    """
    Class represents a linear load change model as list of consequiential load-level points within interval
    """
    def __init__(self, llp_list: LlpList = None):
        if self.is_consistent(llp_list):
            self.llp_list = llp_list
            self.step: StepLoad = StepLoad()
        else:
            raise ValueError(f'LLP list is inconsistent, LLPs are not chained: {llp_list}')

    def __add__(self, other):
        if issubclass(type(other), Interval):
            if self.length == 0:
                return other
            elif other.length == 0:
                return self
            if self.end == other.start:
                self.llp_list.pop(-1)
                self.llp_list.extend(other.llp_list)
                self.remove_aligned()
                return self
            raise ValueError(f'{self.end} != {other.start}. Cannot add non-consecutive intervals!')
        raise TypeError(f'Cannot add Interval with {type(other)}!')

    def __repr__(self):
        plist = ", ".join([str(i) for i in self.llp_list])
        return f'\nINTERVAL\n<[{plist}]\npoints={self.points}, base={self.base}, ' \
            f'start hatch={self.start.hatch}\nstep={self.step}>'

    @property
    def start(self) -> LoadLevelPoint:
        return self.llp_list[0]

    @property
    def end(self):
        return self.llp_list[-1]

    @property
    def length(self) -> int:
        return self.end.time - self.start.time

    @property
    def points(self):
        return len(self.llp_list)

    @property
    def base(self):
        return self.start.load

    def p(self, i):
        """let's count points in a people way"""
        return self.llp_list[i-1]

    def remove_aligned(self):
        """
        If any of three interval points are aligned, remove the second
        :return:
        """
        if self.points > 2:
            for i in range(self.points - 2):
                if are_aligned(self.p(i+1), self.p(i+2), self.p(i+3)):
                    self.llp_list.pop(i+1)  # what a mess with indexes! Actually we remove p(i+2)

    def shift_to_point(self, left_point: LoadLevelPoint):
        """Shifts start of the interval to left_point"""
        if left_point:
            points, self.llp_list = self.llp_list, list()
            self.llp_list = [point + left_point for point in points]

    def contains_time(self, time: int) -> bool:
        return self.start.time < time < self.end.time

    def split_at(self, time_from_start: int) -> tuple:
        """
        Function to split current interval at time_from_start to head:tail
        :param time_from_start: time_from_start point to split interval at
        :return: self, trimmed to 'time_from_start', new Interval with all the rest LLPs from 'time_from_start'
        """
        logger.debug(f'Split {self} at {time_from_start}')
        time = time_from_start + self.start.time
        if not self.contains_time(time):
            return self, None
        split_point = LoadLevelPoint(time=time, load=0, hatch=0)
        shift_base, split_index = self.start, 0
        if self.points >= 2:
            for i in range(self.points - 1):
                if self.llp_list[i] < split_point < self.llp_list[i+1]:
                    shift_base = self.llp_list[i]
                    split_index = i + 1
                    break
        split_point = shift_base.extend_to(time)
        first, second = self.llp_list[:split_index], list()
        first.append(split_point)
        second.append(split_point)
        second.extend(self.llp_list[split_index:])
        self.llp_list = first
        return self, Interval(llp_list=second)

    @staticmethod
    def is_consistent(llp_list: LlpList) -> bool:
        if len(llp_list) > 0:
            for i in range(len(llp_list) - 1):
                if not llp_list[i].is_pointing_at(llp_list[i + 1]):
                    return False
        return True

    @classmethod
    def make_load_interval(cls, length: int, target_load: int, hatch: int,
                           base: LoadLevelPoint = None, step: StepLoad = None):
        """
        function to calculate single lcp within interval
        :param length: interval length
        :param target_load: target level of load by the end of the interval
        :param hatch: hatch rate
        :param base: point to start interval at
        :param step: stepload parameters for interval
        :return: interval with no or single llp
        """
        logger.debug(f'Make load interval for:{locals()}\n')
        start = LoadLevelPoint(time=0, load=0, hatch=hatch)
        end = LoadLevelPoint(time=length, load=target_load, hatch=0)
        result = [start, end]
        if start.deviation(end) > 0:
            result.insert(1, LoadLevelPoint(time=target_load // hatch, load=target_load, hatch=0))
        elif start.deviation(end) == 0:
            end.hatch = hatch
        else:
            raise ValueError(f'Cannot reach {target_load} load at {hatch} hatch for {length} secs.')
        result = Interval(llp_list=result)
        result.shift_to_point(base)
        if step:
            result.step = step
        logger.debug(f'Load interval: {result}')
        return result

    @classmethod
    def zero(cls):
        """
        function to create start interval for summing chain
        :return: zero-length Interval, starting at zero
        """
        start = LoadLevelPoint(time=0, load=0, hatch=0)
        end = LoadLevelPoint(time=0, load=0, hatch=0)
        return cls(llp_list=[start, end])

    def lambda_load_config(self) -> list:
        """
        Some magic method to tell if load in current interval can be decomposed
        into composition of load templates: hatch, square, stepload.
        Each load template can (and will) be triggered in lambda at specific point of time
        :return: [(lambda start time, lambda config), ...]
        """
        logger.debug(f'Start making load config from: {self}')
        result = list()

        def get_hatch_runner(clients, hatch_rate, duration) -> Runner:
            return Runner(clients, hatch_rate, duration)

        def get_square_runner(clients, duration) -> Runner:
            # hatching all clients at a time
            return Runner(clients, hatch_rate=clients, duration=duration)

        def get_step_runner(clients, hatch_rate, duration, step) -> Runner:
            r = Runner(clients, hatch_rate, duration)
            r.step = step
            return r

        if self.base == 0:
            if self.points == 3 and not self.step.enabled:
                logger.debug('\n_-> "hatch" (= linear load increase until some level)')
                runner = get_hatch_runner(clients=self.end.load,
                                          hatch_rate=self.start.hatch,
                                          duration=self.length)
                result.append((self.start.time, runner.to_config()))
            elif self.step.enabled:
                logger.debug('\n_-> "stepload" (= step load increase)')
                runner = get_step_runner(clients=self.end.load,
                                         hatch_rate=self.start.hatch,
                                         duration=self.length,
                                         step=self.step)
                result.append((self.start.time, runner.to_config()))
        else:
            if self.start.hatch == 0:
                if self.points == 2:
                    logger.debug('\n_-> "square" (= start interval at some level of load to continue previous one)')
                    runner = get_square_runner(clients=self.end.load,
                                               duration=self.length)
                    result.append((self.start.time, runner.to_config()))
                elif self.step.enabled:
                    logger.debug('\n_-> "square" + "stepload"')
                    runner = get_square_runner(clients=self.start.load,
                                               duration=self.length)
                    result.append((self.start.time, runner.to_config()))
                    runner = get_step_runner(clients=self.end.load,
                                             hatch_rate=self.p(2).hatch,
                                             duration=self.p(2).time_gap_to(self.end),
                                             step=self.step)
                    result.append((self.p(2).time, runner.to_config()))
            else:
                if self.points == 3 and not self.step.enabled:
                    logger.debug('\n_-> "square" + "hatch"')
                    runner = get_square_runner(clients=self.start.load,
                                               duration=self.length)
                    result.append((self.start.time, runner.to_config()))
                    runner = get_hatch_runner(clients=self.end.load,
                                              hatch_rate=self.start.hatch,
                                              duration=self.length)
                    result.append((self.start.time, runner.to_config()))
                elif self.step.enabled:
                    logger.debug('\n_-> "square" + "hatch" + "stepload"')
                    runner = get_square_runner(clients=self.start.load,
                                               duration=self.length)
                    result.append((self.start.time, runner.to_config()))
                    runner = get_hatch_runner(clients=self.p(2) - self.start,
                                              hatch_rate=self.start.hatch,
                                              duration=self.length)
                    result.append((self.start.time, runner.to_config()))
                    runner = get_step_runner(clients=self.end.load,
                                             hatch_rate=self.p(3).hatch,
                                             duration=self.p(3).time_gap_to(self.end),
                                             step=self.step)
                    result.append((self.p(3).time, runner.to_config()))
        logger.debug(f'Interval config: {result}')
        return result

