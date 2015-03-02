# coding=utf-8
"""
reposmon

Usage:
    reposmon <giturl> <command>
    [-g <gitdirectory>|--git-directory=<gitdirectory>]
    [-c <commanddirectory>|--command-directory=<commanddirectory>]

Options:
  -h --help                               Show this screen.
  -i --check-interval                     Seconds between checks [default: 10].
  -g --git-directory=<gitdirectory>          Directory to check the git repos out [default: .].
  -c --command-directory=<commanddirectory>  Directory from where to run the command [default: .].
"""

# coding=utf-8
from os.path import join, expanduser, exists, basename, expanduser
from docopt import docopt
from schema import Schema, SchemaError, Or, Optional, And
from git import Repo


def print_dictionary(argdict):
    keys = argdict.keys()
    keys.sort(key=lambda x: len(x))
    sp = ""
    lk = 0
    ls = []
    for k in keys:
        s = "\033[31m" + k + "\033[0m"
        s += "\033[32m" + "`:" + argdict[k] + "\033[0m\n"
        ls.append((len(k), s))
        
        if len(k) > lk:
            lk = len(k)
    for lns, s in ls:
        s = s.replace("`", " " * (1 + (lk - lns)))
        sp += s
    print sp


def print_arguments(arguments):
    """
    @type arguments: dict
    @return: None
    """
    options = {}
    arguments = {}
    for k in arguments:
        if k.startswith("")
    print_dictionary(arguments)


def parse_docopt():
    """
    parse_docopt
    """
    arguments = dict(docopt(__doc__, version='0.1'))

    for k in arguments:
        if "directory" in k or "path" in k:
            arguments[k] = arguments[k].replace("~", expanduser("~"))
    try:
        schema = Schema({"<command>": str,
                         "<giturl>": lambda x: ".git" in x,
                         Optional("-i"): int,
                         Optional("--check-interval"): int,
                         Optional("--git-directory"): And(str, exists, error='--git-directory should exist'),
                         Optional("--command-directory"): And(str, exists, error='--command-directory should exist')})

        arguments = schema.validate(arguments)
        arguments = dict((x.replace("<", "pa_").replace(">", "").replace("--", "op_").replace("-", "_"), y) for x, y in arguments.viewitems())
    except SchemaError as e:
        if "lambda" in str(e):
            err = "Error: giturl should end with .git"
        else:
            err = str(e)

        print "\033[31m" + err, "\033[0m"
        exit(1)

    print_arguments(arguments)
    return arguments


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
    arguments = parse_docopt()

    # check_repos(arguments["giturl"])


if __name__ == "__main__":
    main()
