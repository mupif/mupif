'''
Created 3.6.2015
@author: Vit Smilauer and Guillaume Pacquaut
'''

import sys
import os

from setuptools import setup, find_packages

setup(name='mupif',
      version='0.1',
      description='Mupif platform',
      author='guillaume',
      author_email='info@mmp_project.eu',
      packages = ['mupif'],
      #package_dir={'mupif': 'tools'},#this looks where to find __init__.py
      package_data={'mupif': [ '../tools/*.py', '../examples/Ex*/*.*', '../examples/Pi*/*.*', '../examples/Workshop02/*.py', '../doc/refManual/MuPIF.pdf', '../doc/userGuide/MuPIF-userGuide.pdf' ]},#This line is only for python setup.py bdist, for PyPI see MANIFEST.in
      requires=['numpy', 'scipy', 'setuptools'],
      include_package_data=True,
      url='http://sourceforge.net/projects/mupif/'
      )

