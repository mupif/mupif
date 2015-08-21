#!/bin/bash

# accumulates failures, which are stored in $ret for each example
retval=0

# in Travis virtualenv, this can be also python3
export PYTHON=python

pushd Example01; 
	echo $PWD
	$PYTHON Example01.py
	ret=$?
	(( retval=$retval || $ret ))
	echo "=================== Exit status $ret ===================="
popd

pushd Example02
	echo $PWD
	$PYTHON nameserver.py &
	PID1=$!
	echo PID $PID1
	sleep 1
	$PYTHON server.py &
	PID2=$!
	echo $PID2
	sleep 1
	$PYTHON client.py 
	ret=$?
	(( retval=$retval || $ret ))
	echo "=================== Exit status $ret ===================="
	kill -9 $PID1 $PID2
	#kill the pyro nameserver daemon
	pkill pyro4-ns
popd
retval=$retval || $ret

# disabled temporarily: AttributeError: 'application1' object has no attribute 'pyroDaemon'
#
#pushd Example03
#	echo $PWD
#	gcc -o application3 application3.c
#	$PYTHON Example03.py
#	ret=$?
#	(( retval=$retval || $ret ))
#	echo "=================== Exit status $ret ===================="
#popd

pushd Example04
	echo $PWD
	$PYTHON Example04.py
	ret=$?
	(( retval=$retval || $ret ))
	echo "=================== Exit status $ret ===================="
popd

# disabled temporarily: AttributeError: 'Celsian' object has no attribute 'pyroDaemon'
#
#pushd Example05
#	echo $PWD
#	$PYTHON Example05.py
#	ret=$?
#	(( retval=$retval || $ret ))
#	echo "=================== Exit status $ret ===================="
#popd

##
## TODO: run local ssh server with paramiko and test-ping that one
##
#pushd PingTest
#	echo $PWD
#	ssh -n mmp@mech.fsv.cvut.cz "bash -c \"cd mupif-code/examples/PingTest;$PYTHON ctu-server.py& sleep 10; pkill \"$PYTHON ctu-server.py\"\"" &
#	sleep 1
#	$PYTHON test.py 
#	ret=$?
#	(( retval=$retval || $ret ))
#	echo "=================== Exit status $?"
#popd

echo "*** Global return status $retval"
echo "*** Bye."

exit $retval


