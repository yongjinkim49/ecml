import os
import time
import json

from hpo.utils.logger import * 

from flask import jsonify, request
from flask_restful import Resource, reqparse

class Billboard(Resource):
    def __init__(self, **kwargs):
        self.jm = kwargs['job_manager']
        super(Billboard, self).__init__()

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("Authorization", location="headers") # for security reason
        args = parser.parse_args()
        if args['Authorization'] != self.jm.credential:
            return "Unauthorized", 401
        
        # TODO:to be added dynamically
        urls = [{"/": {"method": ['GET']}},
            {"/config": {"method": ['GET']}}, 
            {"/jobs": {"method": ['GET', 'POST']}},
            {"/jobs/active": {"method": ['GET']}},
            {"/jobs/[job_id]": {"method": ['GET', 'PUT', 'DELETE']}}] 
        
        return {"spec" : self.jm.get_spec(), "urls": urls }, 200 