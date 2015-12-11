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

class PyroFile (object):
    """
    Helper Pyro class providing an access to local file. It allows to receive/send the file content from/to remote site (using Pyro) in chunks of configured size.
    """

    def __init__ (self, filename, mode, buffsize=1024):
        """
        Constructor. Opens the corresponding file handle.
        
        :param str filename: file name to open
        :param str mode: file mode ("r" opens for reading, "w" opens for writting, "rb" read binary, "rw" write binary)
        :param int buffsize: optional size of file byte chunk that is to be transferred
        """
        self.filename = filename
        self.myfile = open(filename, mode)
        self.buffsize = buffsize

    def getChunk (self):
        """
        Reads and returns next buffsize bytes from open (should be opened in read mode).
        The returned chunk may contain less bytes if not enouch data can be read, or can be empty if end-of-file is reached.
        :return: Returns next chunk of data read from the file
        :rtype: str
        """
        data = self.myfile.read(self.buffsize)
        return data

    def setChunk (self, buffer):
        """
        Writes the given chunk of data into the file, which should be opened in write mode.
        
        :param str buffer: data chunk to append 
        """
        self.myfile.write(buffer)

    def close (self):
        """
        Closes the associated file handle.
        """
        self.myfile.close()
