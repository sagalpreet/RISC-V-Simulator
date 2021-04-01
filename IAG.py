class IAG:
    def __init__(self, PC):
        self.PC = PC
        self.PCSrc = -1     ## 0 for incrementing 4         ## 1 for branch / jump instructions  ## 2 for jalr

    def update(self, immediate, value):
        if self.PCSrc == 0:
            self.PC += 4
        elif self.PCSrc == 1:
            self.PC += immediate
        elif self.PCSrc == 2:
            self.PC = value

## PC_TEMP has to be stored in a variable