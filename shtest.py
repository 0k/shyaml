#!/usr/bin/env python
"""Shell Doctest

First naive implementation, will probably have to move this
into its own project.


Major concerns and shortcomings that prevents it to be a serious project:
- end of blocks and final "\n" are not tested correctly
- tests execution in current directory with possible consequences.
- no support of checking errlvl
- no support of proper mixed err and stdout content
- limited to ``bash`` testing

Minor concerns, but would be better without:
- fail on first error hardwritten.
- hardwritten support of "<BLANKLINE>"

Possible evolution:
- support of python file (by extracting docs before)
- integration in nosetests ? is it possible ?
- colorize output ?
- move to standalone full fledged program ?
- coverage integration ?

"""

from __future__ import print_function


import re
import sys
import os.path
import subprocess
import difflib
import threading


try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x


PY3 = sys.version_info[0] >= 3
WIN32 = sys.platform == 'win32'

EXNAME = os.path.basename(__file__ if WIN32 else sys.argv[0])

for ext in (".py", ".pyc", ".exe", "-script.py", "-script.pyc"):
    if EXNAME.endswith(ext):
        EXNAME = EXNAME[:-len(ext)]
        break


USAGE = """\
Usage:

    %(exname)s (-h|--help)
    %(exname)s [[-r|--regex REGEX] ...] SHTESTFILE
""" % {"exname": EXNAME}


HELP = """\

%(exname)s - parse file and run shell doctests

%(usage)s

Options:

    -r REGEX, --regex REGEX
              Will apply this regex to the lines to be executed. You
              can have more than one patterns by re-using this options
              as many times as wanted. Regexps will be applied one by one
              in the same order than they are provided on the command line.


Examples:

     ## run tests but replace executable on-the-fly for coverage support
     shtest README.rst -r '/\\bshyaml\\b/coverage run shyaml.py/'

""" % {"exname": EXNAME, "usage": USAGE}


## command line quoting
cmd_line_quote = (lambda e: e.replace('\\', '\\\\')) if WIN32 else (lambda e: e)


##
## Helpers coming from othe projects
##


## XXXvlab: code comes from kids.txt.diff
def udiff(a, b, fa="", fb=""):
    if not a.endswith("\n"):
        a += "\n"
    if not b.endswith("\n"):
        b += "\n"
    return "".join(
        difflib.unified_diff(
            a.splitlines(1), b.splitlines(1),
            fa, fb))


## XXXvlab: code comes from ``kids.sh``
ON_POSIX = 'posix' in sys.builtin_module_names


## XXXvlab: code comes from ``kids.txt``
## Note that a quite equivalent function was added to textwrap in python 3.3
def indent(text, prefix="  ", first=None):
    if first is not None:
        first_line = text.split("\n")[0]
        rest = '\n'.join(text.split("\n")[1:])
        return '\n'.join([first + first_line,
                          indent(rest, prefix=prefix)])
    return '\n'.join([prefix + line
                      for line in text.split('\n')])


## XXXvlab: consider for inclusion in ``kids.sh``
def cmd_iter(cmd, encoding="utf-8"):
    """Asynchrone subprocess driver

    returns an iterator that yields events of the life of the
    process.

    """

    def thread_enqueue(label, f, q):
        t = threading.Thread(target=enqueue_output, args=(label, f, q))
        t.daemon = True  ## thread dies with the program
        t.start()
        return t

    decode = (lambda s: s) if PY3 else (lambda s: s.decode(encoding))

    def enqueue_output(label, out, queue):
        for line in iter(out.readline, '' if PY3 else b''):
            # print("%s: %s" % (label, chomp(line)))
            queue.put((label, decode(line)))
        # print("END of %s" % (label, ))
        out.close()

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=ON_POSIX,
        shell=False,
        universal_newlines=True,
        env=None)
    proc.stdin.close()
    q = Queue()
    t1 = thread_enqueue("out", proc.stdout, q)
    t2 = thread_enqueue("err", proc.stderr, q)
    running = True
    while True:
        try:
            yield q.get(True, 0.001)
        except Empty:
            if not running:
                break
            proc.poll()
            running = proc.returncode is None or \
                      any(t.is_alive() for t in (t1, t2))

    yield "errorlevel", proc.returncode


## XXXvlab: consider for inclusion in ``kids.txt``
def chomp(s):
    if len(s):
        lines = s.splitlines(True)
        last = lines.pop()
        return ''.join(lines + last.splitlines())
    else:
        return ''


def get_docshtest_blocks(lines):
    """Returns an iterator of shelltest blocks from an iterator of lines"""

    block = []
    consecutive_empty = 0
    for line_nb, line in enumerate(lines):
        is_empty_line = not line.strip()
        if not is_empty_line:
            if not line.startswith("    "):
                if block:
                    yield block[:-consecutive_empty] if consecutive_empty else block
                    block = []
                continue
            else:
                line = line[4:]
        if line.startswith("$ ") or block:
            if line.startswith("$ "):
                line = line[2:]
                if block:
                    yield block[:-consecutive_empty] if consecutive_empty else block
                    block = []
            if is_empty_line:
                consecutive_empty += 1
            else:
                consecutive_empty = 0
            block.append((line_nb + 1, line))


def valid_syntax(command):
    """Check if shell command if complete"""

    for ev, value in cmd_iter(["bash", "-n", "-c", cmd_line_quote(command)]):
        if ev == "err":
            if value.endswith("syntax error: unexpected end of file"):
                return False
            if "unexpected EOF while looking for matching" in value:
                return False
            if "here-document at line" in value:
                return False
    return value == 0


class UnmatchedLine(Exception):

    def __init__(self, *args):
        self.args = args


def run_and_check(command, expected_output):
    expected_output = expected_output.replace("<BLANKLINE>\n", "\n")
    orig_expected_output = expected_output
    output = ""
    diff = False
    for ev, value in cmd_iter(["bash", "-c", cmd_line_quote(command)]):
        if ev in ("err", "out"):
            output += value
            if not diff and expected_output.startswith(value):
                expected_output = expected_output[len(value):]
            else:
                diff = True
    if not diff and len(chomp(expected_output)):
        diff = True

    if diff:
        raise UnmatchedLine(output, orig_expected_output)
    return value == 0


def format_failed_test(message, command, output, expected):
    formatted = []
    if "\n" in command:
        formatted.append("command:\n%s" % indent(command, "| "))
    else:
        formatted.append("command: %r" % command)
    formatted.append("expected:\n%s" % indent(expected, "| "))
    formatted.append("output:\n%s" % indent(output, "| "))
    if len(expected.splitlines() + output.splitlines()) > 10:
        formatted.append("diff:\n%s" % udiff(expected, output, "expected", "output"))

    formatted = '\n'.join(formatted)

    return "%s\n%s" % (message, indent(formatted, prefix="  "))


def apply_regex(patterns, s):
    for p in patterns:
        s = re.sub(p[0], p[1], s)
    return s


def shtest_runner(lines, regex_patterns):
    for block_nb, block in enumerate(get_docshtest_blocks(lines)):
        lines = iter(block)
        command_block = ""
        start_line_nb = None
        stop_line_nb = None
        for line_nb, line in lines:
            start_line_nb = start_line_nb or line_nb
            command_block += line
            if valid_syntax(apply_regex(regex_patterns,
                                        command_block)):
                stop_line_nb = line_nb
                break
        else:
            raise ValueError("Invalid Block:\n%s" % (indent(command_block, "   | ")))
        command_block = command_block.rstrip("\n\r")
        command_block = apply_regex(regex_patterns, command_block)
        try:
            run_and_check(command_block, "".join(line for _, line in lines))
        except UnmatchedLine as e:
            print(format_failed_test(
                "shtest %d - failure (line %s):"
                % (block_nb + 1,
                   ("%s-%s" % (start_line_nb, stop_line_nb))
                   if start_line_nb != stop_line_nb else
                   start_line_nb),
                command_block,
                e.args[0],
                e.args[1]))
            exit(1)
        print("shtest %d - success (line %s)."
              % (block_nb + 1,
                 ("%s-%s" % (start_line_nb, stop_line_nb))
                 if start_line_nb != stop_line_nb else
                 start_line_nb))


def split_quote(s, split_char='/', quote='\\'):
    r"""Split args separated by char, possibily quoted with quote char


        >>> tuple(split_sep_args('/pattern/replace/'))
        ('', 'pattern', 'replace', '')

        >>> tuple(split_sep_args('/pat\/tern/replace/'))
        ('', 'pat/tern', 'replace', '')

        >>> tuple(split_sep_args('/pat\/ter\n/replace/'))
        ('', 'pat/ter\n', 'replace', '')

    """

    buf = ""
    parse_str = iter(s)
    for char in parse_str:
        if char == split_char:
            yield buf
            buf = ""
            continue
        if char == quote:
            char = next(parse_str)
            if char != split_char:
                buf += quote
        buf += char
    yield buf


if __name__ == "__main__":
    args = sys.argv[1:]

    pattern = None
    if any(arg in args for arg in ["-h", "--help"]) or \
           len(args) == 0:
        print(HELP)
        exit(0)

    patterns = []
    for arg in ["-r", "--regex"]:
        while arg in args:
            idx = args.index(arg)
            pattern = args[idx + 1]
            del args[idx + 1]
            del args[idx]
            if re.match('^[a-zA-Z1-9]$', pattern[0]):
                print("Error: regex %s should start with a delimiter char, "
                      "not an alphanumerical char." % pattern)
                print(USAGE)
                exit(1)
            parts = tuple(split_quote(pattern, split_char=pattern[0]))
            if not (parts[0] == parts[-1] == ''):
                print("Error: regex should start and end with a delimiter char.")
                exit(1)
            parts = parts[1:-1]
            if len(parts) > 2:
                print("Error: Found too many delimiter char.")
                exit(1)
            patterns.append(parts)

    if len(args) == 0:
        print("Error: please provide a rst filename as argument.")
        exit(1)
    filename = args[0]
    if not os.path.exists(filename):
        print("Error: file %r doesn't exists." % filename)
        exit(1)
    shtest_runner(open(filename), regex_patterns=patterns)
