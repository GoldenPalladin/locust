import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass
class LoadLevelPoint(object):
    """
    Class represents load level vector at time point. Used as definition of load level in:
    - interval start
    - load change point
    - interval end
    """
    time: int          # time value of the point
    load: int          # load level of the point
    hatch: int         # hatch rate after the point

    def __eq__(self, other):
        return self.time == other.time

    def __lt__(self, other):
        return self.time < other.time

    def __add__(self, other):
        return LoadLevelPoint(time=self.time+other.time, load=self.load+other.load, hatch=self.hatch)

    def __sub__(self, other):
        return self.load - other.load

    def __str__(self):
        return f'LLP(time={self.time}, load={self.load}, hatch={self.hatch})'

    def time_gap_to(self, other):
        return other.time - self.time

    def deviation(self, other) -> int:
        """ function to estimate if self.hatch points above (1), directly at (0)
        or below (-1) other LLP"""
        diff = (other.time - self.time) * self.hatch - (other.load - self.load)
        if diff > 0:
            return 1
        elif diff == 0:
            return 0
        else:
            return -1

    def is_pointing_at(self, other) -> bool:
        """function checks if hatch rate of current LLP will lead to other LLP"""
        if isinstance(other, LoadLevelPoint):
            return self.deviation(other) == 0
        else:
            raise TypeError('Can not point at other types!')

    def extend_to(self, time: int):
        """function returns LLP at the specified time with current hatch"""
        return LoadLevelPoint(time=time,
                              load=self.load + self.hatch * (time - self.time),
                              hatch=self.hatch)


def are_aligned(p1: LoadLevelPoint, p2: LoadLevelPoint, p3: LoadLevelPoint) -> bool:
    """ function to check if three points are on the same line """
    if p1.is_pointing_at(p2) and p1.is_pointing_at(p3):
        return True
    return False
