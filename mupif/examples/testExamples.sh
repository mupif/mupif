#!/bin/bash
#You may run all tests without argumens, or to use selected tests such as ./testExamples.sh '1 2'

arrayTests="$@" #arguments from command line, i.e. test numbers

# force running everything locally (ssh clients and servers)
export TRAVIS=1

# in Travis virtualenv with python3, python is actually python3
#export PYTHON=python
export PYTHON=python3
export PYVER=`$PYTHON -c 'import sys; print(sys.version_info[0])'`

# kill all subprocesses when exiting
# http://stackoverflow.com/a/22644006/761090
#trap "exit" INT TERM
#trap "kill 0" TERM
trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT


# run testing SSH server, will be killed by the trap
bash ssh/test_ssh_server.sh &
# testing Pyro nameserver
$PYTHON ../tools/nameserver.py &
sleep 1

# accumulates failures, which are stored in $ret for each example, 1 for failure
retval=0

#Logging failing examples
LOG=()


echo CODECOV flag is set to $USE_CODECOV

if [ "$USE_CODECOV" == true ]
then
    COMMAND="coverage run"
else
    COMMAND=$PYTHON
fi
echo Setting command to $COMMAND




AppendLog () {
        echo "=================== Exit status $1 ===================="
        if [ $1 -ne 0 ]; then
            LOG+=($2)
        fi
}


willRunTest () {
    if [ -z "$arrayTests" ] || [[ " ${arrayTests[@]} " =~ " $1 " ]] ; then
        echo 'Running test' $1
        return 1
    else
        #echo 'FA'
        return 0
    fi
}  

willRunTest '1'; test=$?; if [ "$test" == 1  ] ; then
pushd Example01-local; 
	echo $PWD
	$COMMAND Example01.py
	ret=$?
	(( retval=$retval || $ret ))
	AppendLog $ret `pwd`
popd
fi

willRunTest '2'; test=$?; if [ "$test" == 1  ] ; then
pushd Example02-distrib
	echo $PWD
	$PYTHON server.py &
	PID1=$!
	echo $PID1
	sleep 1
	$COMMAND Example02.py 
	ret=$?
	(( retval=$retval || $ret ))
	AppendLog $ret `pwd`
	kill -9 $PID1
popd
fi

willRunTest '3'; test=$?; if [ "$test" == 1  ] ; then
pushd Example03-executable-local
	echo $PWD
	gcc -o application3 application3.c
	$COMMAND Example03.py
	ret=$?
	(( retval=$retval || $ret ))
	AppendLog $ret `pwd`
popd
fi


willRunTest '4'; test=$?; if [ "$test" == 1  ] ; then
pushd Example04-field-local
	echo $PWD
	$COMMAND Example04.py
	ret=$?
	(( retval=$retval || $ret ))
	AppendLog $ret `pwd`
popd
fi

willRunTest '5'; test=$?; if [ "$test" == 1  ] ; then
pushd Example05-celsian-local
	echo $PWD
	$COMMAND Example05.py
	ret=$?
	(( retval=$retval || $ret ))
	AppendLog $ret `pwd`
popd
fi

willRunTest '6'; test=$?; if [ "$test" == 1  ] ; then
pushd Example06-jobMan-distrib
	echo $PWD
	$PYTHON server.py &
	PID1=$!
	sleep 1
	$COMMAND Example06.py
	ret=$?
	(( retval=$retval || $ret ))
	AppendLog $ret `pwd`
	kill -9 $PID1
popd
fi

willRunTest '7'; test=$?; if [ "$test" == 1  ] ; then
pushd Example07-micress-local
	echo $PWD
	$COMMAND Example07.py
	ret=$?
	(( retval=$retval || $ret ))
	AppendLog $ret `pwd`
popd
fi

willRunTest '9'; test=$?; if [ "$test" == 1  ] ; then
pushd Example09-units-local
	echo $PWD
	$COMMAND Example09.py
	ret=$?
	(( retval=$retval || $ret ))
	AppendLog $ret `pwd`
popd
fi

willRunTest '10'; test=$?; if [ "$test" == 1  ] ; then
pushd Example10-stacTM-local
	echo $PWD
	$COMMAND Example10.py
	ret=$?
	(( retval=$retval || $ret ))
	AppendLog $ret `pwd`
popd
fi

willRunTest '11'; test=$?; if [ "$test" == 1  ] ; then
pushd Example11-stacTM-JobMan-distrib
	echo $PWD
	$COMMAND thermalServer.py &
	PID1=$!
	$COMMAND mechanicalServer.py &
	PID2=$!
	sleep 2 #wait for servers to start
	$COMMAND Example11.py
	ret=$?
	(( retval=$retval || $ret ))
	AppendLog $ret `pwd`
	kill -9 $PID1
	kill -9 $PID2
popd
fi

willRunTest '12'; test=$?; if [ "$test" == 1  ] ; then
pushd Example12-stacTmultiscale-local
    $COMMAND Example12.py
    ret=$?
    (( retval=$retval || $ret ))
    AppendLog $ret `pwd`
popd
fi

willRunTest '13'; test=$?; if [ "$test" == 1  ] ; then
pushd Example13-transiTM-local
    $COMMAND Example13.py
    ret=$?
    (( retval=$retval || $ret ))
    AppendLog $ret `pwd`
popd
fi

willRunTest '14'; test=$?; if [ "$test" == 1  ] ; then
pushd Example14-transiTM-distrib
        echo $PWD
	$COMMAND thermalServer.py &
	PID1=$!
	$COMMAND mechanicalServer.py &
	PID2=$!
	sleep 2 #wait for servers to start
	$COMMAND Example14.py
	ret=$?
	(( retval=$retval || $ret ))
	AppendLog $ret `pwd`
	kill -9 $PID1
	kill -9 $PID2
popd
fi

willRunTest '16'; test=$?; if [ "$test" == 1  ] ; then
pushd Example16-transiTM-JobMan-distrib
        echo $PWD
	$COMMAND thermalServer.py &
	PID1=$!
	$COMMAND mechanicalServer.py &
	PID2=$!
	sleep 2 #wait for servers to start
	$COMMAND Example16.py
	ret=$?
	(( retval=$retval || $ret ))
	AppendLog $ret `pwd`
	kill -9 $PID1
	kill -9 $PID2
popd
fi

willRunTest '17'; test=$?; if [ "$test" == 1  ] ; then
        pushd Example17-micress-Xstream-local
        $COMMAND Example17.py
	ret=$?
	(( retval=$retval || $ret ))
	AppendLog $ret `pwd`
popd
fi


willRunTest '18'; test=$?; if [ "$test" == 1  ] ; then
pushd Example18-transiTM-JobMan-distrib
        echo $PWD
	$COMMAND thermalServer.py &
	PID1=$!
	$COMMAND mechanicalServer.py &
	PID2=$!
	sleep 2 #wait for servers to start
	$COMMAND Example18.py
	ret=$?
	(( retval=$retval || $ret ))
	AppendLog $ret `pwd`
	kill -9 $PID1
	kill -9 $PID2
popd
fi



echo "*** Global return status $retval."

cnt=${#LOG[@]}
if [ $cnt -ne 0 ]; then
    echo "*** Failed directories:"
else
    if [ -z "$arrayTests" ]; then
        echo "*** All tests passed."
    else
        echo "*** Tests" $arrayTests "passed."
    fi
fi
for ((i=0;i<cnt;i++)); do
    echo ${LOG[i]}
done

echo "*** Bye."

exit $retval
