from qsubg16_PARATERA import filename_class
import subprocess
import os
import time
import sys
import re

base = os.environ['HOME']

'''
--partition:
        "amd_256" for 64Core 256G 
--override:
        Ignore checking of existed mission
-b:
        A float point number>1 that indicates to asking for less cores, in order to get more memory per core in ORCA
-n:
        Number of nodes for ORCA calculation
-t：
    最长时间，单位小时
-m:
    认为机器的内存可用量是多少。若数值小于等于1，认为是当前的机器配置的分数，如果大于1，认为是MB
'''

input_filenames=[]
specified_partition="amd_256"
specified_resource_portion = -1
specified_maximum_time=str(72)
specified_boost_portion=-1
specified_qos = "low"
override=False
specified_node=1
specified_mem=1
mkl_file = None 
mkl_file_option_index=-1

if len(sys.argv)>1:
    input_filenames = sys.argv[1:]
#    # queue specification only works on Gaussian & ORCA, MOPAC is always in the short.q
#    queue_option_index = -1
#    for count,option in enumerate(input_filenames):
#        if option.lower() in ['-q','-queue','--queue']:
#            print("Queue specified to:",end="")
#            queue_option_index=count
#            specified_partition = input_filenames[count+1].strip("'").strip('"')
#            print(specified_partition)
#            break
#    if queue_option_index!=-1:
#        input_filenames.pop(queue_option_index+1)
#        input_filenames.pop(queue_option_index)
        
        
    #找到指定好的partition
    partition_option_index=-1
    for count,option in enumerate(input_filenames):
        if option.lower() in ['-p','-partition','--partition']:
            partition_option_index=count
            specified_partition = input_filenames[count+1].strip("'").strip('"')
            break
    if partition_option_index!=-1:
        input_filenames.pop(partition_option_index+1)
        input_filenames.pop(partition_option_index)
        
    #找到指定好的Memory boost，即扔掉一部分核不用，以增加内存
    for count,option in enumerate(input_filenames):
        if option.lower() in ['-b','-boost','--boost']:
            boost_option_index=count
            specified_boost_portion = float(input_filenames[count+1])
            break
    if specified_boost_portion!=-1:
        input_filenames.pop(boost_option_index+1)
        input_filenames.pop(boost_option_index)

#    #找到指定好的qos
#    qos_option_index=-1
#    for count,option in enumerate(input_filenames):
#        if option.lower() in ['-qos','-qos','--qos']:
#            qos_option_index=count
#            specified_qos = input_filenames[count+1].strip("'").strip('"')
#            break
#    if qos_option_index!=-1:
#        input_filenames.pop(qos_option_index+1)
#        input_filenames.pop(qos_option_index)
    #mkl文件，由Multiwfn产生，作用是把别的程序的波函数给ORCA当初猜
    mkl_file = None 
    for count,option in enumerate(input_filenames):
        if option.lower() in ['-mkl','--mkl']:
            mkl_file_option_index=count
            mkl_file = input_filenames[count+1].strip("'").strip('"')
            assert os.path.isfile(mkl_file), "Specified mkl file not exist:"+mkl_file
            mkl_file = os.path.realpath(mkl_file)
            assert os.path.isfile(mkl_file), "Specified mkl file not exist:"+mkl_file
            break
    if mkl_file_option_index!=-1:
        input_filenames.pop(mkl_file_option_index+1)
        input_filenames.pop(mkl_file_option_index)
        
    #是否override
    override_option_index=-1
    for count,option in enumerate(input_filenames):
        if option.lower() in ['-override','--override']:
            override_option_index=count
            override = True
            break
    if override_option_index!=-1:
        input_filenames.pop(override_option_index)
        
        
    #找到指定好的内存量，防止说占不了内存（奇怪的问题，暂不知原因）
    mem_option_index = -1
    for count,option in enumerate(input_filenames):
        if option.lower() in ['-m','-mem','--mem']:
            mem_option_index=count
            specified_mem = input_filenames[count+1].strip("'").strip('"')
            break
    if mem_option_index!=-1:
        input_filenames.pop(mem_option_index+1)
        input_filenames.pop(mem_option_index)

    #节点数，ORCA可以跨节点
    node_option_index = -1
    for count,option in enumerate(input_filenames):
        if option.lower() in ['-n','-node','--node']:
            node_option_index=count
            specified_node = input_filenames[count+1].strip("'").strip('"')
            break
    if node_option_index!=-1:
        input_filenames.pop(node_option_index+1)
        input_filenames.pop(node_option_index)
        
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
        
    #找到指定好的resource portion
    for count,option in enumerate(input_filenames):
        if option.lower() in ['-r','-resource','--resource']:
            resource_option_index=count
            specified_resource_portion = input_filenames[count+1]
            break
            
    if specified_resource_portion!=-1:
        input_filenames.pop(resource_option_index+1)
        input_filenames.pop(resource_option_index)
            

if not input_filenames:
    print("Filenames (end with empty line):")
    while True:
        input_filename = input()
        if input_filename:
            re_ret = re.findall('Line\s+?\d+?\:\s+(.+)', input_filename)
            if re_ret:
                input_filenames.append(re_ret[0].strip())
            else:
                input_filenames.append(input_filename.strip())
        else:
            break
import copy
origin_input_filenames = copy.deepcopy(input_filenames)
            
to_delete = []
for count,file in enumerate(input_filenames):
    if os.path.isdir(file):
        input_filenames+=sorted([os.path.join(file,x) for x in os.listdir(file)])
input_filenames = [x for count,x in enumerate(input_filenames) if filename_class(x).append.lower() in ['gjf','inp','mop']]



print("Will add the following non-specified input files:")
has_changes = False
count=0
for file in input_filenames:
    if file not in origin_input_filenames:
        count+=1
        has_changes=True
        print("    ",file)
print()
print("Total",count,"files will be added.")
print()
count=0
print("Will delete the following non-specified input files:")
for file in origin_input_filenames:
    if file not in input_filenames:
        count+=1
        has_changes=True
        print("    ",file)
print()
print("Total",count,"files/folders will be removed.")
print()

if has_changes:        
    input("Press Enter to confirm:")

mopac_mission_confirmed_once=False
#input_filenames.sort(reverse=True)
input_filenames.sort()
input_filenames = input_filenames = [x for x in input_filenames if x]
mission_count = 0
for file_count,input_filename in enumerate(input_filenames):
    input_filename = os.path.abspath(input_filename)
    append = filename_class(input_filename).append
    if append.lower()=='gjf':
        print("Gaussian Mission:")
        
        if os.path.isfile(base+"/g16/g16"):
            print("Calling G16...")
            if specified_resource_portion!=-1:
                subprocess.call(['python',base+'/Program/qsubg16_PARATERA.py',input_filename,'-p',specified_partition,'-r',specified_resource_portion,'-t',specified_maximum_time,'-m',str(specified_mem)]+(['-override'] if override else []))
            else:
                subprocess.call(['python',base+'/Program/qsubg16_PARATERA.py',input_filename,'-p',specified_partition,'-t',specified_maximum_time,'-m',str(specified_mem)]+(['-override'] if override else []))
#        else:
#            print('No G16 find, using G09...')
#            if specified_resource_portion!=-1:
#                subprocess.call(['python',base+'/Program/qsubg09_HPC.py',input_filename,'-qos',specified_qos,'-p',specified_partition,'-r',specified_resource_portion,'-t',specified_maximum_time,'-m',str(specified_mem)]+(['-override'] if override else []))
#            else:
#                subprocess.call(['python',base+'/Program/qsubg09_HPC.py',input_filename,'-qos',specified_qos,'-p',specified_partition,'-t',specified_maximum_time,'-m',str(specified_mem)]+(['-override'] if override else []))
                
        print("End of Gaussian Mission qsub.")
        mission_count+=1
    elif append.lower()=='inp':
#        print("ORCA Mission:")
        to_call = ['python',base+'/Program/qsuborca_PARATERA.py',input_filename,'-p',specified_partition,'-t',specified_maximum_time,'-m',str(specified_mem),'-b',str(specified_boost_portion),'-n',str(specified_node)]
        
        if specified_resource_portion!=-1:
            to_call+=['-r',specified_resource_portion]
        if override:
            to_call+=['-override']
        if mkl_file:
            to_call+=['-mkl',mkl_file]
        subprocess.call(to_call)
        print("End of ORCA Mission qsub.")
        mission_count+=1
    elif append.lower()=='mop':
        print("MOPAC Mission:")
        #if mission_count%2==0:
        #    subprocess.call(['python',base+'/Program/qsubmopac_HPC.py',input_filename,'-qos',specified_qos,'-p',specified_partition])        
        #else:
        subprocess.Popen(['python',base+'/Program/qsubmopac_HPC.py',input_filename,'-qos',specified_qos,'-p',specified_partition])        
        #time.sleep(0.02)
        print("End of MOPAC Mission qsub.")
        mission_count+=1
    else:
        continue
    if file_count!=len(input_filenames)-1:
        if append.lower() in ['gjf','inp'] or not mopac_mission_confirmed_once:
            input("QSub: Press Enter to continue...\n\n")
            if append.lower()=='mop':
                mopac_mission_confirmed_once=True
                time.sleep(0.2)

print("Total",mission_count,"missions submitted.")
#print("Initiating CPU binding control...")
#subprocess.Popen(["nohup",'python','/home/gauuser/Program/set_cpu_binding.py','&'])        
#print("CPU binding control running.")