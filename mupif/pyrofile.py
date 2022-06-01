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

from __future__ import annotations

import zlib
import Pyro5.api
import serpent
import pathlib
import typing
import shutil
import logging
import deprecated
import pydantic
import os.path
from .mupifobject import MupifObjectBase

log=logging.getLogger(__name__)


class PyroFile (MupifObjectBase):
    """
    Helper class wrapping file functionality, allowing copying files (both remote and local).
    """
    filename: str
    mode: str
    bufSize: int = 2**20
    compressFlag: bool = False

    def __init__(self, **kw):
        super().__init__(**kw)
        if self.mode not in ('rb', 'wb'):
            raise ValueError(f"mode must be 'rb' or 'wb' (not '{self.mode}').")
        self.fileobj = open(self.filename, self.mode)
        self.compressor = None
        self.decompressor = None

    @Pyro5.api.expose
    def rewind(self):
        self.fileobj.seek(0)

    @Pyro5.api.expose
    def getChunk(self):
        """
        Reads and returns next bufSize bytes from open (should be opened in read mode).
        The returned chunk may contain less bytes if not enouch data can be read, or can be empty if end-of-file is reached.
        :return: Returns next chunk of data read from the file
        :rtype: str
        """
        comp=zlib.compressobj() if self.compressFlag else None
        while True:
            data=self.fileobj.read(self.bufSize)
            #log.error(f'ø {len(data)} b')
            if not data:
                self.rewind() # we still rewind in copy as well, but it can't hurt
                return # EOF, no more data
            finish=(len(data)<self.bufSize) # EOF, some data still read
            if comp: data=comp.compress(data)+comp.flush(zlib.Z_SYNC_FLUSH)+(comp.flush(zlib.Z_FINISH) if finish else b'')
            #log.error(f'→ {len(data)} b')
            yield data
            # this saves one more call to read returning nothing
            if finish:
                self.rewind()
                return

    @Pyro5.api.expose
    def getBasename(self):
        return os.path.basename(self.filename)

    @Pyro5.api.expose
    def setChunk(self, buffer):
        """
        Writes the given chunk of data into the file, which should be opened in write mode.

        :param str buffer: data chunk to append
        """
        # https://pyro5.readthedocs.io/en/stable/tipstricks.html#binary-data-transfer-file-transfer
        if type(buffer) == dict:
            buffer = serpent.tobytes(buffer)
        if self.compressFlag:
            if not self.decompressor:
                self.decompressor = zlib.decompressobj()
            self.fileobj.write(self.decompressor.decompress(buffer))
        else:
            self.fileobj.write(buffer)

    @Pyro5.api.expose
    @deprecated.deprecated('PyroFile.setBuffSize is deprecated, use setBufSize instead')
    def setBuffSize(self, bs): self.setBufSize(bs)

    @Pyro5.api.expose
    def setBufSize(self, bufSize):
        """
        Allows to set the receiver buffer size.
        :param int bufSize: new buffer size
        """
        self.bufSize = bufSize

    @Pyro5.api.expose
    def setCompressionFlag(self, value=True):
        """
        Sets the compressionFlag to True
        """
        self.compressFlag = value

    @Pyro5.api.expose
    def close(self):
        """
        Closes the associated file handle.
        """
        self.fileobj.close()

    # MUST be called as mp.PyroFile.copy(src,dst)
    @staticmethod
    #@pydantic.validate_arguments # does not work yet, see https://stackoverflow.com/q/70965979
    def copy(src: typing.Union[PyroFile, Pyro5.api.Proxy, str, pathlib.Path],
             dst: typing.Union[PyroFile, Pyro5.api.Proxy, str, pathlib.Path],
             compress=True):
        """
        Copy the content of *src* to *dst*; any of them might be local instance of PyroFile,
        Pyro5.api.Proxy to remote PyroFile, or *str* or *pathlib.Path*. If both are local
        paths, fast-copy is done (without compression), otherwise the tranfer is done by
        chunks.
        """
        # fast-path if both are local files
        if isinstance(src, (str, pathlib.Path)) and isinstance(dst, (str, pathlib.Path)):
            shutil.copy(src, dst)
            return
        if isinstance(src, (str, pathlib.Path)):
            src = PyroFile(filename=src, mode='rb')
        else:
            src.rewind()  # necessary if the file was used already
        if isinstance(dst, (str, pathlib.Path)):
            dst = PyroFile(filename=dst, mode='wb')
        # both ends must have the same compression options
        src.setCompressionFlag(compress)
        dst.setCompressionFlag(compress)
        for data in src.getChunk():
            # log.error(f'← {len(data)} b')
            dst.setChunk(data)
        dst.close()
