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
            'CARRY': 0,
            'ZERO': 0,
            'NEGATIVE': 0,
            'OVERFLOW': 0,
            'T0': True,
            'T1': False,
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

class DB_SRC:
    DL = object()       # DL/DB
    PCL = object()      # PCL/DB
    PCH = object(),     # PCH/DB
    SB = object(),      # SB/DB
    P = object()        # P/DB

class AI_SRC:
    SB = object()       # SB/ADD
    ZERO = object()     # O/ADD

class BI_SRC:
    DB = object()       # DB/ADD
    INV_DB = object()   # ~DB/ADD
    ADL = object()      # ADL/ADD

class ALU_OPS:
    SUM = object()
    OR = object()
    XOR = object()
    AND = object()
    SRS = object()

class CARRY_SRC:
    ACR = object()      # ACR/C
    KEEP = object()

class OVERFLOW_SRC:
    AVR = object()      # AVR/V
    KEEP = object()

class AB_SRC:
    DL_AB = object(),
    PC_AB = object(),
    S_AB = object(),
    ADD_AB = object(),

class PC_SRC:
    AB = object(),
    INC = object(),
    KEEP = object(),

class MEM_SRC:
    FETCH = object(),
    STORE = object(),
    KEEP = object()

class USelect:
    def __init__(self, t0=None, t1=None):
        self.t0 = t0
        self.t1 = t1

    def __eq__(self, other): 
        return self.__dict__ == other.__dict__

    def match(self, regs):
        return (
           self.t0 == None or self.t0 == regs.T0 and
           self.t1 == None or self.t1 == regs.T1
        )

class UDrive:
    def __init__(self,
                 sb = None,
                 db = None,
                 ai = None,
                 bi = None,
                 alu = None,
                 c = None,
                 v = None):
        self.sb = sb
        self.db = db
        self.ai = ai
        self.bi = bi
        self.alu = alu
        self.c = c
        self.v = v

    def merge(self, other):
        for key in self.__dict__:
            if other.__dict__[key] != None:
                assert self.__dict__[key] != None
                self.__dict__[key] = other.__dict__[key]
    
class UCode:
    lines = {
        USelect(): UDrive(),
        USelect(t0=True): UDrive()
    }


def special_bus(regs, src):
    return {
        SB_SRC.ADD: regs.ADD,
        SB_SRC.X: regs.X,
        SB_SRC.Y: regs.Y,
        SB_SRC.S: regs.S,
        None: 0,
    }[src]

def data_bus(regs, DL, SB, src):
    return {
        DB_SRC.DL: DL,
        DB_SRC.PCL: regs.PC & 255,
        DB_SRC.PCH: (regs.PC>>8) & 255,
        DB_SRC.SB: SB,
        DB_SRC.P: ((  1 if regs.CARRY    else 0) |
                   (  2 if regs.ZERO     else 0) |
                   ( 64 if regs.OVERFLOW else 0) |
                   (128 if regs.NEGATIVE else 0)),
        None: 0,
    }[src]

def program_counter(regs, AB, src):
    regs.PC = {
        PC_SRC.AB: AB,
        PC_SRC.INC: regs.PC + 1,
        PC_SRC.KEEP: regs.PC,
        None: regs.PC
    }[src]

def address_bus(regs, DL, src):
    return {
        AB_SRC.DL_AB: DL,
        AB_SRC.PC_AB: regs.PC,
        AB_SRC.S_AB: regs.S,
        AB_SRC.ADD_AB: regs.ADD,
        None: 0,
    }[src]

def input_reg_A(regs, SB, src):
    regs.AI = {
        AI_SRC.SB: SB,
        AI_SRC.ZERO: 0,
        None: 0
    }[src]

def input_reg_B(regs, DB, ADL, src):
    regs.BI = {
        BI_SRC.DB: DB,
        BI_SRC.INV_DB: (~DB) & 255 ,
        BI_SRC.ADL: ADL & 255,
        None: 0
    }[src]


def alu(regs, alu_ops):
    A = regs.AI
    B = regs.BI
    O = {
        ALU_OPS.SUM: (A + B + regs.CARRY), 
        ALU_OPS.OR:  (A | B),
        ALU_OPS.XOR: (A ^ B),
        ALU_OPS.AND: (A & B),
        ALU_OPS.SRS: (A << 1) | regs.CARRY,
        None: 0,
    }[alu_ops]
    i = 1 if A & 128 else 0
    j = 1 if B & 128 else 0
    k = 1 if O & 128 else 0
    AVR = (~(i ^ j) & (i ^ k))&1
    ACR = 1 if O & 256 else 0
    regs.ADD = O & 255
    return ACR, AVR

def mem_latch(regs, AB, mem, src):
    if src == MEM_SRC.FETCH:
        regs.MEM_I = mem[AB]
    elif src == MEM_SRC.STORE:
        mem[AB] = regs.MEM_O

def status_register(regs, ACR, AVR, carry_src, overflow_src):
    regs.CARRY = {
        CARRY_SRC.ACR: ACR,
        CARRY_SRC.KEEP, None: regs.CARRY,
    }[carry_src]
    regs.OVERFLOW = {
        OVERFLOW_SRC.AVR: AVR,
        OVERFLOW_SRC.KEEP, None: regs.OVERFLOW
    }[overflow_src]


class CPU:
    def __init__(self, ram):
        self.ram = ram
        self.regs = RegisterFile()

    def tick(self):
        self.regs.tick()

        drive = UDrive()
        for line in UCode.lines:
            if line.match(regs=self.regs):
                drive.merge(line)

        DL = 0  # Input data latch
        SB = special_bus(self.regs, drive.sb)
        DB = data_bus(self.regs, DL, SB, drive.db)
        AB = address_bus(self.regs, DL, drive.ab)
        program_counter(self.regs, AB, drive.pc)
        input_reg_A(self.regs, SB, drive.ai)
        input_reg_B(self.regs, DB, AB, drive.bi)
        ACR, AVR = alu(self.regs, drive.alu)
        status_register(self.regs, ACR, AVR, carry_src=drive.c, overflow_src=drive.v)


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
