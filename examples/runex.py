#!/usr/bin/env -S python3 -u
import subprocess, argparse, os, os.path, sys, time, typing, atexit, logging, multiprocessing
thisDir=os.path.dirname(os.path.abspath(__file__))
sys.path.append(thisDir+'/..')
multiprocessing.current_process().name='EX'
import mupif as mp
log=logging.getLogger('runex')
log.setLevel(logging.DEBUG)

parser=argparse.ArgumentParser('Run some/all MuPIF examples')
parser.add_argument('--codecov',action='store_true',help='Run with codecov')
parser.add_argument('--wenv',choices=['all','main','servers'],help='Run some components under *wenv*: the main script, associated servers, or both (all).')
parser.add_argument('exnum',nargs='*',type=str,help='Example numbers to run (if not given, all examples will be run)',metavar='N')
args=parser.parse_args(sys.argv[1:])

netOpts=[]

from dataclasses import dataclass
@dataclass
class ExCfg():
    num: str
    dir: str
    scripts: typing.List[str]
    skip: bool=False

allEx=[
    ExCfg('1','01-local',['Example01.py']),
    ExCfg('2','02-distrib',['Example02.py','server.py']),
    ExCfg('3','03-field-local',['Example03.py']),
    ExCfg('4','04-jobMan-distrib',['Example04.py','server.py']),
    ExCfg('5','05-units-local',['Example05.py']),
    ExCfg('6','06-stacTM-local',['Example06.py']),
    ExCfg('7','07-stacTM-JobMan-distrib',  ['Example07.py','thermalServer.py','mechanicalServer.py']),
    ExCfg('8','08-transiTM-JobMan-distrib',['Example08.py','thermalServer.py','mechanicalServer.py']),
    ExCfg('9','09-operatorEmail',['Example09.py'],skip=True),
    ExCfg('11','11',['workflow.py']),
    ExCfg('11d','11',['dist-ex11.py','dist-m1.py','dist-m2.py'],skip=True),
    ExCfg(13,'13',['main.py','server.py','application13.py'])
]


def getExec(main):
    if (main and args.wenv in ('all','main')) or (not main and args.wenv in ('all','servers')):
        ret=['wenv','python','-u']
    else: ret=[sys.executable,'-u']
    # don't run servers under coverage (some tests fail with busy ports; reason unknown)
    if args.codecov and main: ret+=['-m','coverage','run']
    return tuple(ret)

nsBg=mp.pyroutil.runNameserverBg()
import time
time.sleep(.5)

def runEx(ex):
    env=os.environ.copy()
    exDir=thisDir+'/'+ex.dir
    env['PYTHONPATH']=os.pathsep.join([thisDir+'/..',thisDir,exDir])
    env['MUPIF_NS']=f'{nsBg.host}:{nsBg.port}'
    bg=[]
    try:
        for iScript,script in enumerate(ex.scripts[1:]):
            cmd=[*getExec(main=False),script]+netOpts
            log.info(f'Running {cmd} in {exDir} (background)')
            bg.append(subprocess.Popen(cmd,cwd=exDir,env=env|{'MUPIF_LOG_PROCESSNAME':f'EX-{ex.num}/{iScript}'},bufsize=0))
        time.sleep(len(ex.scripts[1:])) # sleep one second per background server
        args=[*getExec(main=True),ex.scripts[0]]+netOpts
        log.info(f'Running {args} in {exDir}')
        ret=subprocess.run(args,cwd=exDir,env=env|{'MUPIF_LOG_PROCESSNAME':f'EX-{ex.num}/0'},bufsize=0).returncode
        return ret
    except:
        log.exception(f'Exception running example {ex.num}')
        return -1
    finally:
        failed=[]
        for b in bg:
            if b.returncode is not None: failed.append(b) # process died meanwhile
            else: b.terminate()
        time.sleep(.5)
        for b in bg:
            if b.returncode is None: b.kill()
        if failed: raise RuntimeError('Failed background processes:\n\n'+'\n * '.join([str(b.args) for b in failed]))

# no examples means all examples
if not args.exnum: args.exnum=[e.num for e in allEx if not e.skip]

runEex=[e for e in allEx if e.num in args.exnum]
failed=[]
for ex in runEex:
    log.info(f'==================== {ex.num} starting ================')
    retval=runEx(ex)
    log.info(f'==================== {ex.num} exited with {retval} ================')
    if retval!=0: failed.append(ex)

if failed:
    log.critical('** The following examples failed:')
    for f in failed:
        log.critical(f'**    {f.num} {f.dir}')
    sys.exit(1)
else:
    log.info('** All examples finished without error.')


