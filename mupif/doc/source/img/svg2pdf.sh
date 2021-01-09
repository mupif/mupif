#!/bin/bash
set -e -x
for f in *.svg; do
    rsvg-convert -f pdf -o ${f%.*}.pdf "$f";
done
