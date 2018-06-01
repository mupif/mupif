#!/usr/bin/env python

import socketserver, subprocess, sys
from threading import Thread
import getopt
HOST = ''   # Symbolic name, meaning all available interfaces
PORT = 2000 # override using -r portnum 


def usage():
    print("Usage: testserver.py -r port")
    print()
    print("port : port where nameserver listens")
    print() 



class SingleTCPHandler(socketserver.BaseRequestHandler):
    "One instance per connection.  Override handle(self) to customize action."
    def handle(self):
        # self.request is the client connection
        print("Connection from: ", self.client_address)
        self.request.send('Hello!\n'.encode('utf-8'))
        data = self.request.recv(1024)  # clip input at 1Kb
        text = data.decode('utf-8')
        print('Received:'+text)
        self.request.send('OK'.encode('utf-8'))
        self.request.close()

class SimpleServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    # Ctrl-C will cleanly kill all spawned threads
    daemon_threads = True
    # much faster rebinding
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass):
        socketserver.TCPServer.__init__(self, server_address, RequestHandlerClass)

if __name__ == "__main__":

    try:
        opts, args = getopt.getopt(sys.argv[1:], "r:")
    except getopt.GetoptError as err:
        # print help information and exit:
        # log.exception(err)
        usage()
        sys.exit(2)

    for o, a in opts:
        if o in ("-r"):
            PORT = int(a)
    
        else:
            usage()
            sys.exit(2)
            

    print ("Simple server listening on port "+str(PORT)+"\n")
    server = SimpleServer((HOST, PORT), SingleTCPHandler)
    # terminate with Ctrl-C
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)
