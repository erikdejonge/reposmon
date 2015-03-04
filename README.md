
# reposmon
Monitor a git repository, execute a command when it changes.

###purpose
Execute a chain of command when a git-repository changes

###use case
Run testsets and build docker container after commit
[change detected]
    * Run a testset
    * Build a docker container
    * Push to registry


###requirements
```bash
pip install -r requirements.txt
```

###use
```
reposmon.py

Monitor a git repository, execute a command when it changes.

Usage:
    reposmon.py [options] [--] [<giturl> <command>]
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
```

###example
When <giturl> in local directory or work-directory changes, execute the command in the local directory or command-directory.

```bash
python reposmon.py git@github.com:erikdejonge/reposmon.git "docker build ."
```

###optional
#####bash alias
alias reposmon="#/usr/bin/env python ~/[...]/reposmon/reposmon.py

install alias with a workspace checkout of reposmon:

```bash
alias reposmon="#/usr/bin/env python /Users/rabshakeh/workspace/reposmon/reposmon.py"
```

#####commit and sort aliases on osx
On osx the sortalias command sorts all aliasses in .bash_profile

```bash
alias sortalias='cat ~/.bash_profile > ~/.bash_profile.backup; cat ~/.bash_profile | grep -v alias | grep -v '\''^$'\'' > ~/.bash_profile_without_alias; alias | grep -v '\''^$'\'' > ~/.bash_profile_only_alias; cat ~/.bash_profile_without_alias > ~/.bash_profile; echo -e '\''\n'\'' >>  ~/.bash_profile; cat ~/.bash_profile_only_alias >>  ~/.bash_profile; rm ~/.bash_profile_without_alias; rm ~/.bash_profile_only_alias'
```
