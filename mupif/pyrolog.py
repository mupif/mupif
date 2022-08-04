import logging
import Pyro5
import Pyro5.api
import sys
import time
import pickle
import serpent


class PyroLogHandler(logging.StreamHandler):
    '''
    Handler which sends records over Pyro; there is no formatting happening on this side of the logger,
    it only sends pickled LogRecord over to the PyroLogReceiver side, which forwards the record to the
    logger on the remote side. That is where formatting happens.

    The handler should be set up automatically when MUPIF_LOG_PYRO is set.

    The *tag* is currently unused, but something similar should be used (and added to the formatter on
    the remote side) so that records are identified with their originating machine and model.
    '''
    def __init__(self,*,uri,tag):
        self.tag=tag
        self.remoteLog=Pyro5.api.Proxy(uri)
        super().__init__()
    def emit(self,record):
        record.tag=self.tag
        self.remoteLog.handleRecord(pickle.dumps(record))

@Pyro5.api.expose
class PyroLogReceiver(object):
    '''
    Receives LogRecords from remote PyroLogHandler and dispatches them to the local logging system.
    Formatting happens as configured locally.
    '''
    def __init__(self):
        self.log=logging.getLogger('PyroLogReceiver')
    def handleRecord(self,recPickle):
        if isinstance(recPickle,dict): recPickle=serpent.tobytes(recPickle)
        rec=pickle.loads(recPickle)
        # print(f'{rec.tag=}')
        self.log.handle(rec)

if __name__=='__main__':
    #
    # 1. run the receiver with "python pyrolog.py --server"; it will display its URI, leave it running
    #
    # 2. run the client with "python pyrolog PYRO:obj_a9592911d4af4e99b5c73ecf9c5e7a87@127.0.0.1:46119";
    #    It will log 3 messages to the remote end.
    #
    Pyro5.configure.PYRO_SERVERTYPE='multiplex'
    Pyro5.configure.SERIALIZER='serpent'
    if sys.argv[1]=='--server':
        import mupif as mp
        daemon=mp.pyroutil.getDaemon()
        recvr=PyroLogReceiver()
        uri=daemon.register(recvr)
        print(f'Receiver URI {uri}')
        while True: time.sleep(1)
    else:
        logging.basicConfig(level=logging.DEBUG)
        pyroHandler=PyroLogHandler(uri=sys.argv[1],tag='foobar')
        log=logging.getLogger()
        log.addHandler(pyroHandler)
        log.info('This is being logged over Pyro (info)')
        time.sleep(.5)
        log.warning('This is being logged over Pyro (warning)')
        time.sleep(.5)
        log.error('This is being logged over Pyro (error)')
        time.sleep(.5)


