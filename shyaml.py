#!/usr/bin/env python
"""
YAML for command line.
"""

## Note: to launch test, you can use:
##   python -m doctest -d shyaml.py
## or
##   nosetests

from __future__ import print_function

import sys
import os.path
import re
import textwrap

import yaml


if os.environ.get("FORCE_PYTHON_YAML_IMPLEMENTATION"):
    from yaml import SafeLoader, SafeDumper
else:
    try:
        from yaml import CSafeLoader as SafeLoader, CSafeDumper as SafeDumper
    except ImportError:  ## pragma: no cover
        from yaml import SafeLoader, SafeDumper


PY3 = sys.version_info[0] >= 3
WIN32 = sys.platform == 'win32'

EXNAME = os.path.basename(__file__ if WIN32 else sys.argv[0])

for ext in (".py", ".pyc", ".exe", "-script.py", "-script.pyc"):  ## pragma: no cover
    if EXNAME.endswith(ext):  ## pragma: no cover
        EXNAME = EXNAME[:-len(ext)]
        break

USAGE = """\
Usage:

    %(exname)s (-h|--help)
    %(exname)s [-y|--yaml] ACTION KEY [DEFAULT]
""" % {"exname": EXNAME}

HELP = """
Parses and output chosen subpart or values from YAML input.
It reads YAML in stdin and will output on stdout it's return value.

%(usage)s

Options:

    -y, --yaml
              Output only YAML safe value, more precisely, even
              literal values will be YAML quoted. This behavior
              is required if you want to output YAML subparts and
              further process it. If you know you have are dealing
              with safe literal value, then you don't need this.
              (Default: no safe YAML output)

    ACTION    Depending on the type of data you've targetted
              thanks to the KEY, ACTION can be:

              These ACTIONs applies to any YAML type:

                get-type          ## returns a short string
                get-value         ## returns YAML

              These ACTIONs applies to 'sequence' and 'struct' YAML type:

                get-values{,-0}   ## returns list of YAML
                get-length        ## returns an integer

              These ACTION applies to 'struct' YAML type:

                keys{,-0}         ## returns list of YAML
                values{,-0}       ## returns list of YAML
                key-values,{,-0}  ## returns list of YAML

              Note that any value returned is returned on stdout, and
              when returning ``list of YAML``, it'll be separated by
              a newline or ``NUL`` char depending of you've used the
              ``-0`` suffixed ACTION.

    KEY       Identifier to browse and target subvalues into YAML
              structure. Use ``.`` to parse a subvalue. If you need
              to use a literal ``.`` or ``\\``, use ``\\`` to quote it.

              Use struct keyword to browse ``struct`` YAML data and use
              integers to browse ``sequence`` YAML data.

    DEFAULT   if not provided and given KEY do not match any value in
              the provided YAML, then DEFAULT will be returned. If no
              default is provided and the KEY do not match any value
              in the provided YAML, %(exname)s will fail with an error
              message.

Examples:

     ## get last grocery
     cat recipe.yaml       | %(exname)s get-value groceries.-1

     ## get all words of my french dictionary
     cat dictionaries.yaml | %(exname)s keys-0 french.dictionary

     ## get YAML config part of 'myhost'
     cat hosts_config.yaml | %(exname)s get-value cfgs.myhost

""" % {"exname": EXNAME, "usage": USAGE}


class ShyamlSafeLoader(SafeLoader):
    """Shyaml specific safe loader"""


class ShyamlSafeDumper(SafeDumper):
    """Shyaml specific safe dumper"""


## Ugly way to force both the Cython code and the normal code
## to get the output line by line.
class ForcedLineStream(object):

    def __init__(self, fileobj):
        self._file = fileobj

    def read(self, size=-1):
        ## don't care about size
        return self._file.readline()

    def close(self):
        return self._file.close()


class LineLoader(ShyamlSafeLoader):
    """Forcing stream in line buffer mode"""

    def __init__(self, stream):
        stream = ForcedLineStream(stream)
        super(LineLoader, self).__init__(stream)


##
## Keep previous order in YAML
##

try:
    ## included in standard lib from Python 2.7
    from collections import OrderedDict
except ImportError:  ## pragma: no cover
    ## try importing the backported drop-in replacement
    ## it's available on PyPI
    from ordereddict import OrderedDict


## Ensure that there are no collision with legacy OrderedDict
## that could be used for omap for instance.
class MyOrderedDict(OrderedDict):
    pass


ShyamlSafeDumper.add_representer(
    MyOrderedDict,
    lambda cls, data: cls.represent_dict(data.items()))


def construct_omap(cls, node):
    ## Force unfolding reference and merges
    ## otherwise it would fail on 'merge'
    cls.flatten_mapping(node)
    return MyOrderedDict(cls.construct_pairs(node))


ShyamlSafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    construct_omap)


##
## Support local and global objects
##

class EncapsulatedNode(object):
    """Holds a yaml node"""


def mk_encapsulated_node(s, node):

    method = "construct_%s" % (node.id, )
    data = getattr(s, method)(node)

    class _E(data.__class__, EncapsulatedNode):
        pass

    _E.__name__ = str(node.tag)
    _E._node = node
    return _E(data)


def represent_encapsulated_node(s, o):
    value = s.represent_data(o.__class__.__bases__[0](o))
    value.tag = o.__class__.__name__
    return value


ShyamlSafeDumper.add_multi_representer(EncapsulatedNode,
                                       represent_encapsulated_node)
ShyamlSafeLoader.add_constructor(None, mk_encapsulated_node)


##
## Key specifier
##

def tokenize(s):
    r"""Returns an iterable through all subparts of string splitted by '.'

    So:

        >>> list(tokenize('foo.bar.wiz'))
        ['foo', 'bar', 'wiz']

    Contrary to traditional ``.split()`` method, this function has to
    deal with any type of data in the string. So it actually
    interprets the string. Characters with meaning are '.' and '\'.
    Both of these can be included in a token by quoting them with '\'.

    So dot of slashes can be contained in token:

        >>> print('\n'.join(tokenize(r'foo.dot<\.>.slash<\\>')))
        foo
        dot<.>
        slash<\>

    Notice that empty keys are also supported:

        >>> list(tokenize(r'foo..bar'))
        ['foo', '', 'bar']

    Given an empty string:

        >>> list(tokenize(r''))
        ['']

    And a None value:

        >>> list(tokenize(None))
        []

    """
    if s is None:
        return
    tokens = (re.sub(r'\\(\\|\.)', r'\1', m.group(0))
              for m in re.finditer(r'((\\.|[^.\\])*)', s))
    ## an empty string superfluous token is added after all non-empty token
    for token in tokens:
        if len(token) != 0:
            next(tokens)
        yield token


def mget(dct, key):
    r"""Allow to get values deep in recursive dict with doted keys

    Accessing leaf values is quite straightforward:

        >>> dct = {'a': {'x': 1, 'b': {'c': 2}}}
        >>> mget(dct, 'a.x')
        1
        >>> mget(dct, 'a.b.c')
        2

    But you can also get subdict if your key is not targeting a
    leaf value:

        >>> mget(dct, 'a.b')
        {'c': 2}

    As a special feature, list access is also supported by providing a
    (possibily signed) integer, it'll be interpreted as usual python
    sequence access using bracket notation:

        >>> mget({'a': {'x': [1, 5], 'b': {'c': 2}}}, 'a.x.-1')
        5
        >>> mget({'a': {'x': 1, 'b': [{'c': 2}]}}, 'a.b.0.c')
        2

    Keys that contains '.' can be accessed by escaping them:

        >>> dct = {'a': {'x': 1}, 'a.x': 3, 'a.y': 4}
        >>> mget(dct, 'a.x')
        1
        >>> mget(dct, r'a\.x')
        3
        >>> mget(dct, r'a.y')  ## doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ...
        MissingKeyError: missing key 'y' in dict.
        >>> mget(dct, r'a\.y')
        4

    As a consequence, if your key contains a '\', you should also escape it:

        >>> dct = {r'a\x': 3, r'a\.x': 4, 'a.x': 5, 'a\\': {'x': 6}}
        >>> mget(dct, r'a\\x')
        3
        >>> mget(dct, r'a\\\.x')
        4
        >>> mget(dct, r'a\\.x')
        6
        >>> mget({'a\\': {'b': 1}}, r'a\\.b')
        1
        >>> mget({r'a.b\.c': 1}, r'a\.b\\\.c')
        1

    And even empty strings key are supported:

        >>> dct = {r'a': {'': {'y': 3}, 'y': 4}, 'b': {'': {'': 1}}, '': 2}
        >>> mget(dct, r'a..y')
        3
        >>> mget(dct, r'a.y')
        4
        >>> mget(dct, r'')
        2
        >>> mget(dct, r'b..')
        1

    It will complain if you are trying to get into a leaf:

        >>> mget({'a': 1}, 'a.y')   ## doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ...
        NonDictLikeTypeError: can't query subvalue 'y' of a leaf...

    if the key is None, the whole dct should be sent back:

        >>> mget({'a': 1}, None)
        {'a': 1}

    """
    return aget(dct, tokenize(key))


class MissingKeyError(KeyError):
    """Raised when querying a dict-like structure on non-existing keys"""

    def __str__(self):
        return self.args[0]


class NonDictLikeTypeError(TypeError):
    """Raised when attempting to traverse non-dict like structure"""


class IndexNotIntegerError(ValueError):
    """Raised when attempting to traverse sequence without using an integer"""


class IndexOutOfRange(IndexError):
    """Raised when attempting to traverse sequence without using an integer"""


def aget(dct, key):
    r"""Allow to get values deep in a dict with iterable keys

    Accessing leaf values is quite straightforward:

        >>> dct = {'a': {'x': 1, 'b': {'c': 2}}}
        >>> aget(dct, ('a', 'x'))
        1
        >>> aget(dct, ('a', 'b', 'c'))
        2

    If key is empty, it returns unchanged the ``dct`` value.

        >>> aget({'x': 1}, ())
        {'x': 1}

    """
    key = iter(key)
    try:
        head = next(key)
    except StopIteration:
        return dct

    if isinstance(dct, list):
        try:
            idx = int(head)
        except ValueError:
            raise IndexNotIntegerError(
                "non-integer index %r provided on a list."
                % head)
        try:
            value = dct[idx]
        except IndexError:
            raise IndexOutOfRange(
                "index %d is out of range (%d elements in list)."
                % (idx, len(dct)))
    else:
        try:
            value = dct[head]
        except KeyError:
            ## Replace with a more informative KeyError
            raise MissingKeyError(
                "missing key %r in dict."
                % (head, ))
        except Exception:
            raise NonDictLikeTypeError(
                "can't query subvalue %r of a leaf%s."
                % (head,
                   (" (leaf value is %r)" % dct)
                   if len(repr(dct)) < 15 else ""))
    return aget(value, key)


def stderr(msg):
    """Convenience function to write short message to stderr."""
    sys.stderr.write(msg)


def stdout(value):
    """Convenience function to write short message to stdout."""
    sys.stdout.write(value)


def die(msg, errlvl=1, prefix="Error: "):
    """Convenience function to write short message to stderr and quit."""
    stderr("%s%s\n" % (prefix, msg))
    sys.exit(errlvl)


SIMPLE_TYPES = (str if PY3 else basestring, int, float, type(None))
COMPLEX_TYPES = (list, dict)

## these are not composite values
ACTION_SUPPORTING_STREAMING=["get-type", "get-length", "get-value"]


def magic_dump(value):
    """Returns a representation of values directly usable by bash.

    Literal types are printed as-is (avoiding quotes around string for
    instance). But complex type are written in a YAML useable format.

    """
    return str(value) if isinstance(value, SIMPLE_TYPES) \
        else yaml_dump(value)


def yaml_dump(value):
    """Returns a representation of values directly usable by bash.

    Literal types are quoted and safe to use as YAML.

    """
    return yaml.dump(value, default_flow_style=False,
                     Dumper=ShyamlSafeDumper)


def type_name(value):
    """Returns pseudo-YAML type name of given value."""
    return type(value).__name__ if isinstance(value, EncapsulatedNode) else \
           "struct" if isinstance(value, dict) else \
           "sequence" if isinstance(value, (tuple, list)) else \
           type(value).__name__


def _parse_args(args, USAGE, HELP):
    opts = {}

    opts["dump"] = magic_dump
    for arg in ["-y", "--yaml"]:
        if arg in args:
            args.remove(arg)
            opts["dump"] = yaml_dump

    opts["quiet"] = False
    for arg in ["-q", "--quiet"]:
        if arg in args:
            args.remove(arg)
            opts["quiet"] = True

    for arg in ["-L", "--line-buffer"]:
        if arg not in args:
            continue
        args.remove(arg)

        opts["loader"] = LineLoader

    if len(args) == 0:
        stderr("Error: Bad number of arguments.\n")
        die(USAGE, errlvl=1, prefix="")

    if len(args) == 1 and args[0] in ("-h", "--help"):
        stdout(HELP)
        exit(0)

    ## XXXvlab: this validation is violating DRY, and probably
    ## is a strong hint to move away from the current keyword querying
    ## system as it has aspects of a language (namely the "-0" postfix).
    if args[0] not in ["get-value",
                       "get-values", "get-values-0",
                       "get-type", "get-length",
                       "keys", "keys-0",
                       "values", "values-0",
                       "key-values", "key-values-0"]:
        stderr("Error: %r is not a valid action.\n"
               % args[0])
        die(USAGE, errlvl=1, prefix="")

    opts["action"] = args[0]
    opts["key"] = None if len(args) == 1 else args[1]
    opts["default"] = args[2] if len(args) > 2 else None

    return opts


class InvalidPath(KeyError):
    """Invalid Path"""

    def __str__(self):
        return self.args[0]


class InvalidAction(KeyError):
    """Invalid Action"""


def traverse(contents, path, default=None):
    try:
        try:
            value = mget(contents, path)
        except (IndexOutOfRange, MissingKeyError):
            if default is None:
                raise
            value = default
    except (IndexOutOfRange, MissingKeyError,
            NonDictLikeTypeError, IndexNotIntegerError) as exc:
        msg = str(exc)
        raise InvalidPath(
            "invalid path %r, %s"
            % (path, msg.replace('list', 'sequence').replace('dict', 'struct')))
    return value


class ActionTypeError(Exception):

    def __init__(self, action, provided, expected):
        self.action = action
        self.provided = provided
        self.expected = expected

    def __str__(self):
        return ("%s does not support %r type. "
                "Please provide or select a %s."
                % (self.action, self.provided,
                   self.expected[0] if len(self.expected) == 1 else
                   ("%s or %s" % (", ".join(self.expected[:-1]),
                                  self.expected[-1]))))


def act(action, value, dump=yaml_dump):
    tvalue = type_name(value)
    ## Note: ``\n`` will be transformed by ``universal_newlines`` mecanism for
    ## any platform
    termination = "\0" if action.endswith("-0") else "\n"

    if action == "get-value":
        return str(dump(value))
    elif action in ("get-values", "get-values-0"):
        if isinstance(value, dict):
            return "".join("".join((dump(k), termination,
                                    dump(v), termination))
                           for k, v in value.items())
        elif isinstance(value, list):
            return "".join("".join((dump(l), termination))
                           for l in value)
        else:
            raise ActionTypeError(
                action, provided=tvalue, expected=["sequence", "struct"])
    elif action == "get-type":
        return tvalue
    elif action == "get-length":
        if isinstance(value, (dict, list)):
            return len(value)
        else:
            raise ActionTypeError(
                action, provided=tvalue, expected=["sequence", "struct"])
    elif action in ("keys", "keys-0",
                    "values", "values-0",
                    "key-values", "key-values-0"):
        if isinstance(value, dict):
            method = value.keys if action.startswith("keys") else \
                value.items if action.startswith("key-values") else \
                value.values
            output = (lambda x: termination.join(str(dump(e)) for e in x)) \
                if action.startswith("key-values") else \
                dump
            return "".join("".join((str(output(k)), termination)) for k in method())
        else:
            raise ActionTypeError(
                action=action, provided=tvalue, expected=["struct"])
    else:
        raise InvalidAction(action)


def do(stream, action, key, default=None, dump=yaml_dump,
       loader=ShyamlSafeLoader):
    """Return string representation of target value in stream YAML

    The key is used for traversal of the YAML structure to target
    the value that will be dumped.

    :param stream:  file like input yaml content
    :param action:  string identifying one of the possible supported actions
    :param key:     string dotted expression to traverse yaml input
    :param default: optional default value in case of missing end value when
                    traversing input yaml.  (default is ``None``)
    :param dump:    callable that will be given python objet to dump in yaml
                    (default is ``yaml_dump``)
    :param loader:  PYYaml's *Loader subclass to parse YAML
                    (default is ShyamlSafeLoader)
    :return:        string representation of targetted inner yaml value

    :raises ActionTypeError: when there's a type mismatch between the
        action selected and the type of the targetted value.
        (ie: action 'key-values' on non-struct)
    :raises InvalidAction: when selected action is not a recognised valid
        action identifier.
    :raises InvalidPath: upon inexistent content when traversing YAML
        input following the key specification.

    """
    at_least_one_content = False
    for content in yaml.load_all(stream, Loader=loader):
        at_least_one_content = True
        value = traverse(content, key, default=default)
        yield act(action, value, dump=dump)

    if at_least_one_content is False:
        value = traverse(None, key, default=default)
        yield act(action, value, dump=dump)


def main(args):  ## pylint: disable=too-many-branches
    """Entrypoint of the whole commandline application"""

    EXNAME = os.path.basename(__file__ if WIN32 else sys.argv[0])

    for ext in (".py", ".pyc", ".exe", "-script.py", "-script.pyc"):  ## pragma: no cover
        if EXNAME.endswith(ext):  ## pragma: no cover
            EXNAME = EXNAME[:-len(ext)]
            break

    USAGE = """\
    Usage:

        %(exname)s (-h|--help)
        %(exname)s [-y|--yaml] [-q|--quiet] ACTION KEY [DEFAULT]
    """ % {"exname": EXNAME}

    HELP = """
    Parses and output chosen subpart or values from YAML input.
    It reads YAML in stdin and will output on stdout it's return value.

%(usage)s

    Options:

        -y, --yaml
                  Output only YAML safe value, more precisely, even
                  literal values will be YAML quoted. This behavior
                  is required if you want to output YAML subparts and
                  further process it. If you know you have are dealing
                  with safe literal value, then you don't need this.
                  (Default: no safe YAML output)

        -q, --quiet
                  In case KEY value queried is an invalid path, quiet
                  mode will prevent the writing of an error message on
                  standard error.
                  (Default: no quiet mode)

        -L, --line-buffer
                  Force parsing stdin line by line allowing to process
                  streamed YAML as it is fed instead of buffering
                  input and treating several YAML streamed document
                  at once. This is likely to have some small performance
                  hit if you have a huge stream of YAML document, but
                  then you probably don't really care about the
                  line-buffering.
                  (Default: no line buffering)

        ACTION    Depending on the type of data you've targetted
                  thanks to the KEY, ACTION can be:

                  These ACTIONs applies to any YAML type:

                    get-type          ## returns a short string
                    get-value         ## returns YAML

                  These ACTIONs applies to 'sequence' and 'struct' YAML type:

                    get-values{,-0}   ## returns list of YAML
                    get-length        ## returns an integer

                  These ACTION applies to 'struct' YAML type:

                    keys{,-0}         ## returns list of YAML
                    values{,-0}       ## returns list of YAML
                    key-values,{,-0}  ## returns list of YAML

                  Note that any value returned is returned on stdout, and
                  when returning ``list of YAML``, it'll be separated by
                  a newline or ``NUL`` char depending of you've used the
                  ``-0`` suffixed ACTION.

        KEY       Identifier to browse and target subvalues into YAML
                  structure. Use ``.`` to parse a subvalue. If you need
                  to use a literal ``.`` or ``\\``, use ``\\`` to quote it.

                  Use struct keyword to browse ``struct`` YAML data and use
                  integers to browse ``sequence`` YAML data.

        DEFAULT   if not provided and given KEY do not match any value in
                  the provided YAML, then DEFAULT will be returned. If no
                  default is provided and the KEY do not match any value
                  in the provided YAML, %(exname)s will fail with an error
                  message.

    Examples:

         ## get last grocery
         cat recipe.yaml       | %(exname)s get-value groceries.-1

         ## get all words of my french dictionary
         cat dictionaries.yaml | %(exname)s keys-0 french.dictionary

         ## get YAML config part of 'myhost'
         cat hosts_config.yaml | %(exname)s get-value cfgs.myhost

    """ % {"exname": EXNAME, "usage": USAGE}

    USAGE = textwrap.dedent(USAGE)
    HELP = textwrap.dedent(HELP)

    opts = _parse_args(args, USAGE, HELP)
    quiet = opts.pop("quiet")

    try:
        first = True
        for output in do(stream=sys.stdin, **opts):
            if first:
                first = False
            else:
                if opts["action"] not in ACTION_SUPPORTING_STREAMING:
                    die("Source YAML is multi-document, "
                        "which doesn't support any other action than %s"
                        % ", ".join(ACTION_SUPPORTING_STREAMING))
                if opts["dump"] is yaml_dump:
                    print("---\n", end="")
                else:
                    print("\0", end="")
                if opts.get("loader") is LineLoader:
                    sys.stdout.flush()

            print(output, end="")
            if opts.get("loader") is LineLoader:
                sys.stdout.flush()
    except (InvalidPath, ActionTypeError) as e:
        if quiet:
            exit(1)
        else:
            die(str(e))
    except InvalidAction as e:
        die("Invalid argument.\n%s" % USAGE)


def entrypoint():
    sys.exit(main(sys.argv[1:]))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
