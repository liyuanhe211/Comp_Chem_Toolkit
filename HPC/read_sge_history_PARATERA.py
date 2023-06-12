	# input something like python read_sge_history.py 48 24 24 2 2 0 to show 3 groups of missions, span 48-24, 24-2, and 2-0 hours

from show_running_PARATERA import *
Python_Lib_path = str(pathlib.Path(__file__).parent.resolve())
sys.path.append(os.path.join(Python_Lib_path,"Privates"))
sys.path.append(os.path.join(Python_Lib_path,"Python_Lib"))
from HPC_Settings_Private import username
from My_Lib_Stock import *


import sys
if len(sys.argv)==2:
    hours_list = [float(sys.argv[1])]
    hours_end_list = [0]
elif len(sys.argv)==3:
    hours_list = [float(sys.argv[1])]
    hours_end_list = [float(sys.argv[2])]
elif len(sys.argv)>3:
    assert len(sys.argv)%2==1
    hours_list = sys.argv[1::2]
    hours_end_list = sys.argv[2::2]
else:
    hours_list = [24]
    hours_end_list = [0]
    
hours_list = [float(x) for x in hours_list]
hours_end_list = [float(x) for x in hours_end_list]

days_to_see = int(max(hours_list)/24)+1

import datetime
days_to_see  = datetime.datetime.now()-datetime.timedelta(days=days_to_see)
days_to_see = days_to_see.strftime('%Y-%m-%d')
#print(1)
job_object_list = subprocess.check_output(["sacct",'-u',username,'--noheader', "--starttime", days_to_see, "--format=jobid%200,jobname%200,state%200,start%200,end%200,NCPUS%200,state%200,Partition%200,ElapsedRaw%200,CPUTime%200"])

#print(' '.join(["sacct",'--noheader', "--starttime", days_to_see, "--format=jobid%200,jobname%200,state%200,start%200,end%200,NCPUS%200,state%200,Partition%200,ElapsedRaw%200"]))

#print(2)

job_object_list = job_object_list.decode('utf-8').splitlines()

#print(3)
#print(len(job_object_list))

#list of ['5091', 'LYH_Test...', 'FAILED', '2017-10-12T15:23:08', '2017-10-12T15:23:08','32','RUNNING'] # append to this list, do not insert something into it or delete something
# change the range(7) number if you modify this list
job_object_list = [[job_line[x*201:(x+1)*201].strip() for x in range(10)] for job_line in job_object_list] 
job_object_list.sort(key=lambda x:x[4])

#print(job_object_list)

import time
current_time = time.time()
import datetime

for count,hours in enumerate(hours_list):
    hours_end = hours_end_list[count]
    print('''---------------------------------------------------------------------------------------------------------

                                                    Last -'''+str(int(hours))+((' to -'+str(int(hours_end))) if int(hours_end)!=0 else "")+''' hours
    ''')

    for job_object in job_object_list:
#        print(job_object)
        
        #让运行时间是1s，会报错
        #if job_object[3]=='Unknown':
        #    start_timestamp=0
        #else:
        #    start_timestamp=datetime.datetime.strptime(job_object[3],'%Y-%m-%dT%H:%M:%S').timestamp()
        #if job_object[4]=='Unknown':
        #    end_timestamp=1 
        
        if 'Unknown' not in job_object[3:5]:
            start_timestamp=datetime.datetime.strptime(job_object[3],'%Y-%m-%dT%H:%M:%S').timestamp()
            end_timestamp=datetime.datetime.strptime(job_object[4],'%Y-%m-%dT%H:%M:%S').timestamp()
        else:
            start_timestamp=0
            end_timestamp=1
        
        
        if '.batch' in job_object[0]:
        #奇怪的会带一个id.batch，如1500.batch的名字
            continue
        if '.extern' in job_object[0]:
        #奇怪的会带一个id.extern，如1500.extern的名字
            continue
        #print(current_time)
        #print(end_timestamp)
        #print(current_time-int(end_timestamp))
        #print(current_time-int(start_timestamp)-int(job_object[8]))
        if hours_end*3600<current_time-int(end_timestamp)<hours*3600 and int(job_object[5])>1: #排除mopac
            mission_time = (float(end_timestamp)-float(start_timestamp))/3600
            original_mission_time = mission_time
            if mission_time<6/3600: #小于20秒，应该有问题了
                mission_time=' ■■ E ■■ h'
            elif mission_time<0.1:
                mission_time="{:>6.1f} [m]".format(mission_time*60)
            else:
                mission_time = "{:>8.1f} h".format(mission_time)
            print_str = "[ "+datetime.datetime.fromtimestamp(int(end_timestamp)).strftime('%m.%d %H:%M')+' ] '+job_object[0]+" "
            if original_mission_time<20/3600 and "CANCELLED" in job_object[6]:
                print_str+=" ●● C ●● h                    "+job_object[1]
            else:
                print_str+=mission_time+" "+"{:>10} ".format(job_object[7])+"{:>10}".format("CANCELLED" if 'CANCELLED' in job_object[6] else job_object[6])+" "+job_object[1]
            print(print_str)

    print()
