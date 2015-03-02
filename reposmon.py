# coding=utf-8
"""
Testpygit

Usage:
    docker_on_git <giturl> <docker>

Options:
  -h --help     Show this screen.
"""

# coding=utf-8

from os.path import join, expanduser, exists, basename

from docopt import docopt
from schema import Schema, SchemaError
from git import Repo


def parse_docopt():
    """
    parse_docopt
    """
    arguments = dict(docopt(__doc__, version='0.1'))
    arguments = dict((x.replace("<", "").replace(">", ""), y) for x, y in arguments.viewitems())
    try:
        schema = Schema({"giturl": lambda x: "git@" in x}, error="git@ should be in url")
        arguments = schema.validate(arguments)
    except SchemaError as e:
        raise e

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
    check_repos(arguments["giturl"])


if __name__ == "__main__":
    main()
