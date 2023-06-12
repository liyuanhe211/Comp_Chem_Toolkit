# -*- coding: utf-8 -*-
__author__ = 'LiYuanhe'

import os
import sys
import re
import email.utils
import subprocess
import getpass
import multiprocessing
import random
from psutil import virtual_memory


base = os.environ['HOME']
class filename_class:
# copy from my_lib
    def __init__(self, fullpath):
        fullpath=fullpath.replace('\\','/')
        self.re_path_temp = re.match(r".+/", fullpath)
        if self.re_path_temp:
            self.path = self.re_path_temp.group(0)
        else:
            self.path = ""
        self.name = fullpath[len(self.path):]
        self.name_stem = self.name[:self.name.rfind('.')]

        self.append = self.name[len(self.name_stem)-len(self.name)+1:]
        self.only_remove_append = self.path+self.name_stem

    def replace_append_to(self,new_append):
        return self.only_remove_append+'.'+new_append
        
if __name__ == '__main__':        

    # get home folder & email address set
    home_folder = os.path.expanduser("~")
    email_config_file = home_folder+'/mail_address.ini'

    email_addr = ""
    if os.path.isfile(email_config_file):
        email_addr = open(email_config_file).read()
        email_addr = email.utils.parseaddr(email_addr)[1]
    if not email_addr:
        print("Email address set in correctly.")
        exit()

    # obtain input file name from $1

    input_filenames=[]
    specified_partition = 'amd256'
    override=False
    total_core = 64 #不包括超线程的核
    total_mem = 256*1024*1024*1024*0.8 #余10%给系统防止占虚拟内存
    specified_resource_portion = 1
    specified_maximum_time=120
    specified_mem=1
    override=False
    specified_node=1
    if len(sys.argv)>1:
        input_filenames = sys.argv[1:]
        partition_option_index = -1
        for count,option in enumerate(input_filenames):
            if option.lower() in ['-p','-partition','--partition']:
                partition_option_index=count
                specified_partition = input_filenames[count+1].strip("'").strip('"')
                break
        if partition_option_index!=-1:
            input_filenames.pop(partition_option_index+1)
            input_filenames.pop(partition_option_index)
            specified_resource_portion='hahaha'            
            
        mem_option_index = -1
        for count,option in enumerate(input_filenames):
            if option.lower() in ['-m','-mem','--mem']:
                mem_option_index=count
                specified_mem = float(input_filenames[count+1].strip("'").strip('"'))
                break
        if mem_option_index!=-1:
            input_filenames.pop(mem_option_index+1)
            input_filenames.pop(mem_option_index)
        original_total_mem = total_mem
        if specified_mem>1:
            total_mem = float(specified_mem)
        else:
            total_mem*=float(specified_mem)
        job_memory_in_MB=int(total_mem/1024/1024*0.8)
                    
        #是否override
        override_option_index=-1
        for count,option in enumerate(input_filenames):
            if option.lower() in ['-override','--override']:
                override_option_index=count
                override = True
                break
        if override_option_index!=-1:
            input_filenames.pop(override_option_index)
            
        # #节点数，ORCA可以跨节点
        # node_option_index = -1
        # for count,option in enumerate(input_filenames):
        #     if option.lower() in ['-n','-node','--node']:
        #         node_option_index=count
        #         specified_node = int(input_filenames[count+1].strip("'").strip('"'))
        #         break
        # if node_option_index!=-1:
        #     input_filenames.pop(node_option_index+1)
        #     input_filenames.pop(node_option_index)
			
        time_option_index = -1
        for count,option in enumerate(input_filenames):
            if option.lower() in ['-t','-time','--time']:
                time_option_index=count
                specified_maximum_time = input_filenames[count+1].strip("'").strip('"')
                break
        if time_option_index!=-1:
            input_filenames.pop(time_option_index+1)
            input_filenames.pop(time_option_index)
    if not input_filenames:
        input_filenames=[]
        print("Filenames (end with empty line):")
        while True:
            input_filename = input()
            if input_filename:
                input_filenames.append(input_filename)
            else:
                break
    if not input_filenames:
        print("No Input File Specified.")
        exit()
        
    for input_filename in input_filenames:
        if not os.path.isfile(input_filename):
            print("File not exist:",input_filename)
            exit()
            
    for file_count,input_filename in enumerate(input_filenames):
        # get abs. input filename
        input_filename = os.path.abspath(input_filename)
        
        # replace "#__RESOURCE_PORTION__="
        with open(input_filename) as input_file:
            input_file = input_file.read()
        re_ret = re.findall("(#__RESOURCE_PORTION__=([01]\.*\d*))",input_file)
        # re_ret is like: [('#__RESOURCE_PORTION__=0.5', '0.5')]
        
        
        if re_ret or specified_resource_portion!=-1:
            if len(set(re_ret))>1: # 文件中出现多次，必须一致
                print("RESOURCE_PORTION inconsistent in file:",input_filename)
                print(re_ret)
                exit()
                
            if re_ret:
                re_ret = re_ret[0] 
                portion = float(re_ret[1])
            if specified_resource_portion!=-1 or not re_ret:
                portion = specified_resource_portion

                
                
            if 1/portion>total_core:
                portion_core=1
            elif abs(round(total_core*portion)-total_core*portion)<1E-2:
                #足够接近整数
                portion_core = round(total_core*portion)
            else:
                portion_core = int(total_core*portion)
            
            portion_core_num = portion_core
            job_memory_in_MB = int(total_mem*portion/1024/1024/portion_core*0.9)
            
			portion_mem = '%maxcore '+str(job_memory_in_MB)
			portion_core="%pal nprocs "+str(portion_core*specified_node)+" end"
            
            if specified_resource_portion!=-1 or not re_ret:
                # 删去所有%pal nprocs ，将%maxcore替换为所需的东西
                file_lines = input_file.splitlines()
                to_remove = []
                for count,line in enumerate(file_lines):
                    if line.lower().strip().startswith('%pal'):
                        to_remove.append(count)

                file_lines = [x for count,x in enumerate(file_lines) if count not in to_remove]
                to_replace = []
                for count,line in enumerate(file_lines):
                    if line.lower().strip().startswith('%maxcore'):
                        to_replace.append(count)
                file_lines = [(x if count not in to_replace else portion_core+'\n'+portion_mem) for count,x in enumerate(file_lines)]
                input_file = '\n'.join(file_lines)
            if re_ret and '%maxcore' not in input_file:
                input_file = input_file.replace(re_ret[0],portion_core+'\n'+portion_mem)
        
        else:
            # auto mem
            input_file_lines = input_file.splitlines()
            auto_mem=False
            for i,line in enumerate(input_file_lines):
                if "!__AUTO_MEM__" in line:
                    auto_mem=True
                    portion_mem = '%mem='+str(int(total_mem/total_core/1024/1024))+'MB'
            
            if auto_mem:
                input_file = input_file.replace("#__AUTO_MEM__",portion_mem)
            
        with open(input_filename,'w') as input_file_replaced:
            input_file_replaced.write(input_file.replace("/home/gauuser",base)+"\n\n\n\n\n\n\n\n\n")
        
        input_file_lines = input_file.splitlines()
        base_name=""
        for line in input_file_lines:
            re_ret = re.findall(r'%base \"(.+)\"',line)
            if re_ret:
                base_name = re_ret[0]
                break
                
            
        
        if " " in input_filename:
            print('Space in filename')
            exit()
            
        # output file must be in the same folder with input file
        output_filename = filename_class(input_filename).only_remove_append+'.orca'

        # read input file, obtain required proc num
        with open(input_filename) as input_file:
            input_file = input_file.readlines()
            
        # read charge and multiplicity
        charge,multiplicity = 999,999
        for line in input_file:
            re_ret = re.findall(r"^\*\s*xyz\s+(-*\d+)\s+(\d+)",line)
            if re_ret:
                charge,multiplicity = re_ret[0]
                break

        proc_find = []
        for line in input_file:
            re_ret = re.findall(r'%pal +nprocs +(\d+) +end',line)
            if re_ret:
                proc_find+=re_ret

        # verify proc is set to be an integer
        proc_int = [int(x) for x in proc_find if x.isnumeric()]


        if len(proc_int)!=len(proc_find):
            print("nProcShared Specification Chaos.")
            exit()

        if not proc_find:
            print("Num of Proc not specified.")
            exit()

        if len(list(set(proc_find)))!=1:
            print("Num of Proc specification inconsistent.")
            exit()

        proc_num_str = proc_find[0]
        from show_running_PARATERA import *


        # job name for SGE
        job_name = generate_job_name_orca(input_filename)
        
        if not override:
            # verify whether the job is existed

            queued = queued_jobs()
            for job in queued:
                if job.job_name==job_name:
                    print("Job",job_name,"existed as job",job.id)
                    exit()
          
            
        random_num = random.randint(1,100000000)
        if not os.path.isdir('Scripts'):
            os.mkdir('Scripts')
        script_name = "Scripts/auto_generated_script_"+str(random_num)+".sh"
        std_script='''#!/bin/bash
#SBATCH -o [NAME].%j.%N.out
#SBATCH --partition=[PARTITION]                 
#SBATCH -J [NAME]                        
#SBATCH --get-user-env                     
#SBATCH --nodes=[NODE]       
#SBATCH --ntasks-per-node=[CORES]               
#SBATCH --mail-type=ALL                    
#SBATCH --mail-user=liyuanhe211@163.com
#SBATCH --time=[MAXIMUM_TIME_IN_MINUTES]              
#SBATCH -c 1
#SBATCH --mem [MEM]

. $HOME/.bashrc
mkdir $ORCA/temp/
mkdir $ORCA/temp/[NAME]
cd $ORCA/temp/[NAME]
echo [INPUT] > INPUT_FilePath.txt
$ORCA/orca [INPUT] >& [OUTPUT]    
python $HOME/Program/generate_orca_molden_file.py $ORCA/temp/[NAME] [INPUT]
'''
        input_filepath = filename_class(input_filename).path
        xyz_file = os.path.join("$ORCA/temp/[NAME]".replace('[NAME]',job_name),base_name+".xyz")
        trj_file = os.path.join("$ORCA/temp/[NAME]".replace('[NAME]',job_name),base_name+".trj")
        trj_file_xyz_append = filename_class(input_filename).only_remove_append+".trj.xyz"
        
        ret=std_script.replace('[NAME]',job_name)
        if specified_boost_portion>1:
            core_for_slurm = str(int(portion_core_num))            
        else:
            core_for_slurm = str(int(proc_num_str))
        ret=ret.replace('[CORES]',str(int(int(core_for_slurm)/specified_node)))
        ret=ret.replace('[NODE]',str(specified_node))
        ret=ret.replace('[PARTITION]',specified_partition)
        ret=ret.replace('[INPUT]',input_filename)
        ret=ret.replace('[OUTPUT]',output_filename)
        ret=ret.replace('[MAXIMUM_TIME_IN_MINUTES]',str(int(specified_maximum_time)*60))
        ret=ret.replace('[EMAIL_ADDRESS]',email_addr)
        ret=ret.replace('[MEM]',str(max(int(job_memory_in_MB*portion_core_num/0.9),int(original_total_mem*portion_core_num/total_core/1024/1024*0.9))))#申请的内存量比gaussian想要量多一点，并且要少于机器总量
        ret=ret.replace('[XYZ_FILE]',xyz_file)
        ret=ret.replace('[TRJ_FILE]',trj_file)
        ret=ret.replace('[INPUT_FILEPATH]',input_filepath)
        ret=ret.replace('[TRJ_FILE_XYZ_APPEND]',trj_file_xyz_append)

        
        with open(script_name,'w') as output_script:
            output_script.write(ret)
        

        print()
        print('---------------------------------------------------------------------------------------------------------')    
        print()
        print("Starting job...")
        print()
        print("Partition: ",specified_partition)
        print()
        print('---------------------------------------------------------------------------------------------------------')
        print("User: ",getpass.getuser())
        print("Email: ",email_addr)
        print("Job name: ",job_name)
        print("Input file: ", input_filename)
        print("Output file: ", output_filename)
        print('---------------------------------------------------------------------------------------------------------')
        print()
        print("Charge: ", charge,"   Multiplicity: ",multiplicity,sep="")
        print()
        print("ORCA cores: ",proc_num_str)
        print()
        print("Slurm cores: ",core_for_slurm)
        print()
        print('---------------------------------------------------------------------------------------------------------')

        #cpu=multiprocessing.cpu_count()/2
        #if int(proc_num_str)/2<cpu<int(proc_num_str):
        #    print("Warning! You are requiring", proc_num_str, "cores.")
        #    print(cpu, "cores detected, and such that you are blocking all the remaining cores.")
        #    respound=input("Input 'override' if you still want to submit the job, or press ENTER otherwize:")
        #    if respound.lower()!="override":
        #        exit()
        
        subprocess.Popen(["qsub",script_name])

        print()
        
        if file_count!=len(input_filenames)-1:
            input("Press Enter to continue...\n\n")




