// C:\iverilog\bin\iverilog.exe -o vga vga.v
// C:\iverilog\bin\vvp.exe vga

module clock_by_4(
		output wire clk_pixel,	// Pixel output at rising edge, quarter of clk_base-
		output wire clk_sync,	// Is one clk_base pulse ahead of clk_pixel.
		input clk_base
	);
	reg q0 = 0;
	reg q1 = 0;

	always @(posedge clk_base) begin
		if(q0) q1 <= ~q1;
		q0 <= ~q0;
	end
	assign clk_pixel = q1;
	assign clk_sync = q1 ^ q0;
endmodule


module sync(
		output reg [13:0] hpos,
		output reg [13:0] vpos,
		output wire hsync,
		output wire vsync,
		output wire enable,
		input clk_pixel
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
		hpos = H_SIZE - 1;
		vpos = V_SIZE - 1;
	end

	always @(posedge clk_pixel) begin
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


module vidgen(
		output wire px_out,
		input [13:0] hpos,
		input [13:0] vpos,
		input clk_pixel,
		input enable
	);

	reg [7:0] store[7:0];
	initial begin
		// $readmemh("foo.hex", store, 0); 
		store[0] = 8'b00111000;
		store[1] = 8'b01101100;
		store[2] = 8'b11000110;
		store[3] = 8'b11111110;
		store[4] = 8'b11000110;
		store[5] = 8'b11000110;
		store[6] = 8'b11000110;
		store[7] = 8'b00000000;
	end

	reg [7:0] shiftdta = 0;

	always @(posedge clk_pixel) begin
		if(enable) begin
			if(hpos[2:0] == 3'd0) begin
				//shiftdta <= 8'haa;
				shiftdta[7:0] <= store[{vpos[2:0]}];
			end
			else begin
				shiftdta[7:0] <= {shiftdta[6:0], 1'b0};
			end
		end
		else shiftdta <= 0;
	end
	assign px_out = shiftdta[7];
endmodule



// Period of 100 Mhz should be 10ns, so half of this to make clock do one full period.
`timescale 1ns/1ns

module tester(
		output reg clk,
		input clk_pixel,
		input clk_sync,
		input [13:0] hpos,
		input [13:0] vpos,
		input hsync,
		input vsync,
		input enable,
		input px_out
	);
	initial begin
		$dumpfile("foo.vcd");	// Dump results to file.
		$dumpvars;
		clk = 0;
	#18000000 $finish;
	//#1800000 $finish;
	end

	always begin
	#5	clk = !clk;
	end
endmodule


module testbench;
	wire [13:0] hpos;
	wire [13:0] vpos;
	wire clk, clk_pixel, clk_sync, q, qn;
	wire hsync, vsync, enable;
	wire px_out;

	clock_by_4 cdiv(clk_pixel, clk_sync, clk);

	sync sync(hpos, vpos, hsync, vsync, enable,  clk_sync);
	vidgen vidgen(px_out, hpos, vpos, clk_pixel, enable);
	tester bar(clk, clk_pixel, clk_sync, hpos, vpos, hsync, vsync, enable, px_out);
endmodule
