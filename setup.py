# coding=utf-8
"""
appinstance
erik@a8.nl (04-03-15)
license: GNU-GPL2
"""
from setuptools import setup
setup(name='reposmon',
      version='1',
      description='Monitor a git repository, execute a command when it changes. Basically a polling git-hook for pull.',
      url='https://github.com/erikdejonge/reposmon',
      author='Erik de Jonge',
      author_email='erik@a8.nl',
      license='GPL',
      packages=['reposmon'],
      zip_safe=True)
