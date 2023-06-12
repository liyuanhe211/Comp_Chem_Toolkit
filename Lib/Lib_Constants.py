# -*- coding: utf-8 -*-
__author__ = 'LiYuanhe'

from Python_Lib.My_Lib_Stock import *

TEMP_FOLDER_PATH = get_config(open_config_file(), 'Temp_Path', r"D:\Gaussian\Temp")
if not os.path.isdir(TEMP_FOLDER_PATH):
    os.makedirs(TEMP_FOLDER_PATH,exist_ok=True)
