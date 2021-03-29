import ALU, IAG, memory, register

TERMINATION_CODE = 0xFFFFFFFF
iag = IAG.IAG(0)
alu = ALU.ALU()
pmi = memory.ProcessorMemoryInterface(4)
reg = register.register_module()

# global variables
IR = opcode = imm = funct3 = funct7 = 0
muxY = 0
PC_Temp = 0

with open('input.mc', 'r') as infile:
    text = True
    for line in infile:
        mloc, instr = [int(x, 16) for x in line.split()]
        if text:
            pmi.__memory.setWordAtAddress(mloc, instr)
        else:
            pmi.__memory.setByteAtAddress(mloc, instr)
            
        if instr == TERMINATION_CODE:
            text = False


def fetch():
    global IR, PC_Temp
    pmi.update(alu.rz, iag.PC, alu.rm, 1, True, 2) # set MAR to PC
    IR = pmi.getMDR() # get instruction corresponding to PC
    PC_Temp = iag.PC
    return

def decode():
    global opcode, funct3, funct7, imm, muxY
    opcode = (1<<7 - 1) & IR
    rd = ((1<<12 - 1<<7) & IR)>>7
    funct3 = ((1<<15 - 1<<12) & IR)>>12
    rs1 = ((1<<20 - 1<<15) & IR)>>15
    rs2 = ((1<<25 - 1<<20) & IR)>>20
    funct7 = ((1<<32 - 1<<25) & IR)>>25

    if opcode == 0b0110011: # R format
        imm = 0
        alu.aluSrc = 0
        alu.aluOp = 2
        muxY = 0
    elif opcode == 0b0010011 or opcode == 0b0000011 or opcode == 0b1100111: # I format
        imm = ((1<<32 - 1<<20) & IR) >> 20
        alu.aluSrc = 1
        if opcode == 0b0010011:
            alu.aluOp = 2
            muxY = 0
        else:
            alu.aluOp = 0
            muxY = 1
    elif opcode == 0b0100011: # S format
        imm = ((1<<32 - 1<<25) & IR) >> 20 + ((1<<12-1<<7) & IR)>>7
        alu.aluSrc = 1
        alu.aluOp = 0
        muxY = 0
        pmi.mem_write = True
        pmi.dataType = funct3

    elif opcode == 0b1100011: # SB format
        imm = ((1<<31) & IR) >> 19 + ((1<<7) & IR) << 4 + ((1<<31 - 1<<25) & IR)>>20 + ((1<<12 - 1<<8)&IR)>>7
        alu.aluSrc = 0
        alu.aluOp = 1
        muxY = 0
    elif opcode == 0b0110111 or opcode == 0b0010111:    # U format
        imm = (1<<32 - 1<<12) & IR
        alu.aluSrc = -1         # to disable ALU
        alu.aluOp = 0
        muxY = 0
    elif opcode == 0b1101111:   # UJ format
        imm = ((1<<31) & IR)>>11 + (1<<20 - 1<<12) & IR + ((1<<20) & IR)>>9 + ((1<<31 - 1<<21) & IR)>>20
        alu.aluSrc = -1
        alu.aluOp = 0
        muxY = 2

    reg.read_register_1 = rs1
    reg.read_register_1 = rs2
    reg.write_register = rd
    reg.read_register()
    return

def execute():
    global imm, funct3, funct7
    if alu.aluSrc != -1:
        alu.execute(reg.read_data_1, reg.read_data_2, imm, funct3, funct7)
    return

def memory_access():
    global imm
    alu.process_output(muxY, pmi.getMDR(), iag.PC)

    pmi.update(alu.rz, iag.PC, alu.rm, 0, False)
    pmi.update(alu.rz, iag.PC, alu.rm, 0, True)

    iag.PCSrc = alu.zero
    iag.update(imm << 1)

    return

def register_update():
  if muxY in [0, 1, 2]: # if register is not be updated reg_write maybe set to some value like -1
    reg.reg_write = True
  if muxY == 0:
      reg.write_data = alu.rz
    elif muxY == 1:
      reg.write_data = pmi.getMDR()
    elif muxY == 2:
      reg.write_data = PC_Temp
  reg.register_update()
  reg.reg_write = False
  return
  
while (True):
  fetch()
  if iag.PC == TERMINATION_CODE:
    break
  decode()
  execute()
  memory_access()
  register_update()
