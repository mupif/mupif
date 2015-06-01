'''
Created on 18.05.2015

@author: otolli/guillaume
'''
#from distutils.core import setup
import sys
import os
from setuptools import setup, find_packages
#from distutils2.core import setup

import mupif


#def is_package(path):
#    return (
#        os.path.isdir(path) and
#        os.path.isfile(os.path.join(path, '__init__.py'))
#    )

# def find_packages(path, base=""):
#     """ Find all packages in path """
#     packages = {}
#     for item in os.listdir(path):
#         dirWD = os.path.join(path, item)
#         if is_package(dirWD):
#             if base:
#                 module_name = "%(base)s.%(item)s" % vars()
#             else:
#                 module_name = item
#             packages[module_name] = dirWD
#             packages.update(find_packages(dirWD, module_name))
#     return packages

# packages = find_packages(".")



#ver=os.popen("sh ./version.sh", "r").read()
#ver=ver.rstrip()


setup(name='mupif',
      version='0.1',
      description='Mupif platform',
      author='guillaume',
      packages = find_packages(),
      author_email='info@mmp_project.eu',
      #package_dir=packages,
      #packages=packages.keys(),
      requires=['numpy', 'scipy', 'setuptools'],
      include_package_data=True,
      url='http://sourceforge.net/projects/mupif/',
      package_data={}
      )
