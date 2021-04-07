# RISC-V Simulator
##### _An application to simulate the execution of machine code in RISC-V ISA_
#

```
Contributors:
Aayush Sabharwal :- 2019CSB1060
Aman Palariya    :- 2019CSB1060
Sagalpreet Singh :- 2019CSB1113
Uday Gupta       :- 2019CSB1127
Amritanshu Rai   :- 2019EEB1140
```
#
RISC-V is an open standard instruction set architecture based on established reduced instruction set computer principles. The RISC-V ISA is provided under open source licenses that do not require fees to use.
#
*RISC-V Simulator* is an application that can simulate the execution of machine code by showing the changes that occur in the memory and registers and the flow of data during runtime.

- The current version supports the simulation for *32 bit* machine only.
- Execution of each instruction is further split into 5 different parts: Fetch, Decode, Execute, Memory Access and Register Update.
- At any step, user can jump directly to the end of the program, execute the current instruction and jump to next instruction or execute current substep and jump to next substep.

### Instructions Supported
```
R format  - add, and, or, sll, slt, sra, srl, sub, xor, mul, div, rem
I format  - addi, andi, ori, lb, ld, lh, lw, jalr
S format  - sb, sw, sd, sh
SB format - beq, bne, bge, blt
U format  - auipc, lui
UJ format - jal
```

### How to run ?


- Clone the repository to your local machine.
- Install pip3.
- Open terminal and run the following commands.
```
        pip3 install -r requirements.txt
        python3 main.py
```

### How to use the application ?
- Click on **File** in the menubar and select **open**.
- Browse through your PC, select the required .mc file and click **open**.
- The address of selected file should now be visible on the **bottom-most bar**.
- Click the **load button** located at the right end of the bottom-most bar.
- The machine code instructions should now be visible under PC and instructions.
- The memory and registers should also be visible. Memory would not be contiguous and only the memory locations set would be visible. All other memory locations contain default values i.e zero.
- You can go to the desired address by typing in the **textbox** and clicking on **Go**. The desired location would be highlighted. If no location is highlighted, means the address has not been dealt with so far and thus contains the default value 0.
- **Run** button would execute all the instructions till the end.
- **Next Instruction** button would execute the current instruction and take you to the next instruction.
- **Next Substep** would execute the next substep (Fetch, Decode, Execute, Memory Access or Register Update) of the current instruction.
- At the end of execution the **PC** turns red.
- At each instruction, current instruction and corresponding PC is highlighted.
- Any change made in register module is also highlighted.

### Dependencies
- Python 3
- Tkinter (GUI)

### Directory Structure
RISC-V-Simulator
- Test Case Folder
    - bubblesort.mc: contains machine code to run bubble sort on elements to sort them.
    - factorial.mc: calculates factorial of an integer stored and saves it in x10 register
    - fibonacci.mc: stores elements of fibonacci series in the memory
    - sumtilln.mc: finds sum of first n positive integers
    - code.txt: contains all the code used to generate the machine code
 - ALU.py
 - IAG.py
 - README.md
 - control.py
 - gui.py
 - memory.py
 - register.py
 - main.py
