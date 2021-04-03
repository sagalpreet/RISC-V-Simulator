import ALU, IAG, memory, register

TERMINATION_CODE = 0xFFFFFFFF
class Control:
    def __init__(self):
        self.iag = IAG.IAG(0)
        self.alu = ALU.ALU()
        self.pmi = memory.ProcessorMemoryInterface(4)
        self.reg = register.register_module()

        # global variables
        self.IR = self.opcode = self.imm = self.funct3 = self.funct7 = 0
        self.branch = self.jump = 0
        self.PC_Temp = 0
        self.substep_counter = 0

    def fetch(self):
        self.pmi.mem_read = True
        self.pmi.dataType = 2
        self.pmi.update(self.alu.rz, self.iag.PC, self.alu.rm, 1) # set MAR to PC
        self.IR = self.pmi.getMDR() # get instruction corresponding to PC
        self.PC_Temp = self.iag.PC
        return

    def decode(self):
        self.opcode = ((1<<7) - 1) & self.IR
        self.rd = (((1<<12) - (1<<7)) & self.IR)>>7
        self.funct3 = (((1<<15) - (1<<12)) & self.IR)>>12
        self.rs1 = (((1<<20) - (1<<15)) & self.IR)>>15
        self.rs2 = (((1<<25) - (1<<20)) & self.IR)>>20
        self.funct7 = (((1<<32) - (1<<25)) & self.IR)>>25
        print(self.opcode, self.rd, self.funct3, self.rs1, self.rs2, self.funct7)

        if self.opcode == 0b0110011: # R format
            self.imm = 0         # immediate unnecessary
            self.alu.muxA = 0    # use rs1
            self.alu.muxB = 0    # use rs2
            self.alu.aluOp = 2   # determine operation with funct3 and funct7
            self.alu.muxY = 0    # output is output of ALU
            self.branch = 0      # don't branch
            self.jump = 0        # don't jump
            self.reg.reg_write = True    # write to register
        elif self.opcode == 0b0010011 or self.opcode == 0b0000011 or self.opcode == 0b1100111: # I format
            self.imm = (((1<<32) - (1<<20)) & self.IR) >> 20 
            if (self.imm>>11)&1 == 1:            # check if sign bit is 1
                self.imm = -((self.imm ^ ((1<<12)-1)) + 1)
            self.alu.muxA = 0            # op1 is rs1
            self.alu.muxB = 1            # op2 is imm
            self.reg.reg_write = True    # write to register
            self.jump = 0                # don't jump
            self.branch = 0              # don't branch
            if self.opcode == 0b0010011: # arithmetic I format
                self.alu.aluOp = 2       # determine operation with funct3 and funct7
                self.alu.muxY = 0        # output is output of ALU
            else:                   # load or jalr
                self.alu.aluOp = 0       # add
                if self.opcode == 0b0000011:     # load
                    self.alu.muxY = 1    # output is MDR
                    self.pmi.dataType = self.funct3   # datatype to read
                    self.pmi.mem_read = True     # read memory
                else:                       # jalr
                    self.branch = 1              # branch
                    self.jump = 1                # and jump
                    self.alu.muxY = 2            # output is return address
        elif self.opcode == 0b0100011: # S format
            self.imm = ((((1<<32) - (1<<25)) & self.IR) >> 20) + ((((1<<12)-(1<<7)) & self.IR)>>7)
            if (self.imm>>11)&1 == 1:            # check if sign bit is 1
                self.imm = -((self.imm^((1<<12)-1)) + 1)
            self.alu.muxA = 0            # op1 is rs1
            self.alu.muxB = 1            # op2 is imm
            self.alu.aluOp = 0           # add
            self.alu.muxY = -1           # output is nothing
            self.pmi.mem_write = True    # write to memory
            self.pmi.dataType = self.funct3   # datatype to write
            self.branch = 0              # don't branch
            self.jump = 0                # don't jump
        elif self.opcode == 0b1100011: # SB format
            self.imm = (((1<<31) & self.IR) >> 19) + (((1<<7) & self.IR) << 4) + ((((1<<31) - (1<<25)) & self.IR)>>20) + ((((1<<12) - (1<<8))&self.IR)>>7)
            print(self.imm, '{:b}'.format(self.imm))
            if (self.imm>>12)&1 == 1:            # check if sign bit is 1
                self.imm = -((self.imm^((1<<13)-1)) + 1)
            print(self.imm, '{:b}'.format(self.imm))
            self.alu.muxA = 0            # op1 is rs1
            self.alu.muxB = 0            # op2 is rs2
            self.alu.aluOp = 1           # determine branch operation by funct3
            self.alu.muxY = -1           # no output
            self.branch = 1              # branch
            self.jump = 0                # don't jump
        elif self.opcode == 0b0110111 or self.opcode == 0b0010111:    # U format
            self.imm = ((1<<32) - (1<<12)) & self.IR
            if self.opcode == 0b0010111: # if auipc
                self.alu.muxA = 1        # op1 is PC
            else:                   # if lui
                self.alu.muxA = 0        # op1 is rs1
            self.alu.muxB = 1            # op2 is rs2
            self.alu.aluOp = 0           # add
            self.reg.reg_write = True    # write to register
            self.alu.muxY = 0            # output is ALU
            self.branch = 0              # don't branch
            self.jump = 0                # don't jump
        elif self.opcode == 0b1101111:   # UJ format
            self.imm = (((1<<31) & self.IR)>>11) + (((1<<20) - (1<<12)) & self.IR) + (((1<<20) & self.IR)>>9) + ((((1<<31) - (1<<21)) & self.IR)>>20)
            if (self.imm>>20)&1 == 1:            # check if sign bit is 1
                self.imm = -((self.imm^((1<<21)-1)) + 1)
            self.alu.muxA = 0            # op1 is rs1
            self.alu.muxB = 0            # op2 is rs2
            self.reg.reg_write = True    # write to register
            self.alu.aluOp = -1          # no operation
            self.alu.muxY = 2            # output is return address
            self.branch = 1              # branch
            self.jump = 0                # don't jump
        print(f"CNT 7:{self.funct7} rs2:{self.rs2} rs1:{self.rs1} imm:{self.imm}, 3:{self.funct3}, rd:{self.rd}, op:{self.opcode}")
        self.reg.read_register_1 = "{0:b}".format(self.rs1)
        self.reg.read_register_2 = "{0:b}".format(self.rs2)
        self.reg.write_register = "{0:b}".format(self.rd)
        self.reg.read_register()
        return

    def execute(self):
        self.alu.execute(self.reg.read_data_1, self.reg.read_data_2, self.imm, self.funct3, self.funct7, self.iag.PC)
        return

    def memory_access(self):
        self.pmi.update(self.alu.rz, self.iag.PC, self.alu.rm, 0)
        self.alu.process_output(self.pmi.getMDR(), self.iag.PC+4)
        self.iag.PCSrc = self.alu.zero & self.branch | ((self.branch & self.jump)<<1)
        print(self.alu.zero, self.branch)
        self.iag.update(self.imm, self.alu.rz)
        return

    def register_update(self):
        self.reg.write_data = self.alu.ry
        self.reg.register_update()
        print("RU")
        return
    
    def substep(self):
        if self.substep_counter == 0:
            self.fetch()
            print(self.iag.PC, "{:b}".format(self.IR))
        elif self.substep_counter == 1:
            self.decode()
        elif self.substep_counter == 2:
            self.execute()
        elif self.substep_counter == 3:
            self.memory_access()
        elif self.substep_counter == 4:
            self.register_update()
        self.substep_counter += 1
        self.substep_counter %= 5

    def step(self):
        for _ in range(5):
            self.substep()
            if self.substep_counter == 0:
                break

    def load(self, file):
        with open(file, 'r') as infile:
                text = True
                for line in infile:
                    mloc, instr = [int(x, 16) for x in line.split()]
                    if text:
                        self.pmi.memory.setWordAtAddress(mloc, instr)
                    else:
                        self.pmi.memory.setByteAtAddress(mloc, instr)
                        
                    if instr == TERMINATION_CODE:
                        text = False

    def run(self):
        while (True):
            self.step()
            if self.IR == TERMINATION_CODE or self.IR == 0:
                break
