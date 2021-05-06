from tkinter import *
from tkinter import ttk, filedialog
import tkinter as tk


class window:
    def __init__(self, control):
        self.setupRoot()
        self.setupMenu()
        self.setupMain()
        self.setupLeft()
        self.setupCache()
        self.setupPipeline()
        self.setupRight()
        self.setupMid()
        self.setupBottom()
        self.setupCacheStats()
        
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

    def setupCache(self):
        self.cPane = cachePane(self.mainframe, self)

    def setupPipeline(self):
        self.pPane = pipelineView(self.mainframe, self)
    
    def setupCacheStats(self):
        self.cachePane = cache_stats(self.mainframe, self)

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
            memTree.insert(parent='', index='end', iid=i, text="", values=(
                '0x'+format(i, '08X'), '0x'+format(memory[i], '02X')))
        self.pPane.draw(self.control)
        self.cachePane.draw(self.control)

        # update cache
        cacheTree = self.cPane.tree
        sets = self.control.pmi.cache.sets
        numSets = self.control.pmi.cache.numSets
        numBlocksPerSet = self.control.pmi.cache.numBlocksPerSet
        blockSize = self.control.pmi.cache.blockSize
        for i in range(numSets):
            for j in range(len(sets[i].blocks)):
                iid = 'd$'+str(i+1)+'$'+str(j+1)
                tag = sets[i].blocks[j]
                frmt = '0'+str(2*blockSize)+'X'
                cacheTree.item(iid, values=('', '0x'+format(tag, '08X'), '0x'+self.control.pmi.memory.getNBytes(tag*blockSize, blockSize)))

        sets = self.control.i_pmi.cache.sets
        numSets = self.control.i_pmi.cache.numSets
        numBlocksPerSet = self.control.i_pmi.cache.numBlocksPerSet
        blockSize = self.control.i_pmi.cache.blockSize
        for i in range(numSets):
            for j in range(len(sets[i].blocks)):
                iid = 'i$'+str(i+1)+'$'+str(j+1)
                tag = sets[i].blocks[j]
                frmt = '0'+str(2*blockSize)+'X'
                cacheTree.item(iid, values=('', '0x'+format(tag, '08X'), '0x'+self.control.i_pmi.memory.getNBytes(tag*blockSize, blockSize)))


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

        self.tree = ttk.Treeview(
            parent, selectmode='none', yscrollcommand=tree_scroll.set)
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
        # button to execute to the end of program
        run = ttk.Button(parent, text="Run", command=self.run)
        run.grid(column=0, row=0, sticky='news')

        # button to execute current instruction and go to next instruction
        next = ttk.Button(parent, text="Next Instruction", command=self.next)
        next.grid(column=1, row=0, sticky='news')

        # button to execute current substep (F-E-D-M-U)
        next_ = ttk.Button(parent, text="Next Substep", command=self.next_)
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
        '''control = self.win.control
        control.step()
        pc = control.iag.PC
        register = control.reg.register
        memory = control.pmi.memory.byteData
        self.win.update(pc, register, memory)'''
        return

    def next_(self):
        control = self.win.control
        control.substep()
        pc = control.iag.PC
        register = control.reg.register
        memory = control.pmi.memory.byteData
        self.win.update(pc, register, memory)
        return

class cachePane:
    def __init__(self, parent, win):
        self.win = win

        self.setupGUI(parent)

    def setupGUI(self, parent):
        parentFrame = ttk.Frame(parent)
        parentFrame.grid(row=0, column=1, sticky='news')
        parentFrame.columnconfigure(0, weight=1)
        parentFrame.rowconfigure(0, weight=1)

        cacheFrame = ttk.Frame(parentFrame)
        cacheFrame.grid(row=0, column=0, sticky='nws')
        cacheFrame.columnconfigure(0, weight=1)
        cacheFrame.rowconfigure(0, weight=1)
        self.setupCacheFrame(cacheFrame)

    def setupCacheFrame(self, parent):
        tree_scroll = ttk.Scrollbar(parent)
        tree_scroll.pack(side=RIGHT, fill=Y)

        self.tree = ttk.Treeview(
            parent, selectmode='none', yscrollcommand=tree_scroll.set)
        self.tree['columns'] = ['Set Number', 'Tag', 'Cache Content']

        self.tree.column('#0', width=20, stretch=NO)
        self.tree.column('Set Number', width=100, anchor=CENTER)
        self.tree.column('Cache Content', anchor=CENTER)
        self.tree.column('Tag', width=50, anchor=CENTER)

        self.tree.heading('Set Number', text='Set Number')
        self.tree.heading('Cache Content', text='Cache Content')
        self.tree.heading('Tag', text='Tag')

        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        tree_scroll.config(command=self.tree.yview)
        #self.tree.grid(row=0, column=0, sticky='news')

        self.tree.tag_configure('heading', background="lightyellow")
        self.tree.tag_configure('victim', background="lightgreen")


class midPane:
    def __init__(self, parent):
        self.setupGUI(parent)

    def setupGUI(self, parent):
        parentFrame = ttk.Frame(parent)
        parentFrame.grid(row=0, column=2, sticky='news')
        parentFrame.columnconfigure(0, weight=1)
        parentFrame.rowconfigure(0, weight=1)

        self.setupRegisterFrame(parentFrame)

    def setupRegisterFrame(self, parent):
        tree_scroll = ttk.Scrollbar(parent)
        tree_scroll.pack(side=RIGHT, fill=Y)

        self.tree = ttk.Treeview(
            parent, selectmode='browse', yscrollcommand=tree_scroll.set)
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
        parentFrame.grid(row=0, column=3, sticky='news')
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

        self.tree = ttk.Treeview(
            parent, selectmode='browse', yscrollcommand=tree_scroll.set)
        self.tree['columns'] = ['Memory Address', 'Data']

        self.tree.column('#0', width=0, stretch=NO)
        self.tree.column('Memory Address', anchor=CENTER)
        self.tree.column('Data', width=50, anchor=CENTER)

        self.tree.heading('Memory Address', text='Memory Address')
        self.tree.heading('Data', text='Data')

        self.tree.pack(side=LEFT, fill=BOTH)
        tree_scroll.config(command=self.tree.yview)
        #self.tree.grid(row=0, column=0, sticky='news')

        self.tree.tag_configure('normal', background="white")
        self.tree.tag_configure('updated', background="lightyellow")

    def setupButtonFrame(self, parent):
        ttk.Label(parent, text="Address to go: ").grid(
            row=0, column=0, sticky='nws')

        self.toGo = StringVar()  # textbox to get input address
        toGoAddress = ttk.Entry(parent, width=10, textvariable=self.toGo)
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
        parentFrame.grid(row=1, column=0, columnspan=5, sticky='news')
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
            cacheTree = win.cPane.tree

            instrTree.delete(*instrTree.get_children())
            memTree.delete(*memTree.get_children())
            regTree.delete(*regTree.get_children())
            cacheTree.delete(*cacheTree.get_children())

            text = True
            with open(filename, 'r') as infile:
                for line in infile:
                    if text == True:
                        mloc, instr = [str(x) for x in line.split()]
                        instrTree.insert(parent='', index='end', iid=int(
                            mloc, 16), text="", values=(mloc, instr))
                    else:
                        mloc, value = [hex(int(x, 16)) for x in line.split()]
                        memTree.insert(parent='', index='end', iid=int(
                            mloc, 16), text="", values=(mloc, value))
                    if int(instr, 16) == TERMINATION_CODE:
                        text = False
            for i in range(32):
                regTree.insert(parent='', index='end', iid=i, text="", values=(
                    'x'+str(i), '0x'+format(0, '08X')))
            
            cacheTree.insert(parent='', index='end', iid='Data Cache',
                             text="", values=('Data', 'Cache', ''), tags='victim')
            
            cacheTree.insert(parent='', index='end', iid='Instruction Cache',
                             text="", values=('Instruction', 'Cache', ''), tags='victim')

            for setNo in range(1, win.control.pmi.cache.numSets + 1):
                cacheTree.insert(parent='Data Cache', index='end', iid='d$' +
                                 str(setNo), text="", values=(setNo-1, '', ''), tag = 'heading')
                for blockNo in range(1, win.control.pmi.cache.numBlocksPerSet + 1):
                    cacheTree.insert(parent='Data Cache', index='end', iid='d$' +
                                     str(setNo)+'$'+str(blockNo), text='', values=('', 0, 0))
            
            for setNo in range(1, win.control.i_pmi.cache.numSets + 1):
                cacheTree.insert(parent='Instruction Cache', index='end', iid='i$' +
                                 str(setNo), text="", values=(setNo-1, '', ''), tag = 'heading')
                for blockNo in range(1, win.control.i_pmi.cache.numBlocksPerSet + 1):
                    cacheTree.insert(parent='Instruction Cache', index='end', iid='i$' +
                                     str(setNo)+'$'+str(blockNo), text='', values=('', 0, 0))

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


class pipelineView:

    def __init__(self, parent, win, width=500, height=700):
        self.win = win
        self.width = 500
        self.height = 700
        self.setupGUI(parent)

    def setupGUI(self, parent):
        parentFrame = ttk.Frame(parent)
        parentFrame.grid(row=0, column=4, sticky='news')
        parentFrame.columnconfigure(0, weight=1)
        parentFrame.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(parentFrame, bg="white", width=self.width, height=self.height)
        self.canvas.pack()
        self.__draw([], [], [], 0, -1)

    def getPc(self, stage, control):
        pc = None
        if stage==1:
            pc = control.iag.PC
        elif stage<=5:
            pc = control.buffers[stage-2].PC_Temp
        return hex(pc) if pc is not None else ""

    def draw(self, control):
        if control is None:
            return

        # How to draw a pipeline?
        # Create a pipeline array
        # "|": Produces a buffer
        # " ": Produces an empty space
        # "X": Produces a box with "X" written upon it
        #  - Arrows are handled automatically

        # How to draw data forwards?
        # Create a forwards array
        # The forwards array is copy of the pipeline array
        # But a character other than space denotes one end of an arrow
        # In given example, there are 2 forwards with id '1' and '2'
        # ID can be any character other than space

        # `cycleBegin` is the label of the cycle number during which
        # the first step of `pipelineAr[0]` is executed
        # `currentCycle` is the current clock cycle (absolute, control.cycle maybe?)

        #pipelineAr = ["F|D|E|M|W",
        #              "  F| |D|E|M|W",
        #              "    F|D|E|M|W"]
        #forwardsAr = ["       1 ",
        #              "      2  1   ",
        #              "        2      "]

        #cycleBegin = 5
        #currentCycle = 7

        pipelineAr = []
        forwardsAr = []
        pcAr = []
        cycleBegin = control.clock
        currentCycle = control.clock
        for stage in reversed(control.stages):
            pipelineMap = {
                1: " F|D|E|M|W",
                2: "|D|E|M|W",
                3: "|E|M|W",
                4: "|M|W",
                5: "|W",
            }
            if stage in [1, 2, 3, 4, 5]:
                pcAr.append(self.getPc(stage, control))
                pipelineStr = pipelineMap[stage]
                #if control.stall and stage in [1, 2]:
                #    pipelineStr = "  " + pipelineStr
                pipelineAr.append(pipelineStr)
                forwardsAr.append(" "*len(pipelineStr)) # No forwarding shown

        # TODO: Show data forwarding
        # TODO: Hide 0x00000000 instruction
        # TODO: Show instruction PC (optional)

        self.__draw(pipelineAr, forwardsAr, pcAr, cycleBegin=cycleBegin,
                    currentCycle=currentCycle)

    def __draw(self, pipelineAr, forwardsAr, pcAr, cycleBegin=0, currentCycle=0, indentAutomatically=False):
        # self.canvas.size() returns (0, 0)
        W = self.width
        H = self.height
        BOX_SIZE = 40
        BUFFER_W = 5
        BUFFER_H = BOX_SIZE
        MARGIN = 10
        TOP_MARGIN = 50
        LEFT_MARGIN = 100
        offset = (BOX_SIZE - BUFFER_W)/2
        LINEX = LEFT_MARGIN - BOX_SIZE
        forwardsCoordinates = {}

        self.canvas.create_rectangle(0, 0, W, H, fill="white", outline="white")
        self.canvas.create_rectangle(0, 0, LEFT_MARGIN-BOX_SIZE, H, fill="#eeeeee", outline="white")

        # 1. Drawing help lines and cycle labels
        # 2. Highlighting the current cycle
        self.canvas.create_line(0, TOP_MARGIN, W, TOP_MARGIN, fill="black")
        upOffset = 10
        for i in range(10):
            drawCycle = cycleBegin+i
            x = LEFT_MARGIN + MARGIN + (2*i)*BOX_SIZE - BOX_SIZE/2
            if(drawCycle == currentCycle):
                self.canvas.create_rectangle(
                    x, TOP_MARGIN, x+2*BOX_SIZE, H, fill="#bbffbb")
            self.canvas.create_line(x, TOP_MARGIN-upOffset, x, H, dash=(4, 2))
            self.canvas.create_text(
                x, TOP_MARGIN-upOffset-20, text=f"{drawCycle}")
        y = TOP_MARGIN + MARGIN/2
        while(y<H):
            y += BOX_SIZE + MARGIN
            self.canvas.create_line(0, y, LINEX, y)

        self.canvas.create_text(LINEX-MARGIN, TOP_MARGIN - MARGIN, anchor="e", text="PC🡓")
        self.canvas.create_line(LINEX, 0, LINEX, H, width=5)
        self.canvas.create_line(0, TOP_MARGIN/2, LINEX, TOP_MARGIN/2)
        self.canvas.create_text(LINEX-MARGIN, TOP_MARGIN/2 - MARGIN, anchor="e", text="CLK🡒")
        for index, pc in enumerate(pcAr):
            y = TOP_MARGIN+MARGIN + index*(BOX_SIZE+MARGIN) + BOX_SIZE/2
            x = LINEX-MARGIN
            self.canvas.create_text(x, y, text=pc, anchor="e")

        # 1. Drawing boxes, buffers and spaces
        # 2. Noting the `forwardsCoordinates`
        for instIndex, instAr in enumerate(pipelineAr):
            isLeadingSpace = True
            for gridIndex, item in enumerate(instAr):
                y = TOP_MARGIN+MARGIN + instIndex*(BOX_SIZE+MARGIN)
                x = LEFT_MARGIN + MARGIN + ((2*instIndex if indentAutomatically else 0) + gridIndex-1)*BOX_SIZE
                offset = (BOX_SIZE - BUFFER_W)/2
                if item == '|':
                    self.canvas.create_rectangle(
                        x+offset, y, x+offset+BUFFER_W, y+BUFFER_H, fill="black")
                    self.canvas.create_line(
                        x, y+BOX_SIZE/2, x+offset, y+BOX_SIZE/2, arrow=tk.LAST)
                    isLeadingSpace = False
                elif item == " ":
                    if not isLeadingSpace:
                        self.canvas.create_line(
                            x-offset, y+BOX_SIZE/2, x+BOX_SIZE, y+BOX_SIZE/2)
                else:
                    isLeadingSpace = False
                    self.canvas.create_rectangle(x, y, x+BOX_SIZE, y+BOX_SIZE)
                    self.canvas.create_text(
                        x+BOX_SIZE/2, y+BOX_SIZE/2, text=item)
                    if item != "F":
                        self.canvas.create_line(
                            x-offset, y+BOX_SIZE/2, x, y+BOX_SIZE/2, arrow=tk.LAST)
                pipeId = forwardsAr[instIndex][gridIndex]
                if(pipeId != " "):
                    forwardsCoordinates.setdefault(pipeId, [])
                    forwardsCoordinates[pipeId].append((x, y))

        # 1. Drawing the data forwards
        for pipeId in forwardsCoordinates:
            coordinates = forwardsCoordinates[pipeId]
            if(len(coordinates) > 0):
                (x1, y1), (x2, y2) = coordinates
                x1 += BOX_SIZE/2
                x2 += BOX_SIZE/2
                y1 += BOX_SIZE/2
                y2 += BOX_SIZE/2
                self.canvas.create_line(
                    x1, y1, x2, y2, fill="red", arrow=tk.LAST, width=3)


class cache_stats:
    
    def __init__(self, parent, win, width=500, height=90):
        self.win = win
        self.width = 2000
        self.height = 60
        self.setupGUI(parent)
        # data cache stats
        self.d_hits_pane
        self.d_misses_pane
        self.d_accesses_pane
        # instruction cache stats
        self.i_hits_pane
        self.i_misses_pane
        self.i_accesses_pane
        
    def setupGUI(self, parent):
        parentFrame = ttk.Frame(parent)
        parentFrame.grid(row=2, column=0, columnspan=5, sticky='news')
        parentFrame.columnconfigure(0, weight=1)
        parentFrame.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(parentFrame, bg="white", width=self.width, height=self.height)
        self.canvas.pack()
        #self.__draw()
        self.d_hits_pane =self.canvas.create_text(100,15,fill="green",font="Times 15 italic bold",text="No. of D$ hits: 0")
        self.d_misses_pane = self.canvas.create_text(100,45,fill="red",font="Times 15 italic bold",text="No. of D$ misses: 0")
        self.d_accesses_pane = self.canvas.create_text(350,15,fill="darkblue",font="Times 15 italic bold",text="No. of D$ accesses: 0")
        self.d_victim_pane = self.canvas.create_text(350,45,fill="purple",font="Times 15 italic bold",text="D$ Victim Block's Tag: -1")
        
        self.i_hits_pane =self.canvas.create_text(600,15,fill="green",font="Times 15 italic bold",text="No. of I$ hits: 0")
        self.i_misses_pane = self.canvas.create_text(600,45,fill="red",font="Times 15 italic bold",text="No. of I$ misses: 0")
        self.i_accesses_pane = self.canvas.create_text(850,15,fill="darkblue",font="Times 15 italic bold",text="No. of I$ accesses: 0")
        self.i_victim_pane = self.canvas.create_text(850,45,fill="purple",font="Times 15 italic bold",text="I$ Victim Block's Tag: -1")
        
    def get_hits_data_cache(self, control):
        num_hits = control.pmi.cache.hits
        return num_hits
    
    def get_misses_data_cache(self, control):
        num_misses = control.pmi.cache.misses
        return num_misses
    
    def get_accesses_data_cache(self, control):
        num_accesses = control.pmi.cache.numAccesses
        return num_accesses
    
    def get_hits_intruction_cache(self, control):
        num_hits = control.i_pmi.cache.hits
        return num_hits
    
    def get_misses_intruction_cache(self, control):
        num_misses = control.i_pmi.cache.misses
        return num_misses
    
    def get_accesses_intruction_cache(self, control):
        num_accesses = control.i_pmi.cache.numAccesses
        return num_accesses       
    
    def draw(self, control):
        if control is None:
            return
        
        d_hits = self.get_hits_data_cache(control)
        d_misses = self.get_misses_data_cache(control)
        d_accesses = self.get_accesses_data_cache(control)
        d_victim = control.pmi.cache.victim
        
        self.canvas.itemconfigure(self.d_hits_pane, text = f"No. of D$ hits: {d_hits}")
        self.canvas.itemconfigure(self.d_misses_pane, text = f"No. of D$ misses: {d_misses}")
        self.canvas.itemconfigure(self.d_accesses_pane, text = f"No. of D$ accesses: {d_accesses}")
        if d_victim != -1:
            d_victim = '0x'+format(d_victim, '08X')
        self.canvas.itemconfigure(self.d_victim_pane, text = f"D$ Victim Block's Tag: {d_victim}")
        
        i_hits = self.get_hits_intruction_cache(control)
        i_misses = self.get_misses_intruction_cache(control)
        i_accesses = self.get_accesses_intruction_cache(control)
        i_victim = control.i_pmi.cache.victim
        
        self.canvas.itemconfigure(self.i_hits_pane, text = f"No. of I$ hits: {i_hits}")
        self.canvas.itemconfigure(self.i_misses_pane, text = f"No. of I$ misses: {i_misses}")
        self.canvas.itemconfigure(self.i_accesses_pane, text = f"No. of I$ accesses: {i_accesses}")
        if i_victim != -1:
            i_victim = '0x'+format(i_victim, '08X')  
        self.canvas.itemconfigure(self.i_victim_pane, text = f"I$ Victim Block's Tag: {i_victim}")
        
        
        
    def __draw(self):
        self.canvas.create_text(100,15,fill="green",font="Times 15 italic bold",text="No. of hits: 0")
        self.canvas.create_text(100,45,fill="red",font="Times 15 italic bold",text="No. of misses: 0")
        self.canvas.create_text(100,75,fill="darkblue",font="Times 15 italic bold",text="No. of accesses: 0")
        
        
        