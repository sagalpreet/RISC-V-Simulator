class IAG:
    def __init__(self, PC):
        self.PC = PC
        self.PCSrc = -1     ## 0 for incrementing 4         ## 1 for branch / jump instructions  ## 2 for jalr

    def update(self, immediate, value):
        print("\tUpdating PC")
        if self.PCSrc == 0:
            self.PC += 4
            print("\tMoved to next sequential instruction")
        elif self.PCSrc == 1:
            self.PC += immediate
            print("\tJumped to offset provided by immediate")
        elif self.PCSrc == 2:
            self.PC = value
            print("\tJumped to register value")
        print(f"\tPC: {self.PC}")
