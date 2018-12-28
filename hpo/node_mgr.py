import os
import time
import json
import copy

from commons.logger import * 
from commons.proto import ManagerPrototype 


class HPONodeManager(ManagerPrototype):

    def __init__(self, *args, **kwargs):
        self.nodes = {}
        return super(NodeManager, self).__init__("node_manager")

    def register(self, spec):
        ip = None
        port = None

        if "ip_address" in spec:
            ip = spec["ip_address"]
        else:
            raise ValueError("No IP address in specification")
        if "port_num" in spec:
            port = spec["port_num"]
        else:
            raise ValueError("No port number in specification")

        if not self.check_duplicates(ip, port):
            raise ValueError("Node already registered: {}:{}".format(ip, port))

        # Try handshaking with registered node to check it is healthy.
        url = "http://{}:{}".format(ip, port)
        # TODO:Check job type is compatible

        # Create node id and append to node repository
        node_id = "hpo-node_{:03d}".format(len(self.nodes.keys()))
        node_spec = {
            "id" : node_id,
            "ip_address" : ip,
            "port_num" : port
        }
        
        self.nodes[node_id] = node_spec

        return node_id

    def check_duplicates(self, ip_addr, port):
        for nk in self.nodes.keys():
            n = self.nodes[nk]
            if n["ip_address"] == ip_addr and n["port_num"] == port:
                return False
        return True