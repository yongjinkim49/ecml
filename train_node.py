import os
import time

from ws.apis import *
import ws.shared.hp_cfg as hconf
from ws.shared.logger import *

import keras
import argparse
import numpy as np

GPU_ID = 0

class TestLossCallback(keras.callbacks.Callback):
    
    def on_train_begin(self, logs={}):
        self.start_time = time.time()
        self.accs = []

    def on_epoch_end(self, epoch, logs={}):
        cur_acc = logs.get('val_acc')
        self.accs.append(cur_acc)
        elapsed_time = time.time() - self.start_time
        max_i = np.argmax(self.accs)
        debug("Training {} epoch(s) takes {:.1f} secs. Best test accuracy {} at epoch {}".format(
            epoch, elapsed_time, self.accs[max_i], max_i+1))
        update_result_per_epoch(epoch, cur_acc, elapsed_time)


@eval_task
def optimize_mnist_lenet1(config, **kwargs):
    from mnist_lenet1_keras import KerasWorker
    max_epoch = 15
    if "max_epoch" in kwargs:
        max_epoch = kwargs["max_epoch"]    
    global GPU_ID

    history = TestLossCallback()
    debug("Training configuration: {}".format(config))
    worker = KerasWorker(run_id='{}'.format(GPU_ID))
    res = worker.compute(config=config, budget=max_epoch, 
                        working_directory='./gpu{}/'.format(GPU_ID), history=history)
    return res


@eval_task
def optimize_mnist_bm1(config, **kwargs):
    from mnist_bm1_keras_worker import KerasWorker
    max_epoch = 9
    if "max_epoch" in kwargs:
        max_epoch = kwargs["max_epoch"]

    global GPU_ID

    history = TestLossCallback()
    debug("Training configuration: {}".format(config))
    worker = KerasWorker(run_id='{}'.format(GPU_ID))
    res = worker.compute(config=config, budget=max_epoch, 
                        working_directory='./gpu{}/'.format(GPU_ID), history=history)
    return res


def test_main():    
    set_log_level('debug')
    print_trace()

    hp_cfg_path = './hp_conf/{}.json'.format('data2')
    hp_cfg = hconf.read_config(hp_cfg_path)
    wait_train_request(optimize_mnist_lenet1, hp_cfg, True,
                    device_type="gpu",
                    device_index=0, 
                    port=6000, processed=True)

def main(bm_cfg, surrogate_func, gpu_id):
    global GPU_ID
    GPU_ID = gpu_id
    # Set using single GPU only
    os.environ['CUDA_DEVICE_ORDER'] = "PCI_BUS_ID"
    os.environ['CUDA_VISIBLE_DEVICES'] = str(gpu_id)
    
    set_log_level('debug')
    print_trace()

    hp_cfg_path = './hp_conf/{}.json'.format(bm_cfg)
    hp_cfg = hconf.read_config(hp_cfg_path)
    wait_train_request(surrogate_func, hp_cfg, True,
                    device_type="gpu",
                    device_index=gpu_id, 
                    port=6000 + gpu_id, processed=True)

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    
    parser.add_argument('-t', '--target', type=str, default="bm1", help='number of trials.')
    
    parser.add_argument('gpu_id', type=int, default=0, help='GPU id.')
    
    args = parser.parse_args()
    surrogate_func = optimize_mnist_bm1
    if args.target == 'data2':
        surrogate_func = optimize_mnist_lenet1

    main(args.target, surrogate_func, args.gpu_id)
    