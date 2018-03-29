// C:\iverilog\bin\iverilog.exe -o vga vga.v
// C:\iverilog\bin\vvp.exe vga

module clock_by_4(
		output wire clk_out,
		input clk_in
	);
	reg q0 = 0;
	reg q1 = 0;

	always @(posedge clk_in) begin
		if(q0) q1 <= ~q1;
		q0 <= ~q0;
	end
	assign clk_out = q1;
endmodule

module sync(
		output reg [13:0] hpos,
		output reg [13:0] vpos,
		output wire hsync,
		output wire vsync,
		output wire enable,
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

	initial begin
		hpos = 0;
		vpos = 0;
	end

	always @(negedge px_clk) begin
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
	assign hsync = hpos < H_FRONT_PORCH || H_SYNC_PULSE <= hpos ? 1 : 0;
	assign vsync = vpos < V_FRONT_PORCH || V_SYNC_PULSE <= vpos ? 1 : 0;
	assign enable = hpos < WIDTH && vpos < HEIGHT;
endmodule

// Period of 100 Mhz should be 10ns, so half of this to make clock do one full period.
`timescale 1ns/1ns

module tester(
		output reg clk,
		input px_clk,
		input [13:0] hpos,
		input [13:0] vpos,
		input hsync,
		input vsync,
		input enable
	);
	initial begin
		$dumpfile("foo.vcd");	// Dump results to file.
		$dumpvars;
		clk = 0;
	//#18000000 $finish;
	#1800000 $finish;
	end

	always begin
	#5	clk = !clk;
	end
endmodule


module testbench;
	wire [13:0] hpos;
	wire [13:0] vpos;
	wire clk, px_clk, q, qn;
	wire hsync, vsync, enable;

	clock_by_4 cdiv(px_clk, clk);

	sync sync(hpos, vpos, hsync, vsync, enable,  px_clk);
	tester bar(clk, px_clk, hpos, vpos, hsync, vsync, enable);
endmodule
