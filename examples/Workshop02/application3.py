#!/usr/bin/env python

count=0
sum = 0.

f = open('app3.in', 'r')
l =[]
for line in f:
    l.append(float(line.strip("\n")))

for i in l:
    sum += i
    count += 1
f.close

out = open ('app3.out', 'w')
out.write(str(sum/count))
out.close
