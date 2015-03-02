# reposmon
Monitor a git repository, execute a command when it changes.

###purpose
Execute a chain of commands when a repository changes, commands have to return 0 in order to move to the next.

For example
[change detected]
    * Run a testset
    * Build a docker container
    * Push to registry
    

###use
      
```
python reposmon.py <giturl> <bashcmd> [-i|--check-interval] [-d|--git-directory] [-f|--command-directory]
```
When <giturl> in local directory or work-directory changes, execute the command in the local directory or command-directory.

```bash
python reposmon.py git@github.com:erikdejonge/reposmon.git "docker build ."
```
or
```bash
python reposmon.py git@github.com:erikdejonge/reposmon.git "docker build ." -d ~/workspace/reposmon -f ~/workspace/mycontainer
```

###optional
#####bash alias
alias reposmon="#/usr/bin/env python ~/[...]/reposmon/reposmon.py

install alias with a workspace checkout of reposmon:

```bash
echo alias reposmon=\"#/usr/bin/env python ~/workspace/reposmon/reposmon.py\" >> ~/.bash_profile
```

#####sort aliases on osx
On osx the alias command outputs all aliasses in sorted order

```bash
cat ~/.bash_profile > ~/.bash_profile.backup
cat ~/.bash_profile | grep -v alias | grep -v '^$' > ~/.bash_profile_without_alias;
alias | grep -v '^$' > ~/.bash_profile_only_alias;
cat ~/.bash_profile_without_alias > ~/.bash_profile
echo -e "\n" >>  ~/.bash_profile
cat ~/.bash_profile_only_alias >>  ~/.bash_profile
rm ~/.bash_profile_without_alias
rm ~/.bash_profile_only_alias
```
