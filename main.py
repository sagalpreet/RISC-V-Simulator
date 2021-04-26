pipelined = int(input())

if pipelined == 1:
    from pipelined.control import *
    from pipelined.gui import *
else:
    from non_pipelined.control import *
    from non_pipelined.gui import *

control = Control()
w = window(control)

w.root.mainloop()
