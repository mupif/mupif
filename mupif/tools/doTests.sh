### Example01 ####
cd ../examples/Example01; 
python Example01.py
read -p "Finished Example01; Press [Enter] key to continue..."

### Example02 ###
cd ../Example02
pwd
python nameserver.py &
PID1=$!
echo $PID1
sleep 1
python server.py &
PID2=$!
echo $PID2
sleep 1
python client.py 
kill -9 $PID1 $PID2
#kill the pyro nameserver daemon
pkill pyro4-ns
read -p "Finished Example02; Press [Enter] key to continue..."

### Example03 ###
cd ../Example03
gcc -o application3 application3.c
python Example03.py
read -p "Finished Example03; Press [Enter] key to continue..."

### Example04 ###
cd ../Example04
python Example04.py
read -p "Finished Example04; Press [Enter] key to continue..."

### Example05 ###
cd ../Example05
python Example05.py
read -p "Finished Example05; Press [Enter] key to continue..."

### PingTest ###
cd ../PingTest
pwd
ssh -n mmp@mech.fsv.cvut.cz "bash -c \"cd mupif-code/mupif/examples/PingTest;python ctu-server.py& sleep 10; pkill \"python ctu-server.py\"\"" &
sleep 1
python test.py 
read -p "Finished PingTest; Press [Enter] key to continue..."




