#!/usr/bin/python3
# This script lists IP addresses matching a string VPNContains (can be provided as the first argument)
# Works with python3, tested on Linux, Windows
# On windows, sometimes a cached list of addreses is used. Reconnect a device to get actual list of active IP addresses.
# Vit Smilauer 01/2018, vit.smilauer (et) fsv.cvut.cz

# This module can be installed via pip
import netifaces
import sys

if len(sys.argv) >= 2:
    VPNContains = sys.argv[1]
else:
    VPNContains = '172.30.0.'

count = 0
tun = []
# print(netifaces.interfaces())
for i in netifaces.interfaces():
    count += 1
    # print(i)
    try:
        addr = netifaces.ifaddresses(i)[netifaces.AF_INET][0]  # regular internet addresses
        print(addr)
        ip = addr['addr']
        if VPNContains in ip:
            # print(ip)
            tun.append(ip)
    except:
        pass
    
print('%d IP addresses found. List of VPN addresses containing %s:' % (count, VPNContains))
print(tun)


