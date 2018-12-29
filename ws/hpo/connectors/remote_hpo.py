import json
import time
import sys

import numpy as np
import math

from ws.shared.logger import *

from ws.hpo.connectors.remote_job import RemoteJobConnector


class RemoteOptimizerConnector(RemoteJobConnector):
    
    def __init__(self, ip_addr, port, cred, **kwargs):
        url = "http://{}:{}".format(ip_addr, port)
        self.ip_addr = ip_addr
        self.port = port
        super(RemoteOptimizerConnector, self).__init__(url, cred, **kwargs)

    def validate(self):
        try:
            profile = self.get_profile()
            if profile and "spec" in profile and "job_type" in profile["spec"]:
                if profile["spec"]["job_type"] == "HPO_runner":
                    config = self.get_config()
                    if config and "arms" in config and len(config["arms"]) > 0:
                        # TODO: parameter validation process                  
                        return True       

        except Exception as ex:
            warn("Validation failed: {}".format(ex))
            
        return False

