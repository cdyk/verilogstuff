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

class RegisterFile:
    """Latched register file"""
    def __init__(self):
        F = {
            'X': 0,
            'Y': 0,
            'A': 0,
            'S': 0,     # Stack pointer register
            'ADD': 0,   # Adder hold register
            'AI': 0,    # A input register
            'BI': 0,    # B input register
            'PC': 0,
            'UPC': 0,
            'CARRY': 0,
            'ZERO': 0,
            'NEGATIVE': 0,
            'OVERFLOW': 0
        }
        self.__dict__['_R'] = F
        self.__dict__['_W'] = F.copy()

    def tick(self):
        self.__dict__['_R'], self.__dict__['_W'] = self.__dict__['_W'], self.__dict__['_R']

    def __getattr__(self, name):
        return self.__dict__['_R'][name]
    
    def __setattr__(self, name, value):
        self.__dict__['_W'][name] = value

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

def special_bus(regs, add_sb=False, x_sb=False, y_sb=False, s_sb=False):
    if add_sb:
        return regs.ADD
    elif x_sb:
        return regs.X
    elif y_sb:
        return regs.Y
    elif s_sb:
        return regs.S
    else:
        return 0

def data_bus(regs, DL, SB, dl_db=False, pcl_db=False, pch_db=False, sb_db=False, p_db=False):
    if dl_db:
        return DL
    elif pcl_db:
        return regs.PC & 255
    elif pch_db:
        return (regs.PC>>8) & 255
    elif sb_db:
        return SB
    elif p_db:
        return ((  1 if regs.CARRY    else 0) |
                (  2 if regs.ZERO     else 0) |
                ( 64 if regs.OVERFLOW else 0) |
                (128 if regs.NEGATIVE else 0))
    else:
        return 0

def address_bus_lo(regs, DL, dl_adl=False, pcl_adl=False, s_adl=False, add_adl=False):
    if dl_adl:
        return DL
    elif pcl_adl:
        return regs.PC & 255
    elif s_adl:
        return regs.S
    elif add_adl:
        return regs.ADD
    else:
        return 0

def address_bus_hi(regs, DL, dl_adh=False, pch_adh=False):
    if dl_adh:
        return DL
    elif pch_adh:
        return (regs.PC >> 8) & 255
    else:
        return 0

def input_reg_A(regs, SB, sb_add=False, o_add=False):
    if sb_add:
        regs.AI = SB
    elif o_add:
        regs.AI = 0
    else:
        regs.AI = 0

def input_reg_B(regs, DB, ADL, db_add=False, db_add_inv=False, adl_add=False):
    if db_add:
        regs.BI = DB
    elif db_add_inv:
        regs.BI = (~DB)&255
    elif adl_add:
        regs.BI = ADL & 255
    else:
        regs.BI = 0

def alu(regs, sum_en=False, or_en=False, xor_en=False, and_en=False, srs_en=False, acr_c=False, avr_v=False):
    A = regs.AI
    B = regs.BI
    carry = regs.CARRY
    if sum_en:
        O = (A + B + carry)
        carry = 1 if O & 256 else 0
    elif or_en:
        O = (A | B)
    elif xor_en:
        O = (A ^ B)
    elif and_en:
        O = (A & B)
    elif srs_en:
        O = (A << 1) | carry
        carry = 1 if O & 256 else 0
    else:
        O = 0
    if avr_v:
        i = 1 if A & 128 else 0
        j = 1 if B & 128 else 0
        k = 1 if O & 128 else 0
        regs.OVERFLOW = (~(i ^ j) & (i ^ k))&1
    if acr_c:
        regs.CARRY = carry
    regs.ADD = O & 255

def program_counter(PC, inc_en, SP):
    pass

class CPU(MicroCode):
    def __init__(self, ram):
        self.ram = ram
        self.regs = RegisterFile()

    def tick(self):
        self.regs.tick()

        DL = 0  # Input data latch
        SB = special_bus(self.regs, add_sb=False, x_sb=False, y_sb=False, s_sb=False)
        DB = data_bus(self.regs, DL, SB, dl_db=False, pcl_db=False, pch_db=False, sb_db=False, p_db=False)
        ADL = address_bus_lo(self.regs, DL, dl_adl=False, pcl_adl=False, s_adl=False, add_adl=False)
        ADH = address_bus_hi(self.regs, DL, dl_adh=False, pch_adh=False)
        input_reg_A(self.regs, SB, sb_add=False, o_add=False)
        input_reg_B(self.regs, DB, ADL, db_add=False, db_add_inv=False, adl_add=False)
        alu(self.regs, sum_en=False, or_en=False, xor_en=False, and_en=False, srs_en=False, acr_c=False, avr_v=False)

        print("upc={0}".format(self.regs.UPC))

        #uop = urom[self.upc]

        self.regs.UPC +=1



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

for i in range(2):
    cpu.tick()


#import itertools
#for i, j, k in itertools.product(range(2), range(2), range(2)):
#    print("{} {} {} -> {}".format(i, j, k, (~(i ^ j) & (i ^ k))&1))
