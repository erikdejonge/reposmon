# coding=utf-8
"""
reposmon.py:
Monitor a git repository, execute a command when it changes.

Usage:
    reposmon <giturl> <command>
    [-i <interval>|--check-interval=<interval>]
    [-g <gitfolder>|--git-folder=<gitfolder>]
    [-c <commandfolder>|--command-folder=<commandfolder>]

Options:
  -h --help                           Show this screen.
  -i --check-interval=<interval>      Seconds between checks [default: 10].
  -g --git-folder=<gitfolder>         Folder to check the git repos out [default: ~/workspace/reposmon].
  -c --command-folder=<commandfolder> Folder from where to run the command [default: ~/].
"""

# coding=utf-8
from git import Repo
from os.path import join, expanduser, exists, basename, expanduser
from docopt import docopt
from schema import Schema, SchemaError, Or, Optional, And, Use
from subprocess import call


def dictionary_for_console(argdict, indent=""):
    """
    @type argdict: dict

    @type indent: str
    @return: sp
    """
    keys = argdict.keys()
    keys.sort(key=lambda x: len(x))
    sp = ""
    lk = 0
    ls = []

    for k in keys:
        s = indent + "\033[32m" + k + "\033[0m"
        s += "\033[33m" + "`: " + str(argdict[k]) + "\033[0m\n"
        ls.append((len(k), s))

        if len(k) > lk:
            lk = len(k)

    for lns, s in ls:
        s = s.replace("`", " " * (1 + (lk - lns)))
        sp += s

    return sp


def sort_arguments(arguments):
    """
    @type arguments: dict
    @return: tuple
    """
    opts = {}
    posarg = {}

    for k in arguments:
        if k.startswith("pa_"):
            posarg[k.replace("pa_", "")] = arguments[k]

        if k.startswith("op_"):
            opts[k.replace("op_", "")] = arguments[k]

    return opts, posarg


def arguments_for_console(arguments):
    """
    @type arguments: dict
    @return: None
    """
    s = ""
    opts, posarg = sort_arguments(arguments)
    newline = False

    if posarg:
        s += "\033[31mPositional arguments:\033[0m\n"
        s += dictionary_for_console(posarg, "  ")
        newline = True

    if opts:
        if newline:
            s += "\n"

        s += "\033[31mOptions:\033[0m\n"
        s += dictionary_for_console(opts, "  ")

    return s.strip() + "\n"


def raise_or_exit(e, debug=False):
    """
    @type e: Exception
    @return: None
    """
    if debug:
        raise e

        exit(1)
    else:
        exit(1)


def get_arguments(debug=False):
    """
    parse_docopt
    """
    arguments = dict(docopt(__doc__, version='0.1'))
    try:
        for k in arguments:
            if "folder" in k or "path" in k:
                if hasattr(arguments[k], "replace"):
                    arguments[k] = arguments[k].replace("~", expanduser("~"))

    except AttributeError as e:
        print "\033[31mAttribute error:" + k.strip(), "->", str(e), "\033[0m"
        print "\033[30m", "attrs: " + "\033[0m",

        for k in arguments:
            print "\033[30m", k.strip() + "\033[0m",

        print
        raise_or_exit(e, debug)

    try:
        schema = Schema({"<command>": str,
                         "<giturl>": lambda x: ".git" in x,
                         Optional("-i"): int,
                         Optional("--check-interval"): And(Use(int), error="[-i|--check-interval] must be an int"),
                         Optional("--git-folder"): And(str, exists, error='[-g|--git-folder] should exist'),
                         Optional("--command-folder"): And(str, exists, error='[-c|--command-folder] should exist')})

        arguments = schema.validate(arguments)
        arguments = dict((x.replace("<", "pa_").replace(">", "").replace("--", "op_").replace("-", "_"), y) for x, y in arguments.viewitems())
    except SchemaError as e:
        if "lambda" in str(e):
            err = "Error: giturl should end with .git"
        else:
            err = str(e)

        print "\033[31m" + err.strip() + "\033[0m"
        print __doc__
        raise_or_exit(e, debug)

    if debug:
        print arguments_for_console(arguments)

    opts, posarg = sort_arguments(arguments)
    return posarg, opts


def clone_or_pull_from(remote, name):
    """
    @type remote: str, unicode

    @type name: str, unicode
    @return: None
    """
    gp = join(join(join(expanduser("~"), "workspace"), "builds"), name)
    print "\033[37m", name, "\033[0m",
    if exists(gp):
        r = Repo(gp)
        origin = r.remote()
        hcommit_pre = r.head.commit
        origin.fetch()
        origin.pull()
        hcommit_post = r.head.commit
        if hcommit_post != hcommit_pre:
            index = r.index
            changed = "\n  -" + "\n  -".join([str(x).split("\n")[0] for x in index.diff(hcommit_pre)])
            print "\033[37m", changed, "\033[0m"
        else:
            print "\033[30mnot changed", "\033[0m"
    else:
        print "\033[32m", name, "\033[0m"
        ret = name + " " + str(Repo.clone_from(remote, gp).active_branch) + " cloned"
        print "\033[32m", ret, "\033[0m"

    return True


def check_repos(url):
    """
    @type url: str, unicode
    @return: None
    """
    name = basename(url).split(".")[0]
    ls = url.split(":")

    if len(ls) > 0:
        name = ls[1].replace("/", "_").split(".")[0]

    clone_or_pull_from(url, name)


def main():
    """
    main
    git@github.com:erikdejonge/schema.git
    """
    posarg, opts = get_arguments(True)

    # check_repos(arguments["giturl"])


if __name__ == "__main__":
    main()
