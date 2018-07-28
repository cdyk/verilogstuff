class Assembler:
    def __init__(self, ram):
        self.ram = ram

    def curr(self):
        return len(self.ram)

    def LDX(self, val):
        self.ram += [0xA2, val & 255]

    def NOP(self):
        self.ram.append(0xEA)

    def DEX(self):
        self.ram.append(0xCA)

    def BNE(self, addr):
        self.ram.append(0xD0)
        self.ram.append((addr-self.curr())&255)
    
    def JMP(self, addr):
        self.ram += [0x4C, 0x00, 0x00]

class Disassembler:
    def __init__(self, ram):
        self.ram = ram
        self.pc = 0
        self.opcode_length = 0

    def unknown(self):
        self.opcode = "???"

    def opcode_EA(self):
        self.opcode = "NOP"
    
    def opcode_A2(self):
        self.opcode = "LDX #${:02X}".format(self.ram[self.pc+1])
        self.opcode_length = 2

    def opcode_4C(self):
        self.opcode = "JMP ${:02X}{:02X}".format(self.ram[self.pc+2], self.ram[self.pc+1])
        self.opcode_length = 3

    def opcode_CA(self):
        self.opcode = "DEX"
    
    def opcode_D0(self):
        self.opcode = "BNE ${:04X}".format(self.ram[self.pc+1])
        self.opcode_length = 2

    def decode(self):
        q = len(ram)
        n = self.pc + self.opcode_length
        if 0 <= n and n < q:
            self.pc = n
            opcode_handler = getattr(self, "opcode_{:X}".format(self.ram[self.pc]), self.unknown)
            self.opcode_length = 1
            opcode_handler()
            return [self.pc, self.opcode]
        else:
            return None

    def disassembly(self):
        opcode = self.decode()
        while opcode:
            yield opcode
            opcode = self.decode()

class RegisterFileStore:
    def __init__(self):
        self.X = 0
        self.Y = 0
        self.A = 0
        self.PC = 0
        self.UPC = 0

class RegisterFile:
    def __init__(self):
        self.R = RegisterFile()
        self.W = RegisterFile()

    def tick(self):
        self.R, self.W = self.W, self.R

    @property
    def X(self):
        return self.R.X
    
    @X.setter
    def X(self, value):
        self.W.X = value

    @property
    def Y(self):
        return self.R.Y
    
    @Y.setter
    def Y(self, value):
        self.W.Y = value

    @property
    def A(self):
        return self.R.A
    
    @A.setter
    def A(self, value):
        self.W.A = value

    @property
    def PC(self):
        return self.R.PC
    
    @PC.setter
    def PC(self, value):
        self.W.PC = value

    @property
    def UPC(self):
        return self.R.UPC
    
    @UPC.setter
    def UPC(self, value):
        self.W.UPC = value

class MicroCode:
    PRINT = object()
    FETCH = object()
    STORE = object()
    ADDR_PC = object()
    PC_INCR = object()
    PC_SET = object()
    UPC_SET = object()
    UPC_NEXT = object()

    # Ucode
    urom = []

    ulut = {}
    for i in range(255):
        ulut[i] = 0

    ulut[0xEA] = len(urom)          # 0xEA: NOP
    urom.append({FETCH, ADDR_PC, PC_INCR, UPC_SET, PRINT })

    ulut[0x4C] = len(urom)          # 0x4C: JMP #$xxxx
    urom.append({FETCH, ADDR_PC, PC_INCR, UPC_NEXT, PRINT })
    urom.append({FETCH, ADDR_PC, PC_INCR, UPC_NEXT })
    urom.append({FETCH, ADDR_PC, PC_SET, UPC_SET })

    ulut[0xA2] = len(urom)          # 0xA2: LDX #      - UNFINISHED
    urom.append({FETCH, ADDR_PC, PC_INCR, UPC_NEXT, PRINT })
    urom.append({FETCH, ADDR_PC, PC_INCR, UPC_SET })

    ulut[0xCA] = len(urom)          # 0xCA: DEX        - UNFINISHED
    urom.append({ FETCH, ADDR_PC, PC_INCR, UPC_SET, PRINT })

    ulut[0xD0] = len(urom)          # 0xD0: BNE #$xx   - UNFINISHED
    urom.append({FETCH, ADDR_PC, PC_INCR, UPC_NEXT, PRINT })
    urom.append({FETCH, ADDR_PC, PC_INCR, UPC_SET })

class CPU(RegisterFile, MicroCode):
    def __init__(self, ram):
        self.ram = ram

    def tick(self):
        super(RegisterFile, self).tick()

        print("upc={0}".format(self.UPC))

        #uop = urom[self.upc]

        self.UPC +=1


ram = []

asm = Assembler(ram)
asm.LDX(3)
label = asm.curr()
asm.NOP()
asm.DEX()
asm.BNE(label)
asm.JMP(0)

disasm = Disassembler(ram)
for pc, opcode in disasm.disassembly():
    print("{:04X} {:s}".format(pc, opcode))


print(ram)

cpu = CPU(ram)

#for i in range(10):
#    cpu.tick()
