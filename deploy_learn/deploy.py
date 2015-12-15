from fabric.api import local

from deploy_learn.libs.deploy.multijob import Job, JobConsumer, do_jobs
from deploy_learn.libs.deploy.logger import gen_log_name
from deploy_learn.logging import TrialLog

def run(*args, **kwargs):
    """
    run commandline either locally or online depending on the ONLINE global variable
    """
    return local(*args, **kwargs)

def run_experiment_script(driver, param_set, task_num=0, **kwargs):
    """use the commandline to run an experiment

    Args:
        driver (string): name of the driver file. File location relative to the repo root.
        param_set (string): name of the parameter set to run.
            See learntools.deploy.config.get_config()
        task_num (int): this number maintains a counter to distinguish the various runs
            in a batch operation. The first run is 0, the second is 1, etc. The task_num can
            be used to distinguish cross-validation folds etc.

    Returns:
        (string): the name of the log file produced by this experiment. File location relative
            to the repo root.
    """
    log_name = gen_log_name()
    run('python {driver} run -p {param_set} -o {log_name} -t {task_num}'.format(
        **locals()))
    return log_name

def run_experiment_module(driver, param_set, task_num=0, **kwargs):
    driver_module = __import__(driver, fromlist=['run'])
    driver_fn = driver_module.run
    if isinstance(param_set, basestring):
        driver_module = __import__(driver, fromlist=['config'])
        param_set = driver_module.config.get_dict(param_set)
    run_experiment_fn(driver_fn, param_set, task_num=task_num, **kwargs)

def run_experiment_fn(driver, param_set, task_num=0, **kwargs):
    log_name = gen_log_name()
    log = TrialLog(key=log_name, params=param_set)
    driver(log=log, task_num=task_num, **param_set)
    return log_name

def run_batch(param_set, n_workers, driver, num_jobs=1):
    """

    :param param_set: name of the param_set
    :param n_workers: number of workers to run in parallel
    :param driver: python file to be used as driver
    :param num_jobs: number of times to run the driver
    :return:
    """

    if isinstance(driver, basestring):
        # driver is a script file
        jobs = [Job({'driver': driver, 'param_set': param_set, 'task_num': i}, id=str(i))
                for i in range(num_jobs)]
        ids = ['worker{}'.format(i) for i in xrange(n_workers)]
        do_jobs(ids, jobs=jobs, func=run_experiment_module,
                consumer_factory=JobConsumer)
    elif callable(driver):
        # driver is a function
        assert not isinstance(param_set, basestring)  # param_set must be an object
        jobs = [Job({'driver': driver, 'param_set': param_set, 'task_num': i}, id=str(i))
                for i in range(num_jobs)]
        ids = ['worker{}'.format(i) for i in xrange(n_workers)]
        do_jobs(ids, jobs=jobs, func=run_experiment_fn,
                consumer_factory=JobConsumer)
