# -*- coding: utf-8 -*-
__author__ = 'LiYuanhe'

# import sys
# import pathlib
# parent_path = str(pathlib.Path(__file__).parent.resolve())
# sys.path.insert(0,parent_path)

from Python_Lib.My_Lib_Stock import *


import subprocess

def babel_conversion(input_file, output_file):
    """
        Call babel exe and convert the format. The format is determined by the appendix
    Args:
        input_file:
        output_file:

    Returns:

    """
    # Path to the Open Babel executable
    obabel_path = os.path.join(filename_parent(__file__),"OpenBabel-2.3.2","babel.exe")

    # Command to convert GJF to Mol2 using Open Babel
    command = [obabel_path, gjf_file, '-O', mol2_file]

    try:
        # Execute the command
        subprocess.run(command, check=True)
        print(f"Conversion successful: {input_file} -> {output_file}")
    except subprocess.CalledProcessError as e:
        print(traceback.print_exc())
        print(f"Conversion failed: {e}")



if __name__ == '__main__':
    pass