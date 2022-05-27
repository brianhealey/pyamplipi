#!/usr/bin/env python

import os
import sys

VERSION = '0.4.9'

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

license = """
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

setup(name='pyamplipi',
      version=VERSION,
      description='Python API for interacting with the AmpliPi Multizone Audio Controller',
      url='https://github.com/brianhealey/pyamplipi',
      download_url='https://github.com/brianhealey/pyamplipi/archive/{}.tar.gz'.format(VERSION),
      author='HeeHee Software',
      author_email='brian.healey@gmail.com',
      license='GPL',
      install_requires=[],
      packages=['pyamplipi'],
      classifiers=['Development Status :: 4 - Beta',
                   'Programming Language :: Python :: 3.5',
                   'Programming Language :: Python :: 3.6'],
      zip_safe=True)
