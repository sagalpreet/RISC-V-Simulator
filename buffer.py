"""

    buffer module
    
"""

class buffer_module:
    def __init__(self):
        self.data = {}
        
        # written to the if_id_buffer after the instruction fetch stage
        self.data['PC'] = ''  
        
        # written to the id_ex_buffer after the instruction decode stage
        self.data['rs1'] = ''
        self.data['rs2'] = ''
        self.data['imm'] = ''
        
        # written to the ex_mem_buffer after the instruction execute stage
        self.data['RZ'] = ''
        
        # written to the mem_wb_buffer after the memory  stage
        self.data['RY'] = ''        
        
        
        
        


# sample buffer objects

#if_id_buffer = buffer_module() # buffer between instruction fetch stage and instruction decode stage
#id_ex_buffer = buffer_module()
#ex_mem_buffer = buffer_module()
#mem_wb_buffer = buffer_module()
