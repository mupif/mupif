"""
Several model servers for one workflow model: instances, model ID and execution profiles.

Run with ``python runex.py 14``, which starts ``server.py`` twice (two instances of
``example14.mechanical``) and ``server1.py`` (``example14.mechanical-alt``, same model); every
server runs one job at a time. The workflow's model accepts the model server
``example14.mechanical`` (``Jobmanager``) or any server of the model ``Mechanical-1``
(``ModelID``), i.e. all three servers. Shown:

* default execution profile: workflows started together are spread over the servers, the least
  loaded first; when all are busy, the next workflow gets ``ModelServerNoResourcesException``;
* profile 0 prefers servers tagged ``example14.mechanical-alt`` (optional metadata);
* profile 1 requires the tag ``example14.mechanical``: only the two instances of that name.
"""
import sys
sys.path.extend(['.', '..', '../..'])
import mupif as mp
import logging
log = logging.getLogger()


class Example14(mp.Workflow):

    def __init__(self, metadata=None):
        MD = {
            'Name': 'Several model servers',
            'ID': 'example14',
            'Description': 'Placement of a model on one of several compatible model servers',
            'Version_date': '1.0.0, Nov 2026',
            'Inputs': [],
            'Outputs': [],
            'Models': [
                {
                    'Name': 'model',
                    # all instances of this model server ...
                    'Jobmanager': 'example14.mechanical',
                    # ... and any other server of the same model
                    'ModelID': 'Mechanical-1',
                }
            ],
            'ExecutionProfiles': [
                {
                    'Name': 'Prefer the alternative server',
                    'Cost': '$$',
                    'Description': 'Any compatible server, the alternative one if it is free',
                    'Models': [{'Name': 'model', 'RequiredModelMetadata': [], 'OptionalModelMetadata': ['example14.mechanical-alt']}]
                },
                {
                    'Name': 'Main servers only',
                    'Cost': '$',
                    'Description': 'Only the instances of example14.mechanical',
                    'Models': [{'Name': 'model', 'RequiredModelMetadata': ['example14.mechanical'], 'OptionalModelMetadata': []}]
                },
            ]
        }
        super().__init__(metadata=MD)
        self.updateMetadata(metadata)

    def solveStep(self, istep, stageID=0, runInBackground=False):
        pass

    def getCriticalTimeStep(self):
        return 1*mp.U.s

    def getApplicationSignature(self):
        return "Example14 workflow 1.0"

    def getAPIVersion(self):
        return "1.0"


def start(profile=-1):
    'Start a workflow with the given execution profile; return it and the model server of its model.'
    wf = Example14()
    wf.initialize(metadata={'Execution': {'ID': '1', 'Use_case_ID': '1_1', 'Task_ID': '1', 'ExecutionProfileIndex': profile}})
    server = wf.getModelServers()['model']
    print(f'profile {profile}: model allocated on {server}')
    return wf, server


if __name__ == '__main__':
    ns = mp.pyroutil.connectNameserver()
    servers = sorted(ns.yplookup(meta_all={'type:jobmanager', 'ModelID:Mechanical-1'}))
    print('model servers of Mechanical-1:', servers)
    assert len(servers) == 3, servers

    # default profile: three workflows at once occupy the three servers
    running = [start() for i in range(3)]
    assert sorted(s for _, s in running) == servers
    try:
        start()
        raise AssertionError('all model servers are busy, the allocation should have failed')
    except mp.modelserverbase.ModelServerNoResourcesException:
        print('fourth workflow: no free model server, as expected')
    for wf, _ in running:
        wf.terminate()

    # profile 0: the preferred server
    wf, server = start(0)
    assert server == 'example14.mechanical-alt', server
    wf.terminate()

    # profile 1: only the instances of example14.mechanical
    wf, server = start(1)
    assert server.startswith('example14.mechanical') and server != 'example14.mechanical-alt', server
    wf.terminate()

    log.info("Test OK")
    print("OK")
