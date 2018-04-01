`include "ram.v"

`timescale 1ns/1ns

module tester(
		inout [7:0] D,
		output reg [15:0] A,
		output reg clk,
		output reg we,
		output reg re
	);
	reg [7:0] d;

	assign D = we ? d : 8'bzzzzzzzz;
	initial begin
		$dumpfile("foo.vcd");
		$dumpvars;
		clk = 0;
		we = 0;
		re = 0;
		A = 0;
		d = 0;
	#10
		d = 8'haa;
		A = 16'h0000;
		we = 1;
	#10
		we = 0;
		d = 8'hbb;
		A = 16'h0001;
		we = 1;
	#10
		we = 0;
		d = 8'h0c;
		A = 16'h0002;
		we = 1;
	#10
		we = 0;
		A = 0;
		re = 1;
	#10
		d = D;
		re = 0;
		A = 2;
		re = 1;
	#10
		d = D;
		re = 0;
		A = 1;
		re = 1;
	#10
		d = D;
		re = 0;


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

	tester tester(D, A, clk, we, re);
endmodule
