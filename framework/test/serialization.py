import pickle
import zlib
import base64

"""
object byte (de)serialization
https://stackoverflow.com/questions/58432514/how-to-pass-python-objects-that-are-not-json-serializable-from-one-aws-lambd
"""


def native_object_encoded(x):
    x = pickle.dumps(x)
    x = zlib.compress(x)
    x = base64.b64encode(x).decode()
    return x


def native_object_decoded(s):
    s = base64.b64decode(s)
    s = zlib.decompress(s)
    s = pickle.loads(s)
    return s

