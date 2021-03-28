class IAG:
    def __init__(self, PC):
        self.PC = PC
        self.muxControl = -1     ## 0 for incrementing 4         ## 1 for branch / jump instructions

    def update(self, immediate = 0):
        self.PC += 4 * (1 - self.muxControl) + 2 * immediate * (self.muxControl)

## PC_TEMP has to be stored in a variable