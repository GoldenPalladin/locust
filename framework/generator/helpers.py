import os
import csv
import random
from pathlib import Path


def make_file_with_size(name, size_bytes):
    """
    Lambda allows file creation only in \tmp folder
    :param name: file name
    :param size_bytes: file size
    :return: path to created file
    """
    tmp_dir = os.path.abspath(os.path.join(os.sep, 'tmp'))
    if not os.path.isdir(tmp_dir):
        os.mkdir(tmp_dir)
    file_path = os.path.join(tmp_dir, name)
    with open(file_path, "wb") as f:
        f.write(os.urandom(size_bytes))
        return file_path


def read_file_from_path(filename, pathname):
    data_folder = Path(f"/{pathname}")
    file_path = data_folder / filename
    with open(file_path, "rb") as f:
        return f.read()


class CsvData(object):
    """
    Class to handle csv test data
    """
    def __init__(self, file_path, fieldnames):
        file_path = os.path.join(os.path.curdir, file_path)
        with open(file_path) as csv_file:
            self.data = list(csv.DictReader(csv_file, fieldnames=fieldnames))

    def get_rand_item(self):
        return random.choice(self.data)
