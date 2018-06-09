#include <cstdio>
#include <conio.h>
#include <cstdint>
#include <cassert>

enum UCode
{

  AGU_PC_0 =   0 << 0,
  AGU_PC_1 = 1 << 0,
  AGU_PC_2 = 2 << 0,
  AGU_MASK = (AGU_PC_0 | AGU_PC_1 | AGU_PC_2),

  FETCH = 1 << 2,
  STORE = 1 << 3,

  RES_TO_L = 0 << 4,
  RES_TO_A = 1 << 4,
  RES_TO_X = 2 << 4,
  RES_TO_Y = 3 << 4,
  RES_MASK = (RES_TO_L | RES_TO_A| RES_TO_X| RES_TO_Y),

  ALU_ARG0_DATA = 0 << 6,
  ALU_ARG0_A    = 1 << 6,
  ALU_ARG0_X    = 2 << 6,
  ALU_ARG0_Y    = 3 << 6,
  ALU_ARG0_MASK = (ALU_ARG0_DATA | ALU_ARG0_A | ALU_ARG0_X | ALU_ARG0_Y),

  PC_ADD_0 = 0 << 27,
  PC_ADD_1 = 1 << 27,
  PC_ADD_2 = 2 << 27,
  PC_ADD_3 = 3 << 27,
  PC_SET_L = 4 << 27,
  PC_MASK = (PC_ADD_0 | PC_ADD_1 | PC_ADD_2 | PC_ADD_3 | PC_SET_L),

  UPC_NEXT = 0 << 30,    // increase upc by one.
  UPC_SET = 1 << 30,    // set next upc from instruction decode (end of instruction).
  UPC_MASK = (UPC_NEXT | UPC_SET)
};

typedef uint16_t UPC;

struct Registers
{
  uint8_t A = 0;
  uint8_t X = 0;
  uint8_t Y = 0;
  uint16_t L = 0;
  uint16_t pc = 0;
  UCode ucode = (UCode)(FETCH | AGU_PC_0 | UPC_SET);
  UPC upc = 0;
};

struct CPU
{
  Registers reg_l;  // latched, read
  Registers reg_w;  // wire, write
};

UCode uCodeRom[0x10000] = { (UCode)(UPC_SET | PC_ADD_1) };
uint16_t uCodeRomOpCodeMap[256] = { 0 };

uint8_t memory[0x10000] = { 0 };

void init()
{
  uint16_t c = 0;
  // 0xEA: NOP
  uCodeRomOpCodeMap[0xEA] = c;  // NOP
  uCodeRom[c++] = (UCode)(FETCH | UPC_SET | PC_ADD_1);

  // 0x4C: JMP a
  uCodeRomOpCodeMap[0x4C] = c;  // JMP addr
  uCodeRom[c++] = (UCode)(FETCH | AGU_PC_0 | PC_ADD_1 | UPC_NEXT);
  uCodeRom[c++] = (UCode)(FETCH | AGU_PC_0 | PC_ADD_1 | UPC_NEXT);
  uCodeRom[c++] = (UCode)(FETCH | UPC_SET | PC_SET_L);


  // 0xA9: LDA # 


  c = 0;
  memory[c++] = 0xEA; // NOP
  memory[c++] = 0x4c; // JMP #$0000
  memory[c++] = 0x00;
  memory[c++] = 0x00;


}

uint16_t runAGU(CPU& cpu, uint16_t next_pc_w)
{
  uint16_t x;
  uint8_t y;
  switch (cpu.reg_l.ucode & AGU_MASK) {
  case AGU_PC_0: x = next_pc_w; y = 0;  break;
  case AGU_PC_1: x = next_pc_w; y = 1; break;
  case AGU_PC_2: x = next_pc_w; y = 2; break;
  default: assert(false);
  }
  return x + y;
}

uint8_t runMemRead(CPU& cpu, uint16_t addr_w)
{
  if (cpu.reg_l.ucode & FETCH) return memory[addr_w];
  else return 0;
}

void clock(CPU& cpu)
{
  // set up PC for next instruction
  uint16_t next_pc_w;
  switch (cpu.reg_l.ucode & PC_MASK) {
  case PC_ADD_0: next_pc_w = cpu.reg_l.pc;     printf("PC_ADD_0\n");  break;
  case PC_ADD_1: next_pc_w = cpu.reg_l.pc + 1; printf("PC_ADD_1\n"); break;
  case PC_ADD_2: next_pc_w = cpu.reg_l.pc + 2; printf("PC_ADD_2\n"); break;
  case PC_ADD_3: next_pc_w = cpu.reg_l.pc + 3; printf("PC_ADD_3\n"); break;
  case PC_SET_L: next_pc_w = cpu.reg_l.L;      printf("PC_SET_L\n"); break;
  default: assert(false);
  }
  cpu.reg_w.pc = next_pc_w;

  uint16_t addr_w = runAGU(cpu, next_pc_w);

  uint8_t data_r = runMemRead(cpu, addr_w);

  uint16_t opcode_ucode_entry_w = uCodeRomOpCodeMap[data_r];

  // set up pc for next clock
  uint16_t next_upc_w;
  switch (cpu.reg_l.ucode & UPC_MASK)
  {
  case UPC_NEXT: next_upc_w = cpu.reg_l.upc + 1;    printf("UPC_NEXT\n"); break;
  case UPC_SET:  next_upc_w = opcode_ucode_entry_w; printf("UPC_SET\n");  break;
  default: assert(false);
  }
  cpu.reg_w.upc = next_upc_w;

  // set up ucode for next clock
  cpu.reg_w.ucode = uCodeRom[next_upc_w];


  uint8_t alu_res_w = data_r; // no alu op yet

  // do something with alu result.
  switch (cpu.reg_l.ucode & RES_MASK)
  {
  case RES_TO_L: cpu.reg_w.L = (cpu.reg_l.L >> 8) | (alu_res_w << 8); break;
  case RES_TO_A: cpu.reg_w.A = alu_res_w; break;
  case RES_TO_X: cpu.reg_w.X = alu_res_w; break;
  case RES_TO_Y: cpu.reg_w.Y = alu_res_w; break;
  default: assert(false);
  }

  auto a = 1;
}

void print(CPU& cpu)
{
  printf("----    PC=%04x A=%02x  X=%02x  Y=%02x L=%04x upc=%04x ucode=%08x\n",
         cpu.reg_w.pc,
         cpu.reg_w.A, cpu.reg_w.X, cpu.reg_w.Y, cpu.reg_w.L,
         cpu.reg_w.upc, cpu.reg_w.ucode);

}


int main(int argc, char** argv)
{
  init();

  CPU cpu;
  int ch;
  print(cpu);
  do {
    cpu.reg_l = cpu.reg_w;
    clock(cpu);
    print(cpu);
    while ((ch = _getch()) == 0);
  } while (ch != EOF || ch != 'q');

  return 0;
}