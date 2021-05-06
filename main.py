print('Enter 1 for pipelined, 2 for non pipelined: ')
pipelined = int(input())
print(
    'Enter cache size (in bytes), number of blocks per set, block size (in bytes) [space separated]')
cacheSize, numBlocksPerSet, blockSize = map(int, input().strip().split())
numSet = cacheSize // (blockSize*numBlocksPerSet)

if pipelined == 1:
    from pipelined.control import *
    from pipelined.gui import *
    print('Enter 1 for forwarding, 2 for not-forwarding: ')
    forwarding = int(input())
    print('Enter 1 for printing registers, 2 for not: ')
    printreg = int(input())
    control = Control(numSet, numBlocksPerSet, blockSize)

    if forwarding == 1:
        control.forwarding = True
    else:
        control.forwarding = False

    if printreg == 1:
        control.print_registers = True
    else:
        control.print_registers = False
    w = window(control)

else:
    from non_pipelined.control import *
    from non_pipelined.gui import *

    control = Control(numSet, numBlocksPerSet, blockSize)
    w = window(control)

w.root.mainloop()
