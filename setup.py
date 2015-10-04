# coding=utf-8
"""
appinstance
-
Active8 (04-03-15)
author: erik@a8.nl
license: GNU-GPL2
"""

from setuptools import setup
setup(name='reposmon',
      version='65',
      description='Monitor a git repository, execute a command when it changes. Basically a polling git-hook for pull.',
      url='https://github.com/erikdejonge/reposmon',
      author='Erik de Jonge',
      author_email='erik@a8.nl',
      license='GPL',
      entry_points={
          'console_scripts': [
              'reposmon=reposmon:main',
          ],
      },
      packages=['reposmon'],
      zip_safe=True,
      #install_requires=['consoleprinter', 'sh', 'arguments', 'appinstance', 'schema', 'GitPython', 'pyyaml', 'docopt', 'psutil'],
      classifiers=[
          "Programming Language :: Python",
          "Programming Language :: Python :: 3",
          "Development Status :: 4 - Beta ",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
          "Operating System :: POSIX",
          "Topic :: Software Development :: Quality Assurance",
          "Topic :: System",
      ])
