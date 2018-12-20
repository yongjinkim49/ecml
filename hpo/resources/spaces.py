import os
import time
import json

from flask import jsonify, request
from flask_restful import Resource, reqparse

from commons.logger import * 

class Spaces(Resource):
    def __init__(self, **kwargs):
        self.sm = kwargs['space_manager']
        super(Jobs, self).__init__()

    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument("Authorization", location="headers") # for security reason
            args = parser.parse_args()
            if args['Authorization'] != self.sm.credential:
                return "Unauthorized", 401
            
            space_req = request.get_json(force=True)
            # TODO:check whether 'surrogate', 'hp_cfg' existed
            debug("Sampling space creation request accepted.")  
            space_id = self.sm.create(space_req) 

            if space_id is None:
                return "Invalid sampling space creation request: {}".format(space_req), 400
            else:                
                return {"space_id": space_id}, 201

        except Exception as ex:
            return "Sampling space creation failed: {}".format(ex), 400

    def get(self):
        # TODO:add argument handling for windowing items
        parser = reqparse.RequestParser()
        parser.add_argument("Authorization", location="headers") # for security reason
        args = parser.parse_args()
        if args['Authorization'] != self.sm.credential:
            return "Unauthorized", 401
        
        self.sm.sync_result() # XXX: A better way may be existed
        return self.sm.get_available_spaces(n=10), 200