import Queue
import threading
import multiprocessing
from time import sleep
import traceback


def Log(txt):
    print(txt)


class _PopJob():
    def __init__(self, job_queue, timeout=1):
        self.job_queue = job_queue
        self.timeout = timeout

    def __enter__(self):
        return self.job_queue.get(timeout=self.timeout)

    def __exit__(self, exc_type, exc_value, traceback):
        self.job_queue.task_done()


class JobConsumer(threading.Thread):
    def __init__(self, job_queue, func, id='[no_name]'):
        threading.Thread.__init__(self)
        self.job_queue = job_queue
        self.id = id
        self.func = func

    def run(self):
        try:
            while True:
                with _PopJob(self.job_queue) as job:
                    if job is None:
                        break
                    Log('consumer {id} is doing task {job.id}'.format(
                        id=self.id, job=job))
                    self.func(**job.params)
        except:
            Log('consumer did not exit properly with error:\n {err}'.format(
                err=traceback.format_exc()))
        finally:
            self.shutdown()

    def shutdown(self):
        Log('consumer {id} is shutting down'.format(id=self.id))


class Job():
    def __init__(self, params, id='[no name]'):
        self.id = id
        self.params = params

    def __call__(self):
        self.func()


def do_jobs(ids, func, jobs, consumer_factory=JobConsumer):
    print 'running workers with ids: {}'.format(', '.join(ids))
    #job_queue = multiprocessing.JoinableQueue()
    job_queue = Queue.Queue()

    # setup a consumer for every worker
    consumers = map(lambda id: consumer_factory(job_queue=job_queue, func=func, id=id), ids)
    for c in consumers:
        c.start()

    # queue up the jobs
    for j in jobs:
        job_queue.put(j)
    for i in range(len(consumers)):
        job_queue.put(None)

    job_queue.join()
    print('finished')


def _slow_print(num, consumer='[some consumer]'):
    sleep(20)
    Log('doing task {num} on {consumer}'.format(num=num, consumer=consumer))

if __name__ == '__main__':
    # should return in a minute exactly
    job_queue = multiprocessing.JoinableQueue()

    consumers = [JobConsumer(job_queue, _slow_print, id=str(i))
                 for i in range(5)]
    for c in consumers:
        c.start()

    jobs = [Job({'num': i}, id=str(i)) for i in range(15)]
    for j in jobs:
        job_queue.put(j)
    for i in range(len(consumers)):
        job_queue.put(None)

    job_queue.join()
    Log('finished')
