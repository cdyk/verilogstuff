// C:\iverilog\bin\iverilog.exe -o vga vga.v
// C:\iverilog\bin\vvp.exe vga

module clock_by_4(clk_out, rst, clk_in);
	output clk_out;
	input clk_in;
	input rst;
	wire clk_out;
	reg q0, q1;

	always @(posedge clk_in or posedge rst) begin
		if (rst) begin
			q0 <= 1'b0;
			q1 <= 1'b0;
		end
		else begin
			if(q0) q1 <= ~q1;
			q0 <= ~q0;
		end

	end
	assign clk_out = q1;
endmodule

module sync(
		output [13:0] hpos,
		output [13:0] vpos,
		output hsync,
		output vsync,
		output enable,
		input rst,
		input px_clk
	);
	parameter WIDTH = 640;
	parameter H_FRONT_PORCH = WIDTH + 16;
	parameter H_SYNC_PULSE = H_FRONT_PORCH + 96;
	parameter H_SIZE = 800;

	parameter HEIGHT = 480;
	parameter V_FRONT_PORCH = HEIGHT + 10;
	parameter V_SYNC_PULSE = V_FRONT_PORCH + 2;
	parameter V_SIZE = 525;

	reg [13:0] hpos;
	reg [13:0] vpos;
	wire sync;
	wire vsync;
	wire enable;

	always @(negedge px_clk or posedge rst) begin
		if(rst) begin
			hpos <= 0;
			vpos <= 0;
		end
		else begin
			if(hpos == H_SIZE-1) begin
				hpos <= 0;
				if(vpos == V_SIZE-1) begin
					vpos <= 0;
				end
				else begin
					vpos <= vpos + 1;
				end
			end
			else begin
				hpos <= hpos + 1;
			end
		end
	end
	assign hsync = hpos < H_FRONT_PORCH || H_SYNC_PULSE <= hpos ? 1 : 0;
	assign vsync = vpos < V_FRONT_PORCH || V_SYNC_PULSE <= vpos ? 1 : 0;
	assign enable = hpos < WIDTH && vpos < HEIGHT;
endmodule

// Period of 100 Mhz should be 10ns, so half of this to make clock do one full period.
`timescale 1ns/1ns

module tester(
		output rst,
		output clk,
		input px_clk,
		input [13:0] hpos,
		input [13:0] vpos,
		input hsync,
		input vsync,
		input enable
	);
	reg clk, rst;

	initial begin
		$dumpfile("foo.vcd");	// Dump results to file.
		$dumpvars;
		clk = 0;
		rst = 1;
	#1	rst = 0;
	#18000000 $finish;
	end

	always begin
	#5	clk = !clk;
	end
endmodule


module testbench;
	wire [13:0] hpos;
	wire [13:0] vpos;
	wire clk, rst, px_clk, q, qn;
	wire hsync, vsync, enable;

	clock_by_4 cdiv(px_clk, rst, clk);

	sync sync(hpos, vpos, hsync, vsync, enable, rst, px_clk);
	tester bar(rst, clk, px_clk, hpos, vpos, hsync, vsync, enable);
endmodule
