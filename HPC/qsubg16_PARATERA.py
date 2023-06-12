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
    def __init__(self, fullpath):
        fullpath=fullpath.replace('\\','/')
        self.re_path_temp = re.match(r".+/", fullpath)
        if self.re_path_temp:
            self.path = self.re_path_temp.group(0) #包括最后的斜杠
        else:
            self.path = ""
        self.name = fullpath[len(self.path):]
        if self.name.rfind('.')!=-1:
            self.name_stem = self.name[:self.name.rfind('.')] # not including "."
            self.append = self.name[len(self.name_stem) - len(self.name) + 1:]
        else:
            self.name_stem = self.name
            self.append=""
        self.only_remove_append = self.path+self.name_stem  # not including "."

    def replace_append_to(self,new_append):
        return self.only_remove_append+'.'+new_append


if __name__ == '__main__':        

    home_folder = os.path.expanduser("~")
    email_config_file = home_folder+'/mail_address.ini'

    email_addr = ""
    if os.path.isfile(email_config_file):
        email_addr = open(email_config_file).read()
        email_addr = email.utils.parseaddr(email_addr)[1]
    if not email_addr:
        print("Email address set in correctly.")
        exit()

    input_filenames=[]
    specified_partition = 'amd_256'
    specified_qos = 'low'
    override=False
    total_core = 64 #不包括超线程的核
    total_mem = 256*1024*1024*1024*0.8 #余10%给系统防止占虚拟内存
    specified_resource_portion = -1
    specified_maximum_time=120
    specified_mem=1
    if len(sys.argv)>1:
        input_filenames = sys.argv[1:]
        
        
        #找到指定好的partition
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
            
        if specified_partition.lower() == '64g':
            specified_partition = 'v3_64'
            
        elif specified_partition.lower() == '128g':
            specified_partition = 'v3_128'
            total_core = 24
            total_mem = 128*1024*1024*1024*0.8 #余10%给系统防止占虚拟内存
        elif specified_partition.lower() == '256g':
            specified_partition = 'v3_256'
            total_core = 24
            total_mem = 256*1024*1024*1024*0.8 #余10%给系统防止占虚拟内存
            
        #找到指定好的内存量，防止说占不了内存（奇怪的问题，暂不知原因）
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
        
        #找到指定好的resource portion
        for count,option in enumerate(input_filenames):
            if option.lower() in ['-r','-resource','--resource']:
                resource_option_index=count
                specified_resource_portion = float(input_filenames[count+1])
                break
        if specified_resource_portion!=-1 and specified_resource_portion!='hahaha':
            input_filenames.pop(resource_option_index+1)
            input_filenames.pop(resource_option_index)
            
        if specified_resource_portion=='hahaha':
            specified_resource_portion=1
        
#        #找到指定好的qos
#        qos_option_index=-1
#        for count,option in enumerate(input_filenames):
#            if option.lower() in ['-qos','-qos','--qos']:
#                qos_option_index=count
#                specified_qos = input_filenames[count+1].strip("'").strip('"')
#                break
#        if qos_option_index!=-1:
#            input_filenames.pop(qos_option_index+1)
#            input_filenames.pop(qos_option_index)
            
            
        #找到指定好的最长时间，单位小时
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
        input_filename = os.path.abspath(input_filename)
        
        # replace "!__RESOURCE_PORTION__="
        with open(input_filename) as input_file:
            input_file = input_file.read()
        re_ret = re.findall("(!__RESOURCE_PORTION__=([01]\.*\d*))",input_file)
        # re_ret is like: [('!__RESOURCE_PORTION__=0.5', '0.5')]
        
        if 'acc2e=10' not in input_file:
            input("\n\n\n\n\n\nUsing G16, but you didn't specify acc2e, continue?\n\n\n\n\n")
        
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
            portion_core="%nprocshared="+str(portion_core)
            job_memory_in_MB = int(total_mem*portion/1024/1024*0.8)
            portion_mem = '%mem='+str(job_memory_in_MB)+'MB'
            if specified_resource_portion!=-1 or not re_ret:
                # 删去所有%mem，将%nprocshared 替换为所需的东西
                file_lines = input_file.splitlines()
                to_remove = []
                for count,line in enumerate(file_lines):
                    if line.lower().strip().startswith('%mem'):
                        to_remove.append(count)
                file_lines = [x for count,x in enumerate(file_lines) if count not in to_remove]
                to_replace = []
                for count,line in enumerate(file_lines):
                    if line.lower().strip().startswith('%nprocshared'):
                        to_replace.append(count)
                file_lines = [(x if count not in to_replace else portion_core+'\n'+portion_mem) for count,x in enumerate(file_lines)]
                input_file = '\n'.join(file_lines)
            if re_ret and "%nprocshared" not in input_file:
                input_file = input_file.replace(re_ret[0],portion_core+'\n'+portion_mem)

        else:
            # auto mem
            input_file_lines = input_file.splitlines()
            auto_mem=False
            for i,line in enumerate(input_file_lines):
                if "!__AUTO_MEM__" in line:
                    auto_mem=True
                    re_ret = re.findall(r'%nprocshared=(\d+)',input_file_lines[i-1])
                    if not re_ret:
                        print('AUTO_MEM used but number of processers not defined.')
                        exit()
                    portion_core_num = int(re_ret[0])
                    job_memory_in_MB = int(total_mem*portion_core_num/total_core/1024/1024*0.8)
                    portion_mem = '%mem='+str(job_memory_in_MB)+'MB'
            
            if auto_mem:
                input_file = input_file.replace("!__AUTO_MEM__",portion_mem)
            
        with open(input_filename,'w') as input_file_replaced:
            input_file_replaced.write(input_file.replace("/home/gauuser",base)+"\n\n\n\n\n\n\n\n\n")
        
        commands = []
        
        for line in input_file.splitlines():
            re_ret = re.findall(r'!RUN (.+)',line)
            if re_ret:
                commands.append(re_ret[0])

        if " " in input_filename:
            print('Space in filename')
            exit()

        output_filename = filename_class(input_filename).only_remove_append+'.out'


        with open(input_filename) as input_file:
            input_file = input_file.readlines()
            
        #find multiplicity and charge
        charge,multiplicity = 999,999
        count_paragraph = 0
        for line in input_file:
            if count_paragraph==2:
                if len(line.strip().split(" "))==2:
                    charge,multiplicity = line.strip().split(" ")
                    try:
                        charge = int(charge)
                        multiplicity = int(multiplicity)
                    except:
                        charge = 999
                        multiplicity=999
                break
            if line.strip()=="":
                count_paragraph+=1        

        proc_find = []
        for line in input_file:
            re_ret = re.findall(r'%nprocshared=(\d+)',line)
            if re_ret:
                proc_find+=re_ret

        proc_int = [int(x) for x in proc_find if x.isnumeric()]


        assert len(proc_int)==len(proc_find)

        if not proc_find:
            print("Num of Proc not specified.")
            exit()

        if len(list(set(proc_find)))!=1:
            print("Num of Proc specification inconsistent.")
            exit()

        proc_num_str = proc_find[0]

        chk_files = []
        for line in input_file:
            re_ret = re.findall(r'%chk=(.+)',line)
            if re_ret:
                chk_files+=re_ret

        rwf_files = []
        for line in input_file:
            re_ret = re.findall(r'%rwf=(.+)',line)
            if re_ret:
                rwf_files+=re_ret
        
        from show_running_PARATERA import *
        
        job_name = generate_job_name_gaussian(input_filename)
        
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
        print('>>>>>>>>>>',specified_partition)
        std_script='''#!/bin/bash
#SBATCH -o [NAME].%j.%N.out
#SBATCH --partition=[PARTITION]                 
#SBATCH -J [NAME]                        
#SBATCH --get-user-env                     
#SBATCH --nodes=1             
#SBATCH --ntasks-per-node=1                
#SBATCH --mail-type=ALL               
#SBATCH --mail-user=liyuanhe211@163.com
#SBATCH --time=[MAXIMUM_TIME_IN_MINUTES]              
#SBATCH -c [CORES]
#SBATCH --mem [MEM]

''' + '\n'.join(commands)+'''
'''+'python '+base+'/Program/show_remaining_memory.py '+base+'/'+script_name+'.mem'+'\n\n'+'''
'''+base+'''/g16/g16 [INPUT] [OUTPUT]
'''

        formchk_script = base+'''/g16/formchk [CHECK_FILE]
'''


        ret=std_script.replace('[NAME]',job_name)
        ret=ret.replace('[CORES]',proc_num_str)
        ret=ret.replace('[PARTITION]',specified_partition)
        ret=ret.replace('[INPUT]',input_filename)
        ret=ret.replace('[OUTPUT]',output_filename)
        ret=ret.replace('[MAXIMUM_TIME_IN_MINUTES]',str(int(specified_maximum_time)*60))
        ret=ret.replace('[EMAIL_ADDRESS]',email_addr)
        
        ret=ret.replace('[MEM]',str(max(int(job_memory_in_MB/0.8),int(original_total_mem*portion_core_num/total_core/1024/1024*0.9)))) #申请的内存量比gaussian想要量多一点，并且要少于机器总量

        for chk_file in chk_files:
            ret+=formchk_script.replace('[CHECK_FILE]',chk_file)
            
        for rwf_file in rwf_files:
            path_of_rwf = filename_class(rwf_file).path
            if not os.path.isdir(path_of_rwf):
                print("Making directory:",path_of_rwf)                
                os.makedirs(path_of_rwf)
                
            
        # clearchk command
        for chk_file in chk_files:
            ret+='python '+base+'/Program/clean_chk.py '+chk_file+' noIRC'+'\n\n'
        
        ret+='python '+base+'/Program/show_remaining_memory.py '+base+'/'+script_name+'.mem'+'\n\n'
        
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
        for count_chk,chk_file in enumerate(chk_files):
            print("Chk file",count_chk,": ", chk_file)
        print('---------------------------------------------------------------------------------------------------------')
        print()
        print("Charge: ", charge,"   Multiplicity: ",multiplicity,sep="")
        print()
        print("Request cores: ",proc_num_str)
        print()
        print('---------------------------------------------------------------------------------------------------------')

        subprocess.Popen(["qsub",script_name])

        print()
        
        if file_count!=len(input_filenames)-1:
            input("G16: Press Enter to continue...\n\n")



