import ALU, IAG, memory, register

TERMINATION_CODE = 0xFFFFFFFF
iag = IAG.IAG(0)
alu = ALU.ALU()
pmi = memory.ProcessorMemoryInterface(4)
reg = register.register_module()

# global variables
IR = opcode = imm = funct3 = funct7 = immediate = 0

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
  global IR
  pmi.update(alu.rz, iag.PC, alu.rm, 1, True, False, 2) # set MAR to PC
  IR = pmi.getMDR() # get instruction corresponding to PC
  return

def decode():
  global opcode, funct3, funct7, immediate
  opcode = (2**7 - 1) & IR
  rd = (2**12 - 2**7) & IR
  funct3 = (2**15 - 2**12) & IR
  rs1 = (2**20 - 2**15) & IR
  rs2 = (2**25 - 2**20) & IR
  funct7 = (2**32 - 2**25) & IR
  '''
  should we use opcode here to get immediate field by concatenating funct3, funct7, rd, rs1 and rs2 appropriately
  or do you have some better idea ...............................................................................
  '''
  reg.read_register_1 = rs1
  reg.read_register_1 = rs2
  reg.write_register = rd
  reg.read_register()
  '''
  set all the control bits in alu ...............................................................................
  '''
  return

def execute():
  global immediate
  '''
  perform alu operations ........................................................................................
  '''
  return

def memory_access():
  '''
  fetch or write memory .........................................................................................
  '''
  iag.update(immediate)
  return

def register_update():
  # reg.reg_write = True # set this depending upon the instruction type -> should we do it in decode itself or create a mux ?
  # reg.write_data = # this will depend upon above decision
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
