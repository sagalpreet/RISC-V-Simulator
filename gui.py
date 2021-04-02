from tkinter import *
from tkinter import ttk, filedialog
import tkinter as tk

class window:
    def __init__(self):
        self.setupRoot()
        self.setupMenu()
        self.setupMain()
        self.setupLeft()
        self.setupRight()
        self.setupMid()
        self.setupBottom()
    
    def setupRoot(self):
        self.root = Tk()
        self.root.title('RISC-V Simulator')
        self.root.configure()
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.w, self.h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()

    def setupMenu(self):
        menubar = Menu()

        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="New")
        filemenu.add_command(label="Open", command=self.openFile)
        filemenu.add_command(label="Save")
        filemenu.add_command(label="Save as...")
        filemenu.add_command(label="Close")
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.root.quit)
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

        self.root.config(menu=menubar)

        return

    def openFile(self):
        self.filename = filedialog.askopenfilename(
            initialdir='/', title="Select File", filetypes=[("machine code", "*.mc"), ])
        self.bPane.setFileNameLabel(self.filename)

    def setupMain(self):
        self.mainframe = ttk.Frame(self.root)
        self.mainframe.grid(column=0, row=0, sticky='news')
        self.mainframe.columnconfigure(0, weight=1)
        self.mainframe.rowconfigure(0, weight=1)

    def setupLeft(self):
        self.lPane = leftPane(self.mainframe)

    def setupMid(self):
        self.mPane = midPane(self.mainframe)

    def setupRight(self):
        self.rPane = rightPane(self.mainframe)

    def setupBottom(self):
        self.bPane = bottomPane(self.mainframe)

class leftPane:
    def __init__(self, parent):
        self.instructions = {}
        self.setupGUI(parent)

    def setupGUI(self, parent):
        parentFrame = ttk.Frame(parent)
        parentFrame.grid(row=0, column=0, sticky='news')
        parentFrame.columnconfigure(0, weight=1)
        parentFrame.rowconfigure(0, weight=1)
        
        instructionFrame = ttk.Frame(parentFrame)
        instructionFrame.grid(row=0, column=0, sticky='nws')
        instructionFrame.columnconfigure(0, weight=1)
        instructionFrame.rowconfigure(0, weight=1)
        self.setupInstructionFrame(instructionFrame)

        buttonFrame = ttk.Frame(parentFrame)
        buttonFrame.grid(row=1, column=0, sticky='news')
        buttonFrame.columnconfigure(0, weight=1)
        buttonFrame.rowconfigure(0, weight=1)
        self.setupButtonFrame(buttonFrame)

    def setupInstructionFrame(self, parent):
        tree_scroll = ttk.Scrollbar(parent)
        tree_scroll.pack(side=RIGHT, fill=Y)

        self.tree = ttk.Treeview(parent, selectmode='none', yscrollcommand=tree_scroll.set)
        self.tree['columns'] = ['PC', 'Instruction']

        self.tree.column('#0', width=0, stretch=NO)
        self.tree.column('PC', width=100, anchor=CENTER)
        self.tree.column('Instruction', anchor=CENTER)

        self.tree.heading('PC', text='PC')
        self.tree.heading('Instruction', text='Instruction')

        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        tree_scroll.config(command=self.tree.yview)
        #self.tree.grid(row=0, column=0, sticky='news')

    def setupButtonFrame(self, parent):
        run = ttk.Button(parent, text="Run") # button to execute to the end of program
        run.grid(column=0, row=0, sticky='news')

        next = ttk.Button(parent, text="Next Instruction") # button to execute current instruction and go to next instruction
        next.grid(column=1, row=0, sticky='news')

        next_ = ttk.Button(parent, text="Next Substep") # button to execute current substep (F-E-D-M-U)
        next_.grid(column=2, row=0, sticky='news')

class midPane:
    def __init__(self, parent):
        self.setupGUI(parent)
    
    def setupGUI(self, parent):
        parentFrame = ttk.Frame(parent)
        parentFrame.grid(row=0, column=1, sticky='news')
        parentFrame.columnconfigure(0, weight=1)
        parentFrame.rowconfigure(0, weight=1)

        self.setupRegisterFrame(parentFrame)

    def setupRegisterFrame(self, parent):
        tree_scroll = ttk.Scrollbar(parent)
        tree_scroll.pack(side=RIGHT, fill=Y)

        tree = ttk.Treeview(parent, selectmode='browse', yscrollcommand=tree_scroll.set)
        tree['columns'] = ['Register Number', 'Register Content']

        tree.column('#0', width=0, stretch=NO)
        tree.column('Register Number', width=150, anchor=CENTER)
        tree.column('Register Content', anchor=CENTER)

        tree.heading('Register Number', text='Register Number')
        tree.heading('Register Content', text='Register Content')

        tree.pack(side=LEFT, fill=BOTH)
        tree_scroll.config(command=tree.yview)
        #self.tree.grid(row=0, column=0, sticky='news')

class rightPane:
    def __init__(self, parent):
        self.setupGUI(parent)
    
    def setupGUI(self, parent):
        parentFrame = ttk.Frame(parent)
        parentFrame.grid(row=0, column=2, sticky='news')
        parentFrame.columnconfigure(0, weight=1)
        parentFrame.rowconfigure(0, weight=1)

        memoryFrame = ttk.Frame(parentFrame)
        memoryFrame.grid(row=0, column=0, sticky='news')
        memoryFrame.columnconfigure(0, weight=1)
        memoryFrame.rowconfigure(0, weight=1)
        self.setupMemoryFrame(memoryFrame)

        buttonFrame = ttk.Frame(parentFrame)
        buttonFrame.grid(row=1, column=0, sticky='news')
        buttonFrame.columnconfigure(0, weight=1)
        buttonFrame.rowconfigure(0, weight=1)
        self.setupButtonFrame(buttonFrame)

    def setupMemoryFrame(self, parent):
        tree_scroll = ttk.Scrollbar(parent)
        tree_scroll.pack(side=RIGHT, fill=Y)

        tree = ttk.Treeview(parent, selectmode='browse', yscrollcommand=tree_scroll.set)
        tree['columns'] = ['Memory Address', 'Memory Content']

        tree.column('#0', width=0, stretch=NO)
        tree.column('Memory Address', width=200, anchor=CENTER)
        tree.column('Memory Content', anchor=CENTER)

        tree.heading('Memory Address', text='Memory Address')
        tree.heading('Memory Content', text='Memory Content')

        tree.pack(side=LEFT, fill=BOTH)
        tree_scroll.config(command=tree.yview)
        #self.tree.grid(row=0, column=0, sticky='news')

    def setupButtonFrame(self, parent):
        ttk.Label(parent, text="Address to go: ").grid(row=0, column=0, sticky='nws')

        self.toGo = StringVar()  # textbox to get input address
        toGoAddress = ttk.Entry(parent, width=16, textvariable=self.toGo)
        toGoAddress.grid(row=0, column=1, sticky='news')

        # button to go to some memory address
        go = ttk.Button(parent, text="Go", command=self.go)
        go.grid(row=0, column=2, sticky='news')

    def go(self):
        return

class bottomPane:
    def __init__(self, parent):
        parentFrame = ttk.Frame(parent, border=1, relief=RIDGE)
        parentFrame.grid(row=1, column=0, columnspan=3, sticky='news')
        parentFrame.columnconfigure(0, weight=1)
        parentFrame.rowconfigure(0, weight=1)
        self.setupGUI(parentFrame)
    
    def setupGUI(self, parent):
        self.filenameLabel = ttk.Label(parent, text='No File Selected')
        self.filenameLabel.grid(row=0, column=0, sticky='news')

        loadButton = ttk.Button(parent, text='LOAD', command=self.load)
        loadButton.grid(row=0, column=1, sticky='news')

    def setFileNameLabel(self, filename):
        self.filenameLabel['text'] = filename

    def load(self):
        global win
        filename = self.filenameLabel['text']
        TERMINATION_CODE = 0xFFFFFFFF
        left = win.lPane
        try:
            tree = left.tree
            with open(filename, 'r') as infile:
                for line in infile:
                    mloc, instr = [str(x) for x in line.split()]
                    tree.insert(parent='', index='end', iid=int(mloc, 16), text="", values=(mloc, instr))
                    if int(instr, 16) == TERMINATION_CODE:
                        break
        except:
            print("Error loading")
        return

###################
win = window()
win.root.mainloop()
###################
