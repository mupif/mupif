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
        temperatureField = thermalSolver.getField(FieldID.FID_Temperature, 0.0)
        #
        mechanicalSolver.setField(temperatureField)
        mechanicalSolver.solveStep(None)
        displacementField = mechanicalSolver.getField(FieldID.FID_Displacement, 0.0)
        # save results as vtk
        temperatureField.field2VTKData().tofile('temperaturField')
        displacementField.field2VTKData().tofile('displacementField')

        #terminate
        logger.info("Time consumed %f s" % (timeTime.time()-start))
    else:
        logger.debug("Connection to server failed, exiting")

finally:
    if thermalSolverAppRec: thermalSolverAppRec.terminateAll()
    if mechanicalSolverAppRec: mechanicalSolverAppRec.terminateAll()



