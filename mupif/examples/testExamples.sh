#!/bin/bash

# force running everything locally (ssh clients and servers)
export TRAVIS=1

# in Travis virtualenv with python3, python is actually python3
export PYTHON=python
export PYVER=`$PYTHON -c 'import sys; print(sys.version_info[0])'`

# kill all subprocesses when exiting
# http://stackoverflow.com/a/22644006/761090
trap "exit" INT TERM
trap "kill 0 " TERM

# run testing SSH server, will be killed by the trap
bash ssh/test_ssh_server.sh &
# testing Pyro nameserver
$PYTHON ../tools/nameserver.py &
sleep 1

# accumulates failures, which are stored in $ret for each example
retval=0



pushd Example01; 
	echo $PWD
	$PYTHON Example01.py
	ret=$?
	(( retval=$retval || $ret ))
	echo "=================== Exit status $ret ===================="
popd

pushd Example02
	echo $PWD
	$PYTHON server.py &
	PID1=$!
	echo $PID1
	sleep 1
	$PYTHON client.py 
	ret=$?
	(( retval=$retval || $ret ))
	echo "=================== Exit status $ret ===================="
	kill -9 $PID1
popd
retval=$retval || $ret

pushd Example03
	echo $PWD
	gcc -o application3 application3.c
	$PYTHON Example03.py
	ret=$?
	(( retval=$retval || $ret ))
	echo "=================== Exit status $ret ===================="
popd

pushd Example04
	echo $PWD
	$PYTHON Example04.py
	ret=$?
	(( retval=$retval || $ret ))
	echo "=================== Exit status $ret ===================="
popd

pushd Example05
	echo $PWD
	$PYTHON Example05.py
	ret=$?
	(( retval=$retval || $ret ))
	echo "=================== Exit status $ret ===================="
popd

pushd Example06
	echo $PWD
	$PYTHON server.py &
	PID1=$!
	sleep 1
	$PYTHON test.py
	ret=$?
	(( retval=$retval || $ret ))
	echo "=================== Exit status $ret ===================="
	kill -9 $PID1
popd

if [[ $PYVER == 2* ]]; then
	pushd Example07
		echo $PWD
		$PYTHON Example07.py
		ret=$?
		(( retval=$retval || $ret ))
		echo "=================== Exit status $ret ===================="
	popd
else
	echo "------------ Example07 skipped with python 3.x --------------"
fi

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

pushd Example09
	echo $PWD
	$PYTHON Example09.py
	ret=$?
	(( retval=$retval || $ret ))
	echo "=================== Exit status $ret ===================="
popd

echo "*** Global return status $retval"
echo "*** Bye."

exit $retval


