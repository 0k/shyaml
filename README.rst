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

You don't need to download the GIT version of the code as ``shyaml`` is
available on the PyPI. So you should be able to run::

    pip install shyaml

If you have downloaded the GIT sources, then you could add install
the current version via traditional::

    python setup.py install

And if you don't have the GIT sources but would like to get the latest
master or branch from github, you could also::

    pip install git+https://github.com/0k/shyaml

Or even select a specific revision (branch/tag/commit)::

    pip install git+https://github.com/0k/shyaml@master


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
    subvalue.how-much
    subvalue
    subvalue.how-much\.more
    name
    subvalue.how-much\more

Iteration through keys only (\0 terminated strings)::

    $ cat test.yaml | shyaml keys-0 subvalue | xargs -0 -n 1 echo "VALUE:"
    VALUE: how-much
    VALUE: things
    VALUE: how-many
    VALUE: maintainer
    VALUE: description

Iteration through values only (\0 terminated string highly recommended)::

    $ cat test.yaml | shyaml values-0 subvalue |
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

Iteration through keys and values (\0 terminated string highly recommended)::

    $ read-0() {
        while [ "$1" ]; do
            IFS=$'\0' read -r -d '' "$1" || return 1
            shift
        done
      }

    $ cat test.yaml | shyaml key-values-0 subvalue |
      while read-0 key value; do
          echo "KEY: '$key'"
          echo "VALUE: '$value'"
          echo
      done
    KEY: 'how-much'
    VALUE: '1.1'

    KEY: 'things'
    VALUE: '- first
    - second
    - third
    '

    KEY: 'how-many'
    VALUE: '2'

    KEY: 'maintainer'
    VALUE: 'Valentin Lab'

    KEY: 'description'
    VALUE: 'Multiline description:
    Line 1
    Line 2
    '

Notice, that you'll get the same result using
``get-values``. ``get-values`` will support sequences and struct,
and ``key-values`` support only struct. (for a complete table of
which function support what you can look at the usage line)

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
   Error: invalid path 'subvalue.things.5', index 5 is out of range (3 elements in sequence).

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

    $ cat test.yaml | shyaml get-values-0 subvalue |
      while IFS='' read -r -d '' key &&
            IFS='' read -r -d '' value; do
          echo "'$key' -> '$value'"
      done
    'how-much' -> '1.1'
    'things' -> '- first
    - second
    - third
    '
    'how-many' -> '2'
    'maintainer' -> 'Valentin Lab'
    'description' -> 'Multiline description:
    Line 1
    Line 2
    '

Please note that, if ``get-values{,-0}`` actually works on ``struct``,
it's maybe more explicit to use the equivalent ``key-values{,0}``. It
should be noted that ``key-values{,0}`` is not completly equivalent as
it is meant to be used with ``struct`` only and will complain if not.

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


Default Value
-------------

There is a third argument on the command line of shyaml which is the
DEFAULT argument. If the given KEY was not found in the YAML
structure, then ``shyaml`` would return what you provided as DEFAULT.

As of version < 0.3, this argument was defaulted to the empty
string. For all version above 0.3 (included), if not provided, then
an error message will be printed::

   $ echo "a: 3" | shyaml get-value a mydefault
   3

   $ echo "a: 3" | shyaml get-value b mydefault
   mydefault

   $ echo "a: 3" | shyaml get-value b
   Error: invalid path 'b', missing key 'b' in struct.


You can emulate pre v0.3 behavior by specifying explicitely an empty
string as third argument::

   $ echo "a: 3" | shyaml get-value b ''
   $


Ordered mappings
----------------

Currently, using ``shyaml`` in a shell script involves happily taking
YAML inputs and outputting YAML outputs that will further be processed.

And this works very well.

Before version ``0.4.0``, ``shyaml`` would boldly re-order (sorting them
alphabetically) the keys in mappings. If this should be considered
harmless per specification (mappings are indeed supposed to be
unordered, this means order does not matter), in practical, YAML users
could feel wronged by ``shyaml`` when there YAML got mangled and they
wanted to give a meaning to the basic YAML mapping.

Who am I to forbid such usage of YAML mappings ? So starting from
version ``0.4.0``, ``shyaml`` will happily keep the order of your
mappings::

    cat <<EOF > /tmp/test.yml
    mapping:
      a: 1
      c: 2
      b: 3
    EOF

For ``shyaml`` version before ``0.4.0``::

    $ shyaml get-value mapping < test.yml
    a: 1
    b: 3
    c: 2

For ``shyaml`` version including and after ``0.4.0``::

    $ shyaml get-value mapping < test.yml
    a: 1
    c: 2
    b: 3


Usage string
------------

A quick reminder of what is available::

    $ shyaml --help
    Parses and output chosen subpart or values from YAML input.
    It reads YAML in stdin and will output on stdout it's return value.

    Usage:

        shyaml ACTION KEY [DEFAULT]

    Options:

        ACTION    Depending on the type of data you've targetted
                  thanks to the KEY, ACTION can be:

                  These ACTIONs applies to any YAML type:

                    get-type          ## returns a short string
                    get-value         ## returns YAML

                  This ACTION applies to 'sequence' and 'struct' YAML type:

                    get-values{,-0}   ## return list of YAML

                  These ACTION applies to 'struct' YAML type:

                    keys{,-0}         ## return list of YAML
                    values{,-0}       ## return list of YAML
                    key-values,{,-0}  ## return list of YAML

                  Note that any value returned is returned on stdout, and
                  when returning ``list of YAML``, it'll be separated by
                  ``\n`` or ``NUL`` char depending of you've used the
                  ``-0`` suffixed ACTION.

        KEY       Identifier to browse and target subvalues into YAML
                  structure. Use ``.`` to parse a subvalue. If you need
                  to use a literal ``.`` or ``\``, use ``\`` to quote it.

                  Use struct keyword to browse ``struct`` YAML data and use
                  integers to browse ``sequence`` YAML data.

        DEFAULT   if not provided and given KEY do not match any value in
                  the provided YAML, then DEFAULT will be returned. If no
                  default is provided and the KEY do not match any value
                  in the provided YAML, shyaml will fail with an error
                  message.

    Examples:

         ## get last grocery
         cat recipe.yaml       | shyaml get-value groceries.-1

         ## get all words of my french dictionary
         cat dictionaries.yaml | shyaml keys-0 french.dictionary

         ## get YAML config part of 'myhost'
         cat hosts_config.yaml | shyaml get-value cfgs.myhost


Contributing
============

Any suggestion or issue is welcome. Push request are very welcome,
please check out the guidelines.


Push Request Guidelines
-----------------------

You can send any code. I'll look at it and will integrate it myself in
the code base and leave you as the author. This process can take time and
it'll take less time if you follow the following guidelines:

- check your code with PEP8 or pylint. Try to stick to 80 columns wide.
- separate your commits per smallest concern.
- each commit should pass the tests (to allow easy bisect)
- each functionality/bugfix commit should contain the code, tests,
  and doc.
- prior minor commit with typographic or code cosmetic changes are
  very welcome. These should be tagged in their commit summary with
  ``!minor``.
- the commit message should follow gitchangelog rules (check the git
  log to get examples)
- if the commit fixes an issue or finished the implementation of a
  feature, please mention it in the summary.

If you have some questions about guidelines which is not answered here,
please check the current ``git log``, you might find previous commit that
would show you how to deal with your issue.


License
=======

Copyright (c) 2015 Valentin Lab.

Licensed under the `BSD License`_.

.. _BSD License: http://raw.github.com/0k/shyaml/master/LICENSE
