import os
import time
import json
import copy

from commons.logger import * 
from commons.proto import ManagerPrototype 



class SamplingSpaceManager(ManagerPrototype):

    def __init__(self, *args, **kwargs):
        super(SamplingSpaceManager, self).__init__()
        self.spaces = [] # self.database['spaces'] # XXX:for debug only

    def create(self, space_spec):
        # TODO: return space_id
        pass

    def get_available_spaces(self, n=10):
        # TODO: return list of {space_id, description} 
        pass

    def get_space(self, space_id):
        # TODO: return space object (not description)
        pass