import copy
import re
import sys
import subprocess
from My_Lib_Stock import *

if len(sys.argv)>1:
    input_str = ' '.join(sys.argv[1:])
else:
    print("Input mission IDs (one per line) to detele")
    input_str=get_input_with_while_cycle()
    input_str = " ".join(input_str)
input_list = input_str.replace(',',' ').split(' ')
choices = copy.deepcopy(input_list)

def get_job_name(job_id):
    try:
        lines = subprocess.check_output(['scontrol','show','job',str(job_id)]).decode('utf-8').splitlines()
    except subprocess.CalledProcessError:
        return "Not Valid Mission"
    lines = [x for x in lines if "JobName=" in x]
    if lines:
        return re.findall("JobName\=(.+)",lines[0])[0].strip()
    else:
        return "Not Valid Mission"


for choice in input_list:
    if '-' in choice:
        choices.remove(choice)
        if not re.findall('\d+\-\d+',choice):
            print("Invalid")
            exit()

        start,end = choice.split('-')
        choices+=[str(x) for x in range(int(start),int(end)+1)]
        
choices = sorted(list(set([int(x) for x in choices if '-' not in x])))
exclude = []
print("Will terminate job:")
for i in choices:
    job_name = get_job_name(i)
    print(i,job_name)
    if job_name=="Not Valid Mission":
        exclude.append(job_name)
print()

input("Press Enter to confirm, Ctrl+C to cancle.")
for i in choices:
    if i not in exclude:
        subprocess.call(['scancel',str(i)])
        print(['scancel',str(i)])

