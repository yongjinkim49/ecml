from __future__ import print_function
import traceback
import numpy as np
import json
import pickle
import csv
import pandas as pd
from scipy.stats import rankdata

def debug(msg):
    #print(msg)
    pass


def load_json(file_path):
    with open(file_path) as f: 
        return json.load(f)


def load_pickle(file_path):
    with open(file_path, 'rb') as pkl:
        return pickle.load(pkl)    


def get_num_iters_over_threshold(logs, num_runs, threshold):
    num_iterations = []

    for i in range(num_runs):
        opt = logs[str(i)]
        current_num_iterations = len(get_accuracies_under_threshold(opt['accuracy'], threshold))
        num_iterations.append(current_num_iterations)
       
    return num_iterations


def add_opt_time_span(results, opt, num_iters):
    for i in range(num_iters):
        iter_key = str(i)
        eval_case = results[opt][iter_key]
        cum_exec_time = eval_case['cum_exec_time']
        cum_opt_time = eval_case['cum_opt_time']
        exec_time_spans = []
        opt_time_spans = []
        for i in range(len(cum_exec_time)):
            if i == 0:
                exec_time_spans.append(cum_exec_time[i])
                opt_time_spans.append(cum_opt_time[i])
            else:
                exec_time_spans.append( cum_exec_time[i] - cum_exec_time[i-1])
                opt_time_spans.append( cum_opt_time[i] - cum_opt_time[i-1])
        eval_case['exec_time_span'] = exec_time_spans
        eval_case['opt_time_span'] = opt_time_spans
        
        return results


def get_exec_times_over_threshold(logs, num_runs, threshold, unit='Hour'):
    cum_exec_time = []

    for i in range(num_runs):
        opt = logs[str(i)]
        index_cum_time = len(get_accuracies_under_threshold(opt['accuracy'], threshold)) - 1
        if type(opt['accuracy'][0]) is not list:
            total_secs = opt['cum_exec_time'][index_cum_time] + opt['cum_opt_time'][index_cum_time]
        else:
            num_batch = len(opt['accuracy'])
            cur_best_acc = 0.0
            best_index = 0
            for b in range(num_batch):
                single_accs = opt['accuracy'][b]
                if len(single_accs) > index_cum_time:
                    acc = single_accs[index_cum_time]
                    if cur_best_acc < acc:
                        cur_best_acc = acc
                        best_index = b
            total_secs = opt['cum_exec_time'][best_index][index_cum_time] + \
                        opt['cum_opt_time'][best_index][index_cum_time]

        total_mins = float(total_secs) / 60.0
        total_hours = float(total_mins) / 60.0
        if unit == 'Sec':
            cum_exec_time.append(total_secs)
        elif unit == 'Min':
            cum_exec_time.append(total_mins)
        elif unit == '10min':
            cum_exec_time.append(total_mins / 10.0)            
        else:
            cum_exec_time.append(total_hours)

    return cum_exec_time


def get_accuracies_under_threshold(accuracies, threshold):
    
    marginal_accuracies = []
    for k in range(len(accuracies)):
        if type(accuracies[k]) is not list:
            if accuracies[k] >= threshold:
                return accuracies[0:k+1]
        else:
            accs = accuracies[k] # each machine's accuracy result
            #print("{}:{}".format(k, accs))            
            for i in range(len(accs)):
                acc = accs[i]
                if len(marginal_accuracies) <= i:
                    marginal_accuracies.append(acc)
                else:
                    if marginal_accuracies[i] < acc:
                        marginal_accuracies[i] = acc

    if len(marginal_accuracies) == 0:    
        return accuracies
    else:
        for k in range(len(marginal_accuracies)):
            if marginal_accuracies[k] >= threshold:
                return marginal_accuracies[0:k+1]

        return marginal_accuracies


def get_percentile(logs, threshold, num_iters, percentiles, criteria='Hours'):
    
    data_sorted = None
    mean_list = []
    std_list = []
    
    if criteria == 'Iteration':
        data_sorted = np.sort(get_num_iters_over_threshold(logs, num_iters, threshold))
    else:
        data_sorted = np.sort(get_exec_times_over_threshold(logs, num_iters, threshold, unit=criteria))
    
    for percentile in percentiles:
        data_percentile = data_sorted[int(np.ceil(num_iters*percentile)-1):]
        mean_list.append(np.mean(data_percentile))
        std_list.append(np.std(data_percentile))

    return mean_list, std_list


def get_result(logs, arm, run_index):
    if arm in logs.keys():
        log = logs[arm]
        if str(run_index) in log.keys():
            result = log[str(run_index)]
            return result
    raise ValueError('invalid key or run_index: {}, {}'.format(arm, run_index))


def get_total_times(selected_result, unit='Min'):
    cum_total_time = []
    if len(selected_result['cum_exec_time']) != len(selected_result['cum_opt_time']):
        raise ValueError('time record size mismatch: {}, {}'.format(
            len(selected_result['cum_exec_time']), 
            len(selected_result['cum_opt_time'])))
    for t in range(len(selected_result['cum_exec_time'])):
        cet = selected_result['cum_exec_time'][t]
        cot = selected_result['cum_opt_time'][t]
        total_time = cet + cot 
        if unit == 'Min':
            total_time = total_time / 60.0
        elif unit == 'Hour':
            total_time = total_time / 3600.0
        else:
            raise ValueError("Invalid unit: {}".format(unit))
        cum_total_time.append(total_time)
    
    return cum_total_time


def get_best_errors(selected_result):
    cur_best_error = 1.0
    best_errors  = []

    for err in selected_result['error']:

        if cur_best_error > err:
            best_errors.append(err)
            cur_best_error = err
        else:
            best_errors.append(cur_best_error)
    return best_errors


def load_lookup_data(lookup_name, path='./lookup'):
    if not path.endswith('/'):
        path = path + '/'
    lookup_path = "{}{}.csv".format(path, lookup_name)
    try:
        lookup = pd.read_csv(lookup_path)        
        if lookup_name == 'data10':
            lookup['best_acc'] = get_best_acc_of_trial(lookup, metric='perplexity')
        elif lookup_name == 'data20':
            lookup['best_acc'] = get_best_acc_of_trial(lookup, start_col=11, end_col=61)
        elif lookup_name == 'data30':
            lookup['best_acc'] = get_best_acc_of_trial(lookup, start_col=11, end_col=61)
        elif lookup_name == 'data200':
            lookup['best_acc'] = get_best_acc_of_trial(lookup, start_col=110, end_col=210)            
        elif lookup_name == 'data207':
            lookup['best_acc'] = get_best_acc_of_trial(lookup, start_col=110, end_col=210)            
        elif lookup_name == 'data4':
            lookup['best_acc'] = get_best_acc_of_trial(lookup, start_col=9, end_col=24)
        elif lookup_name ==  'data5':
            lookup['best_acc'] = get_best_acc_of_trial(lookup, start_col=8, end_col=23)
        else:
            lookup['best_acc'] = get_best_acc_of_trial(lookup)
        return lookup
    except:
        raise ValueError("{} is not found.".format(lookup_path))


def get_best_acc_of_trial(lookup_table, start_col=10, end_col=25, metric='acc'):
    if metric == 'acc':
        return np.max(lookup_table.iloc[:, start_col:end_col].values, axis=1)
    elif metric == 'perplexity':
        best_perp = np.min(lookup_table.iloc[:, start_col:end_col].values, axis=1)
        max_perplexity = 1000.0
        return (max_perplexity - best_perp) / max_perplexity    


def get_difficulty_stats(lookup, difficulties=[]):
    if len(difficulties) == 0:
        difficulties = np.array([0.01, 0.005, 0.001, 0.0005, 0.0001])
    num_lookup = len(lookup)
    stats = []
    best_accs = lookup['best_acc']
    sorted_accs = np.sort(best_accs)[::-1]
    t_i = 0
    for df in difficulties:
        stat = {}
        th = int(df * num_lookup)        
        stat['difficulty'] = 100 * float(df)
        stat['error'] = 1.0 - sorted_accs[th]
        stat['accuracy'] = sorted_accs[th]
        debug(stat)
        stats.append(stat)
    return stats


def create_no_share_result(results, mix_type, num_iters, max_hours):
    synth_result = {}
    for iteration in range(num_iters):
        synth_result[str(iteration)] = { "accuracy": [], 'error': [], 
                                'cum_exec_time': [], 'cum_opt_time': [], 
                                'exec_time' : [], "opt_time": [],
                                'select_trace' : [] }
        selected_arms = results[mix_type][str(iteration)]['select_trace']
        
        cum_exec_time = 0
        cum_opt_time = 0
        total_op_time = 0

        arm_indexes = {}
        for arm in set(selected_arms):
            arm = arm.replace('+', '_')
            arm_indexes[arm] = 0

        while total_op_time < max_hours * 60 * 60:            
            for arm in selected_arms:
                key = arm.replace('+', '_')
                
                cur_index = arm_indexes[key]
                acc = results[key][str(iteration)]['accuracy'][cur_index]
                synth_result[str(iteration)]['accuracy'].append(acc)
                synth_result[str(iteration)]['error'].append(1.0 - acc)
                
                opt_time = results[key][str(iteration)]['opt_time'][cur_index]
                synth_result[str(iteration)]['opt_time'].append(opt_time)
                cum_opt_time += opt_time
                synth_result[str(iteration)]['cum_opt_time'].append(cum_opt_time)
                
                exec_time = results[key][str(iteration)]['exec_time'][cur_index]
                synth_result[str(iteration)]['exec_time'].append(exec_time)
                cum_exec_time += exec_time
                synth_result[str(iteration)]['cum_exec_time'].append(cum_exec_time)
                
                arm_indexes[key] = cur_index  + 1
                synth_result[str(iteration)]['select_trace'].append(arm)
                total_op_time = cum_exec_time + cum_opt_time
                if total_op_time > max_hours * 60 * 60:
                    break

    file_path = "{}_NO_SHARE".format(mix_type)

    with open(file_path + '.json', 'w') as json_file:
        json_file.write(json.dumps(synth_result))


def get_best_acc_stats(results, arms, num_iters, opt_hour,
                        ratios = [0.3, 0.4, 0.3]):
    stats = {}
    stat_key = 'opt_{}hour'.format(opt_hour) 
    stats[stat_key] = {}
    for selected_arm in arms:
        stat = { 'total' : {}}
        best_acc_list = []
        for i in range(num_iters):
            r = get_result(results, selected_arm, i)
            total_hours = get_total_times(r, 'hour')
            best_errs = get_best_errors(r)
            
            for h in range(len(total_hours)):
                if total_hours[h] >= opt_hour or h == len(total_hours) - 1 :
                    best_acc = 1.0 - best_errs[h]
                    best_acc_list.append(best_acc)
                    break

        stat['total']['best_acc'] = best_acc_list

        stat['total']['mean'] = np.mean(best_acc_list)
        stat['total']['std'] = np.std(best_acc_list)
        sorted_best_accs = np.sort(best_acc_list)

        bi = int(np.ceil(num_iters * ratios[0]))
        mi = int(np.ceil(num_iters * (ratios[0]  + ratios[1])))

        try:
            stat['bottom'] = {}
            
            stat['bottom']['best_acc'] = sorted_best_accs[0:bi]
            stat['bottom']['mean'] = np.mean(stat['bottom']['best_acc'])
            stat['bottom']['std'] = np.std(stat['bottom']['best_acc'])
            
            stat['middle'] = {}
            stat['middle']['best_acc'] = sorted_best_accs[bi:mi]

            stat['middle']['mean'] = np.mean(stat['middle']['best_acc'])
            stat['middle']['std'] = np.std(stat['middle']['best_acc'])
            stat['top'] = {}
            stat['top']['best_acc'] = sorted_best_accs[mi:]
            stat['top']['mean'] =  np.mean(stat['top']['best_acc'])
            stat['top']['std'] = np.std(stat['top']['best_acc'])
        except:
            traceback.print_exc()
        stats[stat_key][selected_arm] = stat
   
    return stats


def write_stats_csv(title, stats_list):
    stat_csv = "stats_{}.csv".format(title)
    with open(stat_csv, 'w') as csvfile:
        fieldnames = ['dataset', 'opt_time', 'group', 'GP_EI', 'GP_PI', 'GP_UCB', 'RF_EI', 'RF_PI', 'RF_UCB']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        hour = 1
        for stats in stats_list:
            for g in ['top', 'middle', 'bottom', 'total']:
                d = { 'dataset' : title}
                d['opt_time'] = hour
                d['group'] = g
                for key in stats.keys():
                    s = stats[key]
                    d[key] = '{:.4f}({:.4f})'.format(s[g]['mean'], s[g]['std'])
                writer.writerow(d)
            hour += 1


def get_opt_successes(results, target_goal, 
                      opts=None, num_runs=50, criteria='hours', min_hour=1, max_hour=25):
    opt_successes = {}
    opt_iterations = {}
        
    if opts is None:
        opts = list(results.keys())

    for opt in sorted(opts):
        x_values = None
        if criteria is 'iterations':
            x_values = np.array(get_num_iters_over_threshold(
                results[opt], num_runs, target_goal))
        else:
            x_values = np.array(get_exec_times_over_threshold(
                results[opt], num_runs, target_goal, unit=criteria))
        opt_iterations[opt] = x_values

        cum_successes = []
        for i in range(min_hour, max_hour, 1):
            cum_success = num_runs - (x_values[x_values > i].shape[0])
            cum_successes.append(cum_success)
        
        
        successes = []
        for i in range(len(cum_successes)):
            if i > 0:
                success = cum_successes[i] - cum_successes[i-1]
            else:
                success = cum_successes[i] - 0
            successes.append(success)
            
        opt_successes[opt] ={
            'successes' : successes,
            'cum_successes': cum_successes
        }
        
    return opt_successes


def calc_rank(type, num_total, arr, index):
    if type == 'var':
        return num_total - int(rankdata(arr)[index]) + 1
    elif type == 'mean':
        return int(rankdata(arr)[index]) - 1
    

def analyze_mean_var_ranks(opt, estimates, results, start_index=0, classifier=None):
    est_opt = estimates[opt]
    result = results[opt]

    rank_traces = { 'opt': opt, 'iterations' : [] }

    for it in est_opt.keys():
        num_exploits = 0
        num_explores = 0

        trials = est_opt[it]
        iter = { 'i' : int(it) + start_index, 'trials': []}

        for i in range(len(trials)):
            trial = {}
            trial['step'] = i + 1

            est = trials[i]['estimated_values']
            arm = opt
            if opt.find('DIV') >= 0:
                arm = result[it]['select_trace'][i]
            trial['arm'] = arm
            trial['cur_acc'] = result[it]['accuracy'][i]
            trial['cum_op_time'] = result[it]['cum_exec_time'][i] + result[it]['cum_opt_time'][i]    
            if est is None:
                num_explores += 1
            else:
                best_cand = np.argmax(est['acq_funcs'])

                debug("best_cand_index: {}".format(best_cand ))
                next_index = int(est['candidates'][best_cand])
                debug('next sobol index: {}'.format(next_index))
                total_cand = len(est['candidates'])
                m = est['means'][best_cand]
                rank_m = calc_rank('mean', total_cand, est['means'], best_cand)
                max_m = np.amax(est['means'])
                min_m = np.amin(est['means'])
                
                debug('selected mean: {}, rank: {}, max: {}, min: {}'.format(m,  
                    rank_m, np.amax(est['means']), np.amin(est['means'])))
                
                trial['mean'] = {'estimate': m, 'rank': rank_m, 
                    'max': max_m, 'min': min_m}            
                
                v = est['vars'][best_cand]
                rank_v = calc_rank('var', total_cand, est['vars'], best_cand)
                max_v = np.amax(est['vars'])
                min_v = np.amin(est['vars'])
                trial['var'] = {'estimate': v, 'rank': rank_v,
                    'max': np.amax(est['vars']), 'min': np.amin(est['vars'])}                
                
                debug('selected var: {}, rank: {}, max: {}, min: {}'.format(v,  rank_v, 
                     max_v, min_v))            
                
                if classifier is None:
                    # if mean rank is higher than variance rank,
                    # count it as exploitation
                    if rank_m < rank_v: 
                        trial['class'] = 1
                        trial['comment'] = 'exploit'
                        num_exploits += 1
                    else:
                        trial['class'] = 0
                        trial['comment'] = 'explore'
                        num_explores += 1
                else:
                    c = classifier(m, rank_m, max_m, min_m, v, rank_v, max_v, min_v)
                    trial['comment'] = c
                    if c == 'explore':
                        trial['class'] = 0                        
                        num_explores += 1
                    elif c == 'exploit':
                        trial['class'] = 1
                        num_exploits += 1
                    else:
                        raise ValueError('invalid class: {}'.format(c))

            iter['trials'].append(trial)

        iter['exploits'] = num_exploits
        iter['explores'] = num_explores

        
        total_trials = num_exploits + num_explores
        debug('iteration {} - explorations: {} ({:.2}%), exploitations: {} ({:.2}%)'.format(it, num_explores, 
            num_explores * 100.0 /total_trials, num_exploits, num_exploits * 100.0 / total_trials))
        
        rank_traces['iterations'].append(iter)

    return rank_traces


def calc_catastrophic_failures(results, target_goal, num_trials, op_hours, 
                                step=1, criteria='time'):
    opt_iterations = {}
    opt_failures = {}

    x_max = op_hours + 1

    x = range(0, x_max, step)
    opts = list(sorted(results.keys()))

    for opt in list(sorted(results.keys())):
        x_values = None
        if criteria is 'iteration':
            x_values = np.array(get_num_iters_over_threshold(
                results[opt], num_trials, target_goal))
        else:
            x_values = np.array(get_exec_times_over_threshold(
                results[opt], num_trials, target_goal, unit=criteria))
        opt_iterations[opt] = x_values

        failures = []
        for i in x:
            failure = (x_values[x_values > i].shape[0] / float(num_trials))
            failures.append(failure)
        opt_failures[opt] = failures 
    return opt_failures


def calc_time_to_achieve(results, target_goal, num_trials):
    criteria='trials' 

    op_times = {}
    
    for o in list(sorted(results.keys())):
        op_times[o] = {} 
        value = get_exec_times_over_threshold(results[o], num_trials, target_goal)
        op_times[o]['op_times'] = value
        op_times[o]['mean'] = np.mean(value)
        op_times[o]['sd'] = np.std(value)

    return op_times


def write_table1_stats(results, target_goal, num_trials, 
        optimizers, stat_csv, title):
    op_hours = 24
    checking_hours = [3, 6, 9, 12, 24]
    fail_summary = calc_catastrophic_failures(results, target_goal, num_trials, op_hours)
    for key in fail_summary.keys():
        print("{} failure rates".format(key))
        for h in checking_hours:
            debug('after {} hours: {:.0f}%'.format(h, fail_summary[key][h] * 100))
    times = calc_time_to_achieve(results, target_goal, num_trials)
    for k in times.keys():
        r = times[k]
        print("{}: mean {:.2f}, stdev: {:.2f}".format(k, r['mean'], r['sd']))    
    with open(stat_csv, 'w', newline='') as csvfile:
        fieldnames = ['dataset',  'algorithm', 'FR3', 'FR6', 'FR9', 'FR12', 'FR24', 'TTA0.05%']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for opt in optimizers:
            d = {'dataset': title,  'optimizer': opt}
            for h in checking_hours:
                d['FR{}'.format(h)] = "{:.0f}%".format(fail_summary[opt][h] * 100)
            d['TTA0.05%'] = "{:.2f} ({:.2f})".format(times[opt]['mean'], times[opt]['sd'])
            writer.writerow(d)    


def compare_batch_performance(results, base, compare, target_acc, fp,  
                            num_trials=50, unit='10 mins'):
    baseline = get_exec_times_over_threshold(results[base], num_trials, target_acc, unit=unit)
    compare = get_exec_times_over_threshold(results[compare], num_trials, target_acc, unit=unit)
    baseline.sort()
    compare.sort()
    index = int(num_trials * (1.0 - fp) - 1)
    c1 = baseline[index]
    c2 = compare[index]
    coeff = c1 / c2
    return coeff


# Flatten the parallelization result
def flatten_results(num_processes, results, opt_name, num_trials):
    sr_r = {}
    sr = results[opt_name]
    for n in range(num_trials):
        fr = flatten_parallel_trial(num_processes, sr, n)
        sr_r[str(n)] = fr
    return sr_r


def flatten_parallel_trial(n_p, sr, num_trial):
    t = sr[str(num_trial)]
    m_i= 0 # machine index
    i = 0 # iteration index
    keys = ["cum_exec_time", "select_trace", "exec_time", "opt_time", "model_idx", "cum_opt_time", "error", "accuracy"]
    flat_results = []
    max_i_list = t["iters"]
    for m_i in range(len(max_i_list)):
        max_i = max_i_list[m_i]
        for i in range(max_i):
            r = {"i" : i, "m": m_i }
            for k in keys:            
                r[k] = t[k][m_i][i]
            r['end_time'] = r['cum_opt_time'] + r['cum_exec_time']
            #print("{}.{}: {}".format(m_i, i, r['end_time']))
            flat_results.append(r)

    # sort dict list  by end_time
    flatted ={}
    from operator import itemgetter
    sorted_list = sorted(flat_results, key=itemgetter('end_time')) 
    for r in sorted_list:
        #print("{}:{}.{}".format(r['end_time'], r['m'], r['i']))
        for k in keys:
            if not k in flatted:
                flatted[k] = []
            flatted[k].append(r[k])
    return flatted

