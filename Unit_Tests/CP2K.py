# -*- coding: utf-8 -*-
__author__ = 'LiYuanhe'

# import sys
# import pathlib
# parent_path = str(pathlib.Path(__file__).parent.resolve())
# sys.path.insert(0,parent_path)

import unittest

from Python_Lib.My_Lib_Stock import *
from Lib.Lib_CP2K import *

# The unit test class
class UnitTest_Content(unittest.TestCase):
    def test_CP2K_input_build(self):
        CP2K_input_object = CP2K_Input("CP2K_Input_Example.inp")
        with open("CP2K_Input_Example_Py_Print.txt") as _:
            std_python_output = _.read().strip()
        self.assertEqual(str(CP2K_input_object).strip(),std_python_output)



if __name__ == "__main__":
    unittest.main()
