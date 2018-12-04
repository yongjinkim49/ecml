from wot.interface import *
from wot.utils.hp_cfg import *
import random as rand

@eval_task
def sample_obj_func(c1_depth, p1_size, c2_depth, 
        p2_size, f1_width, window_size, 
        learning_rate, reg_param, keep_prop_rate):

    values = [c1_depth, p1_size, c2_depth, 
    p2_size, f1_width, window_size, 
    learning_rate, reg_param, keep_prop_rate]

    values_total = sum(values)
    selected = []

    for i in range(3):
        r = rand.randint(0, len(values) - 1)
        selected.append(values[r])

    if sum(selected) > sum(values):
        return 0.0
    else:
        loss = float((sum(values) - sum(selected)) / sum(values))
        print("Random loss: {:.4f}".format(loss))
        return loss

def sample_main():    
    wait_job_request(sample_obj_func, True)

if __name__ == "__main__":
    sample_main()
    