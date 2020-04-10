from framework.test.interval import Interval
from framework.test.runner import Runner
from typing import List


class Timings(object):
    """
    Class to create and handle list of consecutive Intervals for load test
    """
    def __init__(self, runner_config: dict):
        self.runner = Runner.from_config(runner_config)
        self.step = self.runner.step
        self.no_steps = self.runner.clients // self.step.clients
        if not self.__is_runner_consistent():
            raise ValueError('Cannot hatch enough clients for step or whole test')
        self.interval: Interval = Interval.zero()
        self.chopped_intervals: List[Interval] = list()

    def __is_runner_consistent(self) -> bool:
        if self.step.enabled:
            if self.step.duration * self.runner.hatch_rate < self.step.clients:
                return False
        else:
            if self.runner.clients > self.runner.duration * self.runner.hatch_rate:
                return False
        return True

    def __make_base_interval(self):
        """
        Function to create single interval -- either with stepload or with linear hatch
        :return:
        """
        if self.step.enabled:
            step_end = None
            for i in range(self.no_steps):
                step_interval = Interval.make_load_interval(length=self.step.duration,
                                                            target_load=self.step.clients,
                                                            hatch=self.runner.hatch_rate,
                                                            base=step_end,
                                                            step=self.step)
                step_end = step_interval.end
                self.interval += step_interval
            reminder = self.runner.duration - self.interval.length
            if reminder > 0:
                self.interval += Interval.make_load_interval(length=reminder,
                                                             target_load=0,
                                                             hatch=0,
                                                             base=step_end)
        else:
            self.interval = Interval.make_load_interval(length=self.runner.duration,
                                                        target_load=self.runner.clients,
                                                        hatch=self.runner.hatch_rate)

    def chop_for_lambda(self, lambda_duration: int = 900):
        """
        function to split interval into 'lambda_duration' chunks
        :param lambda_duration:
        :return:
        """
        interval = self.interval
        while True:
            head, interval = interval.split_at(time_from_start=lambda_duration)
            self.chopped_intervals.append(head)
            if not interval:
                return

    def get_test_timings(self) -> list:
        """
        Function to get list of lambda launch configs
        :return:
        """
        result = list()
        self.__make_base_interval()
        self.chop_for_lambda()
        for interval in self.chopped_intervals:
            result.extend(interval.lambda_load_config())
        return result
