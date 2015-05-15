class PyroFile (object):
    def __init__ (self, filename, mode, buffsize=1024):
        self.filename = filename
        self.myfile = open(filename, mode)
        self.buffsize = buffsize

    def getChunk (self):
        data = self.myfile.read(self.buffsize)
        return data

    def setChunk (self, buffer):
        self.myfile.write(buffer)

    def close (self):
        self.myfile.close()
