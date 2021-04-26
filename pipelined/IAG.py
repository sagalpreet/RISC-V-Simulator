class IAG:
    def __init__(self, PC):
        self.PC = PC
        self.PCSrc = -1     ## 0 for incrementing 4         ## 1 for branch / jump instructions  ## 2 for jalr

    def update(self, branch_target, register_target):
        print("\tUpdating PC")
        if self.PCSrc == 0:
            print("\tMoved to next sequential instruction")
            return False
        elif self.PCSrc == 1:
            self.PC = branch_target
            print("\tJumped to offset provided by immediate")
            return True
        elif self.PCSrc == 2:
            self.PC = register_target
            print("\tJumped to register value")
            return True
        print(f"\tPC: {self.PC}")
# 0 F(0|4)
# 4 F(4|8) D(0|0+4)
#