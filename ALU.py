class ALU:
    def __init__(self):
        self.__op = 0
        self.rz = 0
        self.rm = 0
        self.ry = 0
        self.aluSrc = 0
        self.aluOp = 0
        self.__inv_zero = 0
    
    def execute(self, rs1, rs2, imm, funct3, funct7):
        op1 = rs1
        op2 = rs2 if self.aluSrc == 0 else imm
        
        self.rm = rs2

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
        zero = self.rz == 0
        if self.__inv_zero:
            zero = not zero
    
    def control(self, funct3, funct7):
        if self.aluOp == 0:
            self.__op = 1
        elif self.aluOp&1 == 1:  # for branch operations
            if funct3&4 == 0:   # beq or bne
                self.__op = 2     # use sub
                self.__inv_zero = funct3&1    # invert zero if bne
            else:             # blt or bge
                self.__op = 12    # use slt
                self.__inv_zero = 1-funct3&1   # invert zero if blt
        elif funct3 == 0:   # add/sub/mul
            if self.aluSrc == 1 or funct7 == 0:
                self.__op = 1 # add/addi
            elif funct7 == 1:
                self.__op = 3 # mul
            elif funct7 == 32:
                self.__op = 2 # sub
            self.__op = funct7&32>>5 + 1 # which is determined by funct3
        elif funct3 == 7:   # and
            self.__op = 6
        elif funct3 == 6:    # or/rem
            if self.aluSrc == 1 or funct7 == 0:
                self.__op = 7 # or/ori
            elif funct7 == 1:
                self.__op = 5 # rem
        elif funct3 == 4:   # xor/div
            if self.aluSrc == 1 or funct7 == 0:
                self.__op = 8 # xor/xori
            elif funct7 == 1:
                self.__op = 4 # div
        elif funct3 == 1:   # sll
            self.__op = 9
        elif funct3 == 101: # srl/sra
            self.__op = 10 + funct7&32>>5  # which is decided by funct7
        elif funct3 == 2:   # slt
            self.__op = 12
    
    def process_output(self, muxY, mar, return_addr):
        if muxY == 0:
            self.ry = self.rz
        elif muxY == 1:
            self.ry = mar
        else:
            self.ry = return_addr
"""
add: 000, 0000000
addi: 000
(no muli)

sub: 000, 0100000

and: 111

or: 110, 0000000
ori: 110
(no remi)

xor: 100, 0000000
xori: 100
(no divi)

sll: 001

srl: 101, 0000000

sra: 101, 0100000

slt: 010    

mul:
    opcode: 0110011
    funct3: 000
    funct7: 0000001
0000001 00010 00001 000 00000 0110011

div:
    opcode: 0110011
    funct3: 100
    funct7: 0000001
0000001 00010 00001 100 00000 0110011

rem:
    opcode: 0110011
    funct3: 110
    funct7: 0000001
0000001 00010 00001 110 00000 0110011

branch instructions - sub input, choose operation by funct3
"""