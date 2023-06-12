# -*- coding: utf-8 -*-
__author__ = 'LiYuanhe'

import re
import os
import subprocess
import datetime
import pickle
import time

from collections import OrderedDict
import sys



Python_Lib_path = str(pathlib.Path(__file__).parent.resolve())
sys.path.append(os.path.join(Python_Lib_path,"Privates"))
sys.path.append(os.path.join(Python_Lib_path,"Python_Lib"))
from HPC_Settings_Private import username

base = os.environ['HOME']
from My_Lib_Stock import *
from Lib_Server import *
        
SGW_jobs_root = "/opt/sge/default/spool/qmaster/job_scripts/"

def generate_job_name_gaussian(filename):
    home_folder = os.path.expanduser("~")
    #job_name = filename.replace(home_folder,"").replace("/",'__').strip("_")
    job_name = filename.replace(home_folder,"")
    if job_name.lower().startswith('gaussian'):
        job_name = job_name[len('gaussian')+1:]
    #job_name = job_name.strip('_')
    #job_name = filename_class(job_name).name_stem
    job_name = "[G]"+job_name
    
    return job_name

def generate_job_name_mopac(filename):
    home_folder = os.path.expanduser("~")
    job_name = filename.replace(home_folder,"").replace("/",'__').strip("_")
    if job_name.lower().startswith('mopac'):
        job_name = job_name[len('mopac')+1:]
    job_name = job_name.strip('_')
    job_name = filename_class(job_name).name_stem
    job_name = "[M]"+job_name
    
    return job_name

def generate_job_name_orca(filename):
    home_folder = os.path.expanduser("~")
    job_name = filename.replace(home_folder,"").replace("/",'__').strip("_")
    if job_name.lower().startswith('gaussian'):
        job_name = job_name[len('gaussian')+1:]
    job_name = job_name.strip('_')
    job_name = filename_class(job_name).name_stem
    job_name = "[O]"+job_name
    
    return job_name


def queued_jobs(sort=True,require_everyone=False,require_every_job=False):
    '''
        require_everyone: show it for every user, not just my
    '''
    qacct_output = subprocess.check_output(['scontrol', 'show', 'job']).decode('utf-8','ignore')
    from My_Lib_Stock import split_list
    jobs = split_list(qacct_output.splitlines(),separator=lambda x:x.strip()=="")
    ret=[]
    for i in jobs:
        if any(['UserId='+username in x for x in i]) or require_everyone:
            #print([x for x in i if 'JobState=' in x][0])
            on_going_states = ['CONFIGURING','COMPLETING','PENDING','RUNNING','RESIZING','SIGNALING']
            on_going_states = ['JobState='+x for x in on_going_states]
            if any([any([on_going_state in x for x in i]) for on_going_state in on_going_states]) or require_every_job:
                ret.append(job(i))
    if sort:
        ret.sort(key=lambda x:x.id)
        
    current_time = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
    running_gaussian = [current_time]+[get_job_output_file(job_object) for job_object in ret if job_object.status=='RUNNING']

    current_path = filename_class(os.path.realpath(sys.argv[0])).path
    
    with open(current_path+"running_gaussian.pickle",'wb') as running_gaussian_output:
        pickle.dump(running_gaussian,running_gaussian_output)
        
    return ret
    
    #ret = []
    #running_job_list = running_jobs()
    #for file in os.listdir(SGW_jobs_root):
    #    filename = SGW_jobs_root+file
    #    if os.path.isfile(filename):
    #        ret.append(job(filename,running_job_list))
    #if sort:
    #    ret.sort(key=lambda x:x.filename)
    #return ret

def get_job_output_file(job_object,no_home=False):
    script_file = job_object.script_file
    if script_file=='(null)':
        return ""
    if not os.path.isfile(script_file):
        return ""
    with open(script_file) as script_file_object:
        script_file = script_file_object.readlines()
    
    for line in script_file:
        re_ret = re.findall('g16 (.+) (.+)',line)
        if re_ret:
            if no_home:
                return re_ret[0][1].strip().replace(base,"~")
            else:
                return re_ret[0][1].strip()
                
    for line in script_file:                
        re_ret = re.findall('orca (.+) >& (.+)',line)
        if re_ret:
            if no_home:
                return re_ret[0][1].strip().replace(base,"~")
            else:
                return re_ret[0][1].strip()
                
    for line in script_file:
        re_ret = re.findall('(.+) (.+)',line)
        if re_ret:
            if no_home:
                return re_ret[0][1].strip().replace(base,"~")
            else:
                return re_ret[0][1].strip()
        
        
class job:
    def __init__(self,qacct_lines):
    
        qacct_lines = [x.split() for x in qacct_lines]
        qacct_lines = sum(qacct_lines,[])
        qacct_dict = OrderedDict()
        
        for item in qacct_lines:
            if '=' in item:
                key = item[:item.find('=')]
                value = item[item.find('=')+1:]
                qacct_dict[key]=value
                #print(key, value)
                
        
        self.dict = qacct_dict

        self.status = qacct_dict['JobState']
        self.id = qacct_dict['JobId']
        self.job_name = qacct_dict['JobName']
        self.partition = qacct_dict['Partition']
        self.qos = qacct_dict['QOS'].upper()
        self.num_of_cores = qacct_dict['NumCPUs']
        self.script_file = qacct_dict['Command']
        
        #print(self.id,self.partition)
        
        self.start_timestamp=-1
        self.end_timestamp=-1
        
        if qacct_dict['StartTime']!='Unknown':
            self.start_timestamp=datetime.datetime.strptime(qacct_dict['StartTime'],'%Y-%m-%dT%H:%M:%S').timestamp()
        if qacct_dict['EndTime']!='Unknown':
            self.end_timestamp=datetime.datetime.strptime(qacct_dict['EndTime'],'%Y-%m-%dT%H:%M:%S').timestamp()
        
        # print(self.job_name,'\n',self.end_timestamp-self.start_timestamp)
        
def print_running_jobs():

    print(  '                                          SGE Queue Status\n' )
    queued = queued_jobs()
    running_job_in_queue = [job for job in queued if job.status=='RUNNING']
    queued_job_in_queue = [job for job in queued if job.status=='PENDING']
    
    print('\n---------------------------------------------------------------------------------------------------------\n')
    print(  '                                    Running Gaussian & ORCA Jobs\n' )

    if len(queued_job_in_queue)>20:
        for count,job in enumerate(queued_job_in_queue):
            print("   ",job.id,' ', "{:<8}".format(job.partition+'-'+job.qos.replace("NORMAL",'NORM'))," ",job.status,"    ",job.num_of_cores,"cores",'    ',job.job_name)
        print()
        for count,job in enumerate(running_job_in_queue):
            print("   ",job.id,' ', "{:<8}".format(job.partition+'-'+job.qos.replace("NORMAL",'NORM'))," ",job.status,"    ",job.num_of_cores,"cores",'    ',job.job_name)
        print()
        print("                                          Total",len(running_job_in_queue)+len(queued_job_in_queue),"jobs running")
        
    else:
        for count,job in enumerate(running_job_in_queue):
            print("   ",job.id,' ', "{:<8}".format(job.partition+'-'+job.qos.replace("NORMAL",'NORM'))," ",job.status,"    ",job.num_of_cores,"cores",'    ',job.job_name)
        print()        
        for count,job in enumerate(queued_job_in_queue):
            print("   ",job.id,' ', "{:<8}".format(job.partition+'-'+job.qos.replace("NORMAL",'NORM'))," ",job.status,"    ",job.num_of_cores,"cores",'    ',job.job_name)
        
    print('\n---------------------------------------------------------------------------------------------------------\n')     


    for running in running_job_in_queue:
        #print(running.partition,running.id)
        start_timestamp=running.start_timestamp
        end_timestamp = time.time()
        
        
        if '.batch' in running.id:
        #奇怪的会带一个id.batch，如1500.batch的名字
            continue
        if '.extern' in running.id:
        #奇怪的会带一个id.extern，如1500.extern的名字
            continue
        mission_time = (float(end_timestamp)-float(start_timestamp))/3600
        if mission_time<20/3600 and int(running.num_of_cores)>1: #小于20秒，应该有问题了  #排除mopac
            mission_time=' ■■ E ■■ h'
        elif mission_time<0.1:
            mission_time='      -- h'
        else:
            mission_time = "{:>8.1f} h".format(mission_time)    
        
        status_str = "                "
        if running.job_name.startswith("[G]/") and running.job_name.endswith('.gjf'):
            file = os.path.join(base, running.job_name[4:-4]+'.out')
            job_status_dict = status(file)
            status_str = "  S{:<3}M{:<4}L{:<5}".format(job_status_dict['current_step'],job_status_dict['opt_step_count'],job_status_dict['last_link'])
            if job_status_dict["fluctruation"]==2:
                status_str += "Fluc"
            elif job_status_dict["fluctruation"]==1:
                status_str += "PosF"
            else:
                status_str += "    "
                               
        
        print("  {:>7}".format(running.id),status_str, " {:<8}".format(running.partition+'-'+running.qos.replace("NORMAL",'NORM')),mission_time,"  {:>9}".format(get_job_output_file(running,no_home=True) if get_job_output_file(running) else running.job_name))
    
    print('\n---------------------------------------------------END---------------------------------------------------\n')        
    
if __name__ == "__main__":
    #queued_jobs()
    print_running_jobs()        

#a=os.popen("top -n 1 | grep 'l[0-9]*.exe'").read()
#a="".join([x for x in a if re.findall('[0-9 a-zA-Z\:\.]',x)])
#print(a)


        

