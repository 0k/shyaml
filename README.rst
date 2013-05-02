=================================
SHYAML: YAML for the command line
=================================


Disclaimer
==========

This scripts was written very quickly and will not support all YAML
manipulation that you could have dreamed of. But it should support
some handy basic query of YAML file.

Please take a look at the next section to get a quick overview of
``shyaml`` capabilities.


Description
===========

Simple scripts that allow read access to YAML files through command line.

This can be handy, if you want to get access to YAML data in your shell
scripts.


Installation
============

This script could be used out of the box, take the ``shyaml`` file and use it
directly.

If you want to use the distribution method I've chosen, which is ``distutils2``,
please first make sure you have ``distutils2``, in which case you could do a::

    pysetup install shyaml

It should be compatible with older distribution method, so this should also
work::

    pip install shyaml

Please note that if you got the code thanks to git. You'll need to execute
``./autogen.sh`` in order to generate missing files as the ``CHANGELOG.rst``
and the ``setup.py``. Then you can choose to directly use the ``shyaml``
binary, or install it thanks to classical ``pysetup install``
(or ``python setup.py``).


Usage
=====

``shyaml`` takes its YAML input file from standard input ONLY. So there are
some sample routine:

Let's create a sample yaml file::

    $ cat <<EOF > test.yaml
    name: "MyName !!"
    subvalue:
        how-much: 1.1
        how-many: 2
        things:
            - first
            - second
            - third
        maintainer: "Valentin Lab"
        description: |
            Multiline description:
            Line 1
            Line 2
    EOF

Simple query of simple attribute::

    $ cat test.yaml | shyaml get-value name
    MyName !!

Query nested attributes::

    $ cat test.yaml | shyaml get-value subvalue.how-much
    1.1

Get type of attributes::

    $ cat test.yaml | shyaml get-type name
    str
    $ cat test.yaml | shyaml get-value subvalue.how-much
    float

Get sub YAML from a structure attribute::

    $ cat test.yaml | shyaml get-type subvalue
    struct
    $ cat test.yaml | shyaml get-value subvalue
    description: 'Multiline description:

      Line 1

      Line 2

      '
    how-many: 2
    how-much: 1.1
    maintainer: Valentin Lab
    things:
    - first
    - second
    - third

Query a list::

   $ cat test.yaml | shyaml get-value subvalue.things
   - first
   - second
   - third
   $ cat test.yaml | shyaml get-value subvalue.things.0
   first
   $ cat test.yaml | shyaml get-value subvalue.things.-1
   third
   $ cat test.yaml | shyaml get-value subvalue.things.5
   Error: list index error in path 'subvalue.things.5'.

Useless fun::

    $ cat test.yaml | shyaml get-value subvalue | shyaml get-value things
    - first
    - second
    - third

A Quick remainder of what is available::

    $ shyaml
    usage:
        shyaml get-value KEY
        shyaml get-type KEY
        shyaml keys

