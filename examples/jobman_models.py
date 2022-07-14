import sys
sys.path += ['..']
import models
import mupif as mp


if len(sys.argv) >= 2:

    model_name = sys.argv[1]
    model_class = None
    idx = None
    if model_name == 'sm':
        model_class = models.MechanicalModel
        idx = 'MuPIF.Example.Mechanical'
    if model_name == 'tm-stat':
        model_class = models.ThermalModel
        idx = 'MuPIF.Example.Thermal_stat'
    if model_name == 'tm-nonstat':
        model_class = models.ThermalNonstatModel
        idx = 'MuPIF.Example.Thermal_nonstat'

    if model_class:
        ns = mp.pyroutil.connectNameserver()

        # Run job manager on a server
        jobMan = mp.SimpleJobManager(
            ns=ns,
            appClass=model_class,
            appName=idx,
        ).runServer()
    else:
        print('Type model identifier argument from: ("sm", "tm-stat", "tm-nonstat")')
else:
    print('Type model identifier argument from: ("sm", "tm-stat", "tm-nonstat")')
