import email.utils
import getpass
import multiprocessing
from psutil import virtual_memory

# input an orca temp file folder and an orca input file, 
# the gbw file will be transformed to a molden file for multiwfn, 
# and then copied to a file that is in the same name as the input file (disregard the %base name)
# usage: python generate_orca_molden_file.py ~/orca/temp/[O]LHY_Spectrum__MVK_test_STEOMCC/ ~/Gaussian/LHY_Spectrum/MVK_test_STEOMCC.inp
# then a MVK_test_STEOMCC.molden file will exist in the ~/Gaussian/LHY_Spectrum/ folder

Python_Lib_path = str(pathlib.Path(__file__).parent.resolve())
sys.path.append(os.path.join(Python_Lib_path,"Python_Lib"))
from My_Lib_Stock import *

assert len(sys.argv)==3, "2 and only 2 parameter should be passed to this script"
temp_folder,input_filename = sys.argv[1:]
temp_folder = os.path.expanduser(temp_folder)
input_filename = os.path.expanduser(input_filename)
for file in os.listdir(temp_folder):
    file = os.path.join(temp_folder,file)
    if filename_class(file).append.lower()=='gbw':
        subprocess.call(['orca_2mkl', file[:-4],'-molden'])
        molden_file = filename_class(file).replace_append_to('molden.input')
        target_filename = get_unused_filename(filename_class(input_filename).replace_append_to('molden'))
        shutil.copy(molden_file,target_filename)
        print("Generated file:",target_filename)
    elif filename_class(file).append.lower()=='mp2nat':
        os.rename(file,file+'.gbw')
        subprocess.call(['orca_2mkl', file[:-4],'-molden'])
        molden_file = filename_class(file).replace_append_to('molden.input')
        target_filename = get_unused_filename(filename_class(input_filename).replace_append_to('MP2_NO.molden'))
        shutil.copy(molden_file,target_filename)
        print("Generated file:",target_filename)









