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

sys.path.append('D:\My_Program\Python_Lib')
sys.path.append('E:\My_Program\Python_Lib')
from My_Lib import *
import mogli
import gr.pygr
if __name__ == '__main__':

    # 第一个参数是文件名，第二个参数为显示的分子序数

    assert os.path.isfile(sys.argv[1])
    file = sys.argv[1]
    if len(sys.argv)==3:
        count = int(sys.argv[2])
    else:
        count = 0
    molecules = mogli.read(file)
    mogli.show(molecules[count], title=filename_class(file).name_stem,width=450,height=450)