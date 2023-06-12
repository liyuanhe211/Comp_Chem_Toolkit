import sys
from psutil import virtual_memory
with open(sys.argv[1],'a') as output_file:
    output_file.write(str(virtual_memory())+'\n\n')
    