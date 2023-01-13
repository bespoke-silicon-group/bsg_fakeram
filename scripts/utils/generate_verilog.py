import os
import math

################################################################################
# GENERATE VERILOG VIEW
#
# Generate a .v file based on the given SRAM.
################################################################################

def generate_verilog(mem, tmChkExpand=False):
  '''Generate a verilog view for the RAM'''
  name  = str(mem.name)
  depth = int(mem.depth)
  bits  = int(mem.width_in_bits)
  addr_width = math.ceil(math.log2(depth))
  crpt_on_x = 1
  latch_last_read = int(mem.process.latch_last_read)

  # Generate the 'setuphold' timing checks
  setuphold_checks  = SH_LINE.format(sig='       we_in')
  setuphold_checks += SH_LINE.format(sig='       ce_in')
  if tmChkExpand: # per-bit checks
    for i in range(addr_width): setuphold_checks += SH_LINE.format(sig=f'  addr_in[{i}]')
    for i in range(      bits): setuphold_checks += SH_LINE.format(sig=f'    wd_in[{i}]')
    for i in range(      bits): setuphold_checks += SH_LINE.format(sig=f'w_mask_in[{i}]')
  else: # per-signal checks
    setuphold_checks += SH_LINE.format(sig='     addr_in')
    setuphold_checks += SH_LINE.format(sig='       wd_in')
    setuphold_checks += SH_LINE.format(sig='   w_mask_in')

  fout = os.sep.join([mem.results_dir, name + '.v'])
  with open(fout, 'w') as f:
    f.write(VLOG_TEMPLATE.format(name=name, data_width=bits, depth=depth, addr_width=addr_width, 
      crpt_on_x=crpt_on_x, latch_last_read=latch_last_read, setuphold_checks=setuphold_checks))

def generate_verilog_bb( mem ):
  '''Generate a verilog black-box view for the RAM'''
  name  = str(mem.name)
  depth = int(mem.depth)
  bits  = int(mem.width_in_bits)
  addr_width = math.ceil(math.log2(depth))
  crpt_on_x = 1

  fout = os.sep.join([mem.results_dir, name + '.bb.v'])
  with open(fout, 'w') as f:
    f.write(VLOG_BB_TEMPLATE.format(name=name, data_width=bits, depth=depth, addr_width=addr_width, 
      crpt_on_x=crpt_on_x))

# Template line for a 'setuphold' time check
SH_LINE = '      $setuphold (posedge clk, {sig}, 0, 0, notifier);\n'

# Template for a verilog 1rw RAM model
VLOG_TEMPLATE = '''\
module {name}
(
   rd_out,
   addr_in,
   we_in,
   wd_in,
   w_mask_in,
   clk,
   ce_in
);
   parameter BITS = {data_width};
   parameter WORD_DEPTH = {depth};
   parameter ADDR_WIDTH = {addr_width};
   parameter corrupt_mem_on_X_p = {crpt_on_x};
   parameter latch_last_read_p  = {latch_last_read};

   output reg [BITS-1:0]    rd_out;
   input  [ADDR_WIDTH-1:0]  addr_in;
   input                    we_in;
   input  [BITS-1:0]        wd_in;
   input  [BITS-1:0]        w_mask_in;
   input                    clk;
   input                    ce_in;

   reg    [BITS-1:0]        mem [0:WORD_DEPTH-1];

   integer j;

   always @(posedge clk)
   begin
      if (ce_in)
      begin
         //if ((we_in !== 1'b1 && we_in !== 1'b0) && corrupt_mem_on_X_p)
         if (corrupt_mem_on_X_p &&
             ((^we_in === 1'bx) || (^addr_in === 1'bx))
            )
         begin
            // WEN or ADDR is unknown, so corrupt entire array (using unsynthesizeable for loop)
            for (j = 0; j < WORD_DEPTH; j = j + 1)
               mem[j] <= 'x;
            $display("warning: ce_in=1, we_in is %b, addr_in = %x in fakeram_d64_w8", we_in, addr_in);
         end
         else if (we_in)
         begin
            mem[addr_in] <= (wd_in & w_mask_in) | (mem[addr_in] & ~w_mask_in);
         end
         // read
         rd_out <= mem[addr_in];
      end
      else
      begin
         // Make sure read fails if ce_in is low
         if (latch_last_read_p == 0) begin
            rd_out <= 'x;
        end
      end
   end

   // Timing check placeholders (will be replaced during SDF back-annotation)
   reg notifier;
   specify
      // Delay from clk to rd_out
      (posedge clk *> rd_out) = (0, 0);

      // Timing checks
      $width     (posedge clk,               0, 0, notifier);
      $width     (negedge clk,               0, 0, notifier);
      $period    (posedge clk,               0,    notifier);
{setuphold_checks}
   endspecify

endmodule
'''

# Template for a verilog 1rw RAM interface
VLOG_BB_TEMPLATE = '''\
module {name}
(
   rd_out,
   addr_in,
   we_in,
   wd_in,
   w_mask_in,
   clk,
   ce_in
);
   parameter BITS = {data_width};
   parameter WORD_DEPTH = {depth};
   parameter ADDR_WIDTH = {addr_width};
   parameter corrupt_mem_on_X_p = {crpt_on_x};

   output reg [BITS-1:0]    rd_out;
   input  [ADDR_WIDTH-1:0]  addr_in;
   input                    we_in;
   input  [BITS-1:0]        wd_in;
   input  [BITS-1:0]        w_mask_in;
   input                    clk;
   input                    ce_in;

endmodule
'''
