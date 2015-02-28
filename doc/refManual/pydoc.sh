#!/bin/bash

#Create documentation for MuPIF using PyDoc python module for automatic documentation
#smilauer@cml.fsv.cvut.cz Feb 28, 2015

DIR1=`pwd`
DIR2=$(dirname "${DIR1}")
DIR3=$(dirname "${DIR2}")
DIR4=$DIR3/mupif

#Set path to MuPIF modules so pydoc can access it directly (pydoc does not allow slashes in module name)
export PYTHONPATH=$PYTHONPATH:$DIR3

#Create the main mupif.html for the whole MuPIF module
pydoc -w mupif

#Add classes from MuPIF - go through all *.py files
for f1 in $(ls $DIR4 | grep \.py$)
do
  f2=mupif.${f1%.py}
  #echo $f2
  pydoc -w $f2
done


