#!/usr/bin/env python

##
## You can download latest version of this file:
##  $ wget https://gist.github.com/vaab/e0eae9607ae806b662d4/raw -O setup.py
##  $ chmod +x setup.py
##
## This setup.py is meant to be run along with ``./autogen.sh`` that
## you can also find here: https://gist.github.com/vaab/9118087/raw
##

from setuptools import setup

##
## Ensure that ``./autogen.sh`` is run prior to using ``setup.py``
##

if "%%short-version%%".startswith("%%"):
    import os.path
    import sys
    WIN32 = sys.platform == 'win32'
    autogen = os.path.join(".", "autogen.sh")
    if not os.path.exists(autogen):
        sys.stderr.write(
            "This source repository was not configured.\n"
            "Please ensure ``./autogen.sh`` exists and that you are running "
            "``setup.py`` from the project root directory.\n")
        sys.exit(1)
    if os.path.exists('.autogen.sh.output'):
        sys.stderr.write(
            "It seems that ``./autogen.sh`` couldn't do its job as expected.\n"
            "Please try to launch ``./autogen.sh`` manualy, and send the "
            "results to the\nmaintainer of this package.\n"
            "Package will not be installed !\n")
        sys.exit(1)
    sys.stderr.write("Missing version information: "
                     "running './autogen.sh'...\n")
    import os
    import subprocess
    os.system('%s%s > .autogen.sh.output'
              % ("bash " if WIN32 else "",
                 autogen))
    cmdline = sys.argv[:]
    if cmdline[0] == "-c":
        ## for some reason, this is needed when launched from pip
        cmdline[0] = "setup.py"
    errlvl = subprocess.call(["python", ] + cmdline)
    os.unlink(".autogen.sh.output")
    sys.exit(errlvl)


##
## Normal d2to1 setup
##

setup(
    setup_requires=['d2to1'],
    extras_require={'test': [
        "docshtest==0.0.3",
        ]},
    d2to1=True
)
