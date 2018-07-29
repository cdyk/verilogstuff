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

class SB_SRC:
    ADD = object()      # ADD/SB
    X = object()        # X/SB
    Y = object()        # Y/SB
    S = object()        # S/SB
    NONE = object()

class DB_SRC:
    DL = object()       # DL/DB
    PCL = object()      # PCL/DB
    PCH = object(),     # PCH/DB
    SB = object(),      # SB/DB
    P = object()        # P/DB
    NONE = object()

class AI_SRC:
    SB = object()       # SB/ADD
    ZERO = object()     # O/ADD
    NONE = object()     # don't care

class BI_SRC:
    DB = object()       # DB/ADD
    INV_DB = object()   # ~DB/ADD
    ADL = object()      # ADL/ADD
    NONE = object()     # don't care

class ALU_OPS:
    SUM = object()
    OR = object()
    XOR = object()
    AND = object()
    SRS = object()
    NONE = object()     # don't care

class CARRY_SRC:
    ACR = object()      # ACR/C
    NONE = object()

class OVERFLOW_SRC:
    AVR = object()      # AVR/V
    NONE = object()


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

def special_bus(regs, sb_src=SB_SRC.NONE):
    return {
        SB_SRC.ADD: regs.ADD,
        SB_SRC.X: regs.X,
        SB_SRC.Y: regs.Y,
        SB_SRC.S: regs.S,
        SB_SRC.NONE: 0,
    }[sb_src]

def data_bus(regs, DL, SB, db_src=DB_SRC.NONE):
    return {
        DB_SRC.DL: DL,
        DB_SRC.PCL: regs.PC & 255,
        DB_SRC.PCH: (regs.PC>>8) & 255,
        DB_SRC.SB: SB,
        DB_SRC.P: ((  1 if regs.CARRY    else 0) |
                   (  2 if regs.ZERO     else 0) |
                   ( 64 if regs.OVERFLOW else 0) |
                   (128 if regs.NEGATIVE else 0)),
        DB_SRC.NONE: 0,
    }[db_src]

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

def input_reg_A(regs, SB, ai_src=AI_SRC.NONE):
    regs.AI = {
        AI_SRC.SB: SB,
        AI_SRC.ZERO: 0,
        AI_SRC.NONE: 0
    }[ai_src]

def input_reg_B(regs, DB, ADL, bi_src=BI_SRC.NONE):
    regs.BI = {
        BI_SRC.DB: DB,
        BI_SRC.INV_DB: (~DB) & 255 ,
        BI_SRC.ADL: ADL & 255,
        BI_SRC.NONE: 0
    }[bi_src]


def alu(regs, alu_ops=ALU_OPS.NONE, acr_c=False, avr_v=False):
    A = regs.AI
    B = regs.BI
    O = {
        ALU_OPS.SUM: (A + B + regs.CARRY), 
        ALU_OPS.OR:  (A | B),
        ALU_OPS.XOR: (A ^ B),
        ALU_OPS.AND: (A & B),
        ALU_OPS.SRS: (A << 1) | regs.CARRY,
        ALU_OPS.NONE: 0,
    }[alu_ops]
    i = 1 if A & 128 else 0
    j = 1 if B & 128 else 0
    k = 1 if O & 128 else 0
    AVR = (~(i ^ j) & (i ^ k))&1
    ACR = 1 if O & 256 else 0
    regs.ADD = O & 255
    return ACR, AVR

def status_register(regs, ACR, AVR, carry_src, overflow_src):
    regs.CARRY = {
        CARRY_SRC.ACR: ACR,
        CARRY_SRC.NONE: regs.CARRY
    }[carry_src]
    regs.OVERFLOW = {
        OVERFLOW_SRC.AVR: AVR,
        OVERFLOW_SRC.NONE: regs.OVERFLOW
    }[overflow_src]

def program_counter(PC, inc_en, SP):
    pass

class CPU(MicroCode):
    def __init__(self, ram):
        self.ram = ram
        self.regs = RegisterFile()

    def tick(self):
        self.regs.tick()

        DL = 0  # Input data latch
        SB = special_bus(self.regs, sb_src=SB_SRC.NONE)
        DB = data_bus(self.regs, DL, SB, db_src=DB_SRC.NONE)
        ADL = address_bus_lo(self.regs, DL, dl_adl=False, pcl_adl=False, s_adl=False, add_adl=False)
        ADH = address_bus_hi(self.regs, DL, dl_adh=False, pch_adh=False)
        input_reg_A(self.regs, SB, ai_src=AI_SRC.NONE)
        input_reg_B(self.regs, DB, ADL, bi_src=BI_SRC.NONE)

        ACR, AVR = alu(self.regs, alu_ops=ALU_OPS.NONE)
        status_register(self.regs, ACR, AVR, carry_src=CARRY_SRC.NONE, overflow_src=OVERFLOW_SRC.NONE)


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
