=================================
SHYAML: YAML for the command line
=================================

.. image:: https://pypip.in/v/shyaml/badge.png
    :target: https://pypi.python.org/pypi/shyaml

.. image:: https://secure.travis-ci.org/0k/shyaml.png?branch=master
    :target: http://travis-ci.org/0k/shyaml

Description
===========

Simple scripts that allow read access to YAML files through command line.

This can be handy, if you want to get access to YAML data in your shell
scripts.

This scripts supports only read access and it might not support all
the subtilties of YAML specification. But it should support some handy
basic query of YAML file.


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
    subvalue.how-much: 1.2
    subvalue.how-much\more: 1.3
    subvalue.how-much\.more: 1.4
    EOF


General browsing struct and displaying simple values
----------------------------------------------------

Simple query of simple attribute::

    $ cat test.yaml | shyaml get-value name
    MyName !!

Query nested attributes by using '.' between key labels::

    $ cat test.yaml | shyaml get-value subvalue.how-much
    1.1

Get type of attributes::

    $ cat test.yaml | shyaml get-type name
    str
    $ cat test.yaml | shyaml get-type subvalue.how-much
    float


Parse structure
---------------

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

Iteration through keys only::

    $ cat test.yaml | shyaml keys
    subvalue
    name

Iteration through keys only (\0 terminated strings)::

    $ cat test.yaml | shyaml keys-0 subvalue | xargs -0 -n 1 echo "VALUE:"
    VALUE: how-much
    VALUE: things
    VALUE: how-many
    VALUE: maintainer
    VALUE: description

Iteration though values only (\0 terminated string highly recommended)::

    $ cat test.yaml | shyaml values-0 | \
      while read -r -d $'\0' value; do
          echo "RECEIVED: '$value'"
      done
    RECEIVED: '1.1'
    RECEIVED: '- first
    - second
    - third'
    RECEIVED: '2'
    RECEIVED: 'Valentin Lab'
    RECEIVED: 'Multiline description:
    Line 1
    Line 2'


Parse sequence
--------------

Query a sequence with ``get-value``::

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

More usefull, parse a list in one go with ``get-values``::

   $ cat test.yaml | shyaml get-values subvalue.things
   first
   second
   third

Note that the action is called ``get-values``, and that output is separated by
``\n`` chars, this can bring havoc if you are parsing values containing this
character. Hopefully, ``shyaml`` has a ``get-values-0`` to terminate strings by
``\0`` char, which allows complete support of any type of values, including
YAML.  ``get-values`` outputs key and values for ``struct`` types and only
values for ``sequence`` types::

    $ cat test.yaml | shyaml get-values-0 subvalue | \
      while read -r -d $'\0' key value; do
          echo "'$key' -> '$value'"
      done
    'how-much' -> '1.1'
    'things' -> '- first
    - second
    - third'
    'how-many' -> '2'
    'maintainer' -> 'Valentin Lab'
    'description' -> 'Multiline description:
    Line 1
    Line 2'

You should also notice that values that are displayed are YAML compatible. So
if they are complex, you can re-use ``shyaml`` on them to parse their content.


Keys containing '.'
-------------------

Use and ``\\`` to access keys with ``\`` and ``\.`` to access keys
with literal ``.`` in them. Just be mindful of shell escaping (example
uses single quotes)::

    $ cat test.yaml | shyaml get-value 'subvalue\.how-much'
    1.2
    $ cat test.yaml | shyaml get-value 'subvalue\.how-much\\more'
    1.3
    $ cat test.yaml | shyaml get-value 'subvalue\.how-much\\.more' default
    default

This last one didn't escape correctly the last ``.``, this is the
correct version::

    $ cat test.yaml | shyaml get-value 'subvalue\.how-much\\\.more' default
    1.4


empty string keys
-----------------

Yep, ``shyaml`` supports empty stringed keys. You might never have use
for this one, but it's in YAML specification. So ``shyaml`` supports
it::

    $ cat <<EOF > test.yaml
    empty-sub-key:
        "":
           a: foo
           "": bar
    "": wiz
    EOF

    $ cat test.yaml | shyaml get-value empty-sub-key..
    bar
    $ cat test.yaml | shyaml get-value ''
    wiz

Please notice that one empty string is different than no string at all::

    $ cat <<EOF > test.yaml
    "":
       a: foo
       b: bar
    "x": wiz
    EOF
    $ cat test.yaml | shyaml keys

    x
    $ cat test.yaml | shyaml keys ''
    a
    b

The first asks for keys of the root YAML, the second asks for keys of the
content of the empty string named element located in the root YAML.


Usage string
------------

A Quick remainder of what is available::

    $ shyaml
    usage:
        shyaml {get-value{,-0},get-type,keys{,-0},values{,-0}} KEY DEFAULT

