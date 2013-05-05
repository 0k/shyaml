import sys


SIMPLE_TYPES = (basestring, int, float)
COMPLEX_TYPES = (list, dict)



def mget(dct, key, default=None):
    """Allow to get values deep in a dict with doted keys.

    >>> mget({'a': {'x': 1, 'b': {'c': 2}}}, "a.x")
    1
    >>> mget({'a': {'x': 1, 'b': {'c': 2}}}, "a.b.c")
    2
    >>> mget({'a': {'x': 1, 'b': {'c': 2}}}, "a.b")
    {'c': 2}
    >>> mget({'a': {'x': [1, 5], 'b': {'c': 2}}}, "a.x.-1")
    5
    >>> mget({'a': {'x': 1, 'b': [{'c': 2}]}}, "a.b.0.c")
    2

    >>> mget({'a': {'x': 1, 'b': {'c': 2}}}, "a.y", default='N/A')
    'N/A'

    """
    if key == "":
        return dct
    if not "." in key:
        if isinstance(dct, list):
            return dct[int(key)]
        return dct.get(key, default)
    else:
        head, tail = key.split(".", 1)
        value = dct[int(head)] if isinstance(dct, list) else dct.get(head, {})
        return mget(value, tail, default)


def stderr(msg):
    sys.stderr.write(msg + "\n")


def die(msg, errlvl=1, prefix="Error: "):
    stderr("%s%s" % (prefix, msg))
    sys.exit(errlvl)



def stdout(value):
    sys.stdout.write(value)


