#!/usr/bin/env python3
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
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

# Active8 (04-03-15)
# author: erik@a8.nl
# license: GNU-GPL2

import time
from arguments import *
from git import Repo, GitCommandError
from appinstance import *
from cmdssh import call_command


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
                        console("Pulling:", name, color="green")

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
                            console(changed, color="blue")

                        return True
                    else:
                        return False
                except GitCommandError as ge:
                    console(ge, color="red")
                    raise SystemExit(ge)
            else:
                try:
                    if verbose:
                        console("Cloning:", name, color="green")

                    ret = name + " " + str(Repo.clone_from(remote, gp).active_branch) + " cloned"

                    if verbose:
                        console(ret, color="yellow")
                except GitCommandError as ge:
                    console(ge, color="red")
                    raise SystemExit(ge)

                return True
        except AssertionError as ae:
            console(ae, color="red")
            return False
        except KeyboardInterrupt:
            raise
        except BaseException as be:
            console(be, color="red")
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
            console(gp, color="yellow")

        # if exists(gp):
        return self.clone_or_pull_from(gp, url, name, verbose)


def main_loop(parsedargs):
    """
    @type parsedargs: Arguments
    @return: None
    """
    r = GitRepos()

    while True:
        if r.check_repos(parsedargs.gitfolder, parsedargs.giturl, verbose=parsedargs.verbose):
            if parsedargs.verbose:
                console("changed, calling:", parsedargs.command, "in", parsedargs.cmdfolder, color="yellow")

            result = call_command(parsedargs.command, parsedargs.cmdfolder, parsedargs.verbose, streamoutput=False, returnoutput=True)
            fout = open(join(parsedargs.cmdfolder, "reposmon.out"), "w")
            fout.write(result)
            fout.close()
        else:
            if parsedargs.verbose:
                console(parsedargs.giturl, "not changed")

        time.sleep(parsedargs.interval)

        if parsedargs.once:
            break


def main():
    """
    git@github.com:erikdejonge/schema.git
    """
    parsedargs = None
    try:
        parsedargs = Arguments()
        argstring = ""

        if parsedargs.command and parsedargs.giturl:
            argstring = str(parsedargs.command) + str(parsedargs.giturl)
        with AppInstance(args=argstring):
            schema = Schema({"command": Or(None, str),
                             "giturl": Or(None, lambda x: ".git" in x),
                             Optional("-i"): int,
                             Optional("help"): Or(Use(bool), error="[-h|--help] must be a bool"),
                             Optional("verbose"): Or(Use(bool), error="[-v|--verbose] must be a bool"),
                             Optional("once"): Or(Use(bool), error="[-o|--once] must be a bool"),
                             Optional("interval"): Or(Use(int), error="[-i|--interval] must be an int"),
                             Optional("load"): Or(None, exists, error='[-l|--load] path should not exist'),
                             Optional("write"): Or(None, not_exists, exists, error='[-w|--write] path exists'),
                             Optional("gitfolder"): Or(str, exists, error='[-g|--gitfolder] path should exist'),
                             Optional("cmdfolder"): Or(str, exists, error='[-c|--cmdfolder] path should exist')})

            parsedargs.parse_arguments(schema)

            if parsedargs.giturl and parsedargs.command:
                main_loop(parsedargs)
            else:
                print(__doc__)

    except KeyboardInterrupt:
        console(color="yellow", msg="bye")
    except AppInstanceRunning:
        if parsedargs is not None:
            if parsedargs.verbose:
                console(color="red", msg="instance runs already")
        else:
            console('parsedargs is None')
    except DocoptExit as de:
        if hasattr(de, "usage"):
            console(de.usage, plainprint=True)
        else:
            de = str(de).strip()

            if "Options:" in de:
                console(de, plainprint=True)


if __name__ == "__main__":
    main()
