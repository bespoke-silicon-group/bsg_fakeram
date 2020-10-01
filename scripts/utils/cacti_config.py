################################################################################
# CACTI CONFIG
#
# This list is used to write out the Cacti configuration file for the SRAMs we
# are generating so we can extract the power, timing and area numbers.
################################################################################

# This configuration is baed on the cacti/cache.cfg file which is considered
# the default according to the cacti technical report.

# **WARNING** the very first line in this file cannot be blank otherwise cacti
# stalls forever...

cacti_config = '''# cacti.cfg
-size (bytes) {0}
-block size (bytes) {1}
-read-write port {2}
-exclusive read port {3}
-exclusive write port {4}
-technology (u) {5}
-output/input bus width {6}
-UCA bank count 1
-Array Power Gating - "false"
-WL Power Gating - "false"
-CL Power Gating - "false"
-Bitline floating - "false"
-Interconnect Power Gating - "false"
-Power Gating Performance Loss 0.01
-associativity 1
-single ended read ports 0
-page size (bits) 8192 
-burst length 8
-internal prefetch width 8
-Data array cell type - "itrs-lop"
-Data array peripheral type - "itrs-hp"
-Tag array cell type - "itrs-lop"
-Tag array peripheral type - "itrs-hp"
-operating temperature (K) 300
-cache type "{8}"
-tag size (b) "default"
-access mode (normal, sequential, fast) - "normal"
-design objective (weight delay, dynamic power, leakage power, cycle time, area) 0:0:0:100:0
-deviate (delay, dynamic power, leakage power, cycle time, area) 20:100000:100000:100000:100000
-NUCAdesign objective (weight delay, dynamic power, leakage power, cycle time, area) 100:100:0:0:100
-NUCAdeviate (delay, dynamic power, leakage power, cycle time, area) 10:10000:10000:10000:10000
-Optimize ED or ED^2 (ED, ED^2, NONE): "NONE"
-Cache model (NUCA, UCA)  - "UCA"
-NUCA bank count 0
-Wire signaling (fullswing, lowswing, default) - "default"
-Wire inside mat - "default"
-Wire outside mat - "default"
-Interconnect projection - "conservative"
-Core count 8
-Cache level (L2/L3) - "L3"
-Add ECC - "true"
-Print level (DETAILED, CONCISE) - "DETAILED"
-Print input parameters - "true"
-Force cache config - "false"
-Ndwl 1
-Ndbl 1
-Nspd 0
-Ndcm 1
-Ndsam1 0
-Ndsam2 0
-dram_type "DDR3"
-io state "WRITE"
-addr_timing 1.0
-mem_density 4 Gb
-bus_freq 800 MHz
-duty_cycle 1.0
-activity_dq 1.0
-activity_ca 0.5
-num_dq 72
-num_dqs 18
-num_ca 25
-num_clk 2
-num_mem_dq 2
-mem_data_width 4
-rtt_value 10000
-ron_value 34
-tflight_value
-num_bobs 1
-capacity 80	
-num_channels_per_bob 1	
-first metric "Cost"
-second metric "Bandwidth"
-third metric "Energy"	
-DIMM model "ALL"
-mirror_in_bob "F"
'''

