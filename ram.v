module ram(
		inout [7:0] D,			// Data lines.
		input [15:0] A,			// Address lines.
		input clk,
		input we,
		input re
	);

	reg [7:0] store [31:0];
	initial begin
		$readmemh("mem.dat", store);
	end

	assign D = we ? 8'bzzzzzzzz : store[A[7:0]];

	always @(posedge clk) begin
		if(we) begin
			store[A[7:0]] = D;
		end
	end


endmodule
