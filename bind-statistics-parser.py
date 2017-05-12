#!/usr/bin/env python

import re
import os
import socket
import sys
import time

graphiteip = "" # IP address to Graphite metrics collector (carbon)
graphiteport = "" # Port

namedstatsfile = "" # Example: /var/named/chroot/var/named/data/named_stats.txt
metricpath = "" # path.to.metric
hostname = ""

if os.path.isfile(namedstatsfile):
    os.remove(namedstatsfile)
    os.system('/usr/sbin/rndc stats')
else:
    os.system('/usr/sbin/rndc stats')

fh = open(namedstatsfile, 'r')

conflist    = []
sectionlist = []
statsdict   = {}

for line in fh:
    cleanline = line.strip('\n')

    if '+++ Statistics Dump +++' in cleanline:
        continue
    elif '[' in cleanline:
        continue
    elif '--- Statistics Dump ---' in cleanline:
        continue

    conflist.append(cleanline)

def parsesections(conflist):

    record = False

    for row in conflist:
        if '++' in row:
            sectionname = row.strip('++').strip('---').replace('/','').replace(' ', '').lower().split(' ')[0]
            if not sectionname in statsdict:
                statsdict[sectionname] = {}
            record = True
        elif '++' in row:
            record = False

        if record and '++' not in row:
            metriclist = row.split(' ')
            metriclist = filter(None, metriclist)

            if len(metriclist) > 2:
                stat = metriclist[0]
                stattype = ''
                for i in range(1, len(metriclist)):
                    stattype += metriclist[i].lower()
                stattype = re.sub(r'\W+', '', stattype)
            else:
                stat = metriclist[0]
                stattype = metriclist[1].lower()

            if '!' in stattype:
                stattype = stattype.replace('!', 'NX-')

            statsdict[sectionname][stattype] = stat

def gsend(metric):
        sock = socket.socket()
        sock.connect((graphiteip, graphiteport))
        sock.sendall(metric)
        sock.close()

parsesections(conflist)

for k,v in statsdict.iteritems():
    section = k
    for stattype,stat in v.iteritems():
        metric = metricpath + '.' + hostname + '.' + section + '.' + stattype + ' ' + stat + ' %d\n' % int(time.time())
        gsend(metric)
