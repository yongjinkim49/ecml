
class DictObject(object):
    def __init__(self, d):
        for a, b in d.items():
            if isinstance(b, (list, tuple)):
                setattr(self, a, [DictObject(x) 
                    if isinstance(
                        x, dict) else x for x in b])
            else:
                setattr(self, a, DictObject(b) 
                    if isinstance(b, dict) else b)


class EmptyHyperparameterVector(object):
    pass


class HyperparameterVector(DictObject):
    def __init__(self, d):
        super(HyperparameterVector, self).__init__(d)
        

