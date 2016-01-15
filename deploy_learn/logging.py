import os
import csv
import json

LOG_FOLDER_PATH = 'dev_logs'

class TrialLog(object):
    def __init__(self, key, params):
        self.key = key
        self.lines = []
        self.log_folder = os.path.join(LOG_FOLDER_PATH, key)
        self.log_name = os.path.join(self.log_folder, 'log.csv')
        try:
            os.makedirs(os.path.dirname(self.log_name))
        except OSError:
            pass
        self.headers = []

        # write params
        param_file_name = os.path.join(self.log_folder, 'log.json')
        with open(param_file_name, 'w') as f:
            json.dump(params, fp=f)

        # write meta
        self.meta_file_name = os.path.join(self.log_folder, 'meta.json')
        self.meta = {}

    def rewrite_all(self, headers):
        self.headers = headers
        self.write_line(self.headers, mode='w')
        for line in self.lines:
            self.write_obj(line)

    def write_line(self, line, mode='a+'):
        with open(self.log_name, mode) as f:
            writer = csv.writer(f)
            writer.writerow(line)

    def write_obj(self, obj):
        self.write_line([obj.get(v, '') for v in self.headers])

    def add_line(self, **kwargs):
        self.lines.append(kwargs)
        headers = sorted(kwargs.iterkeys())
        if headers != self.headers:
            self.rewrite_all(headers)
        else:
            self.write_obj(kwargs)

    def write_meta(self, key, val):
        self.meta[key] = val
        with open(self.meta_file_name, 'w') as f:
            json.dump(self.meta, fp=f)

    def savetxt(self, ending, obj):
        import numpy as np
        np.savetxt(os.path.join(self.log_folder, ending), obj)

    def savenp(self, ending, obj):
        import numpy as np
        np.save(os.path.join(self.log_folder, ending), obj)

    def cp(self, dest, dest_file_name=None):
        self.__cp_helper(dest, dest_file_name, n_tries_remain=10)

    def __cp_helper(self, dest, dest_file_name=None, n_tries_remain=0):
        import shutil
        log_folder_ending = os.path.split(self.log_folder)[-1]
        if dest_file_name is None:
            dest_file_name = log_folder_ending
        dest = os.path.join(dest, dest_file_name)

        try:
            shutil.copytree(self.log_folder, dest)
        except shutil.Error:
            self.__cp_helper(dest, dest_file_name + '(1)')
