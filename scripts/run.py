#!/usr/bin/env python3

import sys
import json

from utils.class_process import Process
from utils.class_memory import Memory

from utils.generate_lib import generate_lib
from utils.generate_lef import generate_lef
from utils.generate_verilog import generate_verilog

################################################################################
# RUN GENERATOR
#
# This is the main part of the script. It will read in the JSON configuration
# file, create a Cacti configuration file, run Cacti, extract the data from
# Cacti, and then generate the timing, physical and logical views for each SRAM
# found in the JSON configuration file.
################################################################################

def main ( argc, argv ):

  # Check the command line arguments
  if argc != 2:
    print('Usage: %s <json cfg>' % argv[0])
    sys.exit(1)

  # Load the JSON configuration file
  with open(argv[1], 'r') as fid:
    raw = [line.strip() for line in fid if not line.strip().startswith('#')]
  json_data = json.loads('\n'.join(raw))

  # Create a process object (shared by all srams)
  process = Process(json_data)

  # Go through each sram and generate the lib, lef and v files
  for sram_data in json_data['srams']:
    memory = Memory(process, sram_data)
    generate_lib(memory)
    generate_lef(memory)
    generate_verilog(memory)

### Entry point
if __name__ == '__main__':
  main( len(sys.argv), sys.argv )

