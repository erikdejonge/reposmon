#!/usr/bin/env python
# coding=utf-8
"""
reposmon.py
Monitor a git repository, execute a command when it changes.

Usage:
    reposmon.py [options] [--] <giturl> <command>
    reposmon.py -h | --help

Options:
  -h --help                   Show this screen.
  -o --once                   Run only once
  -v --verbose                Verbose mode
  -i --interval=<interval>    Seconds between checks [default: 60].
  -g --gitfolder=<gitfolder>  Folder to check the git repos out [default: .].
  -c --cmdfolder=<cmdfolder>  Folder from where to run the command [default: .].
"""

import os
import time
import subprocess
import yaml
import psutil
import hashlib
from git import Repo, GitCommandError
from docopt import docopt
from schema import Schema, SchemaError, Or, Optional, Use
from os.path import join, exists, basename, expanduser


def colorize_for_print(v):
    """
    @type v: str, unicode
    @return: None
    """
    s = ""
    v = v.strip()

    if v == "false":
        v = "False"
    elif v == "true":
        v = "True"

    num = v.isdigit()

    if not num:
        try:
            v2 = v.replace("'", "").replace('"', "")
            num = float(v2)
            num = True
            v = v2
        except ValueError:
            pass

    ispath = exists(v)

    if num is True:
        s += "\033[93m" + v + "\033[0m"
    elif ispath is True:
        s += "\033[35m" + v + "\033[0m"
    elif v == "False":
        s += "\033[31m" + v + "\033[0m"
    elif v == "True":
        s += "\033[32m" + v + "\033[0m"
    else:
        s += "\033[33m" + v + "\033[0m"

    return s


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
        s += colorize_for_print(v)
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
        try:
            possnum = arguments[k]

            if isinstance(possnum, str):
                if "." in possnum:
                    arguments[k] = float(possnum)
                else:
                    arguments[k] = int(possnum)

        except ValueError:
            pass

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
        s += "\033[91mPositional arguments:\033[0m"
        s += dictionary_for_console(posarg, "\n  ")
        newline = True

    if opts:
        if newline:
            s += "\n\n"

        s += "\033[91mOptions:\033[0m"
        s += dictionary_for_console(opts, "\n  ")

    return s + "\n"


def raise_or_exit(e, debug=False):
    """
    @type e: str, unicode
    @type debug: bool
    @return: None
    """
    print "\033[31mraise_or_exit\033[0m"
    if debug:
        raise e
    else:
        exit(1)


def get_print_yaml(yamlstring):
    """
    @type yamlstring: str, unicode
    @return: None
    """
    s = ""

    for i in yamlstring.split("\n"):
        ls = [x for x in i.split(":") if x]
        cnt = 0

        if len(ls) > 1:
            for ii in ls:
                if cnt == 0:
                    s += "\033[36m" + ii + ": " + "\033[0m"
                else:
                    s += colorize_for_print(ii)

                cnt += 1
        else:
            if i.strip().startswith("---"):
                s += "\033[95m" + i + "\033[0m"
            else:
                s += "\033[91m" + i + "\033[0m"

        s += "\n"

    return s.strip()


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
        self.once = None
        self.command = None
        self.giturl = None
        self.cmdfolder = None
        self.verbose = None
        self.giturl = None
        self.gitfolder = None
        self.interval = None
        self.verbose = None
        dictionary = {}

        if positional and options:
            self.positional = positional.copy()
            self.options = options.copy()
            dictionary = positional.copy()
            dictionary.update(options.copy())
            self.reprdict = {"positional": positional.copy(),
                             "options": options.copy()}

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
        return get_print_yaml("---\n" + y)


def get_arguments(verbose, validate_schema=True):
    """
    @type verbose: bool
    @type validate_schema: bool
    @return: None
    """
    arguments = dict(docopt(__doc__, version='0.1'))
    k = ""
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
        raise_or_exit(e, verbose)

    try:
        schema = Schema({"<command>": str,
                         "<giturl>": lambda x: ".git" in x,
                         Optional("-i"): int,
                         Optional("--help"): Or(Use(bool), error="[-h|--help] must be a bool"),
                         Optional("--verbose"): Or(Use(bool), error="[-v|--verbose] must be a bool"),
                         Optional("--once"): Or(Use(bool), error="[-o|--once] must be a bool"),
                         Optional("--interval"): Or(Use(int), error="[-i|--interval] must be an int"),
                         Optional("--gitfolder"): Or(str, exists, error='[-g|--gitfolder] path should exist'),
                         Optional("--cmdfolder"): Or(str, exists, error='[-c|--cmdfolder] path should exist')})

        del arguments["--"]
        if validate_schema is True:
            arguments = schema.validate(arguments)

        arguments = dict((x.replace("<", "pa_").replace(">", "").replace("--", "op_").replace("-", "_"), y) for x, y in arguments.viewitems())
    except SchemaError as e:
        if "lambda" in str(e):
            err = "Error: giturl should end with .git"
        else:
            err = str(e)

        print "\033[31m" + err.strip() + "\033[0m"
        print __doc__
        raise_or_exit(e, verbose)

    if verbose:
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
    try:
        if exists(gp):
            try:
                if verbose:
                    print "\033[32mPulling:", name, "\033[0m"

                r = Repo(gp)
                origin = r.remote()
                if remote != origin.config_reader.config.get_value('remote "origin"', "url"):
                    raise SystemExit("Different remote url: " + str(remote) + "\n                       " + origin.config_reader.config.get_value('remote "origin"', "url"))

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
                raise SystemExit(e)
        else:
            try:
                if verbose:
                    print "\033[32mCloning:", name, "\033[0m"

                ret = name + " " + str(Repo.clone_from(remote, gp).active_branch) + " cloned"

                if verbose:
                    print "\033[37m", ret, "\033[0m"
            except GitCommandError as e:
                print "\033[91m" + str(e), "\033[0m"
                raise SystemExit(e)

            return True
    except AssertionError as e:
        print "\033[31m", e, "\033[0m"
        return False


def check_repos(folder, url, verbose=False):
    """
    @type folder: str, unicode
    @type url: str, unicode
    @type verbose: bool
    @return: None
    """
    name = basename(url).split(".")[0]
    gp = join(folder, name)

    if verbose:
        print "\033[30musing github folder:", gp, "\033[0m"

    # if exists(gp):
    return clone_or_pull_from(gp, url, name, verbose)


def call_command(command, cmdfolder, verbose=False):
    """
    @type command: str, unicode
    @type cmdfolder: str, unicode
    @type verbose: bool
    @return: None
    """
    try:
        proc = subprocess.Popen(command.split(" "), stderr=subprocess.PIPE, stdout=subprocess.PIPE, cwd=cmdfolder)

        if verbose:
            while proc.poll() is None:
                output = proc.stdout.readline()

                if len(output.strip()) > 0:
                    print "\033[30m", output, "\033[0m",
        else:
            so, se = proc.communicate()
            if proc.returncode != 0 or verbose:
                print "command:"
                print so
                print se

    except OSError as e:
        print e
    except ValueError as e:
        print e
    except subprocess.CalledProcessError as e:
        print e


def running_write_lockfile(lockfile, verbose=False):
    """
    @type lockfile: str, unicode
    @type verbose: bool
    @return: None
    """
    fh = open(lockfile, "w")
    fh.write(str(os.getpid()))
    fh.close()

    if verbose is True:
        print "\033[32m" + lockfile, str(os.getpid()) + "\033[0m"


def running_lockfile_name(arguments):
    """
    @type arguments: str, unicode
    @return: None
    """
    name = basename(__file__).split(".")[0]
    lfname = hashlib.md5(basename(__file__) + arguments.command + arguments.giturl).hexdigest()
    lockfile = join(expanduser("~"), "."+name+"_" + lfname + ".pid")
    print
    print lockfile
    
    return lockfile


def start_profile():
    """
    start_profile
    @rtype: Profile
    """
    from cProfile import Profile
    pr = Profile()
    pr.enable()
    return pr


def end_profile(pr, items=20, printstats=False):
    """
    @type pr: Profile
    @type items: int
    @type printstats: bool
    """
    if not "console" in globals():
        def console(x):
            print "\033[93m$", x, "\033[0m"
    from pstats import Stats
    p = Stats(pr)
    p.strip_dirs()
    console("total time")
    p.sort_stats('time')

    if items is None:
        p.print_stats()
    else:
        p.print_stats(items)

    if printstats:
        console("cumulative time")
        p.sort_stats('cumtime')

        if items is None:
            p.print_stats()
        else:
            p.print_stats(items)

        p.sort_stats('calls')

        if items is None:
            p.print_stats()
        else:
            p.print_stats(items)

def running_remove_lockfile(name):
    """
    @type name: str, unicode
    @return: None
    """
    if exists(name):
        if int(open(name).read()) == os.getpid():
            os.remove(name)


def running_check_lockfile(name, verbose=False):
    """
    @type name: str, unicode
    @type verbose: bool
    @return: None
    """
    running = False

    if exists(name):
        pid = int(open(name).read().strip())
        cmdline = None

        for p in psutil.process_iter():
            if p.pid == pid:
                cmdline = " ".join(p.as_dict()["cmdline"])

                if __file__ in str(cmdline):
                    running = True

        if running is False:
            os.remove(name)

        if verbose is True and cmdline is not None and running is False:
            print "\033[91mAnother type proc found:", pid, "\033[0m"

        if verbose is True:
            if running is True:
                print "\033[91mAnother instance found:", pid, "\033[0m"

    return running


def main_loop(arguments):
    """
    @type arguments: Arguments
    @return: None
    """
    while True:
        if False:
            if check_repos(arguments.gitfolder, arguments.giturl, verbose=arguments.verbose):
                if arguments.verbose:
                    print "\033[32mchanged, calling:", arguments.command, "in", arguments.cmdfolder, "\033[0m"

                call_command(arguments.command, arguments.cmdfolder, arguments.verbose)
            else:
                if arguments.verbose:
                    print "\033[30m" + arguments.giturl, "not changed\033[0m"

        time.sleep(arguments.interval)

        if arguments.once:
            break


def main():
    """
    git@github.com:erikdejonge/schema.git
    """
    schemaless_arguments = get_arguments(False, validate_schema=False)
    lockfile = running_lockfile_name(schemaless_arguments)
    try:
        if running_check_lockfile(lockfile, schemaless_arguments.verbose) is False:
            print "running"
            
            arguments = get_arguments(schemaless_arguments.verbose)
            running_write_lockfile(lockfile, arguments.verbose)
            main_loop(arguments)
    except SystemExit as e:
        e = str(e).strip()

        if "Options:" in e:
            print "\033[33m", e, "\033[0m"
        else:
            print "\033[91m", e, "\033[0m"
    except KeyboardInterrupt:
        print "\n\033[33mbye\033[0m"
    finally:
        running_remove_lockfile(lockfile)


if __name__ == "__main__":

    main()
