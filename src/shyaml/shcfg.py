#!/usr/bin/env python

## Note: to launch test, you can use:
##   python -m doctest -d shyaml.py
## or
##   nosetests

import sys
import os.path

from .yaml_parser import Yaml
from .common import stdout, die, mget

EXNAME = os.path.basename(sys.argv[0])

parser = {
    'yaml': Yaml
    }

def select_parser():
    for key, value in parser.iteritems():
        if EXNAME.endswith(key):
            return value
    return parser['yaml']


def main(args, Parser):
    load = Parser.load
    dump = Parser.dump

    usage = """usage:
    %(exname)s {get-value{,-0},get-type,keys{,-0},values{,-0}} KEY [DEFAULT]
    """ % {"exname": EXNAME}

    if len(args) == 0:
        die(usage, errlvl=0, prefix="")
    action = args[0]
    key_value = "" if len(args) == 1 else args[1]
    default = args[2] if len(args) > 2 else ""
    contents = load(sys.stdin)
    try:
        value = mget(contents, key_value, default)
    except IndexError:
        die("list index error in path %r." % key_value)
    except KeyError, TypeError:
        die("invalid path %r." % key_value)

    tvalue = Parser.type_name(value)
    termination = "\0" if action.endswith("-0") else "\n"

    if action == "get-value":
        print dump(value),
    elif action in ("get-values", "get-values-0"):
        if isinstance(value, dict):
            for k, v in value.iteritems():
                stdout("%s%s%s%s" % (dump(k), termination,
                                     dump(v), termination))
        elif isinstance(value, list):
            for l in value:
                stdout("%s%s" % (dump(l), termination))
        else:
            die("%s does not support %r type. "
                "Please provide or select a sequence or struct."
                % (action, tvalue))
    elif action == "get-type":
        print tvalue
    elif action in ("keys", "keys-0", "values", "values-0"):
        if isinstance(value, dict):
            method = value.keys if action.startswith("keys") else value.values
            for k in method():
                stdout("%s%s" % (dump(k), termination))
        else:
            die("%s does not support %r type. "
                "Please provide or select a struct." % (action, tvalue))
    else:
        die("Invalid argument.\n%s" % usage)


def run():
    sys.exit(main(sys.argv[1:], select_parser()))


if __name__ == "__main__":
    run()
