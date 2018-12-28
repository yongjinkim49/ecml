from commons.rest_client.restful_lib import Connection
from commons.db_mgr import get_database_manager 

from commons.logger import * 

class RemoteConnectorPrototype(object):
    def __init__(self, target_url, credential, **kwargs):
        self.url = target_url
        self.credential = credential
        
        if "timeout" in kwargs:
            self.timeout = kwargs['timeout']
        else:
            self.timeout = 10

        if "num_retry" in kwargs:
            self.num_retry = kwargs['timeout']
        else:
            self.num_retry = 100

        self.conn = Connection(target_url, timeout=self.timeout)
        
        self.headers = {'Content-Type':'application/json', 'Accept':'application/json'}
        self.headers['Authorization'] = "Basic {}".format(self.credential)


class TrainerPrototype(object):

    def reset(self):
        raise NotImplementedError("This should override to reset the accumulated result.")

    def train(self, space, cand_index, estimates=None, min_train_epoch=None):
        raise NotImplementedError("This should return loss and duration.")

    def get_interim_error(self, model_index, cur_dur):
        raise NotImplementedError("This should return interim loss.")


class ManagerPrototype(object):

    def __init__(self, mgr_type):
        self.type = mgr_type
        self.dbm = get_database_manager()
        self.database = self.dbm.get_db()

    def get_credential(self):
        return self.database['credential']

    def save_db(self, key, data):
        if key in self.database: 
            self.database[key] = data
        if self.dbm:
            self.dbm.save(self.database)
        else:
            warn("database can not be updated because it does not loaded yet.")

    def authorize(self, auth_key):
        if auth_key == "Basic {}".format(self.database['credential']):
            return True
        else:
            return False