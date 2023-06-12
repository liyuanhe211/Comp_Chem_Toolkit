# -*- coding: utf-8 -*-
__author__ = 'LiYuanhe'

import os
import sys
import re
import email.utils
import math
import subprocess
import getpass
import multiprocessing
import random
from psutil import virtual_memory
from My_Lib_Stock import *

folder = input("Folder to create copy:")
count = int(input("For how many times:"))
for i in range(count):
	print(i)
	folder_name = folder.rstrip('/')+"_{:0>4}".format(i+1)
	shutil.copytree(folder,folder_name)