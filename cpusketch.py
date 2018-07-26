from enum import Enum, auto


class U(Enum):
    PRINT = auto()
    FETCH = auto()
    STORE = auto()
    ADDR_PC = auto()
    PC_INCR = auto()
    PC_SET = auto()
    UPC_SET = auto()
    UPC_NEXT = auto()

class CPU:
    urom = []

    ulut = {}
    for i in range(255):
        ulut[i] = 0

    ulut[0xEA] = len(urom)          # 0xEA: NOP
    urom.append({U.FETCH, U.ADDR_PC, U.PC_INCR, U.UPC_SET, U.PRINT })

    ulut[0x4C] = len(urom)          # 0x4C: JMP #$xxxx
    urom.append({U.FETCH, U.ADDR_PC, U.PC_INCR, U.UPC_NEXT, U.PRINT })
    urom.append({U.FETCH, U.ADDR_PC, U.PC_INCR, U.UPC_NEXT })
    urom.append({U.FETCH, U.ADDR_PC, U.PC_SET, U.UPC_SET })

    ulut[0xA2] = len(urom)          # 0xA2: LDX #      - UNFINISHED
    urom.append({U.FETCH, U.ADDR_PC, U.PC_INCR, U.UPC_NEXT, U.PRINT })
    urom.append({U.FETCH, U.ADDR_PC, U.PC_INCR, U.UPC_SET })

    ulut[0xCA] = len(urom)          # 0xCA: DEX        - UNFINISHED
    urom.append({ U.FETCH, U.ADDR_PC, U.PC_INCR, U.UPC_SET, U.PRINT })

    ulut[0xD0] = len(urom)          # 0xD0: BNE #$xx   - UNFINISHED
    urom.append({U.FETCH, U.ADDR_PC, U.PC_INCR, U.UPC_NEXT, U.PRINT })
    urom.append({U.FETCH, U.ADDR_PC, U.PC_INCR, U.UPC_SET })

    def __init__(self, ram):
        self.upc = 0
        self.ram = ram
        self.pc = 0
        self.A = 0
        self.X = 0
        self.Y = 0
        self.nA = 0
        self.nX = 0
        self.nY = 0

    def tick(self):
        print("upc={0}".format(self.upc))

        #uop = urom[self.upc]





        self.upc +=1


ram = []
ram += [0xA2, 0x03]                 # LDX #3
label = len(ram)
ram += [0xEA]                       # NOP
ram += [0xCA]                       # DEX
ram += [0xD0, ((label-(len(ram)+1))+256)%256]   # BNE label
ram += [0x4C, 0x00, 0x00]           # JMP #$0000


cpu = CPU(ram)

for i in range(10):
    cpu.tick()
