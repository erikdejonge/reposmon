
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
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import open
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import object

# Active8 (04-03-15)
# author: erik@a8.nl
# license: GNU-GPL2

import time
import hashlib
import subprocess
import stat
from os.path import join, basename
from arguments import *
from git import Repo, GitCommandError
from appinstance import AppInstance, AppInstanceRunning
from consoleprinter import console_exception


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
                except GitCommandError as e:
                    console(e, color="red")
                    raise SystemExit(e)
            else:
                try:
                    if verbose:
                        console("Cloning:", name, color="green")

                    ret = name + " " + str(Repo.clone_from(remote, gp).active_branch) + " cloned"

                    if verbose:
                        console(ret, color="yellow")
                except GitCommandError as e:
                    console(e, color="red")
                    raise SystemExit(e)

                return True
        except AssertionError as e:
            console(e, color="red")
            return False
        except KeyboardInterrupt:
            raise
        except BaseException as e:
            console(e, color="red")
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


def call_command(command, cmdfolder, verbose=False):
    """
    @type command: str, unicode
    @type cmdfolder: str, unicode
    @type verbose: bool
    @return: None
    """
    try:
        if verbose:
            console(cmdfolder, command, color="yellow")

        commandfile = hashlib.md5(command).hexdigest() + ".sh"
        commandfilepath = join(cmdfolder, commandfile)
        open(commandfilepath, "w").write(command)

        if not os.path.exists(commandfilepath):
            raise ValueError("commandfile could not be made")

        os.chmod(commandfilepath, stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)
        proc = subprocess.Popen(commandfilepath, stderr=subprocess.PIPE, stdout=subprocess.PIPE, cwd=cmdfolder, shell=True)

        if verbose:
            while proc.poll() is None:
                output = proc.stdout.readline()

                if len(output.strip()) > 0:
                    console(output, color="yellow"),
        else:
            so, se = proc.communicate()
            if proc.returncode != 0 or verbose:
                print("command:")
                print(so)
                print(se)

            fout = open(join(cmdfolder, "reposmon.out"), "w")
            fout.write(so)
            fout.write(se)
            fout.close()

        if os.path.exists(commandfilepath):
            os.remove(commandfilepath)
    except OSError as e:
        console_exception(e)
    except ValueError as e:
        console_exception(e)
    except subprocess.CalledProcessError as e:
        console_exception(e)


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

            call_command(parsedargs.command, parsedargs.cmdfolder, parsedargs.verbose)
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
        with AppInstance(arguments=argstring):
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

    except DocoptExit as e:
        if hasattr(e, "usage"):
            console(e.usage, plainprint=True)
        else:
            e = str(e).strip()

            if "Options:" in e:
                console(e, plainprint=True)

    except KeyboardInterrupt:
        console(color="yellow", msg="bye")
    except AppInstanceRunning:
        if parsedargs is not None:
            if parsedargs.verbose:
                console(color="red", msg="instance runs already")
        else:
            console('parsedargs is None')


if __name__ == "__main__":
    main()
