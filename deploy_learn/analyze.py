from __future__ import division
import os
from itertools import dropwhile, izip, islice
from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta
import json
import csv

from deploy_learn.libs.deploy.logger import TIME_FORMAT

class BadLogFileException(BaseException):
    pass

def json_arg_parser(arg_file):
    """
    parse the arguments of the arguments file
    :param arg_file:
    :return: dictionary
    """
    with open(arg_file) as f:
        arg_dict = json.loads(f.read())
    return dict(arg_dict.iteritems())

def csv_log_parser(log_file):
    with open(log_file) as f:
        reader = csv.reader(f)
        headers = reader.next()
        data = {header: [] for header in headers}
        for row in reader:
            for i, header in enumerate(headers):
                data[header].append(row[i])
        return data

def parse_log_folder(log_base):
    """ Parse important information from log files.
    Returns:
        args (dict<string, value>): a dictionary of function arguments of the program that
            created the log and the value those arguments were set to.
        runtime (float): runtime of program in seconds
    """
    arg_file = os.path.join(log_base, 'log.json')
    log_file = os.path.join(log_base, 'log.csv')
    if not all(os.path.exists(fn) for fn in (arg_file, log_file)):
        raise BadLogFileException('some log files necessary to analysis are not found')

    args = json_arg_parser(arg_file)
    data = csv_log_parser(log_file)

    if len(data) == 0 or len(args) == 0:
        raise BadLogFileException('some log files were not properly loaded')

    return args, data


def analyze_recent(seconds=0, minutes=0, hours=0, days=0, delta=None, **kwargs):
    """analyze log files that were created recently.

    Analyze log files that were created within a certain time window of the present.

    Args:
        seconds (int): seconds that elapsed since first log to be analyzed
        minutes (int): minutes that elapsed since first log to be analyzed
        hours (int): hours that elapsed since first log to be analyzed
        days (int): days that elapsed since first log to be analyzed
        delta (timedelta): how much time has elapsed since the first log to be analyzed
        **kwargs: other inputs to analyze (see analyze())
    """
    if delta is None:
        delta = timedelta(days=days, seconds=seconds, minutes=minutes, hours=hours)
    start_time = datetime.now() - delta
    return analyze(start_time=start_time, **kwargs)


def analyze(local_dir=None, start_time=None,
            print_individual_trials=False, create_plot=True,
            most_recent_n=None, least_recent_n=None,
            error_window=1, error_thresh=-0.05):
    """analyze log files

    Args:
        local_dir (str, optional): the directory that contains the log files we want to analyze.
        start_time (datetime, optional): only analyze logs that were written after start_time.
        print_individual_trials
    """
    from scipy import stats
    import numpy as np
    from deploy_learn.libs.utils import transpose, max_idx, exception_safe_map
    from deploy_learn.libs.analyze.plottools import grid_plot

    # load log content
    log_folders = os.listdir(local_dir)

    # sort logs in chronological order
    chronological = sorted(log_folders)

    # don't analyze any logs before start_time
    if start_time:
        relevant_tokens = ['{:02}'.format(t) for t in start_time.timetuple()][:6]
        start_time_str = '_'.join(relevant_tokens)

        def _too_early(file_name):
            return file_name[:len(start_time_str)] < start_time_str
        chronological = list(dropwhile(_too_early, chronological))

    # only analyze the most recent n
    if most_recent_n is not None:
        most_recent_n = min(len(chronological), most_recent_n)
        chronological = chronological[-most_recent_n:]

    # only analyze the earliest n
    if least_recent_n is not None:
        earliest_n = min(len(chronological), least_recent_n)
        chronological = chronological[:earliest_n]

    # parse log content
    parsed_content = OrderedDict()
    for log_folder in chronological:
        try:
            parsed = parse_log_folder(os.path.join(local_dir, log_folder))
        except BadLogFileException as e:
            print("failed to parse {log_folder} due to '{error}'".format(log_folder=log_folder,
                                                                         error=e))
            continue
        parsed_content[log_folder] = parsed

    # parse content of each individual log file and fill a data store of
    # the arguments and best_errors of all runs
    num_logs = len(parsed_content)
    arg_all = defaultdict(lambda: np.zeros(num_logs))
    error_all = np.zeros(num_logs)
    if print_individual_trials:
        print '# Trials #'

    for log_i, (key_name, (args, data)) in enumerate(parsed_content.iteritems()):
        # TODO: turn string args into enums rather than discarding
        # store argument values for this log
        for arg, v in args.iteritems():
            try:
                float(v)
            except:
                continue
            arg_all[arg][log_i] = v

        # store best error for this log
        try:
            errors = data['test_loss']
        except KeyError:
            raise Exception("accuracy is not in the data logs")
        try:
            errors = [float(acc) for acc in errors]
        except ValueError:
            raise Exception("accuracies column in data log cannot be converted the floats")
        effective_error_window = min(len(errors), error_window)
        smoothed_errors = [-sum(window) / len(window) for window in
                           izip(*[islice(errors, i, None) for i in xrange(effective_error_window)])]
        best_epoch_idx, best_error = max_idx(smoothed_errors)
        error_all[log_i] = best_error

        if print_individual_trials:
            print ("{key_name} achieved {best_error}% error on epoch #{best_epoch}").format(
                key_name=key_name,
                best_error=best_error,
                best_epoch=best_epoch_idx)

    # remove degenerate learners
    idxs = [i for i, err in enumerate(error_all) if err > error_thresh]
    for key in arg_all:
        arg_all[key] = [arg_all[key][i] for i in idxs]
    error_all = [error_all[i] for i in idxs]

    # analyze each parameter/argument
    outcomes = [None] * len(arg_all)
    for i, (k, v) in enumerate(sorted(arg_all.iteritems())):
        # if arg is binary, then do t-test
        ones = np.equal(v, 1)
        zeros = np.equal(v, 0)
        if (ones | zeros).all():
            test_type = 't-test'
            _on, _off = error_all[ones], error_all[zeros]
            try:
                t, p = stats.ttest_ind(_on, _off)
            except:
                if len(_on) == 0 or len(_off) == 0:
                    p = 1
                else:
                    raise
            better = 'on' if np.mean(_on) > np.mean(_off) else 'off'
        else:  # if not binary, do correlation
            test_type = 'pearson r'
            r, p = stats.pearsonr(v, error_all)
            better = 'high' if r > 0 else 'low'
        outcomes[i] = 'p={p:.5f} for {test_type} of {key}: {better} is better'.format(
            test_type=test_type, key=k, p=p, better=better)

    # print analysis
    print "# Descriptive #"
    print 'n: {n} mean: {mean} variance: {variance}'.format(
        n=len(error_all), mean=np.mean(error_all), variance=np.var(error_all))
    print "# Parameter Analysis #"
    for o in sorted(outcomes):
        print o

    # plot arguments
    if create_plot:
        plot_args = [arg for arg in arg_all.keys() if max(arg_all[arg]) != min(arg_all[arg])]
        if len(plot_args) == 0:
            print 'No arguments to plot'
        else:
            grid_plot(xs=[arg_all[arg] for arg in plot_args],
                      ys=error_all,
                      x_labels=plot_args,
                      y_labels='error')

if __name__ == '__main__':
    analyze(local_dir='logs', print_individual_trials=True)
