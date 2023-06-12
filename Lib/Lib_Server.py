# -*- coding: utf-8 -*-
__author__ = 'LiYuanhe'

import sys
import os
import math
import copy
import shutil
import re
import time
import random

from My_Lib_Stock import *
from Lib import Gaussian_output, fluctuation_determine


# a simpler, less-dependent lib that is used by servers
def status(gaussian_output_file):
    """

    :param gaussian_output_file:
    :return:
    """
    from Lib import Gaussian_output, fluctuation_determine
    ret = {"last_link": -1,
           "current_step": -1,
           "opt_step_count": -1,
           "normal_termination": False,
           "fluctuation": 0}
    try:
        gaussian_output_object = Gaussian_output(gaussian_output_file)
    except:
        return ret
    # fluctruation = 0, not fluc; fluctruation = 1, possible fluc; fluctruation = 2, definiate fluc

    ret['last_link'] = gaussian_output_object.steps[-1].links[-1].num
    if gaussian_output_object.steps[-1].is_opt:
        ret['opt_step_count'] = len(gaussian_output_object.steps[-1].opt_energies)
    else:
        ret['opt_step_count'] = -1
    ret['normal_termination'] = gaussian_output_object.steps[-1].normal_termination
    ret['current_step'] = len(gaussian_output_object.steps)

    energies = [float(x) for x in gaussian_output_object.steps[-1].opt_energies]
    last_coordinate = gaussian_output_object.steps[-1].last_coord
    atom_count = last_coordinate.atom_count

    fluctuation = fluctuation_determine(energies, atom_count, silent=True)
    if fluctuation[0] == "Definitive Fluctuation.":
        ret['fluctuation'] = 2
    elif fluctuation[0] == "Possible Fluctuation.":
        ret['fluctuation'] = 1
    return ret


if __name__ == "__main__":
    pass
