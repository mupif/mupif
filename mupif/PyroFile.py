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

import zlib
import Pyro4

@Pyro4.expose
class PyroFile (object):
    """
    Helper Pyro class providing an access to local file. It allows to receive/send the file content from/to remote site (using Pyro) in chunks of configured size.
    """

    def __init__ (self, filename, mode, buffsize=1024, compressFlag=False):
        """
        Constructor. Opens the corresponding file handle.

        :param str filename: file name to open
        :param str mode: file mode ("r" opens for reading, "w" opens for writting, "rb" read binary, "rw" write binary)
        :param int buffsize: optional size of file byte chunk that is to be transferred
        :param bool compressFlag: whether set to True the chunks given/set are compressed uzing zlib module, default is False
        """
        self.filename = filename
        self.myfile = open(filename, mode)
        self.buffsize = buffsize
        self.compressFlag = compressFlag
        self.compressor = None
        self.decompressor = None

    def getChunk (self):
        """
        Reads and returns next buffsize bytes from open (should be opened in read mode).
        The returned chunk may contain less bytes if not enouch data can be read, or can be empty if end-of-file is reached.
        :return: Returns next chunk of data read from the file
        :rtype: str
        """
        data = self.myfile.read(self.buffsize)
        if (data and self.compressFlag):
            if not self.compressor:
                self.compressor = zlib.compressobj()
            data = self.compressor.compress(data) + self.compressor.flush(zlib.Z_SYNC_FLUSH)
        return data

    def getTerminalChunk(self):
        """
        Reads and returns the terminal bytes from source. In case of of source without compression, an empty string should be returned,
        in case of compressed stream the termination sequence is returned (see zlib flush(Z_FINAL))
        :rtype: str
        """
        if (self.compressFlag):
            return self.compressor.flush(zlib.Z_FINISH)
        else:
            return ""

    def setChunk (self, buffer):
        """
        Writes the given chunk of data into the file, which should be opened in write mode.

        :param str buffer: data chunk to append
        """
        if (self.compressFlag):
            if not self.decompressor:
                self.decompressor = zlib.decompressobj()
            self.myfile.write(self.decompressor.decompress(buffer))
        else:
            self.myfile.write(buffer)

    def setBuffSize (self, buffSize):
        """
        Allows to set the receiver buffer size.
        :param int buffSize: new buffer size
        """
        self.buffsize = buffSize

    def setCompressionFlag (self):
        """
        Sets the compressionFlag to True
        """
        self.compressFlag = True

    def close (self):
        """
        Closes the associated file handle.
        """
        self.myfile.close()
