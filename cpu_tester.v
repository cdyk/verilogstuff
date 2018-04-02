`include "ram.v"
`include "cpu.v"

`timescale 1ns/1ns

module tester(
		output reg clk
	);
	initial begin
		$dumpfile("foo.vcd");
		$dumpvars;
		clk = 0;
	#1000 $finish;
	end


	always begin
		#5 clk = !clk;
	end

endmodule

module testbench;
	wire [7:0] D;
	wire [15:0] A;
	wire clk;
	wire we;
	wire re;

	ram ram(D, A, clk, we, re);
	cpu cpu(D, A, we, re, clk);

	tester tester(clk);
endmodule
