# 
#           MuPIF: Multi-Physics Integration Framework 
#               Copyright (C) 2010-2014 Borek Patzak
# 
#    Czech Technical University, Faculty of Civil Engineering,
#  Department of Structural Mechanics, 166 29 Prague, Czech Republic
# 
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, 
# Boston, MA  02110-1301  USA
#
import logging
import argparse
import os

import Pyro5

_formatLog = '%(asctime)s [%(process)d|%(threadName)s] %(levelname)s:%(filename)s:%(lineno)d %(message)s'
_formatTime = '%H:%M:%S'  # '%Y-%m-%d %H:%M:%S'


def setupLoggingAtStartup():
    """
    Configure global python logging system at MuPIF import. As this happens automatically,
    all parameters are passed via environment variables:

    * **MUPIF_LOG_LEVEL**, if given, will set log level for the main (root) logger; the value must be one of
      `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` (see [Logging levels](https://docs.python.org/3/library/logging.html#logging-levels));
      nothing is done if this env var is not defined.

    * **MUPIF_LOG_FILE**, if given, will (in addition to console output) write log messages to the file given.
      The file will be overwritten if it exists. No redirection to file is done if this env var is not defined.

    In addition, some formatting options will be changed for the whole Python logging system:

    * `colorlog` will be used for formatting console messages (if importable).

    """
    root=logging.getLogger()

    level=os.environ.get('MUPIF_LOG_LEVEL',None)
    if level is not None:
        root.setLevel(level)

    out=os.environ.get('MUPIF_LOG_FILE',None)
    if out is not None:
        fileHandler=logging.FileHandler(out, mode='w')
        fileHandler.setFormatter(logging.Formatter(_formatLog, _formatTime))
        root.addHandler(fileHandler)

    try:
        import colorlog
        streamHandler=colorlog.StreamHandler()
        streamHandler.setFormatter(colorlog.ColoredFormatter('%(asctime)s %(log_color)s%(levelname)s:%(filename)s:%(lineno)d %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    except ImportError:
        streamHandler=logging.StreamHandler()
        streamHandler.setFormatter(logging.Formatter(_formatLog, _formatTime))

    root.addHandler(streamHandler)


def redirectLog(out):
    """
    Change root logger by giving a new file name. Useful in parallel processes on a single machine.
    
    :return: Nothing
    """
    root = logging.getLogger()  # root logger
    # remove all old handlers
    for hdlr in root.handlers[:]: root.removeHandler(hdlr)
    h=logging.FileHandler(out,mode='w')
    h.setFormatter(logging.Formatter(_formatLog,_formatTime))
    root.addHandler(h)


def quadratic_real(a, b, c):
    """ 
    Finds real roots of quadratic equation: ax^2 + bx + c = 0. By substituting x = y-t and t = a/2, the equation reduces to y^2 + (b-t^2) = 0 which has easy solution y = +/-sqrt(t^2-b)

    :param float a: Parameter from quadratic equation
    :param float b: Parameter from quadratic equation
    :param float c: Parameter from quadratic equation
    :return: Two real roots if they exist
    :rtype: tuple
    """ 
    import math
    if math.fabs(a) <= 1.e-10:
        if math.fabs(b) <= 1.e-10:
            return ()
        else:
            return (-c/float(b),)
    else:
        a, b = b / float(a), c / float(a) 
        t = a / 2.0 
        r = t**2 - b 
        if r >= 0:  # real roots
            y1 = math.sqrt(r) 
        else:  # complex roots
            return ()
        y2 = -y1 
        return y1 - t, y2 - t


def NoneOrInt(arg):
    """ 
    Check if None or Int types.
    :param str,int arg: Parameter
        
    :return: argument (converted to int)
    :rtype: None of int
    """
    if arg is None:
        return None
    else:
        return int(arg)


def getVersion():
    '''
    Return structured data about this mupif installation. Supports:

    * regular in-place install: ``pip install git+https://github.com/mupif/mupif@master``
    * editable install ``pip install -e git+https://...`` (relies on the gitpython module)
    * symlinked to Python path from local repository checkout

    Does *not* support legacy ``pip install mupif``.

    The returned named tuple has ``url``, ``branch`` and ``commit`` fields.
    '''
    import mupif
    import importlib.metadata
    import collections
    import os.path
    import json
    # use realpath instead of abspath to resolve symlinks
    # (for installs where mupif/ is symlinked into module directory, where ../.git would not resolve correctly)
    mupifDir=os.path.dirname(os.path.realpath(mupif.__file__))
    MupifVerInfo=collections.namedtuple('VerInfo','url branch commit') # timestamp

    # editable checkout, use git
    if os.path.exists(mupifDir+'/../.git'):
        try: import git
        except ImportError as ie: raise ImportError('Install gitpython first.') from ie
        repo=git.Repo(mupifDir+'/../')
        return MupifVerInfo(
            url=list(repo.remote().urls)[0],
            branch=repo.head.reference.name,
            commit=repo.head.commit.hexsha,
            # timestamp=repo.head.commited_datetime
        )
    # direct install from remote path
    try:
        dist=importlib.metadata.distribution('mupif')
        url=[f for f in dist.files if f.name=='direct_url.json']
        if len(url)==1:
            dta=json.load(open(url[0].locate()))
            return MupifVerInfo(
                url=dta['url'],
                branch=dta['vcs_info']['requested_revision'],
                commit=dta['vcs_info']['commit_id']
            )
    except importlib.metadata.PackageNotFoundError: pass

    raise RuntimeError('Unable to get version data (did you install via "pip install mupif"?).')
