print('Enter 1 for pipelined, 2 for non pipelined: ')
pipelined = int(input())

if pipelined == 1:
    from pipelined.control import *
    from pipelined.gui import *
    print('Enter 1 for forwarding, 2 for not-forwarding: ')
    forwarding = int(input())
    print('Enter 1 for printing registers, 2 for not: ')
    printreg = int(input())
    control = Control()

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

    control = Control()
    w = window(control)

w.root.mainloop()
