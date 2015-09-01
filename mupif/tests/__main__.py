import unittest, sys

try:
	import colour_runner.runner
	MyTestRunner=colour_runner.runner.ColourTextTestRunner
except ImportError:
	print '(colour-runner not installed, using uncolored output for tests; see https://github.com/meshy/colour-runner/)'
	MyTestRunner=unittest.TextTestRunner

#mupifTestMods=[]
#for (loader,mod_name,ispkg) in pkgutil.iter_modules(path='.'):
#	mupifTestMods.append(importlib.import_module(mod_name,package='mupif'))
#print mupifTestMods
#

suite=unittest.defaultTestLoader.discover('.',pattern='*.py')
try:
	result=MyTestRunner(verbosity=2).run(suite)
	if result.wasSuccessful():
		print '*** ALL TESTS PASSED ***'
		sys.exit(0)
	else:
		print 20*'*'+' SOME TESTS FAILED '+20*'*'
		sys.exit(1)
except SystemExit: raise # re-raise
except:
	print 20*'*'+' UNEXPECTED EXCEPTION WHILE RUNNING TESTS '+20*'*'
	print 20*'*'+' '+str(sys.exc_info()[0])
	# print 20*'*'+" Please report bug to https://github.com/eudoxos/woodem/issues providing the following traceback:"
	import traceback; traceback.print_exc()
	print 20*'*'+' --- '+20*'*'
	sys.exit(2)


