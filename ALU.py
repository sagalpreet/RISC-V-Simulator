class ALU:
    def __init__(self):
        # operation to perform
        self.__op = 0
        # intermediate registers
        self.rz = 0
        self.rm = 0
        self.ry = 0
        # output of stage 3, input to stage 4 determined by muxY
        self.muxY = 0
        # Is the second operand rs2 or imm
        self.muxB = 0
        # input to op1. Is it rs1 or PCTemp?
        self.muxA = 0
        # 0 for add (load, store), X1 for branch (chooses operation and inv_zero)
        self.aluOp = 0
    
    def execute(self, rs1, rs2, rz, ry, imm, funct3, funct7, pc):
        op1 = [rs1, pc, rz, ry][self.muxA]
        op2 = [rs2, imm, rz, ry][self.muxB]
        print(f"\talu.operand1: 0x{op1:08x}")
        print(f"\talu.toperand2: 0x{op2:08x}")
        # no operation to be performed
        if self.aluOp == 3:
            print("\tNo operation: exiting")
            self.rz = 0
            return
        
        # figure out correct operation to perform
        self.control(funct3, funct7)
        if self.__op == 1:    # add
            self.rz = op1 + op2
        elif self.__op == 2:  # sub
            self.rz = op1 - op2
        elif self.__op == 3:  # mul
            self.rz = op1 * op2
        elif self.__op == 4:  # div
            self.rz = op1 // op2
        elif self.__op == 5:  # rem
            self.rz = op1 % op2
        elif self.__op == 6:  # and
            self.rz = op1 & op2
        elif self.__op == 7:  # or
            self.rz = op1 | op2
        elif self.__op == 8:  # xor
            self.rz = op1 ^ op2
        elif self.__op == 9:  # sll
            self.rz = op1 << op2
        elif self.__op == 10:  # srl
            self.rz = (op1 % (1 << 32)) >> op2
        elif self.__op == 11: # sra
            self.rz = op1 >> op2
        elif self.__op == 12: # slt
            self.rz = int(op1 < op2)
        elif self.__op == 13: # lui
            if op1 < 0:
                op1 += 1<<32
            self.rz = ((op1<<20)>>20)+op2
        
        if self.rz < 0:
            self.rz += 1<<32
        print(f"\talu.RZ: 0x{self.rz:08x}")
    
    # use aluOp, funct3 and funct7 to find operation to perform
    def control(self, funct3, funct7):
        if self.aluOp == 0:     # add, for load/store instructions
            self.__op = 1
        elif self.aluOp&1 == 1:
            self.__op = 13
        elif funct3 == 0:   # add/sub/mul
            if self.muxB == 1 or funct7 == 0:   # add(i) if the immediate value is used or funct7 is 0
                self.__op = 1
            elif funct7 == 1:       # mul distinguished on the basis of funct7
                self.__op = 3
            elif funct7 == 32:      # similarly for sub
                self.__op = 2
        elif funct3 == 7:   # and operation
            self.__op = 6
        elif funct3 == 6:    # or/rem
            if self.muxB == 1 or funct7 == 0:   # or(i) if immediate is used or funct7 is 0, similar to add(i)
                self.__op = 7
            elif funct7 == 1:   # rem operation
                self.__op = 5
        elif funct3 == 4:   # xor/div
            if self.muxB == 1 or funct7 == 0:   # xor(i) if imm is used or funct7 is 0
                self.__op = 8
            elif funct7 == 1:   # div operation
                self.__op = 4
        elif funct3 == 1:       # sll operation
            self.__op = 9
        elif funct3 == 101:     # srl/sra
            self.__op = 10 + funct7&32>>5  # which of the two is decided by funct7
        elif funct3 == 2:   # slt
            self.__op = 12
    
    # output of muxY that goes to register file
    def process_output(self, mdr, return_addr): # output is either rz, MDR or return address
        if self.muxY == 0:
            self.ry = self.rz
        elif self.muxY == 1:
            self.ry = mdr
        elif self.muxY == 2:
            self.ry = return_addr
        print(f"\talu.RY: 0x{self.ry:08x}")
