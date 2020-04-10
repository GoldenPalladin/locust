import logging
from framework.test.serialization import native_object_decoded
from contextlib import closing
from locust.stats import RequestStats, StatsEntry, StatsError
from botocore import response

# stats_logger = logging.getLogger("load_test.stats_logger")
# sh = logging.StreamHandler()
# sh.setLevel(logging.INFO)
# sh.setFormatter(logging.Formatter('%(message)s'))
# stats_logger.addHandler(sh)
logging.basicConfig(level=logging.INFO, format='%(message)s')
stats_logger = logging.getLogger("stats_logger")


def extend_stats(stats_log: RequestStats, stats_chunk: RequestStats) -> RequestStats:
    """
    Function to extend stats log (of the whole test) with stats chunk (from load generator).
    It was mostly copy-pasted from locust.stats.extend stats since the latter uses global
    variables of locust.stats module
    :param stats_log: total test stats
    :param stats_chunk: piece of stats to
    :return: resulting extended stats
    """

    for entry in stats_chunk.entries.values():
        request_key = (entry.name, entry.method)
        if request_key not in stats_log.entries:
            stats_log.entries[request_key] = StatsEntry(entry.stats, entry.name, entry.method)
        stats_log.entries[request_key].extend(entry)
    for error_key, error in stats_chunk.errors.items():
        if error_key not in stats_log.errors:
            stats_log.errors[error_key] = StatsError(error.method, error.name, error.error, error.occurrences)
        else:
            stats_log.errors[error_key].occurrences += error.occurrences
    old_last_request_timestamp = stats_log.total.last_request_timestamp
    stats_log.total.extend(stats_chunk.total)
    if stats_log.total.last_request_timestamp \
            and stats_log.total.last_request_timestamp > (old_last_request_timestamp or 0):
        stats_log.total._cache_response_times(int(stats_log.total.last_request_timestamp))
    return stats_log


def get_stats_from_response(resp: response) -> RequestStats:
    """
    Function do decode lambda response into RequestStats object
    :param resp: botocore.response
    :return:
    """
    b_stats_stream = resp.get('Payload')
    with closing(b_stats_stream):
        b_stats = b_stats_stream.read()
        stats: RequestStats = native_object_decoded(b_stats)
    return stats


def print_stats(stats: RequestStats, logger=stats_logger):
    """
    Function to output total request statistics. 
    :param logger: logger to output 
    :param stats:
    :return:
    """
    logger.info(f"\nTEST STATISTICS\n{'='*170}\nPercentage of the requests completed within given times")
    logger.info((" %-" + str(60) + "s %-" + str(20) + "s %8s %6s %6s %6s %6s %6s %6s %6s %6s %6s %6s %6s") % (
        'Type',
        'Name',
        '# reqs',
        '50%',
        '66%',
        '75%',
        '80%',
        '90%',
        '95%',
        '98%',
        '99%',
        '99.9%',
        '99.99%',
        '100%',
    ))
    logger.info("-" * 170)
    for key in sorted(stats.entries.keys()):
        r = stats.entries[key]
        if r.response_times:
            logger.info(r.percentile())
    logger.info("-" * 170)
    if stats.total.response_times:
        logger.info(stats.total.percentile())
    logger.info("")
    if not len(stats.errors):
        return
    logger.info("Error report")
    logger.info(" %-18s %-100s" % ("# occurrences", "Error"))
    logger.info("-" * 170)
    for error in stats.errors.values():
        logger.info(" %-18i %-100s" % (error.occurrences, error.to_name()))
    logger.info("-" * 170)
    logger.info("")
    

def load_stats() -> RequestStats:
    with open('resp.b', 'rb') as file:
        return native_object_decoded(file.read())