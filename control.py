import ALU, IAG, memory, register
import sys

TERMINATION_CODE = 0xFFFFFFFF
iag = IAG.IAG(0)
alu = ALU.ALU()
pmi = memory.ProcessorMemoryInterface(4)
reg = register.register_module()

# global variables
IR = opcode = imm = funct3 = funct7 = 0
branch = jump = 0
PC_Temp = 0

def fetch():
    global IR, PC_Temp
    pmi.mem_read = True
    pmi.dataType = 2
    pmi.update(alu.rz, iag.PC, alu.rm, 1) # set MAR to PC
    IR = pmi.getMDR() # get instruction corresponding to PC
    PC_Temp = iag.PC
    return

def decode():
    global opcode, funct3, funct7, imm, branch, jump, IR
    opcode = ((1<<7) - 1) & IR
    rd = (((1<<12) - (1<<7)) & IR)>>7
    funct3 = (((1<<15) - (1<<12)) & IR)>>12
    rs1 = (((1<<20) - (1<<15)) & IR)>>15
    rs2 = (((1<<25) - (1<<20)) & IR)>>20
    funct7 = (((1<<32) - (1<<25)) & IR)>>25
    print(opcode, rd, funct3, rs1, rs2, funct7)

    if opcode == 0b0110011: # R format
        imm = 0         # immediate unnecessary
        alu.muxA = 0    # use rs1
        alu.muxB = 0    # use rs2
        alu.aluOp = 2   # determine operation with funct3 and funct7
        alu.muxY = 0    # output is output of ALU
        branch = 0      # don't branch
        jump = 0        # don't jump
        reg.reg_write = True    # write to register
    elif opcode == 0b0010011 or opcode == 0b0000011 or opcode == 0b1100111: # I format
        imm = (((1<<32) - (1<<20)) & IR) >> 20 
        if (imm>>11)&1 == 1:            # check if sign bit is 1
            imm = -((imm ^ ((1<<12)-1)) + 1)
        alu.muxA = 0            # op1 is rs1
        alu.muxB = 1            # op2 is imm
        reg.reg_write = True    # write to register
        jump = 0                # don't jump
        branch = 0              # don't branch
        if opcode == 0b0010011: # arithmetic I format
            alu.aluOp = 2       # determine operation with funct3 and funct7
            alu.muxY = 0        # output is output of ALU
        else:                   # load or jalr
            alu.aluOp = 0       # add
            if opcode == 0b0000011:     # load
                alu.muxY = 1    # output is MDR
                pmi.dataType = funct3   # datatype to read
                pmi.mem_read = True     # read memory
            else:                       # jalr
                branch = 1              # branch
                jump = 1                # and jump
                alu.muxY = 2            # output is return address
    elif opcode == 0b0100011: # S format
        imm = ((((1<<32) - (1<<25)) & IR) >> 20) + ((((1<<12)-(1<<7)) & IR)>>7)
        if (imm>>11)&1 == 1:            # check if sign bit is 1
            imm = -((imm^((1<<12)-1)) + 1)
        alu.muxA = 0            # op1 is rs1
        alu.muxB = 1            # op2 is imm
        alu.aluOp = 0           # add
        alu.muxY = -1           # output is nothing
        pmi.mem_write = True    # write to memory
        pmi.dataType = funct3   # datatype to write
        branch = 0              # don't branch
        jump = 0                # don't jump
    elif opcode == 0b1100011: # SB format
        imm = (((1<<31) & IR) >> 19) + (((1<<7) & IR) << 4) + ((((1<<31) - (1<<25)) & IR)>>20) + ((((1<<12) - (1<<8))&IR)>>7)
        if (imm>>12)&1 == 1:            # check if sign bit is 1
            imm = -((imm^(1<<13-1)) + 1)
        alu.muxA = 0            # op1 is rs1
        alu.muxB = 0            # op2 is rs2
        alu.aluOp = 1           # determine branch operation by funct3
        alu.muxY = -1           # no output
        branch = 1              # branch
        jump = 0                # don't jump
    elif opcode == 0b0110111 or opcode == 0b0010111:    # U format
        imm = ((1<<32) - (1<<12)) & IR
        if opcode == 0b0010111: # if auipc
            alu.muxA = 1        # op1 is PC
        else:                   # if lui
            alu.muxA = 0        # op1 is rs1
        alu.muxB = 1            # op2 is rs2
        alu.aluOp = 0           # add
        reg.reg_write = True    # write to register
        alu.muxY = 0            # output is ALU
        branch = 0              # don't branch
        jump = 0                # don't jump
    elif opcode == 0b1101111:   # UJ format
        imm = (((1<<31) & IR)>>11) + (((1<<20) - (1<<12)) & IR) + (((1<<20) & IR)>>9) + ((((1<<31) - (1<<21)) & IR)>>20)
        if (imm>>20)&1 == 1:            # check if sign bit is 1
            imm = -((imm^((1<<21)-1)) + 1)
        alu.muxA = 0            # op1 is rs1
        alu.muxB = 0            # op2 is rs2
        reg.reg_write = True    # write to register
        alu.aluOp = -1          # no operation
        alu.muxY = 2            # output is return address
        branch = 1              # branch
        jump = 0                # don't jump
    reg.read_register_1 = "{0:b}".format(rs1)
    reg.read_register_2 = "{0:b}".format(rs2)
    reg.write_register = "{0:b}".format(rd)
    reg.read_register()
    return

def execute():
    global imm, funct3, funct7
    alu.execute(reg.read_data_1, reg.read_data_2, imm, funct3, funct7, iag.PC)
    return

def memory_access():
    global imm
    pmi.update(alu.rz, iag.PC, alu.rm, 0)
    alu.process_output(pmi.getMDR(), iag.PC)
    iag.PCSrc = alu.zero & branch | ((branch & jump)<<1)
    print(alu.zero, branch)
    iag.update(imm, alu.rz)
    return

def register_update():
    reg.write_data = alu.ry
    reg.register_update()
    return

def step():
    fetch()
    print(iag.PC, "{:b}".format(IR))
    decode()
    execute()
    memory_access()
    register_update()

def run(file):
    with open(file, 'r') as infile:
            text = True
            for line in infile:
                mloc, instr = [int(x, 16) for x in line.split()]
                if text:
                    pmi.memory.setWordAtAddress(mloc, instr)
                else:
                    pmi.memory.setByteAtAddress(mloc, instr)
                    
                if instr == TERMINATION_CODE:
                    text = False
        
    while (True):
        step()
        if IR == TERMINATION_CODE or IR == 0:
            break

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Need one argument for input file")
        exit()
    
    run(sys.argv[1])
