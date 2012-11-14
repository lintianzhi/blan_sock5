#!/usr/bin/env python

import SocketServer
import socket
import select
import struct

PORT = 9000

class ThreadingTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    def __init__(self, server_addr, RequestHandlerClass):
        self.allow_reuse_address = True
        SocketServer.TCPServer.__init__(self, server_addr, RequestHandlerClass)

class Sock5Server(SocketServer.StreamRequestHandler):
    def handle(self):
        print 'sock connection from {0}'.format(self.client_address)
        sock = self.connection
        data = self.recv(sock,257)
        if not data:
            sock.close()
            return
        self.handle_auth(sock,data)

        rst = self.recv(sock,256)

        if  ord(rst[1]) != 1:
            reply = '\x05\x07\x00\x01\x00\x00\x00\x00\x00\x00'
            self.send(sock,reply)
            return
        if ord(rst[3]) == 1:
            addr = socket.inet_ntoa(rst[4:8])
            port = struct.unpack('>H',rst[8:10])
        elif ord(rst[3]) == 3:
            addr = rst[5:5+ord(rst[4])]
            port = struct.unpack('>H',rst[(5+ord(rst[4])):(7+ord(rst[4]))])
        else:  #ip-6
            return

        try:
            remote = socket.create_connection((addr,port[0]))
        except:
            reply = '\x05\x05\x00\x01\x00\x00\x00\x00\x00\x00'
            self.send(sock,reply)
            print 'socket error'

            return

        pair = remote.getsockname()
        print 'Connect to remote: {0}:{1}'.format(addr, port[0])
        reply = '\x05\x00\x00\x01'
        reply += socket.inet_aton(pair[0]) + struct.pack('>H',pair[1])
        try:
            self.send(sock,reply)
        except socket.error:
            sock.close()
            remote.close()
            return

        self.handle_chat(sock,remote)



    def recv(self,sock,l):
        return sock.recv(l)

    def send(self,sock,data):
        return sock.send(data)

    def handle_chat(self,sock,remote):
        try:
            fdset = [sock,remote]
            while True:
                r, w, e = select.select(fdset,[],[])
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

    def handle_auth(self,sock,data):
        self.send(sock,'\x05\x00')

def main():
    server = ThreadingTCPServer(('', PORT), Sock5Server)
#    server.allow_reuse_address = True
    print 'start server at port {0}'.format(PORT)
    server.serve_forever()

if __name__ == '__main__':
    main()

