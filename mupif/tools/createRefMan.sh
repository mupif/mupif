#!/bin/bash
#Create reference manual for MuPIF
#Vit Smilauer, May 18, 2015

#Get version and authors, remove trailing apostrophes

VER=`awk '/__version__/ {$1=$2=""; print $0}' ../__init__.py | sed "s/'//g"`
AUTHORS=`awk '/__author__/ {$1=$2=""; print $0}' ../__init__.py | sed "s/'//g"`

cd ../doc/refManual

#echo $VER, $AUTHORS

sphinx-apidoc -A "$AUTHORS" -H "MuPIF" -R "$VER" -f -F  -o . ../../../mupif/

mv conf.py conf.py.old

#Insert   sys.path.append(os.path.abspath('../..'))

awk '/import os/ { print; print "sys.path.append(os.path.abspath(\047../..\047))"; next }1' conf.py.old > conf.py

#Create html, _build/html/
make html

#Create pdf, _build/latex/
make latexpdf

cp _build/latex/MuPIF.pdf .
