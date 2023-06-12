import subprocess
import sys

a=subprocess.check_output('''squeue --format="%.7A %.21V %.13u %.20j %.15P %.11T %.5D %.5C %100R" --states="PENDING"''',shell=True)
output=[]
for i in a.decode('utf-8').splitlines():
    reason=i[97+8:].strip().strip('(').strip(')')
    if reason.startswith('QOSMax'):
        continue
    output.append(i)

output.sort(key=lambda x:0 if ' JOBID' in x else int(x[:8]))
for i in output:
    print(i.rstrip())

print()
print('---------------------------------------------------------------------------------------------------------------------------------------')
print()
print()
print()