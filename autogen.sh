#!/bin/sh

##
## You can download latest version of this file:
##  $ wget https://gist.github.com/vaab/9118087/raw -O autogen.sh
##  $ chmod +x autogen.sh
##

##
## Functions
##

exname="$(basename "$0")"
long_tag="[0-9]+\.[0-9]+(\.[0-9]+)?-[0-9]+-[0-9a-f]+"
short_tag="[0-9]+\.[0-9]+(\.[0-9]+)?"
get_short_tag="s/^($short_tag).*\$/\1/g"

get_path() { (
    IFS=:
    for d in $PATH; do
        filename="$d/$1"
        if test -x "$filename"; then echo "$d/$1"; return 0; fi
    done
    return 1
) }

print_exit() {
    echo "$@"
    exit 1
}

print_syntax_error() {
    [ "$*" ] ||	print_syntax_error "$FUNCNAME: no arguments"
    print_exit "${ERROR}script error:${NORMAL} $@" >&2
}

print_syntax_warning() {
    [ "$*" ] || print_syntax_error "$FUNCNAME: no arguments."
    [ "$exname" ] || print_syntax_error "$FUNCNAME: 'exname' var is null or not defined."
    echo "$exname: ${WARNING}script warning:${NORMAL} $@" >&2
}

print_error() {
    [ "$*" ] || print_syntax_warning "$FUNCNAME: no arguments."
    [ "$exname" ] || print_exit "$FUNCNAME: 'exname' var is null or not defined." >&2
    print_exit "$exname: ${ERROR}error:${NORMAL} $@" >&2
}

depends() {

    local i tr path

    tr=$(get_path "tr") ||
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

die() {
    [ "$*" ] || print_syntax_warning "$FUNCNAME: no arguments."
    [ "$exname" ] || print_exit "$FUNCNAME: 'exname' var is null or not defined." >&2
    print_exit "$exname: ${ERROR}error:${NORMAL}" "$@" >&2
}

matches() {
   echo "$1" | "$grep" -E "^$2\$" >/dev/null 2>&1
}

get_current_git_date_timestamp() {
    "$git" show -s --pretty=format:%ct
}


dev_version_tag() {
    compat_date "$(get_current_git_date_timestamp)" "+%Y%m%d%H%M"
}


get_current_version() {

    version=$("$git" describe --tags)
    if matches "$version" "$short_tag"; then
        echo "$version"
    else
        version=$(echo "$version" | compat_sed "$get_short_tag")
        echo "${version}.dev$(dev_version_tag)"
    fi

}

prepare_files() {

    version=$(get_current_version)
    short_version=$(echo "$version" | cut -f 1,2,3 -d ".")


    for file in $FILES; do
        if [ -e "$file" ]; then
            compat_sed_i "s#%%version%%#$version#g;
                          s#%%short-version%%#${short_version}#g;
                          s#%%name%%#${NAME}#g;
                          s#%%author%%#${AUTHOR}#g;
                          s#%%email%%#${EMAIL}#g;
                          s#%%author-email%%#${AUTHOR_EMAIL}#g;
                          s#%%description%%#${DESCRIPTION}#g" \
                      "$file"
        fi
    done

    echo "Version updated to $version."
}

##
## LOAD CONFIG
##

if [ -e ./.package ]; then
    . ./.package
else
    echo "'./.package' file is missing."
    exit 1
fi

## list of files where %%version*%% macros are to be replaced:
[ -z "$FILES" ] && FILES="setup.cfg setup.py CHANGELOG.rst"

[ -z "$NAME" ] && die "No \$NAME was defined in './package'."


##
## CHECK DEPS
##

depends git grep

## BSD / GNU sed compatibility layer
if get_path sed >/dev/null; then
    if sed --version >/dev/null 2>&1; then  ## GNU
        compat_sed() { sed -r "$@"; }
        compat_sed_i() { sed -r -i "$@"; }
    else                                    ## BSD
        compat_sed() { sed -E "$@"; }
        compat_sed_i() { sed -E -i "" "$@"; }
    fi
else
    ## Look for ``gsed``
    if (get_path gsed && gsed --version) >/dev/null 2>&1; then
        compat_sed() { gsed -r "$@"; }
        compat_sed_i() { gsed -r -i "$@"; }
    else
        print_error "$exname: required GNU or BSD sed not found"
    fi
fi

## BSD / GNU date compatibility layer
if get_path date >/dev/null; then
    if date --version >/dev/null 2>&1 ; then  ## GNU
        compat_date() { date -d "@$1" "$2"; }
    else                                      ## BSD
        compat_date() { date -j -f %s "$1" "$2"; }
    fi
else
    if (get_path gdate && gdate --version) >/dev/null 2>&1; then
        compat_date() { gdate -d "@$1" "$2"; }
    else
        print_error "$exname: required GNU or BSD date not found"
    fi
fi

if ! "$git" describe --tags >/dev/null 2>&1; then
    die "Didn't find a git repository (or no tags found). " \
        "\`\`./autogen.sh\`\` uses git to create changelog and version information."
fi


##
## CODE
##

if [ "$1" = "--get-version" ]; then
    get_current_version
    exit 0
fi

if [ "$1" = "--get-name" ]; then
    echo "$NAME"
    exit 0
fi

if get_path gitchangelog >/dev/null; then
    gitchangelog > CHANGELOG.rst
    if [ "$?" != 0 ]; then
        echo "Changelog NOT generated. An error occured while running \`\`gitchangelog\`\`." >&2
    else
        echo "Changelog generated."
    fi
else
    echo "Changelog NOT generated because \`\`gitchangelog\`\` could not be found."
    touch CHANGELOG.rst  ## create it anyway because it's required by setup.py current install
fi

prepare_files
if [ "$?" != 0 ]; then
    print_error "Error while updating version information."
fi
