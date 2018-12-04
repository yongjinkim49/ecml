import os
import time
import json

from hpo.utils.logger import * 

from flask import jsonify, request
from flask_restful import Resource, reqparse

class Candidates(Resource):
    def __init__(self, **kwargs):
        self.worker = kwargs['worker']
        self.credential = kwargs['credential']
        super(Candidates, self).__init__()

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("Authorization", location="headers") # for security reason
        args = parser.parse_args()
        if args['Authorization'] != self.credential:
            return "Unauthorized", 401

        samples = self.worker.get_sampling_space()
        if samples == None:
            return "Sampling space is not initialized", 500

        result = {}

        result["candidates"] = samples.get_candidates().tolist()
        #space["completes"] = samples.get_completes().tolist()
        

        return result, 200 