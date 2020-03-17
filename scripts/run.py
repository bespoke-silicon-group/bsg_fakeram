#!/usr/bin/env python3

import sys
import json
import argparse

from utils.class_process import Process
from utils.class_memory import Memory

from utils.generate_lib import generate_lib
from utils.generate_lef import generate_lef
from utils.generate_verilog import generate_verilog
from utils.generate_verilog import generate_verilog_bb

################################################################################
# RUN GENERATOR
#
# This is the main part of the script. It will read in the JSON configuration
# file, create a Cacti configuration file, run Cacti, extract the data from
# Cacti, and then generate the timing, physical and logical views for each SRAM
# found in the JSON configuration file.
################################################################################

def get_args() -> argparse.Namespace:
    """
    Get command line arguments
    """
    parser = argparse.ArgumentParser(
        description="""
    BSG Black-box SRAM Generator --
    This project is designed to generate black-boxed SRAMs for use in CAD
    flows where either an SRAM generator is not avaible or doesn't
    exist.  """
    )

    parser.add_argument("config", help="JSON configuration file")

    parser.add_argument(
        "--output_dir", action="store", help="Output directory ", required=False, default=None
    )

    parser.add_argument(
        "--cacti_dir", action="store", help="CACTI installation directory ", required=False, default=None
    )

    return parser.parse_args()


def main ( args : argparse.Namespace):

  # Load the JSON configuration file
  with open(args.config, 'r') as fid:
    raw = [line.strip() for line in fid if not line.strip().startswith('#')]
  json_data = json.loads('\n'.join(raw))

  # Create a process object (shared by all srams)
  process = Process(json_data)

  # Go through each sram and generate the lib, lef and v files
  for sram_data in json_data['srams']:
    memory = Memory(process, sram_data, args.output_dir, args.cacti_dir)
    generate_lib(memory)
    generate_lef(memory)
    generate_verilog(memory)
    generate_verilog_bb(memory)

### Entry point
if __name__ == '__main__':
  args = get_args()
  main( args )

