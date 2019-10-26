import os
import math

################################################################################
# GENERATE VERILOG VIEW
#
# Generate a .v file based on the given SRAM.
################################################################################

def generate_verilog( mem ):

    name  = str(mem.name)
    depth = int(mem.depth)
    bits  = int(mem.width_in_bits)
    num_rwport = mem.rw_ports
    addr_width = math.ceil(math.log2(depth))

    V_file = open(os.sep.join([mem.results_dir, name + '.v']), 'w')

    V_file.write('module %s\n' % name)
    V_file.write('(\n')
    for i in range(int(num_rwport)) :
      V_file.write('   rd_out,\n')
    for i in range(int(num_rwport)) :
      V_file.write('   addr_in,\n')
    for i in range(int(num_rwport)) :
      V_file.write('   we_in,\n')
    for i in range(int(num_rwport)) :
      V_file.write('   wd_in,\n')
    for i in range(int(num_rwport)) :
      V_file.write('   w_mask_in,\n')
    V_file.write('   clk,\n')
    V_file.write('   ce_in\n')
    V_file.write(');\n')
    V_file.write('   parameter BITS = %s;\n' % str(bits))
    V_file.write('   parameter WORD_DEPTH = %s;\n' % str(depth))
    V_file.write('   parameter ADDR_WIDTH = %s;\n' % str(addr_width))
    V_file.write('   parameter corrupt_mem_on_X_p = 1;\n')
    V_file.write('\n')
    for i in range(int(num_rwport)) :
      V_file.write('   output reg [BITS-1:0]    rd_out;\n')
    for i in range(int(num_rwport)) :
      V_file.write('   input  [ADDR_WIDTH-1:0]  addr_in;\n')
    for i in range(int(num_rwport)) :
      V_file.write('   input                    we_in;\n')
    for i in range(int(num_rwport)) :
      V_file.write('   input  [BITS-1:0]        wd_in;\n')
    for i in range(int(num_rwport)) :
      V_file.write('   input  [BITS-1:0]        w_mask_in;\n')
    V_file.write('   input                    clk;\n')
    V_file.write('   input                    ce_in;\n')
    V_file.write('\n')
    V_file.write('   reg    [BITS-1:0]        mem [0:WORD_DEPTH-1];\n')
    V_file.write('\n')
    V_file.write('   integer j;\n')
    V_file.write('\n')
    V_file.write('   always @(posedge clk)\n')
    V_file.write('   begin\n')
    V_file.write('      if (ce_in)\n')
    V_file.write('      begin\n')
    for i in range(int(num_rwport)) :
      V_file.write("         //if ((we_in !== 1'b1 && we_in !== 1'b0) && corrupt_mem_on_X_p)\n")
      V_file.write('         if (corrupt_mem_on_X_p &&\n')
      V_file.write("             ((^we_in === 1'bx) || (^addr_in === 1'bx))\n")
      V_file.write('            )\n')
      V_file.write('         begin\n')
      V_file.write('            // WEN or ADDR is unknown, so corrupt entire array (using unsynthesizeable for loop)\n')
      V_file.write('            for (j = 0; j < WORD_DEPTH; j = j + 1)\n')
      V_file.write("               mem[j] <= 'x;\n")
      V_file.write('            $display("warning: ce_in=1, we_in is %b, addr_in = %x in ' + name + '", we_in, addr_in);\n')
      V_file.write('         end\n')
      V_file.write('         else if (we_in)\n')
      V_file.write('         begin\n')
      V_file.write('            mem[addr_in] <= (wd_in & w_mask_in) | (mem[addr_in] & ~w_mask_in);\n')
      V_file.write('         end\n')
    V_file.write('         // read\n')
    for i in range(int(num_rwport)) :
      V_file.write('         rd_out <= mem[addr_in];\n')
    V_file.write('      end\n')
    V_file.write('      else\n')
    V_file.write('      begin\n')
    V_file.write("         // Make sure read fails if ce_in is low\n")
    V_file.write("         rd_out <= 'x;\n")
    V_file.write('      end\n')
    V_file.write('   end\n')
    V_file.write('\n')
    V_file.write('   // Timing check placeholders (will be replaced during SDF back-annotation)\n')
    V_file.write('   reg notifier;\n')
    V_file.write('   specify\n')
    V_file.write('      // Delay from clk to rd_out\n')
    V_file.write('      (posedge clk *> rd_out) = (0, 0);\n')
    V_file.write('\n')
    V_file.write('      // Timing checks\n')
    V_file.write('      $width     (posedge clk,            0, 0, notifier);\n')
    V_file.write('      $width     (negedge clk,            0, 0, notifier);\n')
    V_file.write('      $period    (posedge clk,            0,    notifier);\n')
    V_file.write('      $setuphold (posedge clk, we_in,     0, 0, notifier);\n')
    V_file.write('      $setuphold (posedge clk, ce_in,     0, 0, notifier);\n')
    V_file.write('      $setuphold (posedge clk, addr_in,   0, 0, notifier);\n')
    V_file.write('      $setuphold (posedge clk, wd_in,     0, 0, notifier);\n')
    V_file.write('      $setuphold (posedge clk, w_mask_in, 0, 0, notifier);\n')
    V_file.write('   endspecify\n')
    V_file.write('\n')
    V_file.write('endmodule\n')

    V_file.close()
