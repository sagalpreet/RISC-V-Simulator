"""

    buffer module
    
"""

class buffer(dict):
    def __getattr__(self, attr):
        return self.get(attr)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __setitem__(self, key, value):
        super(buffer, self).__setitem__(key, value)
        self.__dict__.update({key: value})

    def __delattr__(self, item):
        self.__delitem__(item)

    def __delitem__(self, key):
        super(buffer, self).__delitem__(key)
        del self.__dict__[key]


# sample buffer objects

#if_id_buffer = buffer_module() # buffer between instruction fetch stage and instruction decode stage
#id_ex_buffer = buffer_module()
#ex_mem_buffer = buffer_module()
#mem_wb_buffer = buffer_module()
