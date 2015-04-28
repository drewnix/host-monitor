#!/usr/bin/python
import os
import re
import time
import sys
import socket
from threading import Thread, Lock
from operator import itemgetter

# color codes
GREEN = '\033[92m'
BLUE = '\033[94m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'

class PingThread(Thread):
    def __init__ (self, ip):
        Thread.__init__(self)

        self.lifeline = re.compile(r"(\d) (?:packets) received")
        self.running = True
        self.lock = Lock()

        self.ip = ip
        self.ping_status = -1
        self.ssh_status = -1

    def stop(self):
        self.lock.acquire()
        self.running = False
        self.ping_status = -2
        self.lock.release()

    def get_status(self):
        ping_status = -1
        self.lock.acquire()
        ping_status = self.ping_status
        self.lock.release()

        return ping_status

    def get_ssh_status(self):
        ssh_status = -1
        self.lock.acquire()
        ssh_status = self.ssh_status
        self.lock.release()

        return ssh_status

    def check_port(self, host, port):
        srv_socket = socket.socket()
        srv_socket.settimeout(0.25)
        try:
            srv_socket.connect((host, port))
        except socket.error:
            return False

        return True

    def run(self):
        while self.running:
            #srv_status = dict()

            # ping host to check availability
            pingaling = os.popen("ping -q -c2 "+self.ip,"r")
            lines = "".join(pingaling.readlines())

            # ping lifeline
            self.lock.acquire()
            pktstr = re.findall(self.lifeline,lines)
            self.ping_status = int(pktstr[0])
            self.lock.release()

            # ssh status
            self.lock.acquire()
            if self.check_port(self.ip, 22):
                self.ssh_status = 2
            else:
                self.ssh_status = 0
            self.lock.release()

            # nfs status
            # cifs status

            time.sleep(30)

    def run_old(self):
        while self.running:
            # ping host to check availability
            pingaling = os.popen("ping -q -c2 "+self.ip,"r")
            lines = "".join(pingaling.readlines())

            igot = re.findall(self.lifeline,lines)

            if igot:
               self.lock.acquire()
               self.status = int(igot[0])
               self.lock.release()
            time.sleep(60)

class HostMonitor():
    def __init__(self):
        self.watchers = list()

        self.reportvals = (FAIL+"DOWN"+ENDC, WARNING+"PARTIAL"+ENDC, GREEN+"UP"+ENDC, WARNING+"STOPPED"+ENDC, BLUE+"UNKNOWN"+ENDC)

    def add_host(self, hostip, name, type):
        pingthr = PingThread(hostip)
        pingthr.start()

        self.watchers.append({"ip":hostip, "name":name, "type":type, "thread":pingthr})

    def status(self):
        print """
---------------------------
Host Ping Status
---------------------------
""".lstrip().rstrip()

        sorted_watchers = sorted(self.watchers, key=itemgetter('type'))
        last_type = None

        for watcher in sorted_watchers:
            if watcher['type'] != last_type:
                last_type = watcher['type']
                print "\n%s:" % (last_type.title())

            watcher_status = watcher['thread'].get_status()
            watcher_ssh_status = watcher['thread'].get_ssh_status()

            print "\t%s: %s, SSH: %s" % (watcher['name'],
                self.reportvals[watcher_status], self.reportvals[watcher_ssh_status])

    def stopall(self):
        for watcher in self.watchers:
            watcher['thread'].stop()

if __name__=="__main__":
    hm = HostMonitor()

    hm.add_host('192.168.0.12', 'my-iphone', 'iphone')


