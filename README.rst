=================================
SHYAML: YAML for the command line
=================================


Disclaimer
==========

This scripts was written very quickly and will not support all YAML
manipulation that you could have dreamed of. But it should support
some handy basic query of YAML file.


Description
===========

Simple scripts that allow read access to YAML files through command line.

This can be handy, if you want to get access to YAML data in your shell
scripts.


Usage
=====

``shyaml`` takes it YAML input file from standard input ONLY. So there are
some sample routine.

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

Useless fun::

    $ cat test.yaml | shyaml get-value subvalue | shyaml get-value things
    - first
    - second
    - third

