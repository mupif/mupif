import Pyro5
import sys
sys.path.extend(['.', '..', '../..'])
from mupif import pyroutil
import logging
log = logging.getLogger()

ns = Pyro5.api.locate_ns()

pyroutil.connectAppWithMetadata(ns, requiredMData={'model'}).getApplicationSignature()

print(pyroutil.connectAppWithMetadata(ns, requiredMData={'model'}, optionalMData={'Runtime_seconds'}).getModelMetadata()['ID'])
print(pyroutil.connectAppWithMetadata(ns, requiredMData={'model'}, optionalMData={'Runtime_minutes'}).getModelMetadata()['ID'])
print(pyroutil.connectAppWithMetadata(ns, requiredMData={'model', 'Accuracy_Medium'}, optionalMData={'Runtime_minutes'}).getModelMetadata()['ID'])
print(pyroutil.connectAppWithMetadata(ns, requiredMData={'model', 'Runtime_minutes'}, optionalMData={'Accuracy_high'}).getModelMetadata()['ID'])


