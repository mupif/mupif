import clientConfig as cConf
from mupif import *

import time as timeTime
start = timeTime.time()
log.info('Timer started')

thermalSolverAppRec = None
mechanicalSolverAppRec = None
appsTunnel = None

thermalJobManName = 'Mupif.JobManager@ThermalSolverDemo'
mechanicalJobManName = 'Mupif.JobManager@MechanicalSolverDemo'

#locate nameserver
ns = PyroUtil.connectNameServer(nshost=cConf.nshost, nsport=cConf.nsport, hkey=cConf.hkey)
#connect to JobManager running on (remote) server and create a tunnel to it
thermalJobMan = PyroUtil.connectJobManager(ns, thermalJobManName, PyroUtil.SSHContext(sshClient=cConf.sshClient, options=cConf.options, sshHost=cConf.sshHost) )
mechanicalJobMan = PyroUtil.connectJobManager(ns, mechanicalJobManName, PyroUtil.SSHContext(sshClient=cConf.sshClient, options=cConf.options, sshHost=cConf.sshHost) )


#localize JobManager running on (remote) server and create a tunnel to it
#allocate the first application app1
try:
    thermalSolver = PyroUtil.allocateApplicationWithJobManager( ns, thermalJobMan, cConf.jobNatPorts.pop(0), PyroUtil.SSHContext(sshClient=cConf.sshClient, options=cConf.options, sshHost=cConf.sshHost) )
    mechanicalSolver = PyroUtil.allocateApplicationWithJobManager( ns, mechanicalJobMan, cConf.jobNatPorts.pop(0),PyroUtil.SSHContext(sshClient=cConf.sshClient, options=cConf.options, sshHost=cConf.sshHost ))

    #Create a reverse tunnel so mechanical server can access thermal server directly
    appsTunnel = PyroUtil.connectApplicationsViaClient(PyroUtil.SSHContext(sshClient=cConf.sshClient, options=cConf.options, sshHost=PyroUtil.getNSConnectionInfo(ns, mechanicalJobManName)[0]), thermalSolver)

except Exception as e:
    log.exception(e)
else:
    if ((thermalSolver is not None) and (mechanicalSolver is not None)):
        thermalSolverSignature=thermalSolver.getApplicationSignature()
        log.info("Working thermal solver on server " + thermalSolverSignature)

        mechanicalSolverSignature=mechanicalSolver.getApplicationSignature()
        log.info("Working mechanical solver on server " + mechanicalSolverSignature)

        log.info("Uploading input files to servers")
        pf = thermalJobMan.getPyroFile(thermalSolver.getJobID(), "input.in", 'wb')
        PyroUtil.uploadPyroFile("inputT.in", pf)
        mf = mechanicalJobMan.getPyroFile(mechanicalSolver.getJobID(), "input.in", 'wb')
        PyroUtil.uploadPyroFile("inputM.in", mf)

        log.info("Solving thermal problem on server " + thermalSolverSignature)
        thermalSolver.solveStep(None)
        #Get field's uri from thermal application and send it to mechanical application. This prevents copying data to Demo10's computer,
        #mechanical solver will use direct access to thermal field.
        log.info("Thermal problem solved")
        uri = thermalSolver.getFieldURI(FieldID.FID_Temperature, 0.0)
        log.info("URI of thermal problem's field is " + str(uri) )
        field = cConf.cfg.Pyro4.Proxy(uri)
        mechanicalSolver.setField(field)

        #Original version copied data to Demo10's computer and then to thermal solver. This can be time/memory consuming for large data
        #temperatureField = thermalSolver.getField(FieldID.FID_Temperature, 0.0)
        #mechanicalSolver.setField(temperatureField)

        log.info("Solving mechanical problem on server " + mechanicalSolver.getApplicationSignature())
        mechanicalSolver.solveStep(None)
        log.info("URI of mechanical problem's field is " + str(mechanicalSolver.getFieldURI(FieldID.FID_Displacement, 0.0)) )
        displacementField = mechanicalSolver.getField(FieldID.FID_Displacement, 0.0)
        # save results as vtk
        temperatureField = thermalSolver.getField(FieldID.FID_Temperature, 0.0)
        temperatureField.field2VTKData().tofile('temperatureField')
        displacementField.field2VTKData().tofile('displacementField')

        #terminate
        log.info("Time consumed %f s" % (timeTime.time()-start))
    else:
        log.debug("Connection to server failed, exiting")

finally:
    if appsTunnel: appsTunnel.terminate()


