#!/usr/bin/python3

import os
import sys
import json
import math

from cacti_config import cacti_config
from generate_views import generate_lib_view
from generate_views import generate_lef_view
from generate_views import generate_verilog_view

# This script is going to take the CFG file and push it to Cacti
# to generate a CSV that will be used as one of the primary inputs
# to the SRAM generator to generate realistic black-box SRAMs.

import sys

def run_cacti ( argc, argv ):

  if argc != 2:
    print('Usage: %s <json cfg>' % argv[0])
    sys.exit(1)

  with open(argv[1], 'r') as fid:
    json_data = json.load(fid)
  
  tech_node_nm  = int(json_data['tech_nm'])
  minWidth_nm   = int(json_data['minWidth_nm'])
  minSpace_nm   = int(json_data['minSpace_nm'])
  metalPrefix   = str(json_data['metalPrefix'])

  for sram_data in json_data['srams']:
    name          = str(sram_data['name'])
    width_in_bits = int(sram_data['width'])
    depth         = int(sram_data['depth'] )

    # Currently only support 1RW, hopefully support 1R1W soon!
    #rw_ports      = int(argv[5] )
    #r_ports       = int(argv[6] )
    #w_ports       = int(argv[7] )
    rw_ports      = 1
    r_ports       = 0
    w_ports       = 0

    results_dir = 'results' + os.sep + name
    cacti_config_filename = 'cacti.cfg'
    tech_node_um = tech_node_nm / 1000.0
    width_in_bytes = math.ceil(width_in_bits / 8.0)
    size = width_in_bytes * depth

    # Create the results directory
    original_dir = os.getcwd()
    if not os.path.exists( results_dir ):
      os.makedirs( results_dir )
    os.chdir(results_dir)

    # Create the cacti configuration file
    with open(cacti_config_filename, 'w') as fid:
      fid.write('\n'.join(cacti_config).format(size, width_in_bytes, rw_ports, r_ports, w_ports, tech_node_um, width_in_bits))

    # Run cacti
    cacti_exe_str = os.environ['CACTI_BUILD_DIR'] + os.sep + 'cacti' + ' -infile ' + cacti_config_filename
    os.system( cacti_exe_str )

    # Read cacti CSV and extract data
    with open('out.csv', 'r') as fid:
      lines = [line for line in fid]
      csv_data = lines[1].split(',')

    width_um  = float(csv_data[21])*1000.0
    height_um = float(csv_data[22])*1000.0
    #height_um  = float(csv_data[21])*1000.0
    #width_um = float(csv_data[22])*1000.0
    area_um2  = width_um * height_um
    standby_leakage_per_bank_mW = float(csv_data[17])
    access_time_ns = float(csv_data[5])
    t_setup_ns = access_time_ns/4.0   ;# There has to be a better way...
    t_hold_ns  = access_time_ns/10.0  ;# There has to be a better way...
    dynamic_read_power_mW = float(csv_data[16])
    
    generate_lib_view( name, depth, width_in_bits, area_um2, width_um, height_um, standby_leakage_per_bank_mW, t_setup_ns, t_hold_ns, access_time_ns, dynamic_read_power_mW, 1, 1, 1 )
    generate_lef_view( name, depth, width_in_bits, width_um, height_um, minWidth_nm, minSpace_nm, metalPrefix )
    generate_verilog_view( name, depth, width_in_bits )

    os.chdir(original_dir)

if __name__ == '__main__':
  run_cacti( len(sys.argv), sys.argv )

