import sys
sys.path.extend(['..', '../..'])
import time, random
import numpy as np
import os

import mupif as mp
from mupif.units import U as u
import logging
log = logging.getLogger()

class Model2 (mp.Model):
    """
    Simple model that replaces random molecule in grain by another one (dopant)
    """
    def __init__(self, metadata={}):
        MD = {
            'Name': 'Application2',
            'ID': 'App2',
            'Description': 'Replaces random molecule in grain by another one',
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
            'Inputs': [
                {'Type': 'mupif.GrainState', 'Type_ID': 'mupif.PropertyID.PID_GrainState', 'Name': 'Grain state',
                 'Description': 'Initial grain state', 'Units': 'None',
                 'Origin': 'Simulated', 'Required': True}
            ],
            'Outputs': [
                {'Type': 'mupif.GrainState', 'Type_ID': 'mupif.PropertyID.PID_GrainState', 'Name': 'Grain state',
                 'Description': 'Updated grain state with dopant', 'Units': 'None', 'Origin': 'Simulated'}]
        }
        super().__init__(metadata=MD)
        self.updateMetadata(metadata)
        self.inputGrainState=None
        self.outputGrainState=None

    def initialize(self, file='', workdir='', metadata={}, validateMetaData=True, **kwargs):
        super().initialize(file=file, workdir=workdir, metadata=metadata, validateMetaData=validateMetaData)

    def get(self, propID, time, objectID=0):
        if propID == mp.PropertyID.PID_GrainState:
            return self.outputGrainState
        else:
            raise mp.APIError('Unknown property ID')

    def set(self, prop, objectID=0):
        if (type(prop) == mp.heavydata.HeavyDataHandle): #todo: test some ID as well
            self.inputGrainState = prop
        else:
            raise mp.APIError('Unknown property ID')

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        # read source grain state, into new state, then replace random molecule with dopant
        t0=time.time()
        atomCounter = 0
        print(self.inputGrainState)
        self.outputGrainState=mp.HeavyDataHandle()
        log.warning(f'Created temporary {self.outputGrainState.h5path}')
        outGrains = self.outputGrainState.getData(mode='create',schemaName='grain',schemasJson=mp.heavydata.sampleSchemas_json)
        # readRoot fails if still open
        inGrains = self.inputGrainState.getData(mode='readonly')
        outGrains.resize(size=len(inGrains))
        #todo: copy inGrains to outGrains (check for more elegant way)
        for igNum,ig in enumerate(inGrains):
            outGrains[igNum].getMolecules().resize(size=len(ig.getMolecules()))
            for imNum, im in enumerate(ig.getMolecules()):
                om = outGrains[igNum].getMolecules()[imNum]
                om.getIdentity().setMolecularWeight(im.getIdentity().getMolecularWeight())
                om.getAtoms().resize(size=len(im.getAtoms()))
                for iaNum, ia in enumerate(im.getAtoms()):
                    oa = om.getAtoms()[iaNum]
                    oa.getIdentity().setElement(ia.getIdentity().getElement())
                    oa.getProperties().getTopology().setPosition(ia.getProperties().getTopology().getPosition())
                    oa.getProperties().getTopology().setVelocity(ia.getProperties().getTopology().getVelocity())
                    oa.getProperties().getTopology().setStructure(ia.getProperties().getTopology().getStructure())
                    atomCounter+=1
        t1=time.time()
        print(f'{atomCounter} atoms created in {t1-t0:g} sec ({atomCounter/(t1-t0):g}/sec).')
        #todo: replace random molecule with another one
        # select random grain and molecule
        t0=time.time()
        atomCounter = 0
        rgNum = random.randint(0,len(outGrains)-1)
        rmNum = random.randint(0,len(outGrains[rgNum].getMolecules())-1)
        repMol = outGrains[rgNum].getMolecules()[rmNum]
        # replace this molecule
        repMol.getIdentity().setMolecularWeight(random.randint(1,10)*u.yg)
        if (1): 
            #print(repMol.getAtoms()[0]) # call _T_assertDataset()
            #print (repMol.getAtoms())
            #print("Deleting "+repMol.getAtoms().ctx.h5group.name+'/'+repMol.getAtoms()[0].datasetName)
            ##todo: make a method to solve this
            #del self.outputGrainState._h5obj[repMol.getAtoms().ctx.h5group.name+'/'+repMol.getAtoms()[0].datasetName]
            repMol.getAtoms().resize(size=random.randint(30,60),reset=True)
            #print (repMol.getAtoms()[0])
            for a in repMol.getAtoms():
                a.getIdentity().setElement(random.choice(['H','N','Cl','Na','Fe']))
                a.getProperties().getTopology().setPosition((1,2,3)*u.nm)
                a.getProperties().getTopology().setVelocity((24,5,77)*u.m/u.s)
                struct=np.array([random.randint(1,20) for i in range(random.randint(5,20))],dtype='l')
                a.getProperties().getTopology().setStructure(struct)
                atomCounter+=1
        t1=time.time()
        print(f'{atomCounter} atoms replaced in {t1-t0:g} sec ({atomCounter/(t1-t0):g}/sec).')
        self.outputGrainState.closeData()

    def getCriticalTimeStep(self):
        return 1.*mp.U.s

    def getAssemblyTime(self, tstep):
        return tstep.getTime()

    def getApplicationSignature(self):
        return "Application1"
