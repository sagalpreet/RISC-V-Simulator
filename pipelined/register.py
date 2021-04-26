"""

register module

"""

class register_module:
    def __init__(self):
        self.register = [0 for j in range(32)] # 32 registers initialized
        self.register[2] = 0x7FFFFFF0   # sp
        self.register[3] = 0x10000000   # gp
        self.rs1 = 0  # rs1: 5 bit binary string for the rs1 register
        self.rs2 = 0  # rs2: 5 bit binary string for the rs2 register
        self.rd = 0   # rd: 5 bit binary string for the rd register
        self.read_data_1 = 0 # integer data for contents retreived from rs1
        self.read_data_2 = 0 # integer data for contents retreived from rs2
        self.write_data = 0 # integer data to be written
        self.reg_write = False # flag to tell if data has to be written 
        
    def read_register(self):
        """
        
        Reads the data in registers  rs1 and rs2
        and updates the read values in read_data_1 and read_data_2

        Output is 0 for invalid rs1 or rs2 values
        """
        print("\tReading registers")
        try:     
            self.read_data_1 = self.register[self.rs1]
        except:
            self.read_data_1 = 0
        
        try:     
            self.read_data_2 = self.register[self.rs2]
        except:
            self.read_data_2 = 0
        
        print(f"\tA: 0x{self.read_data_1:08x}")
        print(f"\tB: 0x{self.read_data_2:08x}")
    

    def register_update(self):
        """
        
        If the reg write flag is set to True, writes the data present in write_data(int type)
        to the register specified by write_register
        
        
        """
        if self.reg_write == True:
            self.reg_write = False
            if self.rd == 0:        # since the register 0 always stores constant value 0
                return
            print(f"\tWriting value 0x{self.write_data:08x} to register x{self.rd}")
            self.register[self.rd] = self.write_data



"""
############### Sample to use the register module ############### 
reg = register_module()
# reading from register module
reg.rs1 = 0b00001
reg.rs2 = 0b00010
reg.read_register()
print(reg.read_data_1)
print(reg.read_data_2)
# writing to register module
reg.reg_write = True
reg.write_data = 5
reg.rd = 0b00011
reg.register_update()
# reading the data written above
reg.rs1 = 0b00011
reg.read_register()
print(reg.read_data_1)
"""

    
        

        
        
        
        
        
        
        
        
        
        
        
        
        
        
