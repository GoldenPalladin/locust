import gevent

from typing import Tuple, Dict, List
from locust.stats import StatsEntry, RequestStats, StatsError
from locust.runners import LocustRunner
from config.test_config_reader import test_header

Request = Tuple[str, str]
StatsEntries = Dict[Request, StatsEntry]
StatsErrors = Dict[str, StatsError]


class Listener(object):
    """
    Base class for listeners, that can proceed Locust Stats and return Locust stats metrics.
    """
    def __init__(self, config):
        self.interval = config.get('stats_interval', 5)
        self.final_stats = False
        self.now = None                         # emit interval timestamp
        self.stats_dimensions = test_header     # some additional dimensions
        self.stats_dimensions = {str(k).replace(' ', '_'): v for k, v in self.stats_dimensions.items()}

    def start(self,
              locust_runner_reference: LocustRunner,
              final_stats=False,
              additional_dimensions: dict = None):
        """
        Main method to start emitting stats
        :param locust_runner_reference: locust runner instance to get stats and user count from
        :param final_stats: if True, stats are emitted for the whole period of time when greenlet termination is triggered.
        Should be used if emitting takes too much time in order not to slow down other locust greenlets making load.
        :param additional_dimensions: dictionary with additional key-value pairs to add to listener data
        :return:
        """
        if additional_dimensions:
            self.stats_dimensions.update(additional_dimensions)
        self.runner = locust_runner_reference
        self.final_stats = final_stats
        self.on_start()
        try:
            while True:
                if not self.final_stats:
                    self.emit()
                gevent.sleep(self.interval)
        except gevent.GreenletExit:
            if self.final_stats:
                self.emit()
            self.on_stop()
            raise

    def on_start(self):
        """
        Method to handle start, like fire 'test started' event.
        :return:
        """
        pass

    def on_stop(self):
        """
        Method to handle stop, like fire 'test stopped' event.
        :return:
        """
        pass

    def stop(self, greenlet):
        """
        Method to fire 'test stopped' event
        :param greenlet: stub, since method to be called in greenlet.link,
        and "The callback will be called with this instance as an argument once this greenlet is dead."
        :return:
        """
        pass

    def _get_latest_request_stats(self, stats_entries: StatsEntries) -> List[StatsEntry]:
        """
        Function to get latest unique (by request name) list of StatsEntries
        StatsEntry is prepared per every request and averages all previous results.
        :param stats_entries:
        :return:
        """
        if stats_entries:
            result = [entry for _, entry in stats_entries.items()]
            if not self.final_stats:
                result = list(filter(lambda entry: self._within_interval(entry.last_request_timestamp), result))
            if result:
                result = sorted(result, key=lambda entry: entry.last_request_timestamp)
                result = {entry.name: entry for entry in result}
                return list(result.values())
        return list()

    def _get_unposted_error_stats(self, stats_errors: StatsErrors,
                                  posted_errors: list) -> list:
        """
        Function to get StatsError records filtered by already posted keys list
        :param stats_errors:
        :param posted_errors: keys list (keys as in StatsError.create_key)
        :return:
        """
        if stats_errors:
            posted_errors = [] if self.final_stats else posted_errors
            return [(key, error) for key, error in stats_errors.items() if key not in posted_errors]
        return list()

    @staticmethod
    def _get_enrty_stats(entry: StatsEntry, user_count: int) -> dict:
        return {'rps': entry.current_rps,
                'fail_per_sec': entry.current_fail_per_sec,
                'clients': user_count,
                'avg_response_time': entry.avg_response_time,
                'failed': entry.num_failures,
                'total': entry.num_requests}

    def prepare_locust_errors(self, stats: RequestStats, user_count: int, posted_errors: list) -> list:
        """
        Function to prepare list of per-request errors.
        Errors are stored in stats.errors dict as StatsError[md5 hash] without any timestamp, just having
        'occurencies' counter, so to avoid duplication we return errors with not yet known key.
        Error record is enriched by StatsEvent data of pre-defined Locust metrics:
        current_rps, current_fail_per_sec, user_count, avg_response_time, num_failures, num_requests
        :param stats: Locust RequestStats object
        :param user_count: current count of spawned users
        :param posted_errors: list of already posted errors
        :return:
        """
        errors = self._get_unposted_error_stats(stats.errors, posted_errors)
        result = list()
        if errors:
            for key, error in errors:
                entry = stats.get(error.name, error.method)
                error_: dict = error.to_dict()
                error_.update(self._get_enrty_stats(entry, user_count))
                error_.update({'request name': error.name})
                result.append((key, error_))
        return result

    def prepare_locust_stats(self, stats: RequestStats, user_count: int) -> list:
        """
        Function to prepare list of per-request stats. Uses pre-defined Locust metrics:
        current_rps, current_fail_per_sec, user_count, avg_response_time, num_failures, num_requests
        :param stats: Locust RequestStats object
        :param user_count: current count of spawned users
        :return:
        """
        interval_stats_entries = self._get_latest_request_stats(stats.entries)
        result = list()
        if interval_stats_entries:
            for entry in interval_stats_entries:
                result.append((entry.name,
                               entry.last_request_timestamp,
                               self._get_enrty_stats(entry, user_count)))
        return result

    def _within_interval(self, timestamp) -> bool:
        """
        Checks if timestamp falls into interval seconds from now
        :param timestamp:
        :return:
        """
        return timestamp >= (self.now - self.interval)



