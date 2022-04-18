import Pyro5.api
from typing import *

import mupif as mp

import logging
log = logging.getLogger()
log.setLevel(logging.INFO)

log.setLevel(logging.INFO)
class Example11_dist(mp.Workflow):
    def __init__(self,metadata={}):
        MD=dict(
            Name='Generate random grain with dopant',
            ID='Example11-distrib',
            Description='Generate random grain with dopant (distributed workflow)',
            # 'Dependencies' are generated automatically
            Version_date='1.0.0, Feb 2019',
            Inputs=[],
            Outputs=[
                dict(Type='mupif.GrainState',Type_ID='mupif.DataID.ID_GrainState',Name='Grain state',Description='Random grain state (model1) with dopand (added by model2)',Units='None',Origin='Simulated')
            ]
        )
        super().__init__(metadata=MD)
        self.updateMetadata(metadata)

    def initialize(self,workdir='',metadata={}):
        self.ns=mp.pyroutil.connectNameserver()
        self.m1jobman=mp.pyroutil.connectJobManager(self.ns,'ex11-dist-m1')
        self.m2jobman=mp.pyroutil.connectJobManager(self.ns,'ex11-dist-m2')
        self.m1app=mp.pyroutil.allocateApplicationWithJobManager(ns=self.ns,jobMan=self.m1jobman)
        self.m2app=mp.pyroutil.allocateApplicationWithJobManager(ns=self.ns,jobMan=self.m2jobman)
        self.registerModel(self.m1app,'m1')
        self.registerModel(self.m2app,'m2')
        super().initialize(workdir=workdir,metadata=metadata)

        md=dict(Execution=dict(ID=self.getMetadata('Execution.ID'),Use_case_ID=self.getMetadata('Execution.Use_case_ID'),Task_ID=self.getMetadata('Execution.Task_ID')))
        self.m1app.initialize(workdir=self.m1jobman.getJobWorkDir(self.m1app.getJobID()),metadata=md)
        self.m2app.initialize(workdir=self.m2jobman.getJobWorkDir(self.m2app.getJobID()),metadata=md)
    def getCriticalTimeStep(self): return 1*mp.U.s
    def solveStep(self,istep,stageID=0,runInBackground=False):
        log.info('m1.solveStep…'); self.m1app.solveStep(istep); log.info('… m1 done')
        # connect m1 output to m2 input
        self.m2app.set(self.m1app.get(mp.DataID.ID_GrainState))
        log.info('m2.solveStep…'); self.m2app.solveStep(istep); log.info('… m2 done')
        log.debug(f'm2 output data: {self.m2app.get(mp.DataID.ID_GrainState)}')
    def terminate(self):
        for a in (self.m1app,self.m2app): a.terminate()
        super().terminate()
    def getApplicationSignature(self): return "Exmple 11 distributed"
    def getAPIVersion(self): return "1.0"

if __name__=='__main__':
    ex11=Example11_dist()
    md=dict(Execution=dict(ID='1',Use_case_ID='1_1',Task_ID='1'))
    ex11.initialize(metadata=md)
    ex11.solve()
    ex11.terminate()
    log.info('Example11 finished.')
