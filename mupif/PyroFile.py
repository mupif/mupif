class PyroFile:
    def __init__ (self, filename, mode, buffsize=1024):
        self.filename = filename
        self.file = open(filename, mode)
        self.buffsize = buffsize

    def __del__ (self):
        self.close()

    def getChunk (self):
        return self.file.read(self.buffsize)

    def setChunk (self, buffer):
        self.file.write(buffer)

    def close (self):
        self.file.close()
