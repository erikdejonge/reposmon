# coding=utf-8
"""
reposmon.py:
Monitor a git repository, execute a command when it changes.

Usage:
    reposmon.py [options] [--] <giturl> <command>
    reposmon.py -h | --help

Options:
  -h --help                   Show this screen.
  -o --once                   Run only once
  -v --verbose                Verbose mode
  -i --interval=<interval>    Seconds between checks [default: 10].
  -g --gitfolder=<gitfolder>  Folder to check the git repos out [default: .].
  -c --cmdfolder=<cmdfolder>  Folder from where to run the command [default: .].
"""

# coding=utf-8

import os
import yaml
from git import Repo, GitCommandError
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
        s = indent + "\033[36m" + k + "`: " + "\033[0m"
        v = str(argdict[k]).strip()
        num = v.isdigit()
        ispath = exists(v)

        if num:
            s += "\033[96m" + v + "\033[0m\n"
        elif ispath:
            s += "\033[35m" + v + "\033[0m\n"
        elif v == "False":
            s += "\033[31m" + v + "\033[0m\n"
        elif v == "True":
            s += "\033[32m" + v + "\033[0m\n"
        else:
            s += "\033[33m" + v + "\033[0m\n"

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
        key = k.replace("pa_", "").replace("op_", "").strip()

        if len(key) > 0:
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
        s += "\033[91mPositional arguments:\033[0m\n"
        s += dictionary_for_console(posarg, "  ")
        newline = True

    if opts:
        if newline:
            s += "\n"

        s += "\033[91mOptions:\033[0m\n"
        s += dictionary_for_console(opts, "  ")

    return s.strip() + "\n"


def raise_or_exit(e, debug=False):
    """
    @type e: Exception
    @return: None
    """
    print "\033[31mraise_or_exit\033[0m"
    if debug:
        raise e

        exit(1)
    else:
        exit(1)


class Arguments(object):

    """
    Argument dict to boject
    """

    def __init__(self, positional=None, options=None, yamlfile=None):
        """
        @type positional: dict
        @type options: dict
        @return: None
        """
        dictionary = {}

        if positional and options:
            self.positional = positional.copy()
            self.options = options.copy()
            dictionary = positional.copy()
            dictionary.update(options.copy())
            self.reprdict = {}
            self.reprdict["positional"] = positional.copy()
            self.reprdict["options"] = options.copy()
        elif yamlfile:
            raise AssertionError("not implemented")

        def _traverse(key, element):
            """
            @type key: str, unicode
            @type element: str, unicode
            @return: None
            """
            if isinstance(element, dict):
                return key, Arguments(element)
            else:
                return key, element

        object_dict = dict(_traverse(k, v) for k, v in dictionary.iteritems())
        self.__dict__.update(object_dict)

    def __str__(self):
        """
        __str__
        """
        y = yaml.dump(self.reprdict, default_flow_style=False)
        return "---\n" + y


def get_arguments(debug):
    """
    parse_docopt
    """
    verbose = debug
    arguments = dict(docopt(__doc__, version='0.1'))
    try:
        for k in arguments:
            if "folder" in k or "path" in k:
                if hasattr(arguments[k], "replace"):
                    arguments[k] = arguments[k].replace("~", expanduser("~"))

                    if arguments[k].strip() == ".":
                        arguments[k] = os.getcwd()

                    arguments[k] = arguments[k].rstrip("/").strip()

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
                         Optional("--once"): Or(Use(bool), error="[-o|--once] must be a bool"),
                         Optional("--interval"): Or(Use(int), error="[-i|--interval] must be an int"),
                         Optional("--gitfolder"): Or(str, exists, error='[-g|--gitfolder] path should exist'),
                         Optional("--cmdfolder"): Or(str, exists, error='[-c|--cmdfolder] path should exist')})

        # arguments = schema.validate(arguments)
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
    return Arguments(posarg, opts)


def clone_or_pull_from(gp, remote, name, verbose=False):
    """
    @type gp: str, unicode
    @type remote: str, unicode
    @type name: str, unicode
    @type verbose: bool
    @return: None
    """
    if exists(gp):
        try:
            if verbose:
                print "\033[32mPulling:", name, "\033[0m"

            r = Repo(gp)
            origin = r.remote()
            hcommit_pre = r.head.commit
            origin.fetch()
            origin.pull()
            hcommit_post = r.head.commit
            if hcommit_post != hcommit_pre:
                index = r.index
                changed = "\n  -" + "\n  -".join([str(x).split("\n")[0] for x in index.diff(hcommit_pre)])
                if verbose:
                    print "\033[34m", changed, "\033[0m"
                return True
            else:
                return False
        except GitCommandError as e:
            print
            print "\033[91m" + str(e), "\033[0m"
            raise SystemExit()

        return True
    else:
        try:
            if verbose:
                print "\033[32mCloning:", name, "\033[0m"

            ret = name + " " + str(Repo.clone_from(remote, gp).active_branch) + " cloned"

            if verbose:
                print "\033[37m", ret, "\033[0m"
        except GitCommandError as e:
            print "\033[91m" + str(e), "\033[0m"
            raise SystemExit()

        return True


def check_repos(folder, url, verbose=False):
    """
    @type url: str, unicode
    @type verbose: bool
    @return: bool
    """
    name = basename(url).split(".")[0]
    gp = join(folder, name)
    if verbose:
        print "\033[30musing github folder:", gp, "\033[0m"

    # if exists(gp):
    return clone_or_pull_from(gp, url, name, verbose)


def main():
    """
    main
    git@github.com:erikdejonge/schema.git
    """
    args = get_arguments(False)

    while True:
        try:
            if check_repos(args.gitfolder, args.giturl, verbose=args.verbose):
                if args.verbose:
                    print "\033[32mchanged, calling:", args.cmdfolder, "\033[0m"
            else:
                if args.verbose:
                    print "\033[30m"+args.giturl, "not changed\033[0m"

        except SystemExit:
            break

        if args.once:
            break

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
