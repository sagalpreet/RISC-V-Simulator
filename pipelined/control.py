from pipelined import ALU, IAG, memory, register
from pipelined.buffer import buffer
from copy import deepcopy

TERMINATION_CODE = 0xFFFFFFFF


class Control:
    def __init__(self, numSets, numBlocksPerSet, blockSize):
        # instance of all modules
        self.numSets = numSets
        self.numBlocksPerSet = numBlocksPerSet
        self.blockSize = blockSize
        self.iag = IAG.IAG(0)
        self.alu = ALU.ALU()
        self.pmi = memory.ProcessorMemoryInterface(4, self.numSets, self.numBlocksPerSet, self.blockSize, "D$")
        self.i_pmi = memory.ProcessorMemoryInterface(4, self.numSets, self.numBlocksPerSet, self.blockSize, "I$")  # instruction memory
        self.reg = register.register_module()
        # fields and some controls
        self.IR = 0
        self.PC_Temp = 0

        self.buffers = [buffer(), buffer(), buffer(), buffer()]
        self.stall = False
        self.flush = False
        self.forwarding = False
        self.print_registers = False
        self.stages = []

        # modulo 5 clock for substeps
        self.clock = 0

        # input file
        self.file = ""
        
        # stats to be printed        
        # incremented when removing 5 from the stage list
        self.num_instructions_executed = 0           
        
        # updated when removing 5 from the stage list
        self.CPI = 0                                 
        
        # incremented in decode stage when store or load instruction found and self.stall is false
        self.num_instructions_data_transfer = 0     
        
        # incremented in decode stage when R or ALU type I instruction found and self.stall is false
        self.num_instructions_alu = 0               
        
        # incremented in decode stage when SB, UJ or jalr instruction found and self.stall is false
        self.num_instructions_control = 0
        
        # incremented at the end of decode if self.stall is set to true
        self.num_stalls = 0
        
        # incremented in hazard_detection when self.stall is set to true for the last time for a given instruction
        self.num_data_hazards = 0
        
        # incremented in decode when SB instruction and self.stall is false
        self.num_control_hazards = 0
        
        # incremented in decode stage when self.flush is true
        self.num_branch_misprediction = 0
        
        # incremented in hazard_detection whenever self.stall is set to true since currently stalls are introduced due to data hazards (not sure) 
        self.num_stalls_data_hazards = 0
        
        # incremented in decode stage when self.flush is true
        self.num_stalls_control_hazards = 0

    # reset control to initial values
    def reset(self):
        self.iag = IAG.IAG(0)
        self.alu = ALU.ALU()
        self.pmi = memory.ProcessorMemoryInterface(4, self.numSets, self.numBlocksPerSet, self.blockSize, "D$")
        self.i_pmi = memory.ProcessorMemoryInterface(4, self.numSets, self.numBlocksPerSet, self.blockSize, "I$")  # instruction memory
        self.reg = register.register_module()
        self.buffers = [buffer(), buffer(), buffer(), buffer()]
        self.stages = [1]
        self.stall = False
        self.flush = False

        # global variables
        self.IR = 0
        self.PC_Temp = 0
        self.clock = 0
        
        # stats to be printed        
        # incremented when removing 5 from the stage list
        self.num_instructions_executed = 0           
        
        # updated when removing 5 from the stage list
        self.CPI = 0                                 
        
        # incremented in decode stage when store or load instruction found and self.stall is false
        self.num_instructions_data_transfer = 0     
        
        # incremented in decode stage when R or ALU type I instruction found and self.stall is false
        self.num_instructions_alu = 0               
        
        # incremented in decode stage when SB, UJ or jalr instruction found and self.stall is false
        self.num_instructions_control = 0
        
        # incremented at the end of decode if self.stall is set to true
        self.num_stalls = 0
        
        # incremented in hazard_detection when self.stall is set to true for the last time for a given instruction
        self.num_data_hazards = 0
        
        # incremented in decode when SB instruction and self.stall is false
        self.num_control_hazards = 0
        
        # incremented in decode stage when self.flush is true
        self.num_branch_misprediction = 0
        
        # incremented in hazard_detection whenever self.stall is set to true since currently stalls are introduced due to data hazards (not sure) 
        self.num_stalls_data_hazards = 0
        
        # incremented in decode stage when self.flush is true
        self.num_stalls_control_hazards = 0
        

    # fetch step
    def fetch(self):
        print("FETCH")
        # read memory
        self.i_pmi.mem_read = True
        # read a word
        self.i_pmi.dataType = 2
        # set MAR to PC
        self.i_pmi.update(self.iag.PC, 0)
        # get instruction corresponding to PC
        self.IR = self.i_pmi.getMDR()
        print(f"\tIR: 0x{self.IR:08x}")

        self.PC_Temp = self.iag.PC
        self.iag.PC += 4

    def decode(self):
        # extract common fields. Not all of these are applicable to all instructions
        # but are extracted nonetheless, and used where necessary
        self.buffers[0].opcode = ((1 << 7) - 1) & self.buffers[0].IR
        self.buffers[0].rd = (((1 << 12) - (1 << 7)) & self.buffers[0].IR) >> 7
        self.buffers[0].funct3 = (((1 << 15) -
                                   (1 << 12)) & self.buffers[0].IR) >> 12
        self.buffers[0].rs1 = (((1 << 20) -
                                (1 << 15)) & self.buffers[0].IR) >> 15
        self.buffers[0].rs2 = (((1 << 25) -
                                (1 << 20)) & self.buffers[0].IR) >> 20
        self.buffers[0].funct7 = (((1 << 32) -
                                   (1 << 25)) & self.buffers[0].IR) >> 25
        self.buffers[0].numStalls = 0
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
        self.buffers[0].muxMDR = 0
        self.buffers[0].muxRM = 0
        self.buffers[0].muxDA = 0
        self.buffers[0].muxDB = 0

        if self.buffers[0].opcode == 0b0110011:  # R format
            print("\tR format detected")
            self.buffers[0].type = 'R'
            self.buffers[0].imm = 0  # immediate unnecessary
            self.buffers[0].muxA = 0  # use rs1
            self.buffers[0].muxB = 0  # use rs2
            self.buffers[0].aluOp = 2  # determine operation with funct3 and funct7
            self.buffers[0].muxY = 0  # output is output of ALU
            self.buffers[0].branch = 0  # don't branch
            self.buffers[0].jump = 0  # don't jump
            self.buffers[0].reg_write = True  # write to register
            self.detect_data_hazards()
            ###### stats ######
            if not self.stall:
                self.num_instructions_alu += 1
            ###### stats ######
            
        elif self.buffers[0].opcode in [0b0010011, 0b0000011, 0b1100111]:  # I format
            print("\tI format detected")
            self.buffers[0].type = 'I'
            self.buffers[0].imm = (((1 << 32) - (1 << 20)) & self.buffers[0].IR) >> 20
            if (self.buffers[0].imm >> 11) & 1 == 1:  # check if sign bit is 1
                self.buffers[0].imm -= (1<<12)
            print(f"\timmediate: {self.buffers[0].imm:03x}")
            self.buffers[0].muxA = 0  # op1 is rs1
            self.buffers[0].muxB = 1  # op2 is imm
            self.buffers[0].reg_write = True  # write to register
            self.buffers[0].jump = 0  # don't jump
            self.buffers[0].branch = 0  # don't branch
            if self.buffers[0].opcode == 0b0010011:  # arithmetic I format
                self.buffers[0].aluOp = 2  # determine operation with funct3 and funct7
                self.buffers[0].muxY = 0  # output is output of ALU
            else:  # load or jalr
                self.buffers[0].aluOp = 0  # add
                if self.buffers[0].opcode == 0b0000011:  # load
                    self.buffers[0].type = 'L'
                    self.buffers[0].muxY = 1  # output is MDR
                    self.buffers[0].dataType = self.buffers[0].funct3  # datatype to read
                    self.buffers[0].muxMDR = 0  # use rm, irrelevant but necessary
                    self.buffers[0].mem_read = True  # read memory
                else:  # jalr
                    self.buffers[0].branch = 1  # branch
                    self.buffers[0].jump = 1  # and jump
                    self.buffers[0].muxY = 2  # output is return address
                    self.buffers[0].muxDA = 0  # use rs1
            self.detect_data_hazards()
            
            ###### stats ######
            if (not self.stall) and (self.buffers[0].opcode == 0b0010011): # arithmetic I format
                self.num_instructions_alu += 1
            elif (not self.stall) and (self.buffers[0].opcode == 0b0000011): #load
                self.num_instructions_data_transfer += 1
            elif (not self.stall) and (self.buffers[0].opcode == 0b1100111): #jalr
                self.num_instructions_control += 1
            ###### stats ######
        
        elif self.buffers[0].opcode == 0b0100011:  # S format
            print("\tS format detected")
            self.buffers[0].type = 'S'
            self.buffers[0].imm = ((((1 << 32) - (1 << 25)) & self.buffers[0].IR) >> 20) + ((((1 << 12) - (1 << 7)) & self.buffers[0].IR) >> 7)
            if (self.buffers[0].imm >> 11) & 1 == 1:  # check if sign bit is 1
                self.buffers[0].imm -= (1<<12)
            print(f"\timmediate: {self.buffers[0].imm:03x}")
            self.buffers[0].muxA = 0  # op1 is rs1
            self.buffers[0].muxB = 1  # op2 is imm
            self.buffers[0].aluOp = 0  # add
            self.buffers[0].muxY = 0  # output is irrelevant
            self.buffers[0].mem_write = True  # write to memory
            self.buffers[0].dataType = self.buffers[0].funct3  # datatype to write
            self.buffers[0].muxMDR = 0  # use rm
            self.buffers[0].branch = 0  # don't branch
            self.buffers[0].jump = 0  # don't jump
            self.detect_data_hazards()
            
            ###### stats ######
            if (not self.stall): # store instruction
                self.num_instructions_data_transfer += 1
            ###### stats ######

        elif self.buffers[0].opcode == 0b1100011:  # SB format
            print("\tSB format detected")
            self.buffers[0].type = 'SB'
            self.buffers[0].imm = (((1 << 31) & self.buffers[0].IR) >> 19) + ((
                (1 << 7) & self.buffers[0].IR) << 4) + (((
                    (1 << 31) - (1 << 25)) & self.buffers[0].IR) >> 20) + (((
                        (1 << 12) - (1 << 8)) & self.buffers[0].IR) >> 7)
            if ((self.buffers[0].imm >> 12) & 1) == 1:  # check if sign bit is 1
                self.buffers[0].imm -= 1<<13
            print(f"\timmediate: {self.buffers[0].imm:04x}")
            self.buffers[0].muxA = 0  # op1 is rs1
            self.buffers[0].muxB = 0  # op2 is rs2
            self.buffers[0].aluOp = 1  # determine branch operation by funct3
            self.buffers[0].muxY = 0  # irrelevant output
            self.buffers[0].branch = 1  # branch
            self.buffers[0].jump = 0  # don't jump
            self.buffers[0].muxDA = 0  # use rs1
            self.buffers[0].muxDB = 0  # use rs2
            self.detect_data_hazards()
            
            ###### stats ######
            if (not self.stall): # branch instructions
                self.num_instructions_control += 1
                self.num_control_hazards += 1
            ###### stats ######

        elif self.buffers[0].opcode in [0b0110111, 0b0010111]:  # U format
            print("\tU format detected")
            self.buffers[0].type = 'U'
            self.buffers[0].imm = ((1 << 32) - (1 << 12)) & self.buffers[0].IR
            print(f"\timmediate: 0x{self.buffers[0].imm:05x}")
            if self.buffers[0].opcode == 0b0010111:  # if auipc
                self.buffers[0].muxA = 1  # op1 is PC
                self.buffers[0].aluOp = 0  # add
            else:  # if lui
                self.buffers[0].muxA = 0  # op1 is rs1
                self.buffers[0].aluOp = 1   # lui
                print("\tCopying rs1 to rd for lui")
                self.buffers[0].rs1 = self.buffers[0].rd
            
            self.buffers[0].muxB = 1  # op2 is rs2
            self.buffers[0].reg_write = True  # write to register
            self.buffers[0].muxY = 0  # output is ALU
            self.buffers[0].branch = 0  # don't branch
            self.buffers[0].jump = 0  # don't jump
            self.detect_data_hazards()
            
            ###### stats ######
            # it has to be decided if auipc and lui are alu instructions or not
            ###### stats ######
            

        elif self.buffers[0].opcode == 0b1101111:  # UJ format
            print("\tUJ format detected")
            self.buffers[0].type = 'UJ'
            self.buffers[0].imm = (((1 << 31) & self.buffers[0].IR) >> 11) + ((
                (1 << 20) - (1 << 12)) & self.buffers[0].IR) + ((
                    (1 << 20) & self.buffers[0].IR) >> 9) + (((
                        (1 << 31) - (1 << 21)) & self.buffers[0].IR) >> 20)
            if (self.buffers[0].imm >> 20) & 1 == 1:  # check if sign bit is 1
                self.buffers[0].imm -= 1<<21
            print(f"\timmediate: {self.buffers[0].imm:06x}")
            self.buffers[0].muxA = 0  # op1 is rs1
            self.buffers[0].muxB = 0  # op2 is rs2
            self.buffers[0].reg_write = True  # write to register
            self.buffers[0].aluOp = 3  # no operation
            self.buffers[0].muxY = 2  # output is return address
            self.buffers[0].branch = 1  # branch
            self.buffers[0].jump = 0  # don't jump
            self.buffers[0].flush = True
            self.detect_data_hazards()
            
            ###### stats ######
            if (not self.stall): # jal instruction
                self.num_instructions_control += 1
            ###### stats ######
        else:
            return
        
        if not self.stall and self.buffers[0].type == 'SB':
            self.reg.rs1 = self.buffers[0].rs1
            self.reg.rs2 = self.buffers[0].rs2
            self.reg.read_register()
            self.buffers[0].rs1_data = self.reg.read_data_1
            self.buffers[0].rs2_data = self.reg.read_data_2

            # for SB format (branch instructions) comparison operation of execute stage is done in decode stage itself
            signed_rs1 = self.buffers[0].rs1_data
            if (signed_rs1 >> 31) & 1 == 1:
                signed_rs1 -= (1 << 32)
            signed_rs2 = self.buffers[0].rs2_data
            if (signed_rs2 >> 31) & 1 == 1:
                signed_rs2 -= (1 << 32)

            op1 = [signed_rs1, self.buffers[1].rz, self.buffers[2].ry][self.buffers[0].muxDA]
            op2 = [signed_rs2, self.buffers[1].rz, self.buffers[2].ry][self.buffers[0].muxDB]

            if (self.buffers[0].funct3&4) == 0:  # beq or bne
                self.buffers[0].rz = op1 - op2
                self.buffers[0].zero = int(self.buffers[0].rz == 0)
                if (self.buffers[0].funct3&1) == 1:
                    self.buffers[0].zero = 1-self.buffers[0].zero
            else:  # blt or bge
                self.buffers[0].rz = int(op1 < op2)
                self.buffers[0].zero = int(self.buffers[0].rz == 0)
                if (self.buffers[0].funct3&1) == 0:
                    self.buffers[0].zero = 1 - self.buffers[0].zero
            
        elif not self.stall and self.buffers[0].type == 'I' and self.buffers[0].branch == 1:   # jalr
            self.reg.rs1 = self.buffers[0].rs1
            self.reg.read_register()
            self.buffers[0].rs1_data = self.reg.read_data_1
            signed_rs1 = self.buffers[0].rs1_data
            if (signed_rs1 >> 31) & 1 == 1:
                signed_rs1 -= (1 << 32)
            
            op1 = [signed_rs1, self.buffers[1].rz, self.buffers[2].ry][self.buffers[0].muxDA]

            self.buffers[0].rz = signed_rs1 + self.buffers[0].imm
            self.buffers[0].zero = 0

        else:
            self.buffers[0].zero = self.buffers[0].branch
    
        if not self.stall:
            self.iag.PCSrc = self.buffers[0].zero & self.buffers[0].branch | ((self.buffers[0].branch & self.buffers[0].jump) << 1)
            # Update PC. This is done here since its value no longer depends on output of ALU
            self.flush = self.iag.update(self.buffers[0].imm + self.buffers[0].PC_Temp, self.buffers[0].rz)
            
        ###### stats ######
        #if (not self.stall):
            #self.num_instructions_executed += 1
            #self.num_instructions_executed should be incremented when the 5th stage has been completed for an instruction 
        if self.stall:
            self.num_stalls += 1
        if self.flush:
            self.num_stalls_control_hazards += 1
            self.num_branch_misprediction += 1            
        ###### stats ######

        print(f"\talu.muxA: 0b{self.buffers[0].muxA}")
        print(f"\talu.muxB: 0b{self.buffers[0].muxB}")
        print(f"\talu.aluOp: 0b{self.buffers[0].aluOp}")
        print(f"\talu.muxY: 0b{self.buffers[0].muxY}")
        print(f"\tbranch: 0b{self.buffers[0].branch}")
        print(f"\tjump: 0b{self.buffers[0].jump}")
        print(f"\treg_write: {self.buffers[0].reg_write}")
        print(f"\tmem_read: {self.buffers[0].mem_read}")
        print(f"\tmem_write: {self.buffers[0].mem_write}")

    def detect_data_hazards(self):
        # M to D
        # E to D
        if self.buffers[0].type == 'SB':
            # M to D, but in next cycle
            if self.buffers[1].type == 'L' and self.buffers[1].rd != 0 and self.buffers[1].rd in [self.buffers[0].rs1, self.buffers[0].rs2]:
                self.stall = True
                ###### stats ######
                self.num_stalls_data_hazards += 1
                ###### stats ######
                return
            # E to D
            if self.buffers[1].type in ['R', 'I', 'U', 'UJ'] and self.buffers[1].rd != 0 and self.buffers[1].rd in [self.buffers[0].rs1, self.buffers[0].rs2]:
                if self.forwarding:
                    if self.buffers[1].rd == self.buffers[0].rs1:
                        print("\tForwarding E to D (rs1)")
                        self.buffers[0].muxDA = 1
                    if self.buffers[1].rd == self.buffers[0].rs2:
                        print("\tForwarding E to D (rs2)")
                        self.buffers[0].muxDA = 1
                else:
                    self.stall = True
                    ###### stats ######
                    self.num_stalls_data_hazards += 1
                    self.num_data_hazards += 1
                    ###### stats ######
                    return
            # M to D in this cycle
            if self.buffers[2].type not in ['SB', 'S'] and self.buffers[2].rd != 0 and self.buffers[2].rd in [self.buffers[0].rs1, self.buffers[0].rs2]:
                if self.forwarding:
                    if self.buffers[2].rd == self.buffers[0].rs1:
                        print("\tForwarding M to D (rs1)")
                        self.buffers[0].muxDA = 2
                    if self.buffers[2].rd == self.buffers[0].rs2:
                        print("\tForwarding M to D (rs2)")
                        self.buffers[0].muxDB = 2
                else:
                    self.stall = True
                    ###### stats ######
                    self.num_stalls_data_hazards += 1
                    self.num_data_hazards += 1
                    ###### stats ######
            return

        # jalr
        if self.buffers[0].type == 'I' and self.buffers[0].branch == 1:
            # M to D, but in next cycle
            if self.buffers[1].type == 'L' and self.buffers[1].rd != 0 and self.buffers[1].rd == self.buffers[0].rs1:
                self.stall = True
                ###### stats ######
                self.num_stalls_data_hazards += 1
                ###### stats ######
                return
            # E to D
            if self.buffers[1].type in ['R', 'I', 'U', 'UJ'] and self.buffers[1].rd != 0 and self.buffers[1].rd == self.buffers[0].rs1:
                if self.forwarding:
                    print("\tForwarding E to D (rs1)")
                    self.buffers[0].muxDA = 1
                else:
                    self.stall = True
                    ###### stats ######
                    self.num_stalls_data_hazards += 1
                    self.num_data_hazards += 1
                    ###### stats ######
                    return
            # M to D in this cycle
            if self.buffers[2].type not in ['SB', 'S'] and self.buffers[2].rd != 0 and self.buffers[2].rd == self.buffers[0].rs1:
                if self.forwarding:
                    print("\tForwarding M to D (rs1)")
                    self.buffers[0].muxDA = 2
                else:
                    self.stall = True
                    ###### stats ######
                    self.num_stalls_data_hazards += 1
                    self.num_data_hazards += 1
                    ###### stats ######
            return

        # M to E
        # E to E
        if self.buffers[0].type == 'R':
            # M to E
            if self.buffers[1].type == 'L' and self.buffers[1].rd != 0 and self.buffers[1].rd in [self.buffers[0].rs1, self.buffers[0].rs2]:
                if self.forwarding:
                    if self.buffers[1].rd == self.buffers[0].rs1:
                        print("\tForwarding M to E (rs1)")
                        self.buffers[0].muxA = 3
                    if self.buffers[1].rd == self.buffers[0].rs2:
                        print("\tForwarding M to E (rs2)")
                        self.buffers[0].muxB = 3
                else:
                    self.stall = True
                    ###### stats ######
                    self.num_stalls_data_hazards += 1
                    self.num_data_hazards += 1
                    ###### stats ######
                    return
            # E to E
            if self.buffers[1].type in ['R', 'I', 'U'] and self.buffers[1].rd != 0 and self.buffers[1].rd in [self.buffers[0].rs1, self.buffers[0].rs2]:
                if self.forwarding:
                    if self.buffers[1].rd == self.buffers[0].rs1:
                        print("\tForwarding E to E (rs1)")
                        self.buffers[0].muxA = 2
                    if self.buffers[1].rd == self.buffers[0].rs2:
                        print("\tForwarding E to E (rs2)")
                        self.buffers[0].muxB = 2
                else:
                    self.stall = True
                    ###### stats ######
                    self.num_stalls_data_hazards += 1
                    self.num_data_hazards += 1
                    ###### stats ######
                    return
            
            # M to E (because UJ writes to ry)
            if self.buffers[1].type == 'UJ' and self.buffers[1].rd != 0 and self.buffers[1].rd in [self.buffers[0].rs1, self.buffers[0].rs2]:
                if self.forwarding:
                    if self.buffers[1].rd == self.buffers[0].rs1:
                        print("\tForwarding M to E (rs1)")
                        self.buffers[0].muxA = 3
                    if self.buffers[1].rd == self.buffers[0].rs2:
                        print("\tForwarding M to E (rs2)")
                        self.buffers[0].muxB = 3
                else:
                    self.stall = True
                    ###### stats ######
                    self.num_stalls_data_hazards += 1
                    self.num_data_hazards += 1
                    ###### stats ######
            return

        if self.buffers[0].type == 'I' and self.buffers[0].branch == 0 or self.buffers[0].type == 'L': # I format and not jalr
            # M to E
            if self.buffers[1].type == 'L' and self.buffers[1].rd != 0 and self.buffers[1].rd == self.buffers[0].rs1:
                if self.forwarding:
                    print("\tForwarding M to E (rs1)")
                    self.buffers[0].muxA = 3
                else:
                    self.stall = True
                    ###### stats ######
                    self.num_stalls_data_hazards += 1
                    self.num_data_hazards += 1
                    ###### stats ######
                    return
            # E to E
            if self.buffers[1].type in ['R', 'I', 'U'] and self.buffers[1].rd != 0 and self.buffers[1].rd == self.buffers[0].rs1:
                if self.forwarding:
                    print("\tForwarding E to E (rs1)")
                    self.buffers[0].muxA = 2
                else:
                    self.stall = True
                    ###### stats ######
                    self.num_stalls_data_hazards += 1
                    self.num_data_hazards += 1
                    ###### stats ######
                    return
    
            # M to E (because UJ writes to ry)
            if self.buffers[1].type == 'UJ' and self.buffers[1].rd != 0 and self.buffers[1].rd == self.buffers[0].rs1:
                if self.forwarding:
                    if self.buffers[1].rd == self.buffers[0].rs1:
                        print("\tForwarding M to E (rs1)")
                        self.buffers[0].muxA = 3
                else:
                    self.stall = True
                    ###### stats ######
                    self.num_stalls_data_hazards += 1
                    self.num_data_hazards += 1
                    ###### stats ######
            return

        # M to M
        if self.buffers[0].type == 'S':
            # M to M
            if self.buffers[1].type == 'L' and self.buffers[1].rd != 0 and self.buffers[1].rd == self.buffers[0].rs2:
                if self.forwarding:
                    print("\tForwarding M to M (rs2)")
                    self.buffers[0].muxMDR = 1
                    self.buffers[0].muxRM = 0
                else:
                    self.stall = True
                    ###### stats ######
                    self.num_stalls_data_hazards += 1
                    self.num_data_hazards += 1
                    ###### stats ######
                    return
            # M to E
            if self.buffers[1].type == 'L' and self.buffers[1].rd != 0 and self.buffers[1].rd == self.buffers[0].rs1:
                if self.forwarding:
                    print("\tForwarding M to E (rs1)")
                    self.buffers[0].muxA = 3
                else:
                    self.stall = True
                    ###### stats ######
                    self.num_stalls_data_hazards += 1
                    self.num_data_hazards += 1
                    ###### stats ######
                    return
            # E to E
            if self.buffers[1].type in ['R', 'I', 'U'] and self.buffers[1].rd != 0 and self.buffers[1].rd in [self.buffers[0].rs1, self.buffers[0].rs2]:
                if self.forwarding:
                    if self.buffers[1].rd == self.buffers[0].rs1:
                        print("\tForwarding E to E (rs1)")
                        self.buffers[0].muxA = 2
                    if self.buffers[1].rd == self.buffers[0].rs2:
                        print("\tForwarding E to E (rs2)")
                        self.buffers[0].muxRM = 1
                else:
                    self.stall = True
                    ###### stats ######
                    self.num_stalls_data_hazards += 1
                    self.num_data_hazards += 1
                    ###### stats ######
                    return
            
            # M to E|M (because UJ writes to ry)
            if self.buffers[1].type == 'UJ' and self.buffers[1].rd != 0 and self.buffers[1].rd in [self.buffers[0].rs1, self.buffers[0].rs2]:
                if self.forwarding:
                    if self.buffers[1].rd == self.buffers[0].rs1:
                        print("\tForwarding M to E (rs1)")
                        self.buffers[0].muxA = 3
                    if self.buffers[1].rd == self.buffers[0].rs2:
                        print("\tForwarding M to M (rs2)")
                        self.buffers[0].muxMDR = 1
                else:
                    self.stall = True
                    ###### stats ######
                    self.num_stalls_data_hazards += 1
                    self.num_data_hazards += 1
                    ###### stats ######
            return

        # lui
        if self.buffers[0].opcode == 0b0110111:
            # M to E
            if self.buffers[1].type in ['R', 'I', 'L', 'U', 'UJ'] and self.buffers[1].rd != 0 and self.buffers[1].rd == self.buffers[0].rd:
                if self.forwarding:
                    print("\tForwarding M to E (rd)")
                    self.buffers[0].muxA = 3
                else:
                    self.stall = True
                    ###### stats ######
                    self.num_stalls_data_hazards += 1
                    self.num_data_hazards += 1
                    ###### stats ######
                    return
    
    def execute(self):
        print("EXECUTE")
        self.reg.rs1 = self.buffers[1].rs1
        self.reg.rs2 = self.buffers[1].rs2
        self.reg.read_register()
        self.buffers[1].rs1_data = self.reg.read_data_1
        self.buffers[1].rs2_data = self.reg.read_data_2

        if (self.buffers[1].rs1_data>>31)&1 == 1:
            self.buffers[1].rs1_data -= 1<<32
        if (self.buffers[1].rs2_data>>31)&1 == 1:
            self.buffers[1].rs2_data -= 1<<32

        # execute any ALU operation
        self.alu.muxA = self.buffers[1].muxA
        self.alu.muxB = self.buffers[1].muxB
        self.alu.aluOp = self.buffers[1].aluOp
        self.alu.execute(self.buffers[1].rs1_data, self.buffers[1].rs2_data,
                         self.buffers[2].rz, self.buffers[2].ry,
                         self.buffers[1].imm, self.buffers[1].funct3,
                         self.buffers[1].funct7, self.buffers[1].PC_Temp)
        self.buffers[1].rm = [self.reg.read_data_2, self.buffers[2].rz][self.buffers[1].muxRM]
        self.buffers[1].rz = self.alu.rz

    def memory_access(self):
        print("MEMORY ACCESS")
        self.pmi.mem_read = self.buffers[2].mem_read
        self.pmi.mem_write = self.buffers[2].mem_write
        self.pmi.dataType = self.buffers[2].dataType
        
        mdr = [self.buffers[2].rm, self.buffers[3].ry][self.buffers[2].muxMDR]
        # access memory
        self.pmi.update(self.buffers[2].rz, mdr)
        print(f"MDR: {self.pmi.getMDR()}")
        # this runs muxY and processes final output that goes to register file
        self.alu.muxY = self.buffers[2].muxY
        self.alu.process_output(self.pmi.getMDR(), self.buffers[2].PC_Temp + 4)
        self.buffers[2].ry = self.alu.ry

    # writeback stage
    def register_update(self):
        print("REGISTER UPDATE")
        # data to write
        self.reg.rd = self.buffers[3].rd
        self.reg.write_data = self.buffers[3].ry
        self.reg.reg_write = self.buffers[3].reg_write
        # update register. This only writes if self.reg.reg_write was set to True
        self.reg.register_update()
        print("\n")

    # execute one substep
    def substep(self):
        self.stall = False
        self.flush = False
        for stage in reversed(self.stages):
            if not self.flush and stage == 1:
                self.fetch()
            elif stage == 2:
                self.decode()
                if self.stall:
                    print("\tSTALL")
                    break
                if self.flush:
                    print("\tFLUSH")
                    break
            elif stage == 3:
                self.execute()
            elif stage == 4:
                self.memory_access()
            elif stage == 5:
                self.register_update()
                self.num_instructions_executed += 1
                self.CPI = self.clock/self.num_instructions_executed
        
        for i in range(len(self.stages)):
            if self.stages[i] > 2 or not self.stall:
                self.stages[i] += 1
        
        self.stages = [x for x in self.stages if x < 6]

        if self.stall:
            self.buffers = [self.buffers[0], buffer()] + self.buffers[1:-1]
        else:
            self.buffers = [buffer()] + self.buffers[:-1]
            if self.IR not in [TERMINATION_CODE, 0]:
                self.buffers[0].PC_Temp = self.PC_Temp
                self.buffers[0].IR = self.IR
                if not self.flush and 1 not in self.stages:
                    self.stages = [1] + self.stages
            else:
                self.stages = [x for x in self.stages if x not in [1, 2]]
        self.flush = False
        # update counter
        self.clock += 1

        print("Cycle ", self.clock, "completed")
        if self.print_registers:
            print("REGISTER VALUES:")
            for i in range(32):
                print(f"\t{' ' if i < 10 else ''}x{i}: 0x{self.reg.register[i]:08x}")

    # load a .mc file
    def load(self, file):
        self.reset()
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
        with open(self.file[:-3] + '_out.mc', 'w') as file:
            last = max(self.i_pmi.memory.byteData.keys())
            pc = 0
            while pc < last:
                instr = self.i_pmi.memory.getWordAtAddress(pc)
                file.write(f"0x{pc:X} 0x{instr:08X}\n")
                pc += 4
            for k, v in self.pmi.memory.byteData.items():
                file.write(f"0x{k:X} 0x{v:X}\n")
            
            file.write("Statistics of the run:\n")            
            file.write(f"\tStat1: Total number of cycles: {self.clock}\n")
            file.write(f"\tStat2: Total instructions executed: {self.num_instructions_executed}\n")
            file.write(f"\tStat3: CPI: {self.CPI}\n")
            file.write(f"\tStat4: Number of Data-transfer (load and store) instructions executed: {self.num_instructions_data_transfer}\n")
            file.write(f"\tStat5: Number of ALU instructions executed: {self.num_instructions_alu}\n")
            file.write(f"\tStat6: Number of Control instructions executed: {self.num_instructions_control}\n")
            file.write(f"\tStat7: Number of stalls/bubbles in the pipeline: {self.num_stalls}\n")
            file.write(f"\tStat8: Number of data hazards: {self.num_data_hazards}\n")
            file.write(f"\tStat9: Number of control hazards: {self.num_control_hazards}\n")
            file.write(f"\tStat10: Number of branch mispredictions: {self.num_branch_misprediction}\n")
            file.write(f"\tStat11: Number of stalls due to data hazards: {self.num_stalls_data_hazards}\n")
            file.write(f"\tStat12: Number of stalls due to control hazards: {self.num_stalls_control_hazards}\n")
            

    # run the entire program
    def run(self):
        while len(self.stages) > 0:
            self.substep()
"""
muxDA --> forwarding to D rs1  [rs1, buffers[1].rz, buffers[2].ry]
muxDB --> forwarding to D rs2  [rs2, buffers[1].rz, buffers[2].ry]
muxA  --> forwarding to E rs1  [rs1, pc, buffers[2].rz, buffers[2].ry]
muxB  --> forwarding to E rs2  [rs2, imm, buffers[2].rz, buffers[2].ry]
muxMDR--> forwarding to M MDR  [rs2, buffers[3].ry]
muxRM --> forwarding to E RM   [rs2, buffers[2].rz]
"""

"""
[1, 2, 3, 4]
STALL 1
FLUSH
stages -> [1, 2, 4, 5]
NO F

[4, 5]
STALL -> 0
stages -> [1, 2, 5]
NO F

[1, 2, 5]
stages -> [2, 3]
F


0    add x1 x2 x3
4    add x4 x5 x6
8    beq x1 x4 label
c    ...

D8 E4 M0
   E8
F D

"""

"""
E to E
0   add x1 x2 x3
4   add x4 x1 x5
(--)
D4 E0          STALL
D4    M0
   E4    W0

D4 E0
   E4 M0
"""

"""
M to E
0   lw x1 0(x10)
4   add x2 x1 x3

D4 E0          STALL
D4    M0
   E4    W0
"""

"""
M to M
0   lw x1 0(x10)
4   sw x1 0(x12)

D4 E0          STALL
D4    M0       
   E4    W0

D4 E0
   E4 M0
      M4 W0
"""

"""
E to D
0   add x1 x2 x3
4   beq x1 x4 label

D4 E0           STALL
D4    M0        STALL
D4       W0
"""

"""
M to D
0   lw x1 0(x10)
4   beq x1 x2 label

D4 E0           STALL       !! ALWAYS STALLS, EVEN WITH FORWARDING
D4    M0        STALL
D4       W0
"""

"""
Detect

self.stall = True
"""

# auipc lui
