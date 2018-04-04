import sys
sys.path.extend(['..','../../..'])
from mupif import *
import Pyro4
import argparse
#Read int for mode as number behind '-m' argument: 0-local (default), 1-ssh, 2-VPN 
mode = argparse.ArgumentParser(parents=[Util.getParentParser()]).parse_args().mode
from thermalServerConfig import serverConfig
cfg = serverConfig(mode)
import logging
log = logging.getLogger()
import time as timeT
import mupif.Physics.PhysicalQuantities as PQ


def main():

    #locate nameserver
    ns = PyroUtil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport, hkey=cfg.hkey)
    #connect to JobManager running on (remote) server
    thermalJobMan = PyroUtil.connectJobManager(ns, cfg.jobManName, cfg.hkey)
    thermalSolver = None

    #allocate the application instances
    try:
        thermalSolver = PyroUtil.allocateApplicationWithJobManager( ns, thermalJobMan, cfg.jobNatPorts[0], cfg.hkey, PyroUtil.SSHContext(sshClient=cfg.sshClient, options=cfg.options, sshHost=cfg.sshHost) )
        log.info('Created thermal job')
 
    except Exception as e:
        log.exception(e)
    else:
        if ((thermalSolver is not None)):
            thermalSolverSignature=thermalSolver.getApplicationSignature()
            log.info("Working thermal solver on server " + thermalSolverSignature)

            log.info("Uploading input files to servers")
            pf = thermalJobMan.getPyroFile(thermalSolver.getJobID(), "input.in", 'wb')
            PyroUtil.uploadPyroFile("inputT.in", pf, cfg.hkey)
        else:
            log.debug("Connection to server failed, exiting")

    time = PQ.PhysicalQuantity(0., 's')
    dt = PQ.PhysicalQuantity(1., 's')
    targetTime = PQ.PhysicalQuantity(1., 's')
    istep = TimeStep.TimeStep(time, dt, targetTime)

    start = timeT.time()
    log.info('Timer started')
    log.info("Solving thermal problem")
    thermalSolver.solveStep(istep)
    log.info("Thermal problem solved")
    # get temperature field
    temperatureField = thermalSolver.getField(FieldID.FID_Temperature, istep.getTime())
    temperatureField.field2VTKData().tofile('T_distributed')
    #terminate
    log.info("Time consumed %f s" % (timeT.time()-start))



    thermalSolver.terminate()
    thermalJobMan.terminate()

    log.info("Test OK")

if __name__ == '__main__':
    main()


