from tkinter import *
from tkinter import ttk, filedialog
import tkinter as tk

class window:
    def __init__(self, control):
        self.setupRoot()
        self.setupMenu()
        self.setupMain()
        self.setupLeft()
        self.setupRight()
        self.setupMid()
        self.setupBottom()
        
        self.control = control
    
    def setupRoot(self):
        self.root = Tk()
        self.root.title('RISC-V Simulator')
        self.root.configure()
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.minsize(1100, 700)
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
        self.lPane = leftPane(self.mainframe, self)

    def setupMid(self):
        self.mPane = midPane(self.mainframe)

    def setupRight(self):
        self.rPane = rightPane(self.mainframe)

    def setupBottom(self):
        self.bPane = bottomPane(self.mainframe, self)

    def update(self, pc, register, memory):

        '''
        pc : integer
        register : list of 32 integers
        memory : dictionary -> keys(address): integers, values(value at that address): integers
        '''

        # update pc
        instrTree = self.lPane.tree
        try:
            instrTree.item(self.pc, tags='normal')
        except:
            pass
        try:
            instrTree.item(pc, tags='highlight')
            self.pc = pc
        except:
            instrTree.item(instrTree.get_children()[-1], tags='ended')

        # update reg
        regTree = self.mPane.tree
        for i in range(32):
            prevReg = regTree.item(i, 'values')
            regi = register[i]
            if regi < 0:
                regi = 2**32 + regi
            newReg = ('x'+str(i), '0x'+format(regi, '08X'))
            if prevReg != newReg:
                regTree.item(i, values=newReg, tags='updated')
            else:
                regTree.item(i, tags='normal')

        # update mem
        memTree = self.rPane.tree
        memTree.delete(*memTree.get_children())
        for i in memory:
            memTree.insert(parent='', index='end', iid=i, text="", values=('0x'+format(i, '08X'), '0x'+format(memory[i], '02X')))

class leftPane:
    def __init__(self, parent, win):
        self.win = win

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

        self.tree.tag_configure('normal', background="white")
        self.tree.tag_configure('highlight', background="lightblue")
        self.tree.tag_configure('ended', background="red")

    def setupButtonFrame(self, parent):
        run = ttk.Button(parent, text="Run", command=self.run) # button to execute to the end of program
        run.grid(column=0, row=0, sticky='news')

        next = ttk.Button(parent, text="Next Instruction", command=self.next) # button to execute current instruction and go to next instruction
        next.grid(column=1, row=0, sticky='news')

        next_ = ttk.Button(parent, text="Next Substep", command=self.next_) # button to execute current substep (F-E-D-M-U)
        next_.grid(column=2, row=0, sticky='news')

    def run(self):
        control = self.win.control
        control.run()
        pc = control.iag.PC
        register = control.reg.register
        memory = control.pmi.memory.byteData
        self.win.update(pc, register, memory)
        return
    
    def next(self):
        control = self.win.control
        control.step()
        pc = control.iag.PC
        register = control.reg.register
        memory = control.pmi.memory.byteData
        self.win.update(pc, register, memory)
        return
    
    def next_(self):
        control = self.win.control
        control.substep()
        pc = control.iag.PC
        register = control.reg.register
        memory = control.pmi.memory.byteData
        self.win.update(pc, register, memory)
        return

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

        self.tree = ttk.Treeview(parent, selectmode='browse', yscrollcommand=tree_scroll.set)
        self.tree['columns'] = ['Register Number', 'Register Content']

        self.tree.column('#0', width=0, stretch=NO)
        self.tree.column('Register Number', width=150, anchor=CENTER)
        self.tree.column('Register Content', anchor=CENTER)

        self.tree.heading('Register Number', text='Register Number')
        self.tree.heading('Register Content', text='Register Content')

        self.tree.pack(side=LEFT, fill=BOTH)
        tree_scroll.config(command=self.tree.yview)
        #self.tree.grid(row=0, column=0, sticky='news')

        self.tree.tag_configure('normal', background="white")
        self.tree.tag_configure('updated', background="lightgreen")

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

        self.tree = ttk.Treeview(parent, selectmode='browse', yscrollcommand=tree_scroll.set)
        self.tree['columns'] = ['Memory Address', 'Memory Content']

        self.tree.column('#0', width=0, stretch=NO)
        self.tree.column('Memory Address', width=200, anchor=CENTER)
        self.tree.column('Memory Content', anchor=CENTER)

        self.tree.heading('Memory Address', text='Memory Address')
        self.tree.heading('Memory Content', text='Memory Content')

        self.tree.pack(side=LEFT, fill=BOTH)
        tree_scroll.config(command=self.tree.yview)
        #self.tree.grid(row=0, column=0, sticky='news')

        self.tree.tag_configure('normal', background="white")
        self.tree.tag_configure('updated', background="lightyellow")

    def setupButtonFrame(self, parent):
        ttk.Label(parent, text="Address to go: ").grid(row=0, column=0, sticky='nws')

        self.toGo = StringVar()  # textbox to get input address
        toGoAddress = ttk.Entry(parent, width=16, textvariable=self.toGo)
        toGoAddress.grid(row=0, column=1, sticky='news')

        # button to go to some memory address
        go = ttk.Button(parent, text="Go", command=self.go)
        go.grid(row=0, column=2, sticky='news')

    def go(self):
        try:
            iid = int(self.toGo.get(), 16)

            first = int(self.tree.get_children()[0])
            last = int(self.tree.get_children()[-1])

            extent = (iid - first) / (last - first)

            self.tree.yview_moveto(extent)

            self.tree.focus(iid)
            self.tree.selection_set(iid)
        except:
            pass

        return

class bottomPane:
    def __init__(self, parent, win):
        self.win = win

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

        dumpButton = ttk.Button(parent, text='DUMP', command=self.dump)
        dumpButton.grid(row=0, column=2, sticky='news')

    def setFileNameLabel(self, filename):
        self.filenameLabel['text'] = filename

    def load(self):
        win = self.win
        filename = self.filenameLabel['text']
        TERMINATION_CODE = 0xFFFFFFFF
        try:
            win.control.reset()
            win.control.load(filename)

            instrTree = win.lPane.tree
            regTree = win.mPane.tree
            memTree = win.rPane.tree

            instrTree.delete(*instrTree.get_children())
            memTree.delete(*memTree.get_children())
            regTree.delete(*regTree.get_children())

            text = True
            with open(filename, 'r') as infile:
                for line in infile:
                    if text == True:
                        mloc, instr = [str(x) for x in line.split()]
                        instrTree.insert(parent='', index='end', iid=int(mloc, 16), text="", values=(mloc, instr))
                    else:
                        mloc, value = [hex(int(x, 16)) for x in line.split()]
                        memTree.insert(parent='', index='end', iid=int(mloc, 16), text="", values=(mloc, value))
                    if int(instr, 16) == TERMINATION_CODE:
                        text = False
            for i in range(32):
                regTree.insert(parent='', index='end', iid=i, text="", values=('x'+str(i), '0x'+format(0, '08X')))

            control = win.control
            pc = control.iag.PC
            register = control.reg.register
            memory = control.pmi.memory.byteData
            win.update(pc, register, memory)
            
        except:
            print("Error Reading Instructions and Memory Values")
        return

    def dump(self):
        try:
            self.win.control.dump()
        except:
            return