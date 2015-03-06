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
  -o --once                   Run only once.
  -v --verbose                Verbose mode.
  -w --write=<writeymlpath>   Write arguments yaml file.
  -l --load=<loadymlpath>     Load arguments yaml file.
  -i --interval=<interval>    Seconds between checks [default: 60].
  -g --gitfolder=<gitfolder>  Folder to check the git repos out [default: .].
  -c --cmdfolder=<cmdfolder>  Folder from where to run the command [default: .].
"""

# Active8 (04-03-15)
# author: erik@a8.nl
# license: GNU-GPL2

import time
import subprocess
from os.path import join, exists, basename
from arguments import *
from git import Repo, GitCommandError
from appinstance import AppInstance, AppInstanceRunning


class GitRepos(object):
    """
    Repo
    """
    @staticmethod
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
        except KeyboardInterrupt:
            raise
        except BaseException as e:
            print "\033[31m", e, "\033[0m"
            return False

    def check_repos(self, folder, url, verbose=False):
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
        return self.clone_or_pull_from(gp, url, name, verbose)


def call_command(command, cmdfolder, verbose=False):
    """
    @type command: str, unicode
    @type cmdfolder: str, unicode
    @type verbose: bool
    @return: None
    """
    try:
        if verbose:
            print "\033[36m", cmdfolder, command, "\033[0m"

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

            fout = open(join(cmdfolder, "reposmon.out"), "w")
            fout.write(so)
            fout.write(se)
            fout.close()
    except OSError as e:
        print e
    except ValueError as e:
        print e
    except subprocess.CalledProcessError as e:
        print e


def main_loop(parsedargs):
    """
    @type args: tuple
    @return: None
    """
    r = GitRepos()

    while True:
        if r.check_repos(parsedargs.gitfolder, parsedargs.giturl, verbose=parsedargs.verbose):
            if parsedargs.verbose:
                print "\033[32mchanged, calling:", parsedargs.command, "in", parsedargs.cmdfolder, "\033[0m"

            call_command(parsedargs.command, parsedargs.cmdfolder, parsedargs.verbose)
        else:
            if parsedargs.verbose:
                print "\033[30m" + parsedargs.giturl, "not changed\033[0m"

        time.sleep(parsedargs.interval)

        if parsedargs.once:
            break


def main():
    """
    git@github.com:erikdejonge/schema.git
    """
    try:
        parsedargs = Arguments()
        argstring = ""

        if parsedargs.command and parsedargs.giturl:
            argstring = str(parsedargs.command) + str(parsedargs.giturl)
        with AppInstance(arguments=argstring):
            schema = Schema({"pa_command": Or(None, str),
                             "pa_giturl": Or(None, lambda x: ".git" in x),
                             Optional("-i"): int,
                             Optional("op_help"): Or(Use(bool), error="[-h|--help] must be a bool"),
                             Optional("op_verbose"): Or(Use(bool), error="[-v|--verbose] must be a bool"),
                             Optional("op_once"): Or(Use(bool), error="[-o|--once] must be a bool"),
                             Optional("op_interval"): Or(Use(int), error="[-i|--interval] must be an int"),
                             Optional("op_load"): Or(None, exists, error='[-l|--load] path should not exist'),
                             Optional("op_write"): Or(None, not_exists, exists, error='[-w|--write] path exists'),
                             Optional("op_gitfolder"): Or(str, exists, error='[-g|--gitfolder] path should exist'),
                             Optional("op_cmdfolder"): Or(str, exists, error='[-c|--cmdfolder] path should exist')})

            parsedargs.parse_args()

            if parsedargs.giturl and parsedargs.command:
                main_loop(parsedargs)
            else:
                print __doc__

    except SystemExit as e:
        if hasattr(e, "usage"):
            console(e.usage)
        else:
            e = str(e).strip()

            if "Options:" in e:
                console(e)
            else:
                console(e)

    except KeyboardInterrupt:
        print "\n\033[33mbye\033[0m"
    except AppInstanceRunning:
        if parsedargs is not None:
            if parsedargs.verbose:
                print "\033[31minstance runs already\033[0m"
        else:
            console('parsedargs is None')

if __name__ == "__main__":
    main()
