from locust import Locust, TaskSet
from locust.exception import LocustError
from framework.generator.expected import ExpectedResponse


# TODO: need to investigate if we need such approach or will delete this module.

class ContainerLocust(Locust):
    """
    Class with shared data object that can be managed in and transferred between TaskSets or TaskSequences

    """
    def __init__(self):
        super(ContainerLocust, self).__init__()

    def set_shared_data(self, name, value):
        setattr(self, name, value)

    def get_shared_data(self, name):
        return getattr(self, name, None)


class ContainerTaskSet(TaskSet):
    """
    Class with methods to manage shared data of locust
    """
    def __init__(self, parent):
        super(ContainerTaskSet, self).__init__(parent)
        # Init a default expected response
        self.def_exp = ExpectedResponse()

        if isinstance(parent, ContainerTaskSet):
            self.locust = parent.locust
        elif isinstance(parent, ContainerLocust):
            self.locust = parent
        else:
            raise LocustError("ContainerTaskSet should be called with LocustContainer instance "
                              "or ContainerTaskSet instance as first argument")

    def set_shared_data(self, name, value):
        print(f'Name: {name}, value: {value}')
        self.locust.set_shared_data(name, value)

    def get_shared_data(self, name):
        return self.locust.get_shared_data(name)


class ContainerTaskSequence(ContainerTaskSet):
    """
    Class with methods to manage shared data of locust
    """
    def __init__(self, parent):
        super(ContainerTaskSequence, self).__init__(parent)
        self._index = 0
        self.tasks.sort(key=lambda t: t.locust_task_order if hasattr(t, 'locust_task_order') else 1)

    def get_next_task(self):
        task = self.tasks[self._index]
        self._index = (self._index + 1) % len(self.tasks)
        return task

