import clientConfig as cConf
from mupif import *
import logging
logger = logging.getLogger()

import time as timeTime
start = timeTime.time()
logger.info('Timer started')

#locate nameserver
ns = PyroUtil.connectNameServer(nshost=cConf.nshost, nsport=cConf.nsport, hkey=cConf.hkey)

#localize JobManager running on (remote) server and create a tunnel to it
#allocate the first application app1
try:
    thermalSolverAppRec = PyroUtil.allocateApplicationWithJobManager( ns, cConf.thermalSolverJobManRec, cConf.jobNatPorts.pop(0), cConf.sshClient, cConf.options, cConf.sshHost )
    mechanicalSolverAppRec = PyroUtil.allocateApplicationWithJobManager( ns, cConf.mechanicalSolverJobManRec, cConf.jobNatPorts.pop(0), cConf.sshClient, cConf.options, cConf.sshHost )

    thermalSolver = thermalSolverAppRec.getApplication()
    mechanicalSolver = mechanicalSolverAppRec.getApplication()

    #Create a reverse tunnel so mechanical server can access thermal server directly
    appsTunnel = PyroUtil.connectApplicationsViaClient(cConf.mechanicalSolverJobManRec, thermalSolver, sshClient=cConf.sshClient, options=cConf.options )

except Exception as e:
    logger.exception(e)
else:
    if ((thermalSolver is not None) and (mechanicalSolver is not None)):
        thermalSolverSignature=thermalSolver.getApplicationSignature()
        logger.info("Working thermal solver on server " + thermalSolverSignature)

        mechanicalSolverSignature=mechanicalSolver.getApplicationSignature()
        logger.info("Working mechanical solver on server " + mechanicalSolverSignature)

        logger.info("Uploading input files to servers")
        pf = thermalSolverAppRec.getJobManager().getPyroFile(thermalSolverAppRec.getJobID(), "input.in", 'w')
        PyroUtil.downloadPyroFile("inputT.in", pf)
        mf = mechanicalSolverAppRec.getJobManager().getPyroFile(mechanicalSolverAppRec.getJobID(), "input.in", 'w')
        PyroUtil.downloadPyroFile("inputM.in", mf)

        logger.info("Solving thermal problem on server " + thermalSolverSignature)
        thermalSolver.solveStep(None)
        #Get field's uri from thermal application and send it to mechanical application. This prevents copying data to Demo10's computer,
        #mechanical solver will use direct access to thermal field.
        uri = thermalSolver.getFieldURI(FieldID.FID_Temperature, 0.0)
        #logger.info("URI of thermal problem is " + str(uri) )
        field = cConf.cfg.Pyro4.Proxy(uri)
        mechanicalSolver.setField(field)

        #Original version copied data to Demo10's computer and then to thermal solver. This can be time/memory consuming for large data
        #temperatureField = thermalSolver.getField(FieldID.FID_Temperature, 0.0)
        #mechanicalSolver.setField(temperatureField)

        mechanicalSolver.solveStep(None)
        displacementField = mechanicalSolver.getField(FieldID.FID_Displacement, 0.0)
        # save results as vtk
        temperatureField = thermalSolver.getField(FieldID.FID_Temperature, 0.0)
        temperatureField.field2VTKData().tofile('temperatureField')
        displacementField.field2VTKData().tofile('displacementField')

        #terminate
        logger.info("Time consumed %f s" % (timeTime.time()-start))
    else:
        logger.debug("Connection to server failed, exiting")

finally:
    if thermalSolverAppRec: thermalSolverAppRec.terminateAll()
    if mechanicalSolverAppRec: mechanicalSolverAppRec.terminateAll()
    if appsTunnel: appsTunnel.terminate()


