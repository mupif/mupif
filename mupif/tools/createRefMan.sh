#!/bin/bash
#Create reference manual for MuPIF
#Vit Smilauer, May 18, 2015

#Get version and authors, remove trailing apostrophes

VER=`awk '/__version__/ {$1=$2=""; print $0}' ../__init__.py | sed "s/'//g"`
AUTHORS=`awk '/__author__/ {$1=$2=""; print $0}' ../__init__.py | sed "s/'//g"`

#Overwrite now
VER='1.0.0'
AUTHORS='Bořek Patzák, Vít Šmilauer'

cd ../doc/refManual

echo $VER, $AUTHORS

#sphinx-apidoc -A "$AUTHORS" -H "MuPIF" -R "$VER"  -F  -o . ../../../mupif/

#Overwrite all, list excluded direcotries here
sphinx-apidoc -A "$AUTHORS" -H "MuPIF Reference manual" -R "$VER" -f -F  -o . ../../../mupif/ ../../../mupif/tools ../../../mupif/tests

mv conf.py conf.py.old

#Insert   sys.path.append(os.path.abspath('../../..'))

awk '/import os/ { print; print "sys.path.append(os.path.abspath(\047../../..\047))"; next }1' conf.py.old > conf.py

#Exclude setup.py from a list of files
#Replace exclude_patterns=['_build']  for exclude_patterns=['_build','setup.*']
#Exclude_patterns works if and only if the excluded file is not referenced by either a toc or a direct ref. It DOES NOT WORK HERE - put exluded directories in sphinx-apidoc command at the end, see a few lines above

sed -i "/exclude_patterns.*/c\exclude_patterns=['_build','setup.*']" conf.py

#Create html, _build/html/
make html

#exit

#Create pdf, _build/latex/
make latexpdf

#cp _build/latex/MuPIFReferencemanual.pdf ./MuPIF-Reference_manual.pdf

