import sys
sys.path.extend(['..', '../..'])
import time
import random
import numpy as np

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
                {'Type': 'mupif.GrainState', 'Type_ID': 'mupif.DataID.ID_GrainState', 'Name': 'Grain state',
                 'Description': 'Initial grain state', 'Units': 'None',
                 'Origin': 'Simulated', 'Required': True, "Set_at": "timestep"}
            ],
            'Outputs': [
                {'Type': 'mupif.GrainState', 'Type_ID': 'mupif.DataID.ID_GrainState', 'Name': 'Grain state',
                 'Description': 'Updated grain state with dopant', 'Units': 'None', 'Origin': 'Simulated'}]
        }
        super().__init__(metadata=MD)
        self.updateMetadata(metadata)
        self.inputGrainState = None
        self.outputGrainState = None

    def initialize(self, workdir='', metadata={}, validateMetaData=True, **kwargs):
        super().initialize(workdir=workdir, metadata=metadata, validateMetaData=validateMetaData, **kwargs)

    def get(self, objectTypeID, time=None, objectID=0):
        if objectTypeID == mp.DataID.PID_GrainState:
            return self.outputGrainState
        else:
            raise mp.APIError('Unknown property ID')

    def set(self, obj, objectID=0):
        if type(obj) == mp.heavydata.HeavyDataHandle:  # todo: test some ID as well
            if obj.id == mp.dataid.DataID.ID_GrainState:
                self.inputGrainState = obj
        else:
            raise mp.APIError('Unknown property ID')

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        # (1) read source grain state, into new state, then (2) replace a molecule with dopant (different molecule)
        print(self.inputGrainState)
        #
        # (1) copy old state into a new one
        #
        if 1:
            # transfer with cloneHandle which copies underlying storage
            self.outputGrainState = self.inputGrainState.cloneHandle()
            inGrains = self.inputGrainState.openData(mode='readonly')
            outGrains = self.outputGrainState.openData(mode='readwrite')
        elif 1:
            # transfer via inject (serializes into RAM, network-transparent)
            inGrains = self.inputGrainState.openData(mode='readonly')
            self.outputGrainState=mp.HeavyDataHandle(id=mp.dataid.DataID.ID_GrainState)
            log.warning(f'Created temporary {self.outputGrainState.h5path}')
            outGrains = self.outputGrainState.openData(mode='create',schemaName='org.mupif.sample.grain',schemasJson=mp.heavydata.sampleSchemas_json)
            outGrains.inject(inGrains)
        else:
            # transfer via explicit loop over data
            inGrains = self.inputGrainState.openData(mode='readonly')
            self.outputGrainState=mp.HeavyDataHandle(id=mp.dataid.DataID.ID_GrainState)
            log.warning(f'Created temporary {self.outputGrainState.h5path}')
            outGrains = self.outputGrainState.openData(mode='create',schemaName='org.mupif.sample.grain',schemasJson=mp.heavydata.sampleSchemas_json)
            t0=time.time()
            atomCounter=0
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
        #
        # replace one molecule in outGrains with a different molecule
        #
        if 1:
            # use inject to replace outGrains/1/molecules/2 with inGrains/0/molecules/3
            outGrains[1].getMolecules()[2].inject(inGrains[0].getMolecules()[3])
        else:
            # explicit loop over data, random molecule choice
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
        return "Model2"
