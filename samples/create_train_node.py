import os
import sys
import random as rand

# For path arrangement (set the parent directory as the root folder)
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import ws.shared.hp_cfg as hconf
from ws.apis import wait_train_request, eval_task


@eval_task
def dummy_target(c1_depth, p1_size, c2_depth, 
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


def main(hconf_path, port, debug_mode=False):
    
    try:
        hp_cfg = hconf.read_config(hconf_path)

        print(" * Training worker will be ready to serve...")
        wait_train_request(dummy_target, hp_cfg,
                            debug_mode=debug_mode, 
                            port=port)
    
    except KeyboardInterrupt as ki:
        # TODO: stop all threads properly
        sys.exit(0)
    except Exception as ex:
        print("Exception: {}".format(ex))


if __name__ == "__main__":
    main('./hp_conf/data1.json', 6000, True)
    