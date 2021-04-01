from tkinter import *
from tkinter import ttk, filedialog
import os


def openFile():
    filename = filedialog.askopenfilename(initialdir='/', title="Select File", filetypes=[("machine code", "*.mc")])
    return


def MENU():
    menubar = Menu(root)

    filemenu = Menu(menubar, tearoff=0)
    filemenu.add_command(label="New")
    filemenu.add_command(label="Open", command=openFile)
    filemenu.add_command(label="Save")
    filemenu.add_command(label="Save as...")
    filemenu.add_command(label="Close")
    filemenu.add_separator()
    filemenu.add_command(label="Exit", command=root.quit)
    menubar.add_cascade(label="File", menu=filemenu)

    editmenu = Menu(menubar, tearoff=0)
    editmenu.add_command(label="Undo")
    editmenu.add_separator()
    editmenu.add_command(label="Cut")
    editmenu.add_command(label="Copy")
    editmenu.add_command(label="Paste")
    editmenu.add_command(label="Delete")
    editmenu.add_command(label="Select All")
    menubar.add_cascade(label="Edit", menu=editmenu)

    helpmenu = Menu(menubar, tearoff=0)
    helpmenu.add_command(label="Help Index")
    helpmenu.add_command(label="About...")
    menubar.add_cascade(label="Help", menu=helpmenu)

    root.config(menu=menubar)

    return


# main window
root = Tk()
root.title('RISC-V Simulator')
root.configure(background='black', highlightcolor='orange',
               highlightthickness=2)
w, h = root.winfo_screenwidth(), root.winfo_screenheight()
root.geometry("%dx%d+0+0" % (w, h))

# add menubar
MENU()

# add mainframe
mainframe = ttk.Frame(root)
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

# window divided into 2 to show registers/memory and code
leftPane = ttk.Frame(mainframe)
leftPane.grid(column=0, row=0, sticky=(N, W, E, S))
rightPane = ttk.Frame(mainframe)
rightPane.grid(column=1, row=0, sticky=(N, W, E, S))

# run Application
root.mainloop()