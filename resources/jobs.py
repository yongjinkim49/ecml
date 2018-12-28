import os
import time
import json

from flask import jsonify, request
from flask_restful import Resource, reqparse

from commons.logger import * 

class Jobs(Resource):
    def __init__(self, **kwargs):
        self.jm = kwargs['job_manager']
        super(Jobs, self).__init__()

    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument("Authorization", location="headers") # for security reason
            args = parser.parse_args()
            if not self.jm.authorize(args['Authorization']):
                return "Unauthorized", 401
            
            job_req = request.get_json(force=True)
            # TODO:check whether 'surrogate', 'hp_cfg' existed
            debug("Job creation request accepted.")  
            job_id = self.jm.add(job_req) 

            if job_id is None:
                return "invalid job request: {}".format(job_req), 400
            else:                
                return {"job_id": job_id}, 201

        except Exception as ex:
            return "Job creation failed: {}".format(ex), 400

    def get(self):
        # TODO:add argument handling for windowing items
        parser = reqparse.RequestParser()
        parser.add_argument("Authorization", location="headers") # for security reason
        args = parser.parse_args()
        if not self.jm.authorize(args['Authorization']):
            return "Unauthorized", 401
        
        self.jm.sync_result() # XXX: A better way may be existed
        return self.jm.get_all_jobs(n=10), 200