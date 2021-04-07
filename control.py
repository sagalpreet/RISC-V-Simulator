import ALU, IAG, memory, register

TERMINATION_CODE = 0xFFFFFFFF
class Control:
    def __init__(self):
        # instance of all modules
        self.iag = IAG.IAG(0)
        self.alu = ALU.ALU()
        self.pmi = memory.ProcessorMemoryInterface(4)
        self.reg = register.register_module()

        # fields and some controls
        self.IR = self.opcode = self.imm = self.funct3 = self.funct7 = 0
        self.branch = self.jump = 0
        self.PC_Temp = 0
        self.substep_counter = 0

        # input file
        self.file = ""

    # reset control to initial values
    def reset(self):
        self.iag = IAG.IAG(0)
        self.alu = ALU.ALU()
        self.pmi = memory.ProcessorMemoryInterface(4)
        self.reg = register.register_module()

        # global variables
        self.IR = self.opcode = self.imm = self.funct3 = self.funct7 = 0
        self.branch = self.jump = 0
        self.PC_Temp = 0
        self.substep_counter = 0

    # fetch step
    def fetch(self):
        print("FETCH\n")
        # read memory
        self.pmi.mem_read = True
        # read a word
        self.pmi.dataType = 2
        # set MAR to PC
        self.pmi.update(self.alu.rz, self.iag.PC, self.alu.rm, 1)
        # get instruction corresponding to PC
        self.IR = self.pmi.getMDR()
        print(f"\tIR: {self.IR:08x}")
        self.PC_Temp = self.iag.PC

    def decode(self):
        # extract common fields. Not all of these are applicable to all instructions
        # but are extracted nonetheless, and used where necessary
        self.opcode = ((1<<7) - 1) & self.IR
        self.reg.rd = (((1<<12) - (1<<7)) & self.IR)>>7
        self.funct3 = (((1<<15) - (1<<12)) & self.IR)>>12
        self.reg.rs1 = (((1<<20) - (1<<15)) & self.IR)>>15
        self.reg.rs2 = (((1<<25) - (1<<20)) & self.IR)>>20
        self.funct7 = (((1<<32) - (1<<25)) & self.IR)>>25
        print("BRANCH")
        print(f"\tOpcode: {self.opcode:07b}")
        print(f"\trd: {self.reg.rd:05b}")
        print(f"\tfunct3: {self.funct3:03b}")
        print(f"\trs1: {self.reg.rs1:05b}")
        print(f"\trs2: {self.reg.rs2:05b}")
        print(f"\tfunct7: {self.funct7:07b}")

        if self.opcode == 0b0110011: # R format
            print("\tR format detected")
            self.imm = 0         # immediate unnecessary
            self.alu.muxA = 0    # use rs1
            self.alu.muxB = 0    # use rs2
            self.alu.aluOp = 2   # determine operation with funct3 and funct7
            self.alu.muxY = 0    # output is output of ALU
            self.branch = 0      # don't branch
            self.jump = 0        # don't jump
            self.reg.reg_write = True    # write to register
        elif self.opcode == 0b0010011 or self.opcode == 0b0000011 or self.opcode == 0b1100111: # I format
            print("\tI format detected")
            self.imm = (((1<<32) - (1<<20)) & self.IR) >> 20 
            if (self.imm>>11)&1 == 1:            # check if sign bit is 1
                self.imm = -((self.imm ^ ((1<<12)-1)) + 1)
            print(f"\timmediate: {self.imm:03x}")
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
            print("\tS format detected")
            self.imm = ((((1<<32) - (1<<25)) & self.IR) >> 20) + ((((1<<12)-(1<<7)) & self.IR)>>7)
            if (self.imm>>11)&1 == 1:            # check if sign bit is 1
                self.imm = -((self.imm^((1<<12)-1)) + 1)
            print(f"\timmediate: {self.imm:03x}")
            self.alu.muxA = 0            # op1 is rs1
            self.alu.muxB = 1            # op2 is imm
            self.alu.aluOp = 0           # add
            self.alu.muxY = 0           # output is irrelevant
            self.pmi.mem_write = True    # write to memory
            self.pmi.dataType = self.funct3   # datatype to write
            self.branch = 0              # don't branch
            self.jump = 0                # don't jump
        elif self.opcode == 0b1100011: # SB format
            print("\tSB format detected")
            self.imm = (((1<<31) & self.IR) >> 19) + (((1<<7) & self.IR) << 4) + ((((1<<31) - (1<<25)) & self.IR)>>20) + ((((1<<12) - (1<<8))&self.IR)>>7)
            if (self.imm>>12)&1 == 1:            # check if sign bit is 1
                self.imm = -((self.imm^((1<<13)-1)) + 1)
            print(f"\timmediate: {self.imm:04x}")
            self.alu.muxA = 0            # op1 is rs1
            self.alu.muxB = 0            # op2 is rs2
            self.alu.aluOp = 1           # determine branch operation by funct3
            self.alu.muxY = 0           # irrelevant output
            self.branch = 1              # branch
            self.jump = 0                # don't jump
        elif self.opcode == 0b0110111 or self.opcode == 0b0010111:    # U format
            print("\tU format detected")
            self.imm = ((1<<32) - (1<<12)) & self.IR
            print(f"\timmediate: {self.imm:05x}")
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
            print("\tUJ format detected")
            self.imm = (((1<<31) & self.IR)>>11) + (((1<<20) - (1<<12)) & self.IR) + (((1<<20) & self.IR)>>9) + ((((1<<31) - (1<<21)) & self.IR)>>20)
            if (self.imm>>20)&1 == 1:            # check if sign bit is 1
                self.imm = -((self.imm^((1<<21)-1)) + 1)
            print(f"\timmediate: {self.imm:06x}")
            self.alu.muxA = 0            # op1 is rs1
            self.alu.muxB = 0            # op2 is rs2
            self.reg.reg_write = True    # write to register
            self.alu.aluOp = 3          # no operation
            self.alu.muxY = 2            # output is return address
            self.branch = 1              # branch
            self.jump = 0                # don't jump
        
        print(f"\talu.muxA: {self.alu.muxA}")
        print(f"\talu.muxB: {self.alu.muxB}")
        print(f"\talu.aluOp: {self.alu.aluOp}")
        print(f"\talu.muxY: {self.alu.muxY}")
        print(f"\tbranch: {self.branch}")
        print(f"\tjump: {self.jump}")
        print(f"\treg_write: {self.reg.reg_write}")
        print(f"\tmem_read: {self.pmi.mem_read}")
        print(f"\tmem_write: {self.pmi.mem_write}")

    def execute(self):
        print("EXECUTE")
        self.reg.read_register()
        # execute any ALU operation
        self.alu.execute(self.reg.read_data_1, self.reg.read_data_2, self.imm, self.funct3, self.funct7, self.iag.PC)

    def memory_access(self):
        print("MEMORY ACCESS")
        # access memory
        self.pmi.update(self.alu.rz, self.iag.PC, self.alu.rm, 0)
        # this runs muxY and processes final output that goes to register file
        self.alu.process_output(self.pmi.getMDR(), self.iag.PC+4)
        # branch control bits for IAG. If LSB is 1, it's a branch instruction. MSB is only 1 for jalr
        self.iag.PCSrc = self.alu.zero & self.branch | ((self.branch & self.jump)<<1)
        # Update PC. This is done here since its value depends on output of ALU
        self.iag.update(self.imm, self.alu.rz)

    # writeback stage
    def register_update(self):
        print("REGISTER UPDATE")
        # data to write
        self.reg.write_data = self.alu.ry
        # update register. This only writes if self.reg.mem_write was set to True
        self.reg.register_update()
        print("\n")
    
    # execute one substep
    def substep(self):
        # uses a modulo 5 counter
        if self.substep_counter == 0:
            self.fetch()
        elif self.substep_counter == 1:
            self.decode()
        elif self.substep_counter == 2:
            self.execute()
        elif self.substep_counter == 3:
            self.memory_access()
        elif self.substep_counter == 4:
            self.register_update()
        # update counter
        self.substep_counter += 1
        self.substep_counter %= 5

    # process one instruction, or if part of it is processed finish processing
    def step(self):
        if self.IR == TERMINATION_CODE:
            return
        # one instruction involves all 5 substeps
        for _ in range(5):
            self.substep()
            # break if instruction finished early (some steps already executed)
            if self.substep_counter == 0:
                break

    # load a .mc file
    def load(self, file):
        self.file = file
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
    
    # dump memory to file
    def dump(self):
        with open(self.file[:-3]+'_out.mc', 'w') as file:
            word = 0
            addr = 0
            while word != TERMINATION_CODE:
                word = self.pmi.memory.getWordAtAddress(addr)
                file.write(f"0x{addr:X} 0x{word:08X}\n")
                addr += 4
            
            for k, v in self.pmi.memory.byteData.items():
                if k <= addr:
                    continue
                file.write(f"0x{k:X} 0x{v:X}\n")

    # run the entire program
    def run(self):
        while (True):
            self.step()
            if self.IR == TERMINATION_CODE or self.IR == 0:
                break
