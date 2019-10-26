################################################################################
# CACTI CONFIG
#
# This list is used to write out the Cacti configuration file for the SRAMs we
# are generating so we can extract the power, timing and area numbers.
################################################################################

# This configuration is baed on the cacti/cache.cfg file which is considered
# the default according to the cacti technical report. Each line as some sort
# of justification, when "default" is mentioned it is with respect to the
# cacti/cache.cfg configuration.

cacti_config = []
cacti_config.append( '-size (bytes) {0}' )                                                                                    ;# Set by user
cacti_config.append( '-Array Power Gating - "false"' )                                                                        ;# No power gating (default from cache.cfg)
cacti_config.append( '-WL Power Gating - "false"' )                                                                           ;# No power gating (default from cache.cfg)
cacti_config.append( '-CL Power Gating - "false"' )                                                                           ;# No power gating (default from cache.cfg)
cacti_config.append( '-Bitline floating - "false"' )                                                                          ;# No power gating (default from cache.cfg)
cacti_config.append( '-Interconnect Power Gating - "false"' )                                                                 ;# No power gating (default from cache.cfg)
cacti_config.append( '-Power Gating Performance Loss 0.01' )                                                                  ;# No power gating (default from cache.cfg)
cacti_config.append( '-block size (bytes) {1}' )                                                                              ;# Set by user
cacti_config.append( '-associativity 1' )                                                                                     ;# SRAM is "direct mapped"
cacti_config.append( '-read-write port {2}' )                                                                                 ;# Set by user
cacti_config.append( '-exclusive read port {3}' )                                                                             ;# Set by user
cacti_config.append( '-exclusive write port {4}' )                                                                            ;# Set by user
cacti_config.append( '-single ended read ports 0' )                                                                           ;# No single ended read ports
cacti_config.append( '-UCA bank count {7}' )                                                                                  ;# Set by user
cacti_config.append( '-technology (u) {5}' )                                                                                  ;# Set by user
cacti_config.append( '-page size (bits) 8192 ' )                                                                              ;# Not used for ram cache type
cacti_config.append( '-burst length 8' )                                                                                      ;# Not used for ram cache type
cacti_config.append( '-internal prefetch width 8' )                                                                           ;# Not used for ram cache type
cacti_config.append( '-Data array cell type - "itrs-hp"' )                                                                    ;# Default from cache.cfg
cacti_config.append( '-Data array peripheral type - "itrs-hp"' )                                                              ;# Default from cache.cfg
cacti_config.append( '-Tag array cell type - "itrs-hp"' )                                                                     ;# Default from cache.cfg
cacti_config.append( '-Tag array peripheral type - "itrs-hp"' )                                                               ;# Default from cache.cfg
cacti_config.append( '-output/input bus width {6}' )                                                                          ;# Set by user
cacti_config.append( '-operating temperature (K) 300' )                                                                       ;# Typical = 25C, closest allowed value is 300K (26.85C)
cacti_config.append( '-cache type "ram"' )                                                                                    ;# Description -- scrach ram similar to a register file
cacti_config.append( '-tag size (b) "default"' )                                                                              ;# Have cacti calc tag size (no tag for "ram" cache type)
cacti_config.append( '-access mode (normal, sequential, fast) - "normal"' )                                                   ;# Default from cache.cfg
cacti_config.append( '-design objective (weight delay, dynamic power, leakage power, cycle time, area) 0:0:0:100:0' )         ;# Default from cache.cfg
cacti_config.append( '-deviate (delay, dynamic power, leakage power, cycle time, area) 20:100000:100000:100000:100000' )      ;# Default from cache.cfg
cacti_config.append( '-NUCAdesign objective (weight delay, dynamic power, leakage power, cycle time, area) 100:100:0:0:100' ) ;# Default from cache.cfg
cacti_config.append( '-NUCAdeviate (delay, dynamic power, leakage power, cycle time, area) 10:10000:10000:10000:10000' )      ;# Default from cache.cfg
cacti_config.append( '-Optimize ED or ED^2 (ED, ED^2, NONE): "ED^2"' )                                                        ;# Default from cache.cfg
cacti_config.append( '-Cache model (NUCA, UCA)  - "UCA"' )                                                                    ;# SRAM is a "uniform cache"
cacti_config.append( '-NUCA bank count 0' )                                                                                   ;# Not used in UCA mode
cacti_config.append( '-Wire signaling (fullswing, lowswing, default) - "default"' )                                           ;# Allow cacti to consider fullswing and lowswing wires
cacti_config.append( '-Wire inside mat - "semi-global"' )                                                                     ;# Default from cache.cfg
cacti_config.append( '-Wire outside mat - "semi-global"' )                                                                    ;# Default from cache.cfg
cacti_config.append( '-Interconnect projection - "conservative"' )                                                            ;# Not optimistic (default from cache.cfg)
cacti_config.append( '-Core count 8' )                                                                                        ;# Default from cache.cfg
cacti_config.append( '-Cache level (L2/L3) - "L3"' )                                                                          ;# Shouldn't be used for "ram" cache types (kept default from cache.cfg)
cacti_config.append( '-Add ECC - "false"' )                                                                                   ;# Don't model ECC
cacti_config.append( '-Print level (DETAILED, CONCISE) - "DETAILED"' )                                                        ;# Output (doesn't affect model)
cacti_config.append( '-Print input parameters - "false"' )                                                                    ;# Output (doesn't affect model)
cacti_config.append( '-Force cache config - "false"' )                                                                        ;# For debugging (default from cache.cfg)
cacti_config.append( '-Ndwl 1' )                                                                                              ;# For debugging (default from cache.cfg)
cacti_config.append( '-Ndbl 1' )                                                                                              ;# For debugging (default from cache.cfg)
cacti_config.append( '-Nspd 0' )                                                                                              ;# For debugging (default from cache.cfg)
cacti_config.append( '-Ndcm 1' )                                                                                              ;# For debugging (default from cache.cfg)
cacti_config.append( '-Ndsam1 0' )                                                                                            ;# For debugging (default from cache.cfg)
cacti_config.append( '-Ndsam2 0' )                                                                                            ;# For debugging (default from cache.cfg)
cacti_config.append( '-dram_type "DDR3"' )                                                                                    ;# DRAM related, should not affect model? (default from cache.cfg)
cacti_config.append( '-iostate "W"' )                                                                                         ;# DRAM related, should not affect model? (default from cache.cfg)
cacti_config.append( '-addr_timing 1.0' )                                                                                     ;# DRAM related, should not affect model? (default from cache.cfg)
cacti_config.append( '-mem_density 8 Gb' )                                                                                    ;# DRAM related, should not affect model? (default from cache.cfg)
cacti_config.append( '-bus_freq 800 MHz' )                                                                                    ;# DRAM related, should not affect model? (default from cache.cfg)
cacti_config.append( '-duty_cycle 1.0' )                                                                                      ;# DRAM related, should not affect model? (default from cache.cfg)
cacti_config.append( '-activity_dq 1.0' )                                                                                     ;# DRAM related, should not affect model? (default from cache.cfg)
cacti_config.append( '-activity_ca 1.0' )                                                                                     ;# DRAM related, should not affect model? (default from cache.cfg)
cacti_config.append( '-num_dq 72' )                                                                                           ;# DRAM related, should not affect model? (default from cache.cfg)
cacti_config.append( '-num_dqs 36' )                                                                                          ;# DRAM related, should not affect model? (default from cache.cfg)
cacti_config.append( '-num_ca 35' )                                                                                           ;# DRAM related, should not affect model? (default from cache.cfg)
cacti_config.append( '-num_clk  2' )                                                                                          ;# DRAM related, should not affect model? (default from cache.cfg)
cacti_config.append( '-num_mem_dq 1' )                                                                                        ;# DRAM related, should not affect model? (default from cache.cfg)
cacti_config.append( '-mem_data_width 4' )                                                                                    ;# DRAM related, should not affect model? (default from cache.cfg)
cacti_config.append( '-rtt_value 10000' )                                                                                     ;# DRAM related, should not affect model? (default from cache.cfg)
cacti_config.append( '-ron_value 34' )                                                                                        ;# DRAM related, should not affect model? (default from cache.cfg)
cacti_config.append( '-tflight_value' )                                                                                       ;# DRAM related, should not affect model? (default from cache.cfg)
cacti_config.append( '-num_bobs 1' )                                                                                          ;# DRAM related, should not affect model? (default from cache.cfg)
cacti_config.append( '-capacity 80' )                                                                                         ;# DRAM related, should not affect model? (default from cache.cfg)
cacti_config.append( '-num_channels_per_bob 1' )                                                                              ;# DRAM related, should not affect model? (default from cache.cfg)
cacti_config.append( '-first metric "Cost"' )                                                                                 ;# DRAM related, should not affect model? (default from cache.cfg)
cacti_config.append( '-second metric "Bandwidth"' )                                                                           ;# DRAM related, should not affect model? (default from cache.cfg)
cacti_config.append( '-third metric "Energy"' )                                                                               ;# DRAM related, should not affect model? (default from cache.cfg)
cacti_config.append( '-DIMM model "ALL"' )                                                                                    ;# DRAM related, should not affect model? (default from cache.cfg)
cacti_config.append( '-mirror_in_bob "F"' )                                                                                   ;# DRAM related, should not affect model? (default from cache.cfg)

