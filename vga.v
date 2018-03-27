// C:\iverilog\bin\iverilog.exe -o vga vga.v
// C:\iverilog\bin\vvp.exe vga

module vga(d, clk, q, qn);
	input d, clk;
	output q, qn;
	reg q, qn;

	initial	begin
		q = 0;
		qn = 0;
	end

	always @(posedge clk) begin
		q <= d;
		qn <= !d;
	end

endmodule

module tester(q, qn, clk, d);
	input q, qn;
	output clk, d;
	reg clk, d;

	initial begin
		clk = 0;
		$dumpfile("foo.vcd");	// Dump results to file.
		$dumpvars;
		d = 0;
	#9	d = 1;
	#1	d = 0;
	#1	d = 1;
	#2	d = 0;
	#1	d = 1;
	#12	d = 0;
	#1	d = 1;
	#2	d = 0;
	#1	d = 1;
	#1	d = 0;
	#1	d = 1;
	#1	d = 0;
	#7	d = 1;
	#8	$finish;
	end

	always begin
	#4	clk = !clk;
	end
endmodule


module testbench;
	wire clk, d, q, qn;
	vga foo(d, clk, q, qn);
	tester bar(q, qn, clk, d);
endmodule
