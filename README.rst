=================================
SHYAML: YAML for the command line
=================================

.. image:: https://img.shields.io/pypi/v/shyaml.svg
    :target: https://pypi.python.org/pypi/shyaml

.. image:: https://img.shields.io/travis/0k/shyaml/master.svg?style=flat
   :target: https://travis-ci.org/0k/shyaml/
   :alt: Travis CI build status

.. image:: https://img.shields.io/appveyor/ci/vaab/shyaml.svg
   :target: https://ci.appveyor.com/project/vaab/shyaml/branch/master
   :alt: Appveyor CI build status

.. image:: http://img.shields.io/codecov/c/github/0k/shyaml.svg?style=flat
   :target: https://codecov.io/gh/0k/shyaml/
   :alt: Test coverage



Description
===========

Simple script that allow read access to YAML files through command line.

This can be handy, if you want to get access to YAML data in your shell
scripts.

This script supports only read access and it might not support all
the subtleties of YAML specification. But it should support some handy
basic query of YAML file.


Requirements
============

``shyaml`` works in Linux, MacOSX, and Windows with python 2.7 and 3+.


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

On macOS, you can also install the latest release version via `Homebrew
<https://github.com/Homebrew/brew/>`_::

    brew install shyaml

Or to install the master branch::

    brew install shyaml --HEAD


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

Get length of structures or sequences::

    $ cat test.yaml | shyaml get-length subvalue
    5
    $ cat test.yaml | shyaml get-length subvalue.things
    3

But this won't work on other types::

    $ cat test.yaml | shyaml get-length name
    Error: get-length does not support 'str' type. Please provide or select a sequence or struct.


Parse structure
---------------

Get sub YAML from a structure attribute::

    $ cat test.yaml | shyaml get-type subvalue
    struct
    $ cat test.yaml | shyaml get-value subvalue
    how-much: 1.1
    how-many: 2
    things:
    - first
    - second
    - third
    maintainer: Valentin Lab
    description: 'Multiline description:

      Line 1

      Line 2

      '

Iteration through keys only::

    $ cat test.yaml | shyaml keys
    name
    subvalue
    subvalue.how-much
    subvalue.how-much\more
    subvalue.how-much\.more

Iteration through keys only (``\0`` terminated strings)::

    $ cat test.yaml | shyaml keys-0 subvalue | xargs -0 -n 1 echo "VALUE:"
    VALUE: how-much
    VALUE: how-many
    VALUE: things
    VALUE: maintainer
    VALUE: description

Iteration through values only (``\0`` terminated string highly recommended)::

    $ cat test.yaml | shyaml values-0 subvalue |
      while IFS='' read -r -d $'\0' value; do
          echo "RECEIVED: '$value'"
      done
    RECEIVED: '1.1'
    RECEIVED: '2'
    RECEIVED: '- first
    - second
    - third
    '
    RECEIVED: 'Valentin Lab'
    RECEIVED: 'Multiline description:
    Line 1
    Line 2
    '

Iteration through keys and values (``\0`` terminated string highly recommended)::

    $ read-0() {
        while [ "$1" ]; do
            IFS=$'\0' read -r -d '' "$1" || return 1
            shift
        done
      } &&
      cat test.yaml | shyaml key-values-0 subvalue |
      while read-0 key value; do
          echo "KEY: '$key'"
          echo "VALUE: '$value'"
          echo
      done
    KEY: 'how-much'
    VALUE: '1.1'

    KEY: 'how-many'
    VALUE: '2'

    KEY: 'things'
    VALUE: '- first
    - second
    - third
    '

    KEY: 'maintainer'
    VALUE: 'Valentin Lab'

    KEY: 'description'
    VALUE: 'Multiline description:
    Line 1
    Line 2
    '
    <BLANKLINE>

Notice, that you'll get the same result using
``get-values``. ``get-values`` will support sequences and struct,
and ``key-values`` support only struct. (for a complete table of
which function support what you can look at the usage line)

And, if you ask for keys, values, key-values on non struct like, you'll
get an error::

    $ cat test.yaml | shyaml keys name
    Error: keys does not support 'str' type. Please provide or select a struct.
    $ cat test.yaml | shyaml values subvalue.how-many
    Error: values does not support 'int' type. Please provide or select a struct.
    $ cat test.yaml | shyaml key-values subvalue.how-much
    Error: key-values does not support 'float' type. Please provide or select a struct.


Parse sequence
--------------

Query a sequence with ``get-value``::

    $ cat test.yaml | shyaml get-value subvalue.things
    - first
    - second
    - third

And access individual elements with python-like indexing::

    $ cat test.yaml | shyaml get-value subvalue.things.0
    first
    $ cat test.yaml | shyaml get-value subvalue.things.-1
    third
    $ cat test.yaml | shyaml get-value subvalue.things.5
    Error: invalid path 'subvalue.things.5', index 5 is out of range (3 elements in sequence).

Note that this will work only with integer (preceded or not by a minus
sign)::

    $ cat test.yaml | shyaml get-value subvalue.things.foo
    Error: invalid path 'subvalue.things.foo', non-integer index 'foo' provided on a sequence.

More usefull, parse a list in one go with ``get-values``::

    $ cat test.yaml | shyaml get-values subvalue.things
    first
    second
    third

Note that the action is called ``get-values``, and that output is
separated by newline char(s) (which is os dependent), this can bring
havoc if you are parsing values containing newlines itself. Hopefully,
``shyaml`` has a ``get-values-0`` to terminate strings by ``\0`` char,
which allows complete support of any type of values, including YAML.
``get-values`` outputs key and values for ``struct`` types and only
values for ``sequence`` types::

    $ cat test.yaml | shyaml get-values-0 subvalue |
      while IFS='' read -r -d '' key &&
            IFS='' read -r -d '' value; do
          echo "'$key' -> '$value'"
      done
    'how-much' -> '1.1'
    'how-many' -> '2'
    'things' -> '- first
    - second
    - third
    '
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

Of course, ``get-values`` should only be called on sequence elements::

    $ cat test.yaml | shyaml get-values name
    Error: get-values does not support 'str' type. Please provide or select a sequence or struct.


Parse YAML document streams
---------------------------

YAML input can be a stream of documents, the action will then be
applied to each document::

    $ i=0; while true; do
          ((i++))
          echo "ingests:"
          echo " - data: xxx"
          echo "   id: tag-$i"
          if ((i >= 3)); then
              break
          fi
          echo "---"
    done | shyaml get-value ingests.0.id | tr '\0' '&'
    tag-1&tag-2&tag-3


Notice that ``NUL`` char is used by default for separating output
iterations if not used in ``-y`` mode. You can use that to separate
each output.  ``-y`` mode will use conventional YAML way to separate
documents (which is ``---``).

So::

    $ i=0; while true; do
          ((i++))
          echo "ingests:"
          echo " - data: xxx"
          echo "   id: tag-$i"
          if ((i >= 3)); then
              break
          fi
          echo "---"
    done | shyaml get-value -y ingests.0.id
    tag-1
    ...
    ---
    tag-2
    ...
    ---
    tag-3
    ...

Notice that it is not supported to use any query that can output more than one
value (like all the query that can be suffixed with ``*-0``) with a multi-document
YAML::

    $ i=0; while true; do
          ((i++))
          echo "ingests:"
          echo " - data: xxx"
          echo "   id: tag-$i"
          if ((i >= 3)); then
              break
          fi
          echo "---"
    done | shyaml keys ingests.0 | tr '\0' '&'
    Error: Source YAML is multi-document, which doesn't support any other action than get-type, get-length, get-value
    data
    id

You'll probably notice also, that output seems buffered. The previous
content is displayed as a whole only at the end. If you need a
continuous flow of YAML document, then the command line option ``-L``
is required to force a non-buffered line-by-line reading of the file
so as to ensure that each document is properly parsed as soon as
possible. That means as soon as either a YAML document end is detected
(``---`` or ``EOF``):

Without the ``-L``, if we kill our shyaml process before the end::

    $ i=0; while true; do
          ((i++))
          echo "ingests:"
          echo " - data: xxx"
          echo "   id: tag-$i"
          if ((i >= 2)); then
              break
          fi
          echo "---"
          sleep 10
    done 2>/dev/null | shyaml get-value ingests.0.id & pid=$! ; sleep 2; kill $pid


With the ``-L``, if we kill our shyaml process before the end::

    $ i=0; while true; do
          ((i++))
          echo "ingests:"
          echo " - data: xxx"
          echo "   id: tag-$i"
          if ((i >= 2)); then
              break
          fi
          echo "---"
          sleep 10
    done 2>/dev/null | shyaml get-value -L ingests.0.id & pid=$! ; sleep 2; kill $pid
    tag-1


Using ``-y`` is required to force a YAML output that will be also parseable as a stream,
which could help you chain shyaml calls::

    $ i=0; while true; do
          ((i++))
          echo "ingests:"
          echo " - data: xxx"
          echo "   id: tag-$i"
          if ((i >= 3)); then
              break
          fi
          echo "---"
          sleep 0.2
    done | shyaml get-value ingests.0 -L -y | shyaml get-value id | tr '\0' '\n'
    tag-1
    tag-2
    tag-3


An empty string will be still considered as an empty YAML document::

    $ echo | shyaml get-value "toto"
    Error: invalid path 'toto', can't query subvalue 'toto' of a leaf (leaf value is None).


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


Handling missing paths
----------------------

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

Starting with version 0.6, you can also use the ``-q`` or ``--quiet`` to fail
silently in case of KEY not found in the YAML structure::

    $ echo "a: 3" | shyaml -q get-value b; echo "errlvl: $?"
    errlvl: 1
    $ echo "a: 3" | shyaml -q get-value a; echo "errlvl: $?"
    3errlvl: 0


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

    $ cat <<EOF > test.yaml
    mapping:
      a: 1
      c: 2
      b: 3
    EOF

For ``shyaml`` version before ``0.4.0``::

    # shyaml get-value mapping < test.yaml
    a: 1
    b: 3
    c: 2

For ``shyaml`` version including and after ``0.4.0``::

    $ shyaml get-value mapping < test.yaml
    a: 1
    c: 2
    b: 3


Strict YAML for further processing
----------------------------------

Processing yaml can be done recursively and extensively through using
the output of ``shyaml`` into ``shyaml``. Most of its output is itself
YAML. Most ? Well, for ease of use, literal keys (string, numbers) are
outputed directly without YAML quotes, which is often convenient.

But this has the consequence of introducing inconsistent behavior. So
when processing YAML coming out of shyaml, you should probably think
about using the ``--yaml`` (or ``-y``) option to output only strict YAML.

With the drawback that when you'll want to output string, you'll need to
call a last time ``shyaml get-value`` to explicitely unquote the YAML.


Object Tag
----------

YAML spec allows object tags which allows you to map local data to
objects in your application.

When using ``shyaml``, we do not want to mess with these tags, but still
allow parsing their internal structure.

``get-type`` will correctly give you the type of the object::

    $ cat <<EOF > test.yaml
    %TAG !e! tag:example.com,2000:app/
    ---
    - !e!foo "bar"
    EOF

    $ shyaml get-type 0 < test.yaml
    tag:example.com,2000:app/foo

``get-value`` with ``-y`` (see section Strict YAML) will give you the
complete yaml tagged value::

    $ shyaml get-value -y 0 < test.yaml
    !<tag:example.com,2000:app/foo> 'bar'


Another example::

    $ cat <<EOF > test.yaml
    %TAG ! tag:clarkevans.com,2002:
    --- !shape
      # Use the ! handle for presenting
      # tag:clarkevans.com,2002:circle
    - !circle
      center: &ORIGIN {x: 73, y: 129}
      radius: 7
    - !line
      start: *ORIGIN
      finish: { x: 89, y: 102 }
    - !label
      start: *ORIGIN
      color: 0xFFEEBB
      text: Pretty vector drawing.
    EOF
    $ shyaml get-type 2 < test.yaml
    tag:clarkevans.com,2002:label

And you can still traverse internal value::

    $ shyaml get-value -y 2.start < test.yaml
    x: 73
    y: 129


Note that all global tags will be resolved and simplified (as
``!!map``, ``!!str``, ``!!seq``), but not unknown local tags::

    $ cat <<EOF > test.yaml
    %YAML 1.1
    ---
    !!map {
      ? !!str "sequence"
      : !!seq [ !!str "one", !!str "two" ],
      ? !!str "mapping"
      : !!map {
        ? !!str "sky" : !myobj "blue",
        ? !!str "sea" : !!str "green",
      },
    }
    EOF

    $ shyaml get-value < test.yaml
    sequence:
    - one
    - two
    mapping:
      sky: !myobj 'blue'
      sea: green


Empty documents
---------------

When provided with an empty document, ``shyaml`` will consider the
document to hold a ``null`` value::

    $ echo | shyaml get-value -y
    null
    ...


Usage string
------------

A quick reminder of what is available will be printed when calling
``shyaml`` without any argument::

    $ shyaml
    Error: Bad number of arguments.
    Usage:

        shyaml {-h|--help}
        shyaml [-y|--yaml] [-q|--quiet] ACTION KEY [DEFAULT]
    <BLANKLINE>

The full help is available through the usage of the standard ``-h`` or
``-help``::


    $ shyaml --help

    Parses and output chosen subpart or values from YAML input.
    It reads YAML in stdin and will output on stdout it's return value.

    Usage:

        shyaml {-h|--help}
        shyaml [-y|--yaml] [-q|--quiet] ACTION KEY [DEFAULT]


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

    <BLANKLINE>

Using invalid keywords will issue an error and the usage message::

    $ shyaml get-foo
    Error: 'get-foo' is not a valid action.
    Usage:

        shyaml {-h|--help}
        shyaml [-y|--yaml] [-q|--quiet] ACTION KEY [DEFAULT]
    <BLANKLINE>


Python API
==========

``shyaml`` can be used from within python if you need so::

    >>> import shyaml
    >>> try:
    ...     from StringIO import StringIO
    ... except ImportError:
    ...     from io import StringIO

    >>> yaml_content = StringIO("""
    ... a: 1.1
    ... b:
    ...   x: foo
    ...   y: bar
    ... """)

    >>> for out in shyaml.do(stream=yaml_content,
    ...                      action="get-type",
    ...                      key="a"):
    ...    print(repr(out))
    'float'

Please note that ``shyaml.do(..)`` outputs a generator iterating
through all the yaml documents of the stream. In most usage case,
you'll have only one document.

You can have a peek at the code, the ``do(..)`` function has a documented
prototype.


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

Copyright (c) 2018 Valentin Lab.

Licensed under the `BSD License`_.

.. _BSD License: http://raw.github.com/0k/shyaml/master/LICENSE
