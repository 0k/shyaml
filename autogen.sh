#!/bin/bash

exname="$(basename "$0")"

##
## Functions
##

function get_path() {
    local type

    type="$(type -t "$1")"
    case $type in
	("file")
	    type -p "$1"
	    return 0
	    ;;
	("function" | "builtin" )
	    echo "$1"
	    return 0
	    ;;
    esac
    return 1
}

function print_exit() {
    echo $@
    exit 1
}

function print_syntax_error() {
    [ "$*" ] ||	print_syntax_error "$FUNCNAME: no arguments"
    print_exit "${ERROR}script error:${NORMAL} $@" >&2
}

function print_syntax_warning() {
    [ "$*" ] || print_syntax_error "$FUNCNAME: no arguments."
    [ "$exname" ] || print_syntax_error "$FUNCNAME: 'exname' var is null or not defined."
    echo "$exname: ${WARNING}script warning:${NORMAL} $@" >&2
}

function print_error() {
    [ "$*" ] || print_syntax_warning "$FUNCNAME: no arguments."
    [ "$exname" ] || print_exit "$FUNCNAME: 'exname' var is null or not defined." >&2
    print_exit "$exname: ${ERROR}error:${NORMAL} $@" >&2
}

function depends() {

    local i tr path

    tr=$(get_path "tr")
    test "$tr" ||
	print_error "dependency check : couldn't find 'tr' command."

    for i in $@ ; do

      if ! path=$(get_path $i); then
	  new_name=$(echo $i | "$tr" '_' '-')
	  if [ "$new_name" != "$i" ]; then
	     depends "$new_name"
	  else
	     print_error "dependency check : couldn't find '$i' command."
	  fi
      else
	  if ! test -z "$path" ; then
	      export "$(echo $i | "$tr" '-' '_')"=$path
	  fi
      fi

    done
}

function die() {
    [ "$*" ] || print_syntax_warning "$FUNCNAME: no arguments."
    [ "$exname" ] || print_exit "$FUNCNAME: 'exname' var is null or not defined." >&2
    print_exit "$exname: ${ERROR}error:${NORMAL} $@" >&2
}

##
## Code
##

depends git sed grep date gitchangelog

if ! test -e "setup.cfg" >/dev/null 2>&1; then
    die "No 'setup.cfg'... this script is meant to work with a python project"
fi

if ! "$git" describe --tags >/dev/null 2>&1; then
    die "Didn't find a git repository. autogen.sh uses git to create changelog \
         and version information."
fi


function matches() {
   echo "$1" | "$grep" -E "^$2\$" >/dev/null 2>&1
}


long_tag="[0-9]+\.[0-9]+(\.[0-9]+)?-[0-9]+-[0-9a-f]+"
short_tag="[0-9]+\.[0-9]+(\.[0-9]+)?"

get_short_tag="s/^($short_tag).*\$/\1/g"


function get_current_git_date_timestamp() {
    "$git" show -s --pretty=format:%ct
}


function dev_version_tag() {
    "$date" -d "@$(get_current_git_date_timestamp)" +%Y%m%d%H%M
}


function get_current_version() {

    version=$("$git" describe --tags)
    if matches "$version" "$short_tag"; then
        echo "$version"
    else
        version=$(echo "$version" | "$sed" -r "$get_short_tag")
        echo "${version}.1dev_r$(dev_version_tag)"
    fi

}

function set_version_setup_cfg() {

    version=$(get_current_version)
    short_version=$(echo "$version" | cut -f 1,2,3 -d ".")

    "$sed" -ri "s/%%version%%/$version/g" setup.cfg \
                                       CHANGELOG.rst &&
    "$sed" -ri "s/%%short-version%%/${short_version}/g" \
                                       setup.cfg \
                                       CHANGELOG.rst &&
    echo "Version updated to $version."
}


"$gitchangelog" > CHANGELOG.rst

if [ "$?" != 0 ]; then
    print_error "Error while generating changelog."
fi
echo "Changelog generated."


set_version_setup_cfg
if [ "$?" != 0 ]; then
    print_error "Error while updating version information."
fi

