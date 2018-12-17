import os
import numpy as np
import pandas as pd

from sobol_lib import i4_sobol_generate

from hpo.utils.logger import *

class GridGenerator(object):
    def __init__(self, num_dim, num_samples):
        self.num_dim = num_dim
        self.num_samples = num_samples
        

    def generate(self):
        raise NotImplementedError("This method should return given N *M dimensional array.")


class SobolGridGenerator(GridGenerator):
    def __init__(self, params, num_samples, seed=1):
        self.seed = seed
        self.params = params
        num_dim = len(self.params)
        super(SobolGridGenerator, self).__init__(num_dim, num_samples)

    def generate(self, return_type='array'):
        sobol_grid = np.transpose(i4_sobol_generate(self.num_dim, self.num_samples, self.seed)) 
        if return_type == 'array':
            return sobol_grid
        elif return_type == 'table':
            table = pd.DataFrame(data=sobol_grid, columns=self.params)            
            return table 


class HyperparameterVectorGenerator(object):
    def __init__(self, config, num_samples, seed=1, grid_type='Sobol'):
        self.config = config
        self.params = self.config.get_hyperparams()
                
        sobol = None
        if grid_type == 'Sobol':            
            sobol = SobolGridGenerator(self.params, num_samples, seed)
        else:
            raise ValueError("Not supported grid type: {}".format(grid_type))
        
        self.grid = np.asarray(sobol.generate())
        self.hpvs = self.generate()
    
    def get_grid(self):
        return self.grid

    def get_hpv(self):
        debug("HPV-0: {}".format(self.hpvs[0]))
        return self.hpvs

    def generate(self, return_type='array'):
        debug("Generating hyperparams...")
        hps = self.config.hyperparams
        hpv_list = []
        if return_type == 'array':
            for i in range(len(self.grid)):
                vec = self.grid[i]
                hpv = []
                for j in range(len(vec)):
                    param_name = self.params[j]
                    value = vec[j]
                    hp_cfg = getattr(hps, param_name)
                    arg = self.to_param_value(hp_cfg, value)
                    hpv.append(arg)
                #debug("hp{}:{}".format(i, hpv)) 
                hpv_list.append(hpv)
            return hpv_list            
        else: 
            for i in range(len(self.grid)):
                vec = self.grid[i]
                hpv = {}
                for j in range(len(vec)):
                    param_name = self.params[j]
                    value = vec[j]
                    hp_cfg = getattr(hps, param_name)
                    arg = self.to_param_value(hp_cfg, value)
                    hpv[param_name] = arg
                hpv_list.append(hpv)
        
            if return_type == 'table':
                table = pd.DataFrame(data=hpv_list)
                return table
            elif return_type == 'dict':
                return hpv_list
            else:
                raise ValueError("Not supported format: {}".format(return_type))

    def to_param_value(self, hp_cfg, value):
        result = None
        range_list = hp_cfg.range
        range_list.sort()

        if hp_cfg.value_type == "categorical" or hp_cfg.value_type == 'preordered':
            size = len(range_list)
            index = int(value * size)
            if index == size: # handle terminal condition
                index = size - 1 
            result = range_list[index]
        else:
            max_value = max(range_list)
            min_value = min(range_list)

            if hp_cfg.type == 'int':
                result = min_value + int(value * (max_value - min_value + 1)) #XXX:to include max value
            elif hp_cfg.type == 'float':
                result = min_value + (value * (max_value - min_value)) #FIXME:float type can't access max_value.

                if hasattr(hp_cfg, 'power_of'):
                    result = np.power(hp_cfg.power_of, result)
        
        if hp_cfg.type == 'int':
            result = int(result)
        elif hp_cfg.type == 'bool':
            result = bool(result)
        elif hp_cfg.type == 'str':
            result = str(result)
        return result

# def test_main():
#     import hp_cfg
#     json_cfg = './lookup/data10.json'
#     cfg = None
#     if os.path.exists(json_cfg):
#         cfg = hp_cfg.read(json_cfg)
#         if not hp_cfg.validate(cfg):
#             print("invalid configuration format")
#     else:
#         print("file not found")
    
#     if cfg is not None:
#         gg = SobolGridGenerator(cfg.get_hyperparams(), 100)
#         grid = gg.generate('table')
#         print(grid)

# def test_main2():
#     import hp_cfg
#     json_cfg = 'hp_conf/data10.json'
#     cfg = None
#     if os.path.exists(json_cfg):
#         cfg = hp_cfg.read(json_cfg)
#         if not hp_cfg.validate(cfg):
#             print("invalid configuration format")
#     else:
#         print("file not found")
    
#     if cfg is not None:
#         gg = HyperparameterVectorGenerator(cfg, 100)
#         grid = gg.generate()
#         for g in grid:
#             print(["{}".format(i) for i in g])

# if __name__ == '__main__':
#     test_main()
