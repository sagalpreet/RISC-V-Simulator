class IAG:
    def __init__(self, PC):
        self.PC = PC
        self.PCSrc = -1     ## 0 for incrementing 4         ## 1 for branch / jump instructions

    def update(self, immediate = 0):
        self.PC += 4 * (1 - self.PCSrc) + 2 * immediate * (self.PCSrc)

## PC_TEMP has to be stored in a variable