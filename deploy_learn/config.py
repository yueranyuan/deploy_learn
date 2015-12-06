from random import random
from collections import namedtuple
from math import log as ln
from math import exp

def combine_dict(d1, *ds):
    d = {k: v for k, v in d1.iteritems()}
    for d2 in ds:
        for k, v in d2.iteritems():
            d[k] = v
    return d

LOG_SCALE = 1
LINEAR_SCALE = 2
NORMAL = 1
UNIFORM = 2

Var = namedtuple("Var", ['low', 'high', 'scale', 'dist', 'type'])


def GenVar(low, high=None, scale=LINEAR_SCALE, dist=UNIFORM, type=float):
    if high is None:
        high = low
    return Var(low, high, scale, dist, type)

class ConfigObject(object):
    def __init__(self, all_params):
        self.all_params = all_params

    def get_dict(self, param_set='default'):
        self.all_params[param_set]

        def instance_var(var):
            if type(var) in (int, long, float, str):
                return var
            if var.scale == LOG_SCALE:
                low, high = ln(var.low), ln(var.high)  # to log scale
            else:
                low, high = var.low, var.high

            if var.dist == UNIFORM:
                val = low + random() * (high - low)
            else:
                raise NotImplementedError(
                    "failure on probability distribution {d}".format(d=var.dist))

            if var.scale == LOG_SCALE:
                val = exp(val)  # reverse log
            if var.type == int:
                val += 0.5
            return var.type(val)
        return {n: instance_var(v) for n, v in self.all_params[param_set].iteritems()}
