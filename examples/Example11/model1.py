import sys
sys.path.extend(['..', '../..'])
import time
import random
import numpy as np
import Pyro5.api

import mupif as mp
from mupif.units import U as u
import logging
log = logging.getLogger()

@Pyro5.api.expose
class Model1 (mp.Model):
    """
    Simple model that generates random grain state
    """
    def __init__(self, metadata={}):
        MD = {
            'Name': 'Application1',
            'ID': 'App1',
            'Description': 'Generates random grain state data',
            'Version_date': '02/2019',
            'Physics': {
                'Type': 'Atomistic',
                'Entity': 'Grains'
            },
            'Solver': {
                'Software': 'Python script',
                'Language': 'Python3',
                'License': 'LGPL',
                'Creator': 'Unknown',
                'Version_date': '02/2019',
                'Type': 'Generator',
                'Documentation': 'Nowhere',
                'Estim_time_step_s': 1,
                'Estim_comp_time_s': 0.01,
                'Estim_execution_cost_EUR': 0.01,
                'Estim_personnel_cost_EUR': 0.01,
                'Required_expertise': 'None',
                'Accuracy': 'High',
                'Sensitivity': 'High',
                'Complexity': 'Low',
                'Robustness': 'High'
            },
            'Inputs': [],
            'Outputs': [
                {'Type': 'mupif.GrainState', 'Type_ID': 'mupif.DataID.ID_GrainState', 'Name': 'Grain state',
                 'Description': 'Sample Random grain state', 'Units': 'None', 'Origin': 'Simulated'}]
        }
        super().__init__(metadata=MD)
        self.updateMetadata(metadata)
        self.grainState = None

    def initialize(self, workdir='', metadata={}, validateMetaData=True, **kwargs):
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)

    def get(self, objectTypeID, time=None, objectID=0):
        if objectTypeID == mp.DataID.ID_GrainState:
            return self.grainState
        else:
            raise mp.APIError('Unknown DataID')

    def set(self, obj, objectID=0):
        raise mp.APIError('Model has no inputs')

    def solveStep(self, tstep, stageID=0, runInBackground=False):

        # generate random grain state
        t0 = time.time()
        atomCounter = 0
        self.grainState = mp.heavystruct.HeavyStruct(id=mp.dataid.DataID.ID_GrainState, schemaName='org.mupif.sample.grain', schemasJson=mp.heavystruct.sampleSchemas_json)
        grains = self.grainState.openData(mode='create')
        grains.resize(size=2)
        for ig, g in enumerate(grains):
            g.getMolecules().resize(size=random.randint(5, 10))
            log.info(f"Grain #{ig} has {len(g.getMolecules())} molecules")
            for m in g.getMolecules():
                m.getIdentity().setMolecularWeight(random.randint(1, 10)*u.yg)
                m.getAtoms().resize(size=random.randint(30, 60))
                for a in m.getAtoms():
                    a.getIdentity().setElement(random.choice(['H', 'N', 'Cl', 'Na', 'Fe']))
                    a.getProperties().getTopology().setPosition((1, 2, 3)*u.nm)
                    a.getProperties().getTopology().setVelocity((24, 5, 77)*u.m/u.s)
                    struct = np.array([random.randint(1, 20) for i in range(random.randint(5, 20))], dtype='l')
                    a.getProperties().getTopology().setStructure(struct)
                    atomCounter += 1
        self.grainState.closeData()
        t1 = time.time()
        log.info(f'{atomCounter} atoms created in {t1-t0:g} sec ({atomCounter/(t1-t0):g}/sec).')
        md = {
                'Execution': {
                    'ID': self.getMetadata('Execution.ID'),
                    'Use_case_ID': self.getMetadata('Execution.Use_case_ID'),
                    'Task_ID': self.getMetadata('Execution.Task_ID')
                }
            }
        self.grainState.updateMetadata(md)

    def getCriticalTimeStep(self):
        return 1.*mp.U.s

    def getAssemblyTime(self, tstep):
        return tstep.getTime()

    def getApplicationSignature(self):
        return "Model1"
