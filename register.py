"""

register module

"""

class register_module:
    def __init__(self):
        self.num_registers = 32
        self.register_size = 32
        self.register = ['0'*self.register_size for j in range(self.num_registers)]
        self.read_register_1 = '00000'  # read_register_1: 5 bit binary string for the rs1 register
        self.read_register_2 = '00000'  # read_register_2: 5 bit binary string for the rs2 register
        self.write_register = '00000'   # write_register: 5 bit binary string for the rd register
        self.read_data_1 = 0 # integer data for contents retreived from read_register_1
        self.read_data_2 = 0 # integer data for contents retreived from read_register_2
        self.write_data = 0 # integer data to be written
        self.reg_write = False # flag to tell if data has to written 
        
    def read_register(self):
        """
        
        Reads the data in registers  read_register_1 and read_register_2
        and updates the read values in read_data_1 and read_data_2.
        
        This should be called in step 2 after decoding the instruction has been done
        and values of rs1 and rs2 have been extracted.
        """
        try:
            rs_1 = int(self.read_register_1, 2)        
            self.read_data_1 = int(self.register[rs_1], 2)
        except:
            self.read_data_1 = 0
        
        try:
            rs_2 = int(self.read_register_2, 2)        
            self.read_data_2 = int(self.register[rs_2], 2)
        except:
            self.read_data_2 = 0
        #reg_a = self.read_data_1  # updating the global variable 
        #reg_b = self.read_data_2  # updating the global variable
    
    def register_update(self):
        """
        
        If the reg write flag is set to True, writes the data present in write_data(int type)
        to the register specified by write_register as a binary string.
        
        
        """
        if self.reg_write == True:
            rd = int(self.write_register, 2)
            self.register[rd] = bin(self.write_data)


"""
############### Sample to use the register module ############### 
reg = register_module()
# reading from register module
reg.read_register_1 = '00001'
reg.read_register_2 = '00010'
reg.read_register()
print(reg.read_data_1)
print(reg.read_data_2)
# writing to register module
reg.reg_write = True
reg.write_data = 5
reg.write_register = '00011'
reg.register_update()
# reading the data written above
reg.read_register_1 = '00011'
reg.read_register()
print(reg.read_data_1)
"""

    
        

        
        
        
        
        
        
        
        
        
        
        
        
        
        
