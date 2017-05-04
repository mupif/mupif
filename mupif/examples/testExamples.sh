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

#Logging failing examples
LOG=()

AppendLog () {
        if [ $1 -ne 0 ]; then
            LOG+=($2)
        fi
}


pushd Example01; 
	echo $PWD
	$PYTHON Example01.py
	ret=$?
	(( retval=$retval || $ret ))
	AppendLog $ret `pwd`
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
	AppendLog $ret `pwd`
	echo "=================== Exit status $ret ===================="
	kill -9 $PID1
popd

pushd Example03
	echo $PWD
	gcc -o application3 application3.c
	$PYTHON Example03.py
	ret=$?
	(( retval=$retval || $ret ))
	AppendLog $ret `pwd`
	echo "=================== Exit status $ret ===================="
popd

pushd Example04
	echo $PWD
	$PYTHON Example04.py
	ret=$?
	(( retval=$retval || $ret ))
	AppendLog $ret `pwd`
	echo "=================== Exit status $ret ===================="
popd

pushd Example05
	echo $PWD
	$PYTHON Example05.py
	ret=$?
	(( retval=$retval || $ret ))
	AppendLog $ret `pwd`
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
	AppendLog $ret `pwd`
	echo "=================== Exit status $ret ===================="
	kill -9 $PID1
popd

if [[ $PYVER == 2* ]]; then
	pushd Example07
		echo $PWD
		$PYTHON Example07.py
		ret=$?
		(( retval=$retval || $ret ))
		AppendLog $ret `pwd`
		echo "=================== Exit status $ret ===================="
	popd
else
	echo "------------ Example07 skipped with python 3.x --------------"
fi

pushd Example09
	echo $PWD
	$PYTHON Example09.py
	ret=$?
	(( retval=$retval || $ret ))
	AppendLog $ret `pwd`
	echo "=================== Exit status $ret ===================="
popd

pushd Example10
	echo $PWD
	$PYTHON thermalServer.py &
	PID1=$!
	$PYTHON mechanicalServer.py &
	PID2=$!
	sleep 2 #wait for servers to start
	$PYTHON Demo10.py
	ret=$?
	(( retval=$retval || $ret ))
	AppendLog $ret `pwd`
	echo "=================== Exit status $ret ===================="
	kill -9 $PID1
	kill -9 $PID2
popd


pushd Example12-multiscaleThermo:
        $PYTHON Demo12.py
popd

pushd Example12-multiscaleThermo:
        $PYTHON Demo12.py
popd




pushd Example18-thermoMechanicalNonStatWorkflow-VPN-JobMan
        echo $PWD
	$PYTHON thermalServer.py &
	PID1=$!
	$PYTHON mechanicalServer.py &
	PID2=$!
	sleep 2 #wait for servers to start
	$PYTHON Demo18.py
	ret=$?
	(( retval=$retval || $ret ))
	AppendLog $ret `pwd`
	echo "=================== Exit status $ret ===================="
	kill -9 $PID1
	kill -9 $PID2
popd




echo "*** Global return status $retval."

cnt=${#LOG[@]}
if [ $cnt -ne 0 ]; then
    echo "*** Failed directories:"
else
    echo "*** All tests passed."
fi
for ((i=0;i<cnt;i++)); do
    echo ${LOG[i]}
done

echo "*** Bye."

exit $retval


