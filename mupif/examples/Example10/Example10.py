import clientConfig as cConf
from mupif import *
import time as timeTime
import logging
log = logging.getLogger()

thermalJobManName = 'Mupif.JobManager@ThermalSolverDemo'
mechanicalJobManName = 'Mupif.JobManager@MechanicalSolverDemo'

class Demo10(Workflow.Workflow):
   
    def __init__ (self, targetTime=0.):
        """
        Initializes the workflow. As the workflow is non-stationary, we allocate individual 
        applications and store them within a class.
        """
        super(Demo10, self).__init__(file='', workdir='', targetTime=targetTime)

        #locate nameserver
        ns = PyroUtil.connectNameServer(nshost=cConf.nshost, nsport=cConf.nsport, hkey=cConf.hkey)
        #connect to JobManager running on (remote) server and create a tunnel to it
        self.thermalJobMan = PyroUtil.connectJobManager(ns, thermalJobManName, cConf.hkey,  PyroUtil.SSHContext(sshClient=cConf.sshClient, options=cConf.options, sshHost=cConf.sshHost) )
        self.thermalSolver = None
        self.mechanicalJobMan = PyroUtil.connectJobManager(ns, mechanicalJobManName, cConf.hkey, PyroUtil.SSHContext(sshClient=cConf.sshClient, options=cConf.options, sshHost=cConf.sshHost) )

        #allocate the application instances
        try:
            self.thermalSolver = PyroUtil.allocateApplicationWithJobManager( ns, self.thermalJobMan, cConf.jobNatPorts.pop(0), cConf.hkey, PyroUtil.SSHContext(sshClient=cConf.sshClient, options=cConf.options, sshHost=cConf.sshHost) )
            self.mechanicalSolver = PyroUtil.allocateApplicationWithJobManager( ns, self.mechanicalJobMan, cConf.jobNatPorts.pop(0), cConf.hkey, PyroUtil.SSHContext(sshClient=cConf.sshClient, options=cConf.options, sshHost=cConf.sshHost ))

            #Create a reverse tunnel so mechanical server can access thermal server directly
            self.appsTunnel = PyroUtil.connectApplicationsViaClient(PyroUtil.SSHContext(sshClient=cConf.sshClient, options=cConf.options, sshHost=PyroUtil.getNSConnectionInfo(ns, mechanicalJobManName)[0]), self.thermalSolver)

        except Exception as e:
            log.exception(e)
        else:
            if ((self.thermalSolver is not None) and (self.mechanicalSolver is not None)):
                thermalSolverSignature=self.thermalSolver.getApplicationSignature()
                log.info("Working thermal solver on server " + thermalSolverSignature)

                mechanicalSolverSignature=self.mechanicalSolver.getApplicationSignature()
                log.info("Working mechanical solver on server " + mechanicalSolverSignature)

                log.info("Uploading input files to servers")
                pf = self.thermalJobMan.getPyroFile(self.thermalSolver.getJobID(), "input.in", 'wb')
                PyroUtil.uploadPyroFile("inputT.in", pf, cConf.hkey)
                mf = self.mechanicalJobMan.getPyroFile(self.mechanicalSolver.getJobID(), "input.in", 'wb')
                PyroUtil.uploadPyroFile("inputM.in", mf, cConf.hkey)
            else:
                log.debug("Connection to server failed, exiting")



    def solveStep(self, istep, stageID=0, runInBackground=False):

        start = timeTime.time()
        log.info('Timer started')
        log.info("Solving thermal problem")
        print(self.thermalSolver.getApplicationSignature())
        #self.thermalSolver._pyroHmacKey = cConf.hkey.encode(encoding='UTF-8')
        self.thermalSolver.solveStep(tstep=1.)
        #Get field's uri from thermal application and send it to mechanical application.
        #This prevents copying data to Demo10's computer,
        #mechanical solver will use direct access to thermal field.
        log.info("Thermal problem solved")
        uri = self.thermalSolver.getFieldURI(FieldID.FID_Temperature, 0.0)
        log.info("URI of thermal problem's field is " + str(uri) )
        field = cConf.cfg.Pyro4.Proxy(uri)
        #field._pyroHmacKey = cConf.hkey.encode(encoding='UTF-8')
        self.mechanicalSolver.setField(field)

        #Original version copied data to Demo10's computer and then to thermal solver.
        #This can be time/memory consuming for large data
        #temperatureField = self.thermalSolver.getField(FieldID.FID_Temperature, 0.0)
        #self.mechanicalSolver.setField(temperatureField)

        log.info("Solving mechanical problem")
        self.mechanicalSolver.solveStep(None)
        log.info("URI of mechanical problem's field is " + str(self.mechanicalSolver.getFieldURI(FieldID.FID_Displacement, 0.0)) )
        displacementField = self.mechanicalSolver.getField(FieldID.FID_Displacement, 0.0)
        # save results as vtk
        temperatureField = self.thermalSolver.getField(FieldID.FID_Temperature, 0.0)
        temperatureField.field2VTKData().tofile('temperatureField')
        displacementField.field2VTKData().tofile('displacementField')

        #terminate
        log.info("Time consumed %f s" % (timeTime.time()-start))


    def getCriticalTimeStep(self):
        # determine critical time step
        return 1.0

    def terminate(self):
        
        #self.thermalAppRec.terminateAll()
        self.thermalSolver.terminate()
        self.thermalJobMan.terminate()
        self.mechanicalSolver.terminate()
        self.mechanicalJobMan.terminate()
        self.appsTunnel.terminate()
        super(Demo10, self).terminate()

    def getApplicationSignature(self):
        return "Demo10 workflow 1.0"

    def getAPIVersion(self):
        return "1.0"

    
if __name__=='__main__':
    demo = Demo10(targetTime=1.)
    demo.solve()


