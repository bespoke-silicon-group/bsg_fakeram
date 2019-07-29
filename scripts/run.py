#!/usr/bin/python3

import os
import sys
import json
import math
import time
import datetime

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
    json_data = json.load(fid)
  
  tech_node_nm  = int(json_data['tech_nm'])
  minWidth_nm   = int(json_data['minWidth_nm'])
  minSpace_nm   = int(json_data['minSpace_nm'])
  metalPrefix   = str(json_data['metalPrefix'])
  voltage       = str(json_data['voltage'])

  tech_node_um  = tech_node_nm / 1000.0
  minWidth_um   = minWidth_nm  / 1000.0
  minSpace_um   = minSpace_nm  / 1000.0

  for sram_data in json_data['srams']:

    name          = str(sram_data['name'])
    width_in_bits = int(sram_data['width'])
    depth         = int(sram_data['depth'] )
    rw_ports      = 1

    width_in_bytes = math.ceil(width_in_bits / 8.0)
    total_size = width_in_bytes * depth

    results_dir = 'results' + os.sep + name
    cacti_config_filename = 'cacti.cfg'

    # Create the results directory
    if not os.path.exists( results_dir ):
      os.makedirs( results_dir )

    # Change directory to results directory
    original_dir = os.getcwd()
    os.chdir(results_dir)

    # Create the cacti configuration file
    with open( cacti_config_filename, 'w' ) as fid:
      fid.write( '\n'.join(cacti_config).format(total_size, width_in_bytes, rw_ports, 0, 0, tech_node_um, width_in_bits) )

    # Run cacti
    os.system( os.environ['CACTI_BUILD_DIR'] + os.sep + 'cacti' + ' -infile ' + cacti_config_filename )

    # Read cacti CSV and extract data
    with open( 'out.csv', 'r' ) as fid:
      lines = [line for line in fid]
      csv_data = lines[1].split(',')

    # Grab values from the Cacti CSV file
    width_um                    = float(csv_data[21])*1000.0
    height_um                   = float(csv_data[22])*1000.0
    standby_leakage_per_bank_mW = float(csv_data[17])
    access_time_ns              = float(csv_data[5])
    cycle_time_ns               = float(csv_data[6])
    dynamic_read_power_mW       = float(csv_data[16])
    cap_input_pf                = float(csv_data[57])
    cap_output_pf               = float(csv_data[58])

    area_um2  = width_um * height_um

    pin_dynamic_power_mW = 1.0

    # TODO: Figure out the best way to come up with these numbers!!!
    t_setup_ns = access_time_ns/4.0
    t_hold_ns  = access_time_ns/10.0

    # Generate the timing, physical and logic views
    generate_lib_view( name, depth, width_in_bits, area_um2, width_um, height_um, standby_leakage_per_bank_mW, t_setup_ns, t_hold_ns, access_time_ns, dynamic_read_power_mW, pin_dynamic_power_mW, cap_input_pf, cap_output_pf, voltage, cycle_time_ns )
    generate_lef_view( name, depth, width_in_bits, width_um, height_um, minWidth_um, minSpace_um, metalPrefix )
    generate_verilog_view( name, depth, width_in_bits )

    # Back to original working directory
    os.chdir(original_dir)

################################################################################
# GENERATE LIBERTY VIEW
#
# Generate a .lib file based on the timing and power information (and a little
# bit of the area information) provided from Cacti for the SRAM.
################################################################################

def generate_lib_view( name, depth, bits, area, x, y, leakage, tsetup, thold, tcq, pdynamic, pindynamic, min_driver_in_cap, min_driver_out_cap, voltage, max_period ):

  # Make sure the data types are correct
  name              = str(name)
  depth             = int(depth)
  bits              = int(bits)
  area              = float(area)
  x                 = float(x)
  y                 = float(y)
  leakage           = float(leakage)
  tsetup            = float(tsetup)
  thold             = float(thold)
  tcq               = float(tcq)
  pdynamic          = float(pdynamic)
  pindynamic        = float(pindynamic)
  min_driver_in_cap = float(min_driver_in_cap)
  min_driver_out_cap= float(min_driver_out_cap)
  voltage           = float(voltage)

  # Only support 1RW srams. At some point, expose these as well!
  num_rwport = 1

  # Number of bits for address
  addr_width    = math.ceil(math.log2(depth))
  addr_width_m1 = addr_width-1

  # Get the date
  d = datetime.date.today()
  date = d.isoformat()
  current_time = time.strftime("%H:%M:%SZ", time.gmtime())

  # TODO: Arbitrary indicies for the NLDM table. This is used for Clk->Q arcs
  # as well as setup/hold times. We only have a single value for these, there
  # are two options. 1. adding some sort of static variation of the single
  # value for each table entry, 2. use the same value so all interpolated
  # values are the same. The 1st is more realistic but depend on good variation
  # values which is process sepcific and I don't have a strategy for
  # determining decent variation values without breaking NDA so right now we
  # have no variations.
  #
  # The table indicies are main min/max values for interpolation. The tools
  # typically don't like extrapolation so a large range is nice, but makes the
  # single value strategy described above even more unrealistic.
  #
  slew_indicies = '0.01, 0.5'    # input pin transisiton [ns]
  load_indicies = '0.001, 0.500' # output capacitance [pF]

  # Start generating the LIB file

  LIB_file = open(name + '.lib', 'w')

  LIB_file.write( 'library(%s) {\n' % name)
  LIB_file.write( '    technology (cmos);\n')
  LIB_file.write( '    delay_model : table_lookup;\n')
  LIB_file.write( '    revision : 1.0;\n')
  LIB_file.write( '    date : "%s %s";\n' % (date, current_time))
  LIB_file.write( '    comment : "SRAM";\n')
  LIB_file.write( '    time_unit : "1ns";\n')
  LIB_file.write( '    voltage_unit : "1V";\n')
  LIB_file.write( '    current_unit : "1mA";\n')
  LIB_file.write( '    leakage_power_unit : "1mW";\n')
  LIB_file.write( '    nom_process : 1;\n')
  LIB_file.write( '    nom_temperature : 25.000;\n')
  LIB_file.write( '    nom_voltage : %s;\n' % voltage)
  LIB_file.write( '    capacitive_load_unit (1,pf);\n\n')
  LIB_file.write( '    pulling_resistance_unit : "1kohm";\n\n')
  LIB_file.write( '    operating_conditions(tt_1.0_25.0) {\n')
  LIB_file.write( '        process : 1;\n')
  LIB_file.write( '        temperature : 25.000;\n')
  LIB_file.write( '        voltage : %s;\n' % voltage)
  LIB_file.write( '        tree_type : balanced_tree;\n')
  LIB_file.write( '    }\n')
  LIB_file.write( '\n')

  LIB_file.write( '    /* default attributes */\n')
  LIB_file.write( '    default_cell_leakage_power : 0;\n')
  LIB_file.write( '    default_fanout_load : 1;\n')
  LIB_file.write( '    default_inout_pin_cap : 0.0;\n')
  LIB_file.write( '    default_input_pin_cap : 0.0;\n')
  LIB_file.write( '    default_output_pin_cap : 0.0;\n')
  LIB_file.write( '    default_input_pin_cap : 0.0;\n')
  LIB_file.write( '    default_max_transition : 0.0;\n\n')
  LIB_file.write( '    default_operating_conditions : tt_1.0_25.0;\n')
  LIB_file.write( '    default_leakage_power_density : 0.0;\n')
  LIB_file.write( '\n')

  LIB_file.write( '    /* additional header data */\n')
  LIB_file.write( '    slew_derate_from_library : 1.000;\n')
  LIB_file.write( '    slew_lower_threshold_pct_fall : 10.000;\n')
  LIB_file.write( '    slew_upper_threshold_pct_fall : 90.000;\n')
  LIB_file.write( '    slew_lower_threshold_pct_rise : 10.000;\n')
  LIB_file.write( '    slew_upper_threshold_pct_rise : 90.000;\n')
  LIB_file.write( '    input_threshold_pct_fall : 50.000;\n')
  LIB_file.write( '    input_threshold_pct_rise : 50.000;\n')
  LIB_file.write( '    output_threshold_pct_fall : 50.000;\n')
  LIB_file.write( '    output_threshold_pct_rise : 50.000;\n\n')
  LIB_file.write( '\n')

  #  LIB_file.write( '    /* k-factors */\n')
  #  LIB_file.write( '    k_process_cell_fall : 1;\n')
  #  LIB_file.write( '    k_process_cell_leakage_power : 0;\n')
  #  LIB_file.write( '    k_process_cell_rise : 1;\n')
  #  LIB_file.write( '    k_process_fall_transition : 1;\n')
  #  LIB_file.write( '    k_process_hold_fall : 1;\n')
  #  LIB_file.write( '    k_process_hold_rise : 1;\n')
  #  LIB_file.write( '    k_process_internal_power : 0;\n')
  #  LIB_file.write( '    k_process_min_pulse_width_high : 1;\n')
  #  LIB_file.write( '    k_process_min_pulse_width_low : 1;\n')
  #  LIB_file.write( '    k_process_pin_cap : 0;\n')
  #  LIB_file.write( '    k_process_recovery_fall : 1;\n')
  #  LIB_file.write( '    k_process_recovery_rise : 1;\n')
  #  LIB_file.write( '    k_process_rise_transition : 1;\n')
  #  LIB_file.write( '    k_process_setup_fall : 1;\n')
  #  LIB_file.write( '    k_process_setup_rise : 1;\n')
  #  LIB_file.write( '    k_process_wire_cap : 0;\n')
  #  LIB_file.write( '    k_process_wire_res : 0;\n')
  #  LIB_file.write( '    k_temp_cell_fall : 0.000;\n')
  #  LIB_file.write( '    k_temp_cell_rise : 0.000;\n')
  #  LIB_file.write( '    k_temp_hold_fall : 0.000;\n')
  #  LIB_file.write( '    k_temp_hold_rise : 0.000;\n')
  #  LIB_file.write( '    k_temp_min_pulse_width_high : 0.000;\n')
  #  LIB_file.write( '    k_temp_min_pulse_width_low : 0.000;\n')
  #  LIB_file.write( '    k_temp_min_period : 0.000;\n')
  #  LIB_file.write( '    k_temp_rise_propagation : 0.000;\n')
  #  LIB_file.write( '    k_temp_fall_propagation : 0.000;\n')
  #  LIB_file.write( '    k_temp_rise_transition : 0.0;\n')
  #  LIB_file.write( '    k_temp_fall_transition : 0.0;\n')
  #  LIB_file.write( '    k_temp_recovery_fall : 0.000;\n')
  #  LIB_file.write( '    k_temp_recovery_rise : 0.000;\n')
  #  LIB_file.write( '    k_temp_setup_fall : 0.000;\n')
  #  LIB_file.write( '    k_temp_setup_rise : 0.000;\n')
  #  LIB_file.write( '    k_volt_cell_fall : 0.000;\n')
  #  LIB_file.write( '    k_volt_cell_rise : 0.000;\n')
  #  LIB_file.write( '    k_volt_hold_fall : 0.000;\n')
  #  LIB_file.write( '    k_volt_hold_rise : 0.000;\n')
  #  LIB_file.write( '    k_volt_min_pulse_width_high : 0.000;\n')
  #  LIB_file.write( '    k_volt_min_pulse_width_low : 0.000;\n')
  #  LIB_file.write( '    k_volt_min_period : 0.000;\n')
  #  LIB_file.write( '    k_volt_rise_propagation : 0.000;\n')
  #  LIB_file.write( '    k_volt_fall_propagation : 0.000;\n')
  #  LIB_file.write( '    k_volt_rise_transition : 0.0;\n')
  #  LIB_file.write( '    k_volt_fall_transition : 0.0;\n')
  #  LIB_file.write( '    k_volt_recovery_fall : 0.000;\n')
  #  LIB_file.write( '    k_volt_recovery_rise : 0.000;\n')
  #  LIB_file.write( '    k_volt_setup_fall : 0.000;\n')
  #  LIB_file.write( '    k_volt_setup_rise : 0.000;\n')
  #  LIB_file.write( '\n')

  LIB_file.write( '    lu_table_template(%s_mem_out_delay_template) {\n' % name )
  LIB_file.write( '        variable_1 : input_net_transition;\n')
  LIB_file.write( '        variable_2 : total_output_net_capacitance;\n')
  LIB_file.write( '            index_1 ("1000, 1001");\n')
  LIB_file.write( '            index_2 ("1000, 1001");\n')
  LIB_file.write( '    }\n')
  LIB_file.write( '    lu_table_template(%s_mem_out_slew_template) {\n' % name )
  LIB_file.write( '        variable_1 : total_output_net_capacitance;\n')
  LIB_file.write( '            index_1 ("1000, 1001");\n')
  LIB_file.write( '    }\n')
  LIB_file.write( '    lu_table_template(%s_constraint_template) {\n' % name )
  LIB_file.write( '        variable_1 : related_pin_transition;\n')
  LIB_file.write( '        variable_2 : constrained_pin_transition;\n')
  LIB_file.write( '            index_1 ("1000, 1001");\n')
  LIB_file.write( '            index_2 ("1000, 1001");\n')
  LIB_file.write( '    }\n')
  LIB_file.write( '    power_lut_template(%s_energy_template_clkslew) {\n' % name )
  LIB_file.write( '        variable_1 : input_transition_time;\n')
  LIB_file.write( '            index_1 ("1000, 1001");\n')
  LIB_file.write( '    }\n')
  LIB_file.write( '    power_lut_template(%s_energy_template_sigslew) {\n' % name )
  LIB_file.write( '        variable_1 : input_transition_time;\n')
  LIB_file.write( '            index_1 ("1000, 1001");\n')
  LIB_file.write( '    }\n')
  LIB_file.write( '    library_features(report_delay_calculation);\n')
  LIB_file.write( '    type (%s_DATA) {\n' % name )
  LIB_file.write( '        base_type : array ;\n')
  LIB_file.write( '        data_type : bit ;\n')
  LIB_file.write( '        bit_width : %d;\n' % bits)
  LIB_file.write( '        bit_from : %d;\n' % (int(bits)-1))
  LIB_file.write( '        bit_to : 0 ;\n')
  LIB_file.write( '        downto : true ;\n')
  LIB_file.write( '    }\n')
  LIB_file.write( '    type (%s_ADDRESS) {\n' % name)
  LIB_file.write( '        base_type : array ;\n')
  LIB_file.write( '        data_type : bit ;\n')
  LIB_file.write( '        bit_width : %d;\n' % addr_width)
  LIB_file.write( '        bit_from : %d;\n' % addr_width_m1)
  LIB_file.write( '        bit_to : 0 ;\n')
  LIB_file.write( '        downto : true ;\n')
  LIB_file.write( '    }\n')

  LIB_file.write( 'cell(%s) {\n' % name )
  LIB_file.write( '    area : %.3f;\n' % area)
  #LIB_file.write( '    dont_use : true;\n')
  #LIB_file.write( '    dont_touch : true;\n')
  LIB_file.write( '    interface_timing : true;\n')
  LIB_file.write( '    memory() {\n')
  LIB_file.write( '        type : ram;\n')
  LIB_file.write( '        address_width : %d;\n' % addr_width)
  LIB_file.write( '        word_width : %d;\n' % bits)
  LIB_file.write( '    }\n')

  LIB_file.write('    pin(clk)   {\n')
  LIB_file.write('        direction : input;\n')
  LIB_file.write('        capacitance : %.3f;\n' % (min_driver_in_cap*2.5)) ;# Clk pin is usually high cap, somewhere between an X2 and X3 feels about right.
  LIB_file.write('        clock : true;\n')
  #LIB_file.write('        max_transition : 0.01;\n') # Max rise/fall time
  LIB_file.write('        min_pulse_width_high : %.3f ;\n' % (max_period*0.01))
  LIB_file.write('        min_pulse_width_low  : %.3f ;\n' % (max_period*0.01))
  LIB_file.write('        min_period           : %.3f ;\n' % (max_period))
  #LIB_file.write('        minimum_period(){\n')
  #LIB_file.write('            constraint : %.3f ;\n' % max_period)
  #LIB_file.write('            when : "1";\n')
  #LIB_file.write('            sdf_cond : "1";\n')
  #LIB_file.write('        }\n')
  LIB_file.write('        internal_power(){\n')
  LIB_file.write('            rise_power(%s_energy_template_clkslew) {\n' % name)
  LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
  LIB_file.write('                values ("%.3f, %.3f")\n' % (pdynamic, pdynamic))
  LIB_file.write('            }\n')
  LIB_file.write('            fall_power(%s_energy_template_clkslew) {\n' % name)
  LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
  LIB_file.write('                values ("%.3f, %.3f")\n' % (pdynamic, pdynamic))
  LIB_file.write('            }\n')
  LIB_file.write('        }\n')
  LIB_file.write('    }\n')
  LIB_file.write('\n')

  for i in range(int(num_rwport)) :
    LIB_file.write('    bus(rd_out)   {\n')
    LIB_file.write('        bus_type : %s_DATA;\n' % name)
    LIB_file.write('        direction : output;\n')
    LIB_file.write('        max_capacitance : %.3f;\n' % (min_driver_in_cap*32))
    LIB_file.write('        memory_read() {\n')
    LIB_file.write('            address : addr_in;\n')
    LIB_file.write('        }\n')
    LIB_file.write('        timing() {\n')
    LIB_file.write('            related_pin : "clk" ;\n')
    LIB_file.write('            timing_type : rising_edge;\n')
    LIB_file.write('            timing_sense : non_unate;\n')
    LIB_file.write('            cell_rise(%s_mem_out_delay_template) {\n' % name)
    LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
    LIB_file.write('                index_2 ("%s");\n' % load_indicies)
    LIB_file.write('                values ( \\\n')
    LIB_file.write('                  "%.3f, %.3f", \\\n' % (tcq, tcq))
    LIB_file.write('                  "%.3f, %.3f" \\\n' % (tcq, tcq))
    LIB_file.write('                )\n')
    LIB_file.write('            }\n')
    LIB_file.write('            cell_fall(%s_mem_out_delay_template) {\n' % name)
    LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
    LIB_file.write('                index_2 ("%s");\n' % load_indicies)
    LIB_file.write('                values ( \\\n')
    LIB_file.write('                  "%.3f, %.3f", \\\n' % (tcq, tcq))
    LIB_file.write('                  "%.3f, %.3f" \\\n' % (tcq, tcq))
    LIB_file.write('                )\n')
    LIB_file.write('            }\n')
    LIB_file.write('            rise_transition(%s_mem_out_slew_template) {\n' % name)
    LIB_file.write('                index_1 ("%s");\n' % load_indicies)
    LIB_file.write('                values ("%s")\n' % '0.05, 1.00')
    LIB_file.write('            }\n')
    LIB_file.write('            fall_transition(%s_mem_out_slew_template) {\n' % name)
    LIB_file.write('                index_1 ("%s");\n' % load_indicies)
    LIB_file.write('                values ("%s")\n' % '0.05, 1.00')
    LIB_file.write('            }\n')
    LIB_file.write('        }\n')
    LIB_file.write('    }\n')

  for i in range(int(num_rwport)) :
    LIB_file.write('    pin(we_in){\n')
    LIB_file.write('        direction : input;\n')
    LIB_file.write('        capacitance : %.3f;\n' % (min_driver_in_cap))
    LIB_file.write('        timing() {\n')
    LIB_file.write('            related_pin : clk;\n')
    LIB_file.write('            timing_type : setup_rising ;\n')
    LIB_file.write('            rise_constraint(%s_constraint_template) {\n' % name)
    LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
    LIB_file.write('                index_2 ("%s");\n' % slew_indicies)
    LIB_file.write('                values ( \\\n')
    LIB_file.write('                  "%.3f, %.3f", \\\n' % (tsetup, tsetup))
    LIB_file.write('                  "%.3f, %.3f" \\\n'  % (tsetup, tsetup))
    LIB_file.write('                )\n')
    LIB_file.write('            }\n')
    LIB_file.write('            fall_constraint(%s_constraint_template) {\n' % name)
    LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
    LIB_file.write('                index_2 ("%s");\n' % slew_indicies)
    LIB_file.write('                values ( \\\n')
    LIB_file.write('                  "%.3f, %.3f", \\\n' % (tsetup, tsetup))
    LIB_file.write('                  "%.3f, %.3f" \\\n'  % (tsetup, tsetup))
    LIB_file.write('                )\n')
    LIB_file.write('            }\n')
    LIB_file.write('        } \n')
    LIB_file.write('        timing() {\n')
    LIB_file.write('            related_pin : clk;\n')
    LIB_file.write('            timing_type : hold_rising ;\n')
    LIB_file.write('            rise_constraint(%s_constraint_template) {\n' % name)
    LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
    LIB_file.write('                index_2 ("%s");\n' % slew_indicies)
    LIB_file.write('                values ( \\\n')
    LIB_file.write('                    "0.000, 0.000", \\\n')
    LIB_file.write('                    "0.000, 0.000" \\\n')
    LIB_file.write('                )\n')
    LIB_file.write('            }\n')
    LIB_file.write('            fall_constraint(%s_constraint_template) {\n' % name)
    LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
    LIB_file.write('                index_2 ("%s");\n' % slew_indicies)
    LIB_file.write('                values ( \\\n')
    LIB_file.write('                    "0.000, 0.000", \\\n')
    LIB_file.write('                    "0.000, 0.000" \\\n')
    LIB_file.write('                )\n')
    LIB_file.write('            }\n')
    LIB_file.write('        }\n')
    LIB_file.write('        internal_power(){\n')
    LIB_file.write('            rise_power(%s_energy_template_sigslew) {\n' % name)
    LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
    LIB_file.write('                values ("%.3f, %.3f")\n' % ((pindynamic), (pindynamic)))
    LIB_file.write('            }\n')
    LIB_file.write('            fall_power(%s_energy_template_sigslew) {\n' % name)
    LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
    LIB_file.write('                values ("%.3f, %.3f")\n' % ((pindynamic), (pindynamic)))
    LIB_file.write('            }\n')
    LIB_file.write('        }\n')
    LIB_file.write('    }\n')

  LIB_file.write('    pin(ce_in){\n')
  LIB_file.write('        direction : input;\n')
  LIB_file.write('        capacitance : %.3f;\n' % (min_driver_in_cap))
  LIB_file.write('        timing() {\n')
  LIB_file.write('            related_pin : clk;\n')
  LIB_file.write('            timing_type : setup_rising ;\n')
  LIB_file.write('            rise_constraint(%s_constraint_template) {\n' % name)
  LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
  LIB_file.write('                index_2 ("%s");\n' % slew_indicies)
  LIB_file.write('                values ( \\\n')
  LIB_file.write('                  "%.3f, %.3f", \\\n' % (tsetup, tsetup))
  LIB_file.write('                  "%.3f, %.3f" \\\n'  % (tsetup, tsetup))
  LIB_file.write('                )\n')
  LIB_file.write('            }\n')
  LIB_file.write('            fall_constraint(%s_constraint_template) {\n' % name)
  LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
  LIB_file.write('                index_2 ("%s");\n' % slew_indicies)
  LIB_file.write('                values ( \\\n')
  LIB_file.write('                  "%.3f, %.3f", \\\n' % (tsetup, tsetup))
  LIB_file.write('                  "%.3f, %.3f" \\\n'  % (tsetup, tsetup))
  LIB_file.write('                )\n')
  LIB_file.write('            }\n')
  LIB_file.write('        } \n')
  LIB_file.write('        timing() {\n')
  LIB_file.write('            related_pin : clk;\n')
  LIB_file.write('            timing_type : hold_rising ;\n')
  LIB_file.write('            rise_constraint(%s_constraint_template) {\n' % name)
  LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
  LIB_file.write('                index_2 ("%s");\n' % slew_indicies)
  LIB_file.write('                values ( \\\n')
  LIB_file.write('                    "0.000, 0.000", \\\n')
  LIB_file.write('                    "0.000, 0.000" \\\n')
  LIB_file.write('                )\n')
  LIB_file.write('            }\n')
  LIB_file.write('            fall_constraint(%s_constraint_template) {\n' % name)
  LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
  LIB_file.write('                index_2 ("%s");\n' % slew_indicies)
  LIB_file.write('                values ( \\\n')
  LIB_file.write('                    "0.000, 0.000", \\\n')
  LIB_file.write('                    "0.000, 0.000" \\\n')
  LIB_file.write('                )\n')
  LIB_file.write('            }\n')
  LIB_file.write('        }\n')
  LIB_file.write('        internal_power(){\n')
  LIB_file.write('            rise_power(%s_energy_template_sigslew) {\n' % name)
  LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
  LIB_file.write('                values ("%.3f, %.3f")\n' % ((pindynamic), (pindynamic)))
  LIB_file.write('            }\n')
  LIB_file.write('            fall_power(%s_energy_template_sigslew) {\n' % name)
  LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
  LIB_file.write('                values ("%.3f, %.3f")\n' % ((pindynamic), (pindynamic)))
  LIB_file.write('            }\n')
  LIB_file.write('        }\n')
  LIB_file.write('    }\n')

  for i in range(int(num_rwport)) :
    LIB_file.write('    bus(addr_in)   {\n')
    LIB_file.write('        bus_type : %s_ADDRESS;\n' % name)
    LIB_file.write('        direction : input;\n')
    LIB_file.write('        capacitance : %.3f;\n' % (min_driver_in_cap))
    LIB_file.write('        timing() {\n')
    LIB_file.write('            related_pin : clk;\n')
    LIB_file.write('            timing_type : setup_rising ;\n')
    LIB_file.write('            rise_constraint(%s_constraint_template) {\n' % name)
    LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
    LIB_file.write('                index_2 ("%s");\n' % slew_indicies)
    LIB_file.write('                values ( \\\n')
    LIB_file.write('                  "%.3f, %.3f", \\\n' % (tsetup, tsetup))
    LIB_file.write('                  "%.3f, %.3f" \\\n'  % (tsetup, tsetup))
    LIB_file.write('                )\n')
    LIB_file.write('            }\n')
    LIB_file.write('            fall_constraint(%s_constraint_template) {\n' % name)
    LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
    LIB_file.write('                index_2 ("%s");\n' % slew_indicies)
    LIB_file.write('                values ( \\\n')
    LIB_file.write('                  "%.3f, %.3f", \\\n' % (tsetup, tsetup))
    LIB_file.write('                  "%.3f, %.3f" \\\n'  % (tsetup, tsetup))
    LIB_file.write('                )\n')
    LIB_file.write('            }\n')
    LIB_file.write('        } \n')
    LIB_file.write('        timing() {\n')
    LIB_file.write('            related_pin : clk;\n')
    LIB_file.write('            timing_type : hold_rising ;\n')
    LIB_file.write('            rise_constraint(%s_constraint_template) {\n' % name)
    LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
    LIB_file.write('                index_2 ("%s");\n' % slew_indicies)
    LIB_file.write('                values ( \\\n')
    LIB_file.write('                    "0.000, 0.000", \\\n')
    LIB_file.write('                    "0.000, 0.000" \\\n')
    LIB_file.write('                )\n')
    LIB_file.write('            }\n')
    LIB_file.write('            fall_constraint(%s_constraint_template) {\n' % name)
    LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
    LIB_file.write('                index_2 ("%s");\n' % slew_indicies)
    LIB_file.write('                values ( \\\n')
    LIB_file.write('                    "0.000, 0.000", \\\n')
    LIB_file.write('                    "0.000, 0.000" \\\n')
    LIB_file.write('                )\n')
    LIB_file.write('            }\n')
    LIB_file.write('        }\n')
    LIB_file.write('        internal_power(){\n')
    LIB_file.write('            rise_power(%s_energy_template_sigslew) {\n' % name)
    LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
    LIB_file.write('                values ("%.3f, %.3f")\n' % ((pindynamic), (pindynamic)))
    LIB_file.write('            }\n')
    LIB_file.write('            fall_power(%s_energy_template_sigslew) {\n' % name)
    LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
    LIB_file.write('                values ("%.3f, %.3f")\n' % ((pindynamic), (pindynamic)))
    LIB_file.write('            }\n')
    LIB_file.write('        }\n')
    LIB_file.write('    }\n')

  for i in range(int(num_rwport)) :
    LIB_file.write('    bus(wd_in)   {\n')
    LIB_file.write('        bus_type : %s_DATA;\n' % name)
    LIB_file.write('        memory_write() {\n')
    LIB_file.write('            address : addr_in;\n')
    LIB_file.write('            clocked_on : "clk";\n')
    LIB_file.write('        }\n')
    LIB_file.write('        direction : input;\n')
    LIB_file.write('        capacitance : %.3f;\n' % (min_driver_in_cap))
    LIB_file.write('        timing() {\n')
    LIB_file.write('            related_pin     : clk;\n')
    LIB_file.write('            timing_type     : setup_rising ;\n')
    LIB_file.write('            rise_constraint(%s_constraint_template) {\n' % name)
    LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
    LIB_file.write('                index_2 ("%s");\n' % slew_indicies)
    LIB_file.write('                values ( \\\n')
    LIB_file.write('                  "%.3f, %.3f", \\\n' % (tsetup, tsetup))
    LIB_file.write('                  "%.3f, %.3f" \\\n'  % (tsetup, tsetup))
    LIB_file.write('                )\n')
    LIB_file.write('            }\n')
    LIB_file.write('            fall_constraint(%s_constraint_template) {\n' % name)
    LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
    LIB_file.write('                index_2 ("%s");\n' % slew_indicies)
    LIB_file.write('                values ( \\\n')
    LIB_file.write('                  "%.3f, %.3f", \\\n' % (tsetup, tsetup))
    LIB_file.write('                  "%.3f, %.3f" \\\n'  % (tsetup, tsetup))
    LIB_file.write('                )\n')
    LIB_file.write('            }\n')
    LIB_file.write('        } \n')
    LIB_file.write('        timing() {\n')
    LIB_file.write('            related_pin     : clk;\n')
    LIB_file.write('            timing_type     : hold_rising ;\n')
    LIB_file.write('            rise_constraint(%s_constraint_template) {\n' % name)
    LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
    LIB_file.write('                index_2 ("%s");\n' % slew_indicies)
    LIB_file.write('                values ( \\\n')
    LIB_file.write('                  "%.3f, %.3f", \\\n' % (thold, thold))
    LIB_file.write('                  "%.3f, %.3f" \\\n'  % (thold, thold))
    LIB_file.write('                )\n')
    LIB_file.write('            }\n')
    LIB_file.write('            fall_constraint(%s_constraint_template) {\n' % name)
    LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
    LIB_file.write('                index_2 ("%s");\n' % slew_indicies)
    LIB_file.write('                values ( \\\n')
    LIB_file.write('                  "%.3f, %.3f", \\\n' % (thold, thold))
    LIB_file.write('                  "%.3f, %.3f" \\\n'  % (thold, thold))
    LIB_file.write('                )\n')
    LIB_file.write('            }\n')
    LIB_file.write('        }\n')
    LIB_file.write('        internal_power(){\n')
    LIB_file.write('            when : "(! (we_in) )";\n')
    LIB_file.write('            rise_power(%s_energy_template_sigslew) {\n' % name)
    LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
    LIB_file.write('                values ("%.3f, %.3f")\n' % ((pindynamic), (pindynamic)))
    LIB_file.write('            }\n')
    LIB_file.write('            fall_power(%s_energy_template_sigslew) {\n' % name)
    LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
    LIB_file.write('                values ("%.3f, %.3f")\n' % ((pindynamic), (pindynamic)))
    LIB_file.write('            }\n')
    LIB_file.write('        }\n')
    LIB_file.write('        internal_power(){\n')
    LIB_file.write('            when : "(we_in)";\n')
    LIB_file.write('            rise_power(' + name + '_energy_template_sigslew) {\n')
    LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
    LIB_file.write('                values ("%.3f, %.3f")\n' % ((pindynamic), (pindynamic)))
    LIB_file.write('            }\n')
    LIB_file.write('            fall_power(' + name + '_energy_template_sigslew) {\n')
    LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
    LIB_file.write('                values ("%.3f, %.3f")\n' % ((pindynamic), (pindynamic)))
    LIB_file.write('            }\n')
    LIB_file.write('        }\n')
    LIB_file.write('    }\n')

  for i in range(int(num_rwport)) :
    LIB_file.write('    bus(w_mask_in)   {\n')
    LIB_file.write('        bus_type : %s_DATA;\n' % name)
    LIB_file.write('        memory_write() {\n')
    LIB_file.write('            address : addr_in;\n')
    LIB_file.write('            clocked_on : "clk";\n')
    LIB_file.write('        }\n')
    LIB_file.write('        direction : input;\n')
    LIB_file.write('        capacitance : %.3f;\n' % (min_driver_in_cap))
    LIB_file.write('        timing() {\n')
    LIB_file.write('            related_pin     : clk;\n')
    LIB_file.write('            timing_type     : setup_rising ;\n')
    LIB_file.write('            rise_constraint(%s_constraint_template) {\n' % name)
    LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
    LIB_file.write('                index_2 ("%s");\n' % slew_indicies)
    LIB_file.write('                values ( \\\n')
    LIB_file.write('                  "%.3f, %.3f", \\\n' % (tsetup, tsetup))
    LIB_file.write('                  "%.3f, %.3f" \\\n'  % (tsetup, tsetup))
    LIB_file.write('                )\n')
    LIB_file.write('            }\n')
    LIB_file.write('            fall_constraint(%s_constraint_template) {\n' % name)
    LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
    LIB_file.write('                index_2 ("%s");\n' % slew_indicies)
    LIB_file.write('                values ( \\\n')
    LIB_file.write('                  "%.3f, %.3f", \\\n' % (tsetup, tsetup))
    LIB_file.write('                  "%.3f, %.3f" \\\n'  % (tsetup, tsetup))
    LIB_file.write('                )\n')
    LIB_file.write('            }\n')
    LIB_file.write('        } \n')
    LIB_file.write('        timing() {\n')
    LIB_file.write('            related_pin     : clk;\n')
    LIB_file.write('            timing_type     : hold_rising ;\n')
    LIB_file.write('            rise_constraint(%s_constraint_template) {\n' % name)
    LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
    LIB_file.write('                index_2 ("%s");\n' % slew_indicies)
    LIB_file.write('                values ( \\\n')
    LIB_file.write('                  "%.3f, %.3f", \\\n' % (thold, thold))
    LIB_file.write('                  "%.3f, %.3f" \\\n'  % (thold, thold))
    LIB_file.write('                )\n')
    LIB_file.write('            }\n')
    LIB_file.write('            fall_constraint(%s_constraint_template) {\n' % name)
    LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
    LIB_file.write('                index_2 ("%s");\n' % slew_indicies)
    LIB_file.write('                values ( \\\n')
    LIB_file.write('                  "%.3f, %.3f", \\\n' % (thold, thold))
    LIB_file.write('                  "%.3f, %.3f" \\\n'  % (thold, thold))
    LIB_file.write('                )\n')
    LIB_file.write('            }\n')
    LIB_file.write('        }\n')
    LIB_file.write('        internal_power(){\n')
    LIB_file.write('            when : "(! (we_in) )";\n')
    LIB_file.write('            rise_power(%s_energy_template_sigslew) {\n' % name)
    LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
    LIB_file.write('                values ("%.3f, %.3f")\n' % ((pindynamic), (pindynamic)))
    LIB_file.write('            }\n')
    LIB_file.write('            fall_power(%s_energy_template_sigslew) {\n' % name)
    LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
    LIB_file.write('                values ("%.3f, %.3f")\n' % ((pindynamic), (pindynamic)))
    LIB_file.write('            }\n')
    LIB_file.write('        }\n')
    LIB_file.write('        internal_power(){\n')
    LIB_file.write('            when : "(we_in)";\n')
    LIB_file.write('            rise_power(' + name + '_energy_template_sigslew) {\n')
    LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
    LIB_file.write('                values ("%.3f, %.3f")\n' % ((pindynamic), (pindynamic)))
    LIB_file.write('            }\n')
    LIB_file.write('            fall_power(' + name + '_energy_template_sigslew) {\n')
    LIB_file.write('                index_1 ("%s");\n' % slew_indicies)
    LIB_file.write('                values ("%.3f, %.3f")\n' % ((pindynamic), (pindynamic)))
    LIB_file.write('            }\n')
    LIB_file.write('        }\n')
    LIB_file.write('    }\n')

  LIB_file.write('    cell_leakage_power : %.3f;\n' % (leakage))
  LIB_file.write('}\n')

  LIB_file.write('\n')
  LIB_file.write('}\n')

  LIB_file.close()

################################################################################
# GENERATE VERILOG VIEW
#
# Generate a .v file based on the parameterization of the SRAM provided.
################################################################################
def generate_verilog_view( name, depth, bits ):

  name  = str(name)
  depth = int(depth)
  bits  = int(bits)

  # Only support 1RW srams. At some point, expose these as well!
  num_rwport = 1

  # Number of bits for address
  addr_width    = math.ceil(math.log2(depth))

  # Start generating the VERILOG file

  V_file = open(name + '.v', 'w')

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

################################################################################
# GENERATE LEF VIEW
#
# Generate a .lef file based on the physical characteristics for the SRAM
# provided by Cacti.
################################################################################

def generate_lef_view( name, depth, bits, x, y, minWidth, minSpace, metalPrefix ):

  name  = str(name)
  depth = int(depth)
  bits  = int(bits)
  x     = float(x)
  y     = float(y)

  # Only support 1RW srams for now
  num_rwport = 1

  # Number of address pins
  addr_width = math.ceil(math.log2(depth))

  # Short-hand
  x = float(x)
  y = float(y)

  # Specify pin width (x_pin_width) and height (y_pin_width)
  x_pin_width = minWidth
  y_pin_width = minWidth

  # Offsets
  y_top_offset    = 10*(y_pin_width) ;# arbitrary offset (looks decent)
  y_bottom_offset = 10*(y_pin_width) ;# arbitrary offset (looks decent)

  # Calculate the pin spacing (pitch)
  number_of_pins = num_rwport * (2 * bits + addr_width + bits + 1) + 2
  y_usable_space = y - (y_top_offset + y_bottom_offset)
  pin_spacing  = (float(y_usable_space) / float(number_of_pins)) - y_pin_width

  # Check we have enough space
  min_y = y_top_offset + y_bottom_offset + number_of_pins*(minWidth + minSpace)
  if y < min_y:
    print("Error: y = %.2f < minimum (%.2f)\nAborting." % (y, min_y))
    sys.exit(1)

  # Start generating the LEF file

  LEF_file = open(name + '.lef', 'w')

  LEF_file.write('VERSION 5.7 ;\n')
  LEF_file.write('BUSBITCHARS "[]" ;\n')
  LEF_file.write('MACRO %s\n' % (name))
  LEF_file.write('  FOREIGN %s 0 0 ;\n' % (name))
  LEF_file.write('  SYMMETRY X Y R90 ;\n')
  LEF_file.write('  SIZE %.3f BY %.3f ;\n' % (x,y))
  LEF_file.write('  CLASS BLOCK ;\n')

  ########################################
  # Place signal pins
  ########################################

  # We palce all pins on the left side of the macro in the following order:
  #   1. w_mask_in
  #   2. we_in
  #   3. rd_out
  #   4. wd_in
  #   5. addr_in
  #   6. clk
  #   7. ce_in

  y_tmp = y - y_top_offset ;# starting y

  for i in range(int(num_rwport)) :
    for j in range(int(bits)) :
      LEF_file.write('  PIN w_mask_in[%d]\n' % j)
      LEF_file.write('    DIRECTION INPUT ;\n')
      LEF_file.write('    USE SIGNAL ;\n')
      LEF_file.write('    SHAPE ABUTMENT ;\n')
      LEF_file.write('    PORT\n')
      LEF_file.write('      LAYER %s1 ;\n' % metalPrefix)
      LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (0, (y_tmp-y_pin_width), (x_pin_width), (y_tmp)))
      LEF_file.write('      LAYER %s2 ;\n' % metalPrefix)
      LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (0, (y_tmp-y_pin_width), (x_pin_width), (y_tmp)))
      LEF_file.write('      LAYER %s3 ;\n' % metalPrefix)
      LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (0, (y_tmp-y_pin_width), (x_pin_width), (y_tmp)))
      LEF_file.write('      LAYER %s4 ;\n' % metalPrefix)
      LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (0, (y_tmp-y_pin_width), (x_pin_width), (y_tmp)))
      LEF_file.write('      END\n')
      LEF_file.write('    END w_mask_in[%d]\n' % j)
      y_tmp = y_tmp - y_pin_width - pin_spacing

  for i in range(int(num_rwport)) :
    LEF_file.write('  PIN we_in\n')
    LEF_file.write('    DIRECTION INPUT ;\n')
    LEF_file.write('    USE SIGNAL ;\n')
    LEF_file.write('    SHAPE ABUTMENT ;\n')
    LEF_file.write('    PORT\n')
    LEF_file.write('      LAYER %s1 ;\n' % metalPrefix)
    LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (0, (y_tmp-y_pin_width), (x_pin_width), (y_tmp)))
    LEF_file.write('      LAYER %s2 ;\n' % metalPrefix)
    LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (0, (y_tmp-y_pin_width), (x_pin_width), (y_tmp)))
    LEF_file.write('      LAYER %s3 ;\n' % metalPrefix)
    LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (0, (y_tmp-y_pin_width), (x_pin_width), (y_tmp)))
    LEF_file.write('      LAYER %s4 ;\n' % metalPrefix)
    LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (0, (y_tmp-y_pin_width), (x_pin_width), (y_tmp)))
    LEF_file.write('      END\n')
    LEF_file.write('    END we_in\n')
    y_tmp = y_tmp - y_pin_width - pin_spacing

  for i in range(int(num_rwport)) :
    for j in range(int(bits)) :
      LEF_file.write('  PIN rd_out[%d]\n' % j)
      LEF_file.write('    DIRECTION OUTPUT ;\n')
      LEF_file.write('    USE SIGNAL ;\n')
      LEF_file.write('    SHAPE ABUTMENT ;\n')
      LEF_file.write('    PORT\n')
      LEF_file.write('      LAYER %s1 ;\n' % metalPrefix)
      LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (0, (y_tmp-y_pin_width), (x_pin_width), (y_tmp)))
      LEF_file.write('      LAYER %s2 ;\n' % metalPrefix)
      LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (0, (y_tmp-y_pin_width), (x_pin_width), (y_tmp)))
      LEF_file.write('      LAYER %s3 ;\n' % metalPrefix)
      LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (0, (y_tmp-y_pin_width), (x_pin_width), (y_tmp)))
      LEF_file.write('      LAYER %s4 ;\n' % metalPrefix)
      LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (0, (y_tmp-y_pin_width), (x_pin_width), (y_tmp)))
      LEF_file.write('      END\n')
      LEF_file.write('    END rd_out[%d]\n' % j)
      y_tmp = y_tmp - y_pin_width - pin_spacing

  for i in range(int(num_rwport)) :
    for j in range(int(bits)) :
      LEF_file.write('  PIN wd_in[%d]\n' % j)
      LEF_file.write('    DIRECTION INPUT ;\n')
      LEF_file.write('    USE SIGNAL ;\n')
      LEF_file.write('    SHAPE ABUTMENT ;\n')
      LEF_file.write('    PORT\n')
      LEF_file.write('      LAYER %s1 ;\n' % metalPrefix)
      LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (0, (y_tmp-y_pin_width), (x_pin_width), (y_tmp)))
      LEF_file.write('      LAYER %s2 ;\n' % metalPrefix)
      LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (0, (y_tmp-y_pin_width), (x_pin_width), (y_tmp)))
      LEF_file.write('      LAYER %s3 ;\n' % metalPrefix)
      LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (0, (y_tmp-y_pin_width), (x_pin_width), (y_tmp)))
      LEF_file.write('      LAYER %s4 ;\n' % metalPrefix)
      LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (0, (y_tmp-y_pin_width), (x_pin_width), (y_tmp)))
      LEF_file.write('      END\n')
      LEF_file.write('    END wd_in[%d]\n' % j)
      y_tmp = y_tmp - y_pin_width - pin_spacing

  for i in range(int(num_rwport)) :
    for j in range(int(addr_width)) :
      LEF_file.write('  PIN addr_in[%d]\n' % j)
      LEF_file.write('    DIRECTION INPUT ;\n')
      LEF_file.write('    USE SIGNAL ;\n')
      LEF_file.write('    SHAPE ABUTMENT ;\n')
      LEF_file.write('    PORT\n')
      LEF_file.write('      LAYER %s1 ;\n' % metalPrefix)
      LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (0, (y_tmp-y_pin_width), (x_pin_width), (y_tmp)))
      LEF_file.write('      LAYER %s2 ;\n' % metalPrefix)
      LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (0, (y_tmp-y_pin_width), (x_pin_width), (y_tmp)))
      LEF_file.write('      LAYER %s3 ;\n' % metalPrefix)
      LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (0, (y_tmp-y_pin_width), (x_pin_width), (y_tmp)))
      LEF_file.write('      LAYER %s4 ;\n' % metalPrefix)
      LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (0, (y_tmp-y_pin_width), (x_pin_width), (y_tmp)))
      LEF_file.write('      END\n')
      LEF_file.write('    END addr_in[%d]\n' % j)
      y_tmp = y_tmp - y_pin_width - pin_spacing

  LEF_file.write('  PIN clk\n')
  LEF_file.write('    DIRECTION INPUT ;\n')
  LEF_file.write('    USE SIGNAL ;\n')
  LEF_file.write('    SHAPE ABUTMENT ;\n')
  LEF_file.write('    PORT\n')
  LEF_file.write('      LAYER %s1 ;\n' % metalPrefix)
  LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (0, (y_tmp-y_pin_width), (x_pin_width), (y_tmp)))
  LEF_file.write('      LAYER %s2 ;\n' % metalPrefix)
  LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (0, (y_tmp-y_pin_width), (x_pin_width), (y_tmp)))
  LEF_file.write('      LAYER %s3 ;\n' % metalPrefix)
  LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (0, (y_tmp-y_pin_width), (x_pin_width), (y_tmp)))
  LEF_file.write('      LAYER %s4 ;\n' % metalPrefix)
  LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (0, (y_tmp-y_pin_width), (x_pin_width), (y_tmp)))
  LEF_file.write('      END\n')
  LEF_file.write('    END clk\n')
  y_tmp = y_tmp - y_pin_width - pin_spacing

  LEF_file.write('  PIN ce_in\n')
  LEF_file.write('    DIRECTION INPUT ;\n')
  LEF_file.write('    USE SIGNAL ;\n')
  LEF_file.write('    SHAPE ABUTMENT ;\n')
  LEF_file.write('    PORT\n')
  LEF_file.write('      LAYER %s1 ;\n' % metalPrefix)
  LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (0, (y_tmp-y_pin_width), (x_pin_width), (y_tmp)))
  LEF_file.write('      LAYER %s2 ;\n' % metalPrefix)
  LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (0, (y_tmp-y_pin_width), (x_pin_width), (y_tmp)))
  LEF_file.write('      LAYER %s3 ;\n' % metalPrefix)
  LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (0, (y_tmp-y_pin_width), (x_pin_width), (y_tmp)))
  LEF_file.write('      LAYER %s4 ;\n' % metalPrefix)
  LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (0, (y_tmp-y_pin_width), (x_pin_width), (y_tmp)))
  LEF_file.write('      END\n')
  LEF_file.write('    END ce_in\n')
  y_tmp = y_tmp - y_pin_width - pin_spacing

  ########################################
  # Create VDD/VSS Strapes
  ########################################

  temp_x_0 = x/8.0                                      ;# arbitrary but reminiscent of real SRAMs.
  temp_x_1 = x - x/8.0                                  ;# arbitrary but reminiscent of real SRAMs.
  pg_strap_width = 4*y_pin_width                        ;# arbitrary but reminiscent of real SRAMs.
  pg_strap_pitch = 2*pg_strap_width + 2*(4*minSpace)    ;# arbitrary but reminiscent of real SRAMs.

  y_tmp = y - y_top_offset
  while y_tmp > y_bottom_offset:
    LEF_file.write('  PIN VSS\n')
    LEF_file.write('    DIRECTION INOUT ;\n')
    LEF_file.write('    USE GROUND ;\n')
    LEF_file.write('    PORT\n')
    LEF_file.write('      LAYER %s4 ;\n' % metalPrefix)
    LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % ((temp_x_0), (y_tmp), (temp_x_1), (y_tmp + pg_strap_width)))
    LEF_file.write('      END\n')
    LEF_file.write('    END VSS\n')
    y_tmp = y_tmp - pg_strap_width - pg_strap_pitch

  y_tmp = y - y_top_offset - pg_strap_width/2 - pg_strap_pitch/2
  while y_tmp > y_bottom_offset:
    LEF_file.write('  PIN VDD\n')
    LEF_file.write('    DIRECTION INOUT ;\n')
    LEF_file.write('    USE POWER ;\n')
    LEF_file.write('    PORT\n')
    LEF_file.write('      LAYER %s4 ;\n' % metalPrefix)
    LEF_file.write('      RECT %.3f %.3f %.3f %.3f ;\n' % ((temp_x_0), (y_tmp), (temp_x_1), (y_tmp + pg_strap_width)))
    LEF_file.write('      END\n')
    LEF_file.write('    END VDD\n')
    y_tmp = y_tmp - pg_strap_width - pg_strap_pitch

  ########################################
  # Create obstructions
  ########################################

  LEF_file.write('  OBS\n')
  LEF_file.write('    LAYER %s1 ;\n' % metalPrefix)
  y_tmp = y - y_top_offset
  LEF_file.write('    RECT %.3f %.3f %.3f %.3f ;\n' % ((0), (y), (x), (y_tmp)))
  for i in range(number_of_pins):
    LEF_file.write('    RECT %.3f %.3f %.3f %.3f ;\n' % ((x_pin_width), (y_tmp), (x), (y_tmp-y_pin_width)))
    LEF_file.write('    RECT %.3f %.3f %.3f %.3f ;\n' % ((0), (y_tmp-y_pin_width), (x), (y_tmp-y_pin_width-pin_spacing)))
    y_tmp = y_tmp - y_pin_width - pin_spacing
  LEF_file.write('    RECT %.3f %.3f %.3f %.3f ;\n' % ((0), (y_tmp), (x), (0)))
  LEF_file.write('    LAYER %s2 ;\n' % metalPrefix)
  y_tmp = y - y_top_offset
  LEF_file.write('    RECT %.3f %.3f %.3f %.3f ;\n' % ((0), (y), (x), (y_tmp)))
  for i in range(number_of_pins):
    LEF_file.write('    RECT %.3f %.3f %.3f %.3f ;\n' % ((x_pin_width), (y_tmp), (x), (y_tmp-y_pin_width)))
    LEF_file.write('    RECT %.3f %.3f %.3f %.3f ;\n' % ((0), (y_tmp-y_pin_width), (x), (y_tmp-y_pin_width-pin_spacing)))
    y_tmp = y_tmp - y_pin_width - pin_spacing
  LEF_file.write('    RECT %.3f %.3f %.3f %.3f ;\n' % ((0), (y_tmp), (x), (0)))
  LEF_file.write('    LAYER %s3 ;\n' % metalPrefix)
  y_tmp = y - y_top_offset
  LEF_file.write('    RECT %.3f %.3f %.3f %.3f ;\n' % ((0), (y), (x), (y_tmp)))
  for i in range(number_of_pins):
    LEF_file.write('    RECT %.3f %.3f %.3f %.3f ;\n' % ((x_pin_width), (y_tmp), (x), (y_tmp-y_pin_width)))
    LEF_file.write('    RECT %.3f %.3f %.3f %.3f ;\n' % ((0), (y_tmp-y_pin_width), (x), (y_tmp-y_pin_width-pin_spacing)))
    y_tmp = y_tmp - y_pin_width - pin_spacing
  LEF_file.write('    RECT %.3f %.3f %.3f %.3f ;\n' % ((0), (y_tmp), (x), (0)))
  LEF_file.write('    LAYER OVERLAP ;\n')
  LEF_file.write('    RECT 0 0 %.3f %.3f ;\n' % ((x), (y)))
  LEF_file.write('    END\n')
  LEF_file.write('  END %s\n' % name)
  LEF_file.write('\n')
  LEF_file.write('END LIBRARY\n')

  LEF_file.close()

################################################################################
# CACTI CONFIG
#
# This list is used to write out the Cacti configuration file for the SRAMs
# we are generating so we can extract the power, timing and area numbers.
################################################################################

cacti_config = []
cacti_config.append( '-size (bytes) {0}' )
cacti_config.append( '-block size (bytes) {1}' )
cacti_config.append( '-associativity 1' )
cacti_config.append( '-read-write port {2}' )
cacti_config.append( '-exclusive read port {3}' )
cacti_config.append( '-exclusive write port {4}' )
cacti_config.append( '-single ended read ports 0' )
cacti_config.append( '-UCA bank count 1' )
cacti_config.append( '-technology (u) {5}' )
cacti_config.append( '-page size (bits) 8192 ' )
cacti_config.append( '-burst length 8' )
cacti_config.append( '-internal prefetch width 8' )
cacti_config.append( '-Data array cell type - "itrs-hp"' )
cacti_config.append( '-Data array peripheral type - "itrs-hp"' )
cacti_config.append( '-Tag array cell type - "itrs-hp"' )
cacti_config.append( '-Tag array peripheral type - "itrs-hp"' )
cacti_config.append( '-output/input bus width {6}' )
cacti_config.append( '-operating temperature (K) 300' )
cacti_config.append( '-cache type "ram"' )
cacti_config.append( '-tag size (b) "default"' )
cacti_config.append( '-access mode (normal, sequential, fast) - "normal"' )
cacti_config.append( '-design objective (weight delay, dynamic power, leakage power, cycle time, area) 0:0:0:0:100' )
cacti_config.append( '-deviate (delay, dynamic power, leakage power, cycle time, area) 60:100000:100000:100000:1000000' )
cacti_config.append( '-NUCAdesign objective (weight delay, dynamic power, leakage power, cycle time, area) 100:100:0:0:100' )
cacti_config.append( '-NUCAdeviate (delay, dynamic power, leakage power, cycle time, area) 10:10000:10000:10000:10000' )
cacti_config.append( '-Optimize ED or ED^2 (ED, ED^2, NONE): "NONE"' )
cacti_config.append( '-Cache model (NUCA, UCA)  - "UCA"' )
cacti_config.append( '-NUCA bank count 0' )
cacti_config.append( '-Wire signalling (fullswing, lowswing, default) - "default"' )
cacti_config.append( '-Wire inside mat - "global"' )
cacti_config.append( '-Wire outside mat - "global"' )
cacti_config.append( '-Interconnect projection - "conservative"' )
cacti_config.append( '-Core count 4' )
cacti_config.append( '-Cache level (L2/L3) - "L2"' )
cacti_config.append( '-Add ECC - "true"' )
cacti_config.append( '-Print level (DETAILED, CONCISE) - "DETAILED"' )
cacti_config.append( '-Print input parameters - "true"' )
cacti_config.append( '-Force cache config - "false"' )
cacti_config.append( '-Ndwl 64' )
cacti_config.append( '-Ndbl 64' )
cacti_config.append( '-Nspd 64' )
cacti_config.append( '-Ndcm 1' )
cacti_config.append( '-Ndsam1 4' )
cacti_config.append( '-Ndsam2 1' )

### Entry point
if __name__ == '__main__':
  main( len(sys.argv), sys.argv )

