#include <cstdio>
#include <conio.h>
#include <cstdint>
#include <cassert>
#include <string>

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
  
  uCodeRomOpCodeMap[0xEA] = c;  // 0xEA: NOP
  uCodeRom[c++] = (UCode)(FETCH | AGU_PC_0 | PC_ADD_1 | UPC_SET );

  uCodeRomOpCodeMap[0x4C] = c;  // 0x4C: JMP #$xxxx
  uCodeRom[c++] = (UCode)(FETCH | AGU_PC_0 | PC_ADD_1 | UPC_NEXT);
  uCodeRom[c++] = (UCode)(FETCH | AGU_PC_0 | PC_ADD_1 | UPC_NEXT);
  uCodeRom[c++] = (UCode)(FETCH | AGU_PC_0 | PC_SET_L | UPC_SET);

  uCodeRomOpCodeMap[0xA2] = c;  // 0xA2: LDX #      - UNFINISHED
  uCodeRom[c++] = (UCode)(FETCH | AGU_PC_0 | PC_ADD_1 | UPC_NEXT);
  uCodeRom[c++] = (UCode)(FETCH | AGU_PC_0 | PC_ADD_1 | UPC_SET);

  uCodeRomOpCodeMap[0xCA] = c;  //  0xCA DEX        - UNFINISHED
  uCodeRom[c++] = (UCode)(FETCH | AGU_PC_0 | PC_ADD_1 | UPC_SET);

  uCodeRomOpCodeMap[0xD0] = c;  //  0xD0 BNE #$xx   - UNFINISHED
  uCodeRom[c++] = (UCode)(FETCH | AGU_PC_0 | PC_ADD_1 | UPC_NEXT);
  uCodeRom[c++] = (UCode)(FETCH | AGU_PC_0 | PC_ADD_1 | UPC_SET);


  c = 0;
  memory[c++] = 0xA2; // LDX #3
  memory[c++] = 0x03;

  auto l = c;

  memory[c++] = 0xEA; // NOP

  memory[c++] = 0xCA; // DEX

  memory[c++] = 0xD0; // BNE ??
  memory[c++] = l-c;

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
  case PC_ADD_0: next_pc_w = cpu.reg_l.pc;     printf("PC_ADD_0 ");  break;
  case PC_ADD_1: next_pc_w = cpu.reg_l.pc + 1; printf("PC_ADD_1 "); break;
  case PC_ADD_2: next_pc_w = cpu.reg_l.pc + 2; printf("PC_ADD_2 "); break;
  case PC_ADD_3: next_pc_w = cpu.reg_l.pc + 3; printf("PC_ADD_3 "); break;
  case PC_SET_L: next_pc_w = cpu.reg_l.L;      printf("PC_SET_L "); break;
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
  case UPC_NEXT: next_upc_w = cpu.reg_l.upc + 1;    printf("UPC_NEXT "); break;
  case UPC_SET:  next_upc_w = opcode_ucode_entry_w; printf("UPC_SET ");  break;
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

  printf("\n");
}

struct Print
{
  uint16_t PC = 0;
  uint16_t ui = 0;
  char buf[64] = { 0 };
  bool new_instruction = false;
};

void print(Print& p, CPU& cpu)
{
  if (p.new_instruction) {
    p.PC = cpu.reg_l.pc;
    p.ui = 0;

    p.buf[0] = '\0';
    switch (memory[p.PC]) {
    case 0x4C: snprintf(p.buf, sizeof(p.buf), "%02x %02x %02x  JMP %04x", memory[p.PC], memory[p.PC + 1], memory[p.PC + 2], memory[p.PC + 1] | (memory[p.PC + 2] << 8)); break;
    case 0xA2: snprintf(p.buf, sizeof(p.buf), "%02x %02x     LDX #%02x ", memory[p.PC], memory[p.PC + 1], memory[p.PC + 1]); break;
    case 0xCA: snprintf(p.buf, sizeof(p.buf), "%02x        DEX     ", memory[p.PC]); break;
    case 0xD0: snprintf(p.buf, sizeof(p.buf), "%02x %02x     BNE #%02x ", memory[p.PC], memory[p.PC + 1], memory[p.PC + 1]); break;
    case 0xEA: snprintf(p.buf, sizeof(p.buf), "%02x        NOP     ", memory[p.PC]); break;
    default:
      snprintf(p.buf, sizeof(p.buf), "%02x      ???", memory[p.PC]);
      break;
    }
  }
  else {
    snprintf(p.buf, sizeof(p.buf), "                  ");
  }
  p.new_instruction = cpu.reg_w.ucode & UPC_SET;
 
  printf("PC=%04x A=%02x  X=%02x  Y=%02x L=%04x    |    ",
         cpu.reg_l.pc,
         cpu.reg_l.A, cpu.reg_l.X, cpu.reg_l.Y, cpu.reg_l.L);

  printf("%04x@%d: %s  |  ", p.PC, p.ui++, p.buf);
}


int main(int argc, char** argv)
{
  init();

  CPU cpu;
  Print p;
  int ch;
  do {
    cpu.reg_l = cpu.reg_w;
    print(p, cpu);
    clock(cpu);
    while ((ch = _getch()) == 0);
  } while (ch != EOF || ch != 'q');

  return 0;
}