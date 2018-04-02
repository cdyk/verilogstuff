
module cpu(
		inout wire [7:0] D,
		output reg [15:0] A,
		output reg we,
		output reg re,
		input wire clk
	);
	reg [7:0] d;	// 

	reg [15:0] pc;	// program counter
	reg [7:0] i;	// instruction
	reg [7:0] a;	// accumulator
	reg [7:0] x;	// x register
	reg [7:0] y;	// y register

	initial begin
		re = 0;
		we = 0;
		pc = 0;
	end

	assign D = we ? d : 8'bzzzzzzzz;

	always @(posedge clk) begin
		A = pc;
		re = 1;
		pc++;
	end

	always @(negedge clk) begin
		if(re) begin
			i = D;
			re = 0;			
		end
	end	

endmodule
