import ALU, IAG, memory, register
from buffer import buffer

TERMINATION_CODE = 0xFFFFFFFF
class Control:
    def __init__(self):
        # instance of all modules
        self.iag = IAG.IAG(0)
        self.alu = ALU.ALU()
        self.pmi = memory.ProcessorMemoryInterface(4)
        self.i_pmi = memory.ProcessorMemoryInterface(4) # instruction memory
        self.reg = register.register_module()

        # fields and some controls
        self.IR = 0
        self.PC_Temp = 0

        self.buffers = [buffer(), buffer(), buffer(), buffer()]
        self.stages = []

        # modulo 5 clock for substeps
        self.clock = 0

        # input file
        self.file = ""

    # reset control to initial values
    def reset(self):
        self.iag = IAG.IAG(0)
        self.alu = ALU.ALU()
        self.pmi = memory.ProcessorMemoryInterface(4)
        self.i_pmi = memory.ProcessorMemoryInterface(4)
        self.reg = register.register_module()
        self.buffers = [buffer(), buffer(), buffer(), buffer()]
        self.stages = [1]

        # global variables
        self.IR = 0
        self.PC_Temp = 0
        self.clock = 0

    # fetch step
    def fetch(self):
        print("FETCH")
        # read memory
        self.i_pmi.mem_read = True
        # read a word
        self.i_pmi.dataType = 2
        # set MAR to PC
        self.i_pmi.update(self.alu.rz, self.iag.PC, self.alu.rm, 1)
        # get instruction corresponding to PC
        self.IR = self.i_pmi.getMDR()
        print(f"\tIR: 0x{self.IR:08x}")
        self.PC_Temp = self.iag.PC
        self.iag.PC += 4

    def decode(self):
        # extract common fields. Not all of these are applicable to all instructions
        # but are extracted nonetheless, and used where necessary
        self.buffers[0].opcode = ((1<<7) - 1) & self.buffers[0].IR
        self.buffers[0].rd = (((1<<12) - (1<<7)) & self.buffers[0].IR)>>7
        self.buffers[0].funct3 = (((1<<15) - (1<<12)) & self.buffers[0].IR)>>12
        self.buffers[0].rs1 = (((1<<20) - (1<<15)) & self.buffers[0].IR)>>15
        self.buffers[0].rs2 = (((1<<25) - (1<<20)) & self.buffers[0].IR)>>20
        self.buffers[0].funct7 = (((1<<32) - (1<<25)) & self.buffers[0].IR)>>25
        print("DECODE")
        print(f"\tOpcode: 0b{self.buffers[0].opcode:07b}")
        print(f"\trd: 0b{self.buffers[0].rd:05b}")
        print(f"\tfunct3: 0b{self.buffers[0].funct3:03b}")
        print(f"\trs1: 0b{self.buffers[0].rs1:05b}")
        print(f"\trs2: 0b{self.buffers[0].rs2:05b}")
        print(f"\tfunct7: 0b{self.buffers[0].funct7:07b}")

        # defaults
        self.buffers[0].mem_read = False
        self.buffers[0].mem_write = False
        
        if self.buffers[0].opcode == 0b0110011: # R format
            print("\tR format detected")
            self.buffers[0].imm = 0         # immediate unnecessary
            self.buffers[0].muxA = 0    # use rs1
            self.buffers[0].muxB = 0    # use rs2
            self.buffers[0].aluOp = 2   # determine operation with funct3 and funct7
            self.buffers[0].muxY = 0    # output is output of ALU
            self.buffers[0].branch = 0      # don't branch
            self.buffers[0].jump = 0        # don't jump
            self.buffers[0].reg_write = True    # write to register
        elif self.buffers[0].opcode in [0b0010011, 0b0000011, 0b1100111]: # I format
            print("\tI format detected")
            self.buffers[0].imm = (((1<<32) - (1<<20)) & self.buffers[0].IR) >> 20 
            if (self.buffers[0].imm>>11)&1 == 1:            # check if sign bit is 1
                self.buffers[0].imm = -((self.buffers[0].imm ^ ((1<<12)-1)) + 1)
            print(f"\timmediate: {self.buffers[0].imm:03x}")
            self.buffers[0].muxA = 0            # op1 is rs1
            self.buffers[0].muxB = 1            # op2 is imm
            self.buffers[0].reg_write = True    # write to register
            self.buffers[0].jump = 0                # don't jump
            self.buffers[0].branch = 0              # don't branch
            if self.buffers[0].opcode == 0b0010011: # arithmetic I format
                self.buffers[0].aluOp = 2       # determine operation with funct3 and funct7
                self.buffers[0].muxY = 0        # output is output of ALU
            else:                   # load or jalr
                self.buffers[0].aluOp = 0       # add
                if self.buffers[0].opcode == 0b0000011:     # load
                    self.buffers[0].muxY = 1    # output is MDR
                    self.buffers[0].dataType = self.buffers[0].funct3   # datatype to read
                    self.buffers[0].mem_read = True     # read memory
                else:                       # jalr
                    self.buffers[0].branch = 1              # branch
                    self.buffers[0].jump = 1                # and jump
                    self.buffers[0].muxY = 2            # output is return address
        elif self.buffers[0].opcode == 0b0100011: # S format
            print("\tS format detected")
            self.buffers[0].imm = ((((1<<32) - (1<<25)) & self.buffers[0].IR) >> 20) + ((((1<<12)-(1<<7)) & self.buffers[0].IR)>>7)
            if (self.buffers[0].imm>>11)&1 == 1:            # check if sign bit is 1
                self.buffers[0].imm = -((self.buffers[0].imm^((1<<12)-1)) + 1)
            print(f"\timmediate: {self.buffers[0].imm:03x}")
            self.buffers[0].muxA = 0            # op1 is rs1
            self.buffers[0].muxB = 1            # op2 is imm
            self.buffers[0].aluOp = 0           # add
            self.buffers[0].muxY = 0           # output is irrelevant
            self.buffers[0].mem_write = True    # write to memory
            self.buffers[0].dataType = self.buffers[0].funct3   # datatype to write
            self.buffers[0].branch = 0              # don't branch
            self.buffers[0].jump = 0                # don't jump
        elif self.buffers[0].opcode == 0b1100011: # SB format
            print("\tSB format detected")
            self.buffers[0].imm = (((1<<31) & self.buffers[0].IR) >> 19) + (((1<<7) & self.buffers[0].IR) << 4) + ((((1<<31) - (1<<25)) & self.buffers[0].IR)>>20) + ((((1<<12) - (1<<8))&self.buffers[0].IR)>>7)
            if (self.buffers[0].imm>>12)&1 == 1:            # check if sign bit is 1
                self.buffers[0].imm = -((self.buffers[0].imm^((1<<13)-1)) + 1)
            print(f"\timmediate: {self.buffers[0].imm:04x}")
            self.buffers[0].muxA = 0            # op1 is rs1
            self.buffers[0].muxB = 0            # op2 is rs2
            self.buffers[0].aluOp = 1           # determine branch operation by funct3
            self.buffers[0].muxY = 0           # irrelevant output
            self.buffers[0].branch = 1              # branch
            self.buffers[0].jump = 0                # don't jump
            
            
            # for SB format (branch instructions) comparison operation of execute stage is done in decode stage itself
            self.reg.rs1 = self.buffers[0].rs1
            self.reg.rs2 = self.buffers[0].rs2
            self.reg.read_register()            
            self.buffers[0].rs1_data = self.reg.read_data_1
            self.buffers[0].rs2_data = self.reg.read_data_2
            
            signed_rs1 = self.buffers[0].rs1_data
            if (signed_rs1>>31)&1 == 1:
                signed_rs1 = -((signed_rs1^((1<<32)-1)) + 1)
            signed_rs2 = self.buffers[0].rs2_data
            if (signed_rs2>>31)&1 == 1:
                signed_rs2 = -((signed_rs2^((1<<32)-1)) + 1)
        
            op1 = signed_rs1
            op2 = signed_rs2
            
            if self.buffers[0].funct3&4 == 0:   # beq or bne                        
                self.buffers[0].rz = op1 - op2
                self.buffers[0].inv_zero = self.buffers[0].funct3&1 # invert zero if bne
                self.buffers[0].zero = self.buffers[0].rz == 0         
                
                if self.buffers[0].inv_zero:
                    self.buffers[0].zero = not(self.buffers[0].zero)
                    
            else:             # blt or bge
                self.buffers[0].rz =int(op1 < op2)
                self.buffers[0].inv_zero = 1-self.buffers[0].funct3&1   # invert zero if blt
                self.buffers[0].zero = self.buffers[0].rz == 0
                
                if self.buffers[0].inv_zero:
                    self.buffers[0].zero = not(self.buffers[0].zero)
            self.iag.PCSrc = self.buffers[0].zero & self.buffers[0].branch | ((self.buffers[0].branch & self.buffers[0].jump)<<1)
            # Update PC. This is done here since its value no longer depends on output of ALU
            self.iag.update(self.buffers[0].imm, self.buffers[0].rz)
            
            
        elif self.buffers[0].opcode in [0b0110111, 0b0010111]:    # U format
            print("\tU format detected")
            self.buffers[0].imm = ((1<<32) - (1<<12)) & self.buffers[0].IR
            print(f"\timmediate: {self.buffers[0].imm:05x}")
            if self.buffers[0].opcode == 0b0010111: # if auipc
                self.buffers[0].muxA = 1        # op1 is PC
            else:                   # if lui
                self.buffers[0].muxA = 0        # op1 is rs1
            self.buffers[0].muxB = 1            # op2 is rs2
            self.buffers[0].aluOp = 0           # add
            self.buffers[0].reg_write = True    # write to register
            self.buffers[0].muxY = 0            # output is ALU
            self.buffers[0].branch = 0              # don't branch
            self.buffers[0].jump = 0                # don't jump
        elif self.buffers[0].opcode == 0b1101111:   # UJ format
            print("\tUJ format detected")
            self.buffers[0].imm = (((1<<31) & self.buffers[0].IR)>>11) + (((1<<20) - (1<<12)) & self.buffers[0].IR) + (((1<<20) & self.buffers[0].IR)>>9) + ((((1<<31) - (1<<21)) & self.buffers[0].IR)>>20)
            if (self.buffers[0].imm>>20)&1 == 1:            # check if sign bit is 1
                self.buffers[0].imm = -((self.buffers[0].imm^((1<<21)-1)) + 1)
            print(f"\timmediate: {self.buffers[0].imm:06x}")
            self.buffers[0].muxA = 0            # op1 is rs1
            self.buffers[0].muxB = 0            # op2 is rs2
            self.buffers[0].reg_write = True    # write to register
            self.buffers[0].aluOp = 3          # no operation
            self.buffers[0].muxY = 2            # output is return address
            self.buffers[0].branch = 1              # branch
            self.buffers[0].jump = 0                # don't jump
        
        print(f"\talu.muxA: 0b{self.buffers[0].muxA}")
        print(f"\talu.muxB: 0b{self.buffers[0].muxB}")
        print(f"\talu.aluOp: 0b{self.buffers[0].aluOp}")
        print(f"\talu.muxY: 0b{self.buffers[0].muxY}")
        print(f"\tbranch: 0b{self.buffers[0].branch}")
        print(f"\tjump: 0b{self.buffers[0].jump}")
        print(f"\treg_write: {self.buffers[0].reg_write}")
        print(f"\tmem_read: {self.buffers[0].mem_read}")
        print(f"\tmem_write: {self.buffers[0].mem_write}")

    def execute(self):
        print("EXECUTE")
        self.reg.rs1 = self.buffers[1].rs1
        self.reg.rs2 = self.buffers[1].rs2
        self.reg.read_register()
        # execute any ALU operation
        self.alu.muxA = self.buffers[1].muxA
        self.alu.muxB = self.buffers[1].muxB
        self.alu.aluOp = self.buffers[1].aluOp
        self.alu.execute(self.reg.read_data_1, self.reg.read_data_2, self.buffers[1].imm, self.buffers[1].funct3, self.buffers[1].funct7, self.buffers[1].PC_Temp)
        self.buffers[1].zero = self.alu.zero
        self.buffers[1].rm = self.alu.rm
        self.buffers[1].rz = self.alu.rz

    def memory_access(self):
        print("MEMORY ACCESS")
        self.pmi.mem_read = self.buffers[2].mem_read
        self.pmi.mem_write = self.buffers[2].mem_write
        self.pmi.dataType = self.buffers[2].dataType
        # access memory
        self.pmi.update(self.buffers[2].rz, self.buffers[2].PC_Temp, self.buffers[2].rm, 0)
        # this runs muxY and processes final output that goes to register file
        self.alu.process_output(self.pmi.getMDR(), self.buffers[2].PC_Temp+4)
        self.buffers[2].ry = self.alu.ry
        # branch control bits for IAG. If LSB is 1, it's a branch instruction. MSB is only 1 for jalr
        self.iag.PCSrc = self.buffers[2].zero & self.buffers[2].branch | ((self.buffers[2].branch & self.buffers[2].jump)<<1)
        # Update PC. This is done here since its value depends on output of ALU
        self.iag.update(self.buffers[2].imm, self.buffers[2].rz)

    # writeback stage
    def register_update(self):
        print("REGISTER UPDATE")
        # data to write
        self.reg.write_data = self.buffers[3].ry
        self.reg.reg_write = self.buffers[3].reg_write
        # update register. This only writes if self.reg.reg_write was set to True
        self.reg.register_update()
        print("\n")
    
    # execute one substep
    def substep(self):
        if 1 in self.stages:
            self.fetch()
        if 2 in self.stages:
            self.decode()
        if 3 in self.stages:
            self.execute()
        if 4 in self.stages:
            self.memory_access()
        if 5 in self.stages:
            self.register_update()
        
        self.buffers = [buffer()] + self.buffers[:-1]
        self.buffers[0].IR = self.IR
        self.buffers[0].PC_Temp = self.PC_Temp

        self.stages = [1] + [x+1 for x in self.stages]
        # update counter
        self.clock += 1

    # process one instruction, or if part of it is processed finish processing
    def step(self):
        if self.IR == TERMINATION_CODE:
            return
        # one instruction involves all 5 substeps
        for _ in range(5):
            self.substep()
            # break if instruction finished early (some steps already executed)
            if self.clock == 0:
                break

    # load a .mc file
    def load(self, file):
        self.file = file
        with open(file, 'r') as infile:
                text = True
                for line in infile:
                    mloc, instr = [int(x, 16) for x in line.split()]
                    if text:
                        self.i_pmi.memory.setWordAtAddress(mloc, instr)
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
