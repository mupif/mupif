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
            ],
            Models=[
                {
                    'Name': 'm1',
                    'Module': '',
                    'Class': '',
                    'Jobmanager': 'ex11-dist-m1'
                },
                {
                    'Name': 'm2',
                    'Module': '',
                    'Class': '',
                    'Jobmanager': 'ex11-dist-m2'
                }
            ]
        )
        super().__init__(metadata=MD)
        self.updateMetadata(metadata)

    def initialize(self,workdir='',metadata={}):
        ival = super().initialize(workdir=workdir, metadata=metadata)
        if ival is False:
            return False
        md=dict(Execution=dict(ID=self.getMetadata('Execution.ID'),Use_case_ID=self.getMetadata('Execution.Use_case_ID'),Task_ID=self.getMetadata('Execution.Task_ID')))
        ival = self.getModel('m1').initialize(workdir=self.getJobManager('m1').getJobWorkDir(self.getModel('m1').getJobID()),metadata=md)
        if ival is False:
            return False
        ival = self.getModel('m2').initialize(workdir=self.getJobManager('m2').getJobWorkDir(self.getModel('m2').getJobID()),metadata=md)
        if ival is False:
            return False
        return True

    def getCriticalTimeStep(self): return 1*mp.U.s
    def solveStep(self,istep,stageID=0,runInBackground=False):
        log.info('m1.solveStep…'); self.getModel('m1').solveStep(istep); log.info('… m1 done')
        # connect m1 output to m2 input
        self.getModel('m2').set(self.getModel('m1').get(mp.DataID.ID_GrainState))
        log.info('m2.solveStep…'); self.getModel('m2').solveStep(istep); log.info('… m2 done')
        log.debug(f'm2 output data: {self.getModel("m2").get(mp.DataID.ID_GrainState)}')

    def getApplicationSignature(self): return "Exmple 11 distributed"
    def getAPIVersion(self): return "1.0"

if __name__=='__main__':
    ex11=Example11_dist()
    md=dict(Execution=dict(ID='1',Use_case_ID='1_1',Task_ID='1'))
    ex11.initialize(metadata=md)
    ex11.solve()
    ex11.terminate()
    log.info('Example11 finished.')
