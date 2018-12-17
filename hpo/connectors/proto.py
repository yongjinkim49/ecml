from hpo.utils.rest_client.restful_lib import Connection


class RemoteConnectorPrototype(object):
    def __init__(self, target_url, **kwargs):
        self.url = target_url
        if "credential" in kwargs:
            self.credential = kwargs['credential']
        else:
            self.credential = "jo2fulwkq" # XXX:test auth key. It should be deleted later.
        
        if "timeout" in kwargs:
            self.timeout = kwargs['timeout']
        else:
            self.timeout = 10

        if "num_retry" in kwargs:
            self.num_retry = kwargs['timeout']
        else:
            self.num_retry = 10

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
