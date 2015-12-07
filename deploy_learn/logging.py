import os
import csv
import json

LOG_FOLDER_PATH = 'logs'

class TrialLog(object):
    def __init__(self, key, params):
        self.key = key
        self.lines = []
        self.log_name = os.path.join(LOG_FOLDER_PATH, key + '.csv')
        try:
            os.makedirs(os.path.dirname(self.log_name))
        except OSError:
            pass
        self.headers = []

        # write params
        param_file_name = os.path.join(LOG_FOLDER_PATH, key + '.json')
        with open(param_file_name, 'w') as f:
            json.dump(params, fp=f)

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
        print(self.lines)
        if headers != self.headers:
            self.rewrite_all(headers)
        else:
            self.write_obj(kwargs)

    def savetxt(self, ending, obj):
        import numpy as np
        np.savetxt(os.path.join('logs', self.key + ending), obj)

    def savenp(self, ending, obj):
        import numpy as np
        np.save(os.path.join('logs', self.key + ending), obj)
