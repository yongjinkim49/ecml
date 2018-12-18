from wot.interface import *
import wot.utils.hp_cfg as hconf
import random as rand
import argparse

@eval_task
def sample_target_func(c1_depth, p1_size, c2_depth, 
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


def sample_main(args):
    
    debug_mode = False
    if args.log_level == "debug":
        debug_mode = True

    try:
        hconf_path = args.hconf_dir + args.hp_config
        hp_cfg = hconf.read_config(hconf_path)

        print(" * HPO worker is ready to serve...")
        wait_job_request(sample_target_func, hp_cfg,
            debug_mode=debug_mode, 
            port=args.port)
    except KeyboardInterrupt as ki:
        # TODO: stop all threads properly
        sys.exit(0)
    except Exception as ex:
        print("Exception: {}".format(ex))


if __name__ == "__main__":

    parser.add_argument(
        '--log-level',
        type=str,
        default='debug',
        help='The log level')

    parser.add_argument('-hd', '--hconf_dir', default=HP_CONF_PATH, type=str,
                        help='Hyperparameter configuration directory.\n'+\
                        'Default setting is {}'.format(HP_CONF_PATH))

    # Mandatory options
    parser.add_argument('hp_config', type=str, help='hyperparameter configuration name.')
    parser.add_argument(
        'port',
        type=int,
        help='The daemon port number. It must be provided as a number in the valid port range.')

    args = parser.parse_args()
    sample_main(args)
    