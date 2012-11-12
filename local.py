#!/usr/bin/env python

import sys
import SocketServer
import struct
import socket
import select
import simplejson

PORT = 1080

class ThreadingTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    def __init__(self, server_addr, RequestHandlerClass):
        self.allow_reuse_address = True
        SocketServer.TCPServer.__init__(self, server_addr, RequestHandlerClass)

class Hosts():
    def __init__(self, hosts=None):
        self.hosts = hosts
        self.index = 0
    def get_host(self):
        if len(self.hosts) == 0:
            print 'Sorry, you have no sock5 server alive now'
            return None
        self.index += 1
        try:
            return self.hosts[self.index]
        except IndexError:
            self.index = 0
            return self.hosts[0]
hosts = Hosts()
addr = Hosts()

class Sock5Local(SocketServer.StreamRequestHandler):
    def handle(self):
        sock = self.connection
        try:
            addr = hosts.get_host()
            if not addr:
                return
            remote = socket.create_connection(addr)
        except:
            hosts.hosts.remove(addr)
            print 'Socket error'
            return
        self.handle_chat(sock, remote)

    def handle_chat(self, sock, remote):
        fdset = [sock, remote]
        try:
            while True:
                r,w,e = select.select(fdset, [], [])
                if sock in r:
                    if self.send(remote, self.recv(sock, 2096)) <= 0:
                        break
                if remote in r:
                    if self.send(sock, self.recv(remote, 2096)) <= 0:
                        break
        except:
            pass
        finally:
            remote.close()
            sock.close()

    def send(self, sock, data):
        return sock.send(data)

    def recv(self, sock, l):
        return sock.recv(l)

def main():
    hosts_str = open('cfg.json','r').read()
    try:
        hosts_ = simplejson.loads(hosts_str)['hosts']
    except simplejson.decoder.JSONDecodeError:
        print 'Json format error'
        return

    if not hosts_:
        print 'file cfg.json is empty'
        return
    hosts.hosts = hosts_
    server = ThreadingTCPServer(('', PORT), Sock5Local)
    print 'start local proxy at port {0}'.format(PORT)
    server.serve_forever()

if __name__ == '__main__':
    main()


