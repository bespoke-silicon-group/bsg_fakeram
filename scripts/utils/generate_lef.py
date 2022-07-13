import os
import sys
import math

################################################################################
# GENERATE LEF VIEW
#
# Generate a .lef file based on the given SRAM.
################################################################################

def generate_lef( mem ):

    # File pointer
    fid = open(os.sep.join([mem.results_dir, mem.name + '.lef']), 'w')

    # Memory parameters
    name        = mem.name
    depth       = mem.depth
    bits        = mem.width_in_bits
    w           = mem.width_um
    h           = mem.height_um
    num_rwport  = mem.rw_ports
    addr_width  = math.ceil(math.log2(mem.depth))

    # Process parameters
    min_pin_width   = mem.process.pinWidth_um
    pin_height      = mem.process.pinHeight_um
    min_pin_pitch   = mem.process.pinPitch_um
    metalPrefix     = mem.process.metalPrefix
    flip            = mem.process.flipPins.lower() == 'true'

    # Offset from bottom edge to first pin
    x_offset = 10 * min_pin_pitch   ;# arbitrary offset (looks decent)
    y_offset = 10 * min_pin_pitch   ;# arbitrary offset (looks decent)

    #########################################
    # Calculate the pin spacing (pitch)
    #########################################

    number_of_pins = 3*bits + addr_width + 3
    number_of_tracks_available = math.floor((h - 2*y_offset) / min_pin_pitch)
    number_of_spare_tracks = number_of_tracks_available - number_of_pins

    print(f'Final {name} size = {w} x {h}')
    print(f'num pins: {number_of_pins}, available tracks: {number_of_tracks_available}')
    if number_of_spare_tracks < 0:
        print("ERROR: not enough tracks!")
        sys.exit(1)        

    track_count = 1
    while number_of_spare_tracks > 0:
        track_count += 1
        number_of_spare_tracks = number_of_tracks_available - number_of_pins*track_count
    track_count -= 1

    pin_pitch = min_pin_pitch * track_count
    group_pitch = math.floor((number_of_tracks_available - number_of_pins*track_count) / 4)*mem.process.pinPitch_um

    #########################################
    # LEF HEADER
    #########################################

    fid.write('VERSION 5.7 ;\n')
    fid.write('BUSBITCHARS "[]" ;\n')
    fid.write('MACRO %s\n' % (name))
    fid.write('  FOREIGN %s 0 0 ;\n' % (name))
    fid.write('  SYMMETRY X Y R90 ;\n')
    fid.write('  SIZE %.3f BY %.3f ;\n' % (w,h))
    fid.write('  CLASS BLOCK ;\n')

    ########################################
    # LEF SIGNAL PINS
    ########################################

    y_step = y_offset
    for i in range(int(bits)) :
        y_step = lef_add_pin( fid, mem, 'w_mask_in[%d]'%i, True, y_step, pin_pitch )

    y_step += group_pitch-pin_pitch
    for i in range(int(bits)) :
        y_step = lef_add_pin( fid, mem, 'rd_out[%d]'%i, False, y_step, pin_pitch )

    y_step += group_pitch-pin_pitch
    for i in range(int(bits)) :
        y_step = lef_add_pin( fid, mem, 'wd_in[%d]'%i, True, y_step, pin_pitch )

    y_step += group_pitch-pin_pitch
    for i in range(int(addr_width)) :
        y_step = lef_add_pin( fid, mem, 'addr_in[%d]'%i, True, y_step, pin_pitch )

    y_step += group_pitch-pin_pitch
    y_step = lef_add_pin( fid, mem, 'we_in', True, y_step, pin_pitch )
    y_step = lef_add_pin( fid, mem, 'ce_in', True, y_step, pin_pitch )
    y_step = lef_add_pin( fid, mem, 'clk',   True, y_step, pin_pitch )

    ########################################
    # Create VDD/VSS Strapes
    ########################################

    supply_pin_width = min_pin_width*4
    supply_pin_half_width = supply_pin_width/2
    supply_pin_pitch = min_pin_pitch*8
    supply_pin_layer = '%s4' % metalPrefix

    # Vertical straps
    if flip:
        x_step = x_offset
        fid.write('  PIN VSS\n')
        fid.write('    DIRECTION INOUT ;\n')
        fid.write('    USE GROUND ;\n')
        fid.write('    PORT\n')
        fid.write('      LAYER %s ;\n' % supply_pin_layer)
        while x_step <= w - x_offset:
            fid.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (x_step-supply_pin_half_width, y_offset, x_step+supply_pin_half_width, h-y_offset))
            x_step += supply_pin_pitch*2
        fid.write('    END\n')
        fid.write('  END VSS\n')

        x_step = x_offset + supply_pin_pitch
        fid.write('  PIN VDD\n')
        fid.write('    DIRECTION INOUT ;\n')
        fid.write('    USE POWER ;\n')
        fid.write('    PORT\n')
        fid.write('      LAYER %s ;\n' % supply_pin_layer)
        while x_step <= w - x_offset:
            fid.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (x_step-supply_pin_half_width, y_offset, x_step+supply_pin_half_width, h-y_offset))
            x_step += supply_pin_pitch*2
        fid.write('    END\n')
        fid.write('  END VDD\n')

    # Horizontal straps
    else:
        y_step = y_offset
        fid.write('  PIN VSS\n')
        fid.write('    DIRECTION INOUT ;\n')
        fid.write('    USE GROUND ;\n')
        fid.write('    PORT\n')
        fid.write('      LAYER %s ;\n' % supply_pin_layer)
        while y_step <= h - y_offset:
            fid.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (x_offset, y_step-supply_pin_half_width, w-x_offset, y_step+supply_pin_half_width))
            y_step += supply_pin_pitch*2
        fid.write('    END\n')
        fid.write('  END VSS\n')

        y_step = y_offset + supply_pin_pitch
        fid.write('  PIN VDD\n')
        fid.write('    DIRECTION INOUT ;\n')
        fid.write('    USE POWER ;\n')
        fid.write('    PORT\n')
        fid.write('      LAYER %s ;\n' % supply_pin_layer)
        while y_step <= h - y_offset:
            fid.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (x_offset, y_step-supply_pin_half_width, w-x_offset, y_step+supply_pin_half_width))
            y_step += supply_pin_pitch*2
        fid.write('    END\n')
        fid.write('  END VDD\n')

    ########################################
    # Create obstructions
    ########################################

    fid.write('  OBS\n')

    ################
    # Layer 1
    ################

    # No pins (full rect)
    fid.write('    LAYER %s1 ;\n' % metalPrefix)
    fid.write('    RECT 0 0 %.3f %.3f ;\n' % (w,h))

    ################
    # Layer 2
    ################

    # No pins (full rect)
    fid.write('    LAYER %s2 ;\n' % metalPrefix)
    fid.write('    RECT 0 0 %.3f %.3f ;\n' % (w,h))

    ################
    # Layer 3
    ################

    fid.write('    LAYER %s3 ;\n' % metalPrefix)

    # Flipped therefore pins on M3
    if flip:

        # Rect from top to bottom, just right of pins to right edge
        fid.write('    RECT %.3f 0 %.3f %.3f ;\n' % (pin_height,w,h))

        # Walk through same calculation as pins and draw from bottom of the
        # current pin to the top of last pin (start with bottom edge)
        prev_y = 0
        y_step = y_offset
        for i in range(int(bits)) :
            fid.write('    RECT 0 %.3f %.3f %.3f ;\n' % (prev_y,pin_height,y_step-min_pin_width/2))
            prev_y = y_step+min_pin_width/2
            y_step += pin_pitch
        y_step += group_pitch-pin_pitch
        for i in range(int(bits)) :
            fid.write('    RECT 0 %.3f %.3f %.3f ;\n' % (prev_y,pin_height,y_step-min_pin_width/2))
            prev_y = y_step+min_pin_width/2
            y_step += pin_pitch
        y_step += group_pitch-pin_pitch
        for i in range(int(bits)) :
            fid.write('    RECT 0 %.3f %.3f %.3f ;\n' % (prev_y,pin_height,y_step-min_pin_width/2))
            prev_y = y_step+min_pin_width/2
            y_step += pin_pitch
        y_step += group_pitch-pin_pitch
        for i in range(int(addr_width)) :
            fid.write('    RECT 0 %.3f %.3f %.3f ;\n' % (prev_y,pin_height,y_step-min_pin_width/2))
            prev_y = y_step+min_pin_width/2
            y_step += pin_pitch
        y_step += group_pitch-pin_pitch
        for i in range(3):
            fid.write('    RECT 0 %.3f %.3f %.3f ;\n' % (prev_y,pin_height,y_step-min_pin_width/2))
            prev_y = y_step+min_pin_width/2
            y_step += pin_pitch

        # Final shapre from top of last pin to top edge
        fid.write('    RECT 0 %.3f %.3f %.3f ;\n' % (prev_y,pin_height,h))

    # Not flipped therefore no pins on M3 (Full rect)
    else:
        fid.write('    RECT 0 0 %.3f %.3f ;\n' % (w,h))

    ################
    # Layer 4
    ################

    fid.write('    LAYER %s4 ;\n' % metalPrefix)

    # Flipped therefore only vertical pg straps
    if flip:

        # Block under and above the vertical power straps (full width)
        fid.write('    RECT 0 0 %.3f %.3f ;\n' % (w, y_offset))
        fid.write('    RECT 0 %.3f %.3f %.3f ;\n' % (h-y_offset,w,h))

        # Walk through the same calculations to create pg straps and create obs
        # from the left of the current strap to the right of the previous strap
        # (start with the left edge)
        prev_x = 0
        x_step = x_offset
        while x_step <= w - x_offset:
            fid.write('    RECT %.3f %.3f %.3f %.3f ;\n' % (prev_x,y_offset,x_step-supply_pin_half_width,h-y_offset))
            prev_x = x_step+supply_pin_half_width
            x_step += supply_pin_pitch

        # Create a block from the right of the last strap to the right edge
        fid.write('    RECT %.3f %.3f %.3f %.3f ;\n' % (prev_x,y_offset,w,h-y_offset))

    # Not flipped therefore pins on M4 and horizontal pg straps
    else:

        # Block from right of pins to left of straps and a block to the right
        # of the straps (full height)
        fid.write('    RECT %.3f 0 %.3f %.3f ;\n' % (min_pin_width, x_offset, h))
        fid.write('    RECT %.3f 0 %.3f %.3f ;\n' % (w-x_offset, w, h))

        # Walk through the same calculations to create pg straps and create obs
        # from the bottom of the current strap to the top of the previous strap
        # (start with the bottom edge)
        prev_y = 0
        y_step = y_offset
        while y_step <= h - y_offset:
            fid.write('    RECT %.3f %.3f %.3f %.3f ;\n' % (x_offset, prev_y, w-x_offset, y_step-supply_pin_half_width))
            prev_y = y_step+supply_pin_half_width
            y_step += supply_pin_pitch

        # Create a block from the top of the last strap to the top edge
        fid.write('    RECT %.3f %.3f %.3f %.3f ;\n' % (x_offset, prev_y, w-x_offset, h))

        # Walk through same calculation as pins and draw from bottom of the
        # current pin to the top of last pin (start with bottom edge)
        prev_y = 0
        y_step = y_offset
        for i in range(int(bits)) :
            fid.write('    RECT 0 %.3f %.3f %.3f ;\n' % (prev_y,min_pin_width,y_step-min_pin_width/2))
            prev_y = y_step+min_pin_width/2
            y_step += pin_pitch
        y_step += group_pitch-pin_pitch
        for i in range(int(bits)) :
            fid.write('    RECT 0 %.3f %.3f %.3f ;\n' % (prev_y,min_pin_width,y_step-min_pin_width/2))
            prev_y = y_step+min_pin_width/2
            y_step += pin_pitch
        y_step += group_pitch-pin_pitch
        for i in range(int(bits)) :
            fid.write('    RECT 0 %.3f %.3f %.3f ;\n' % (prev_y,min_pin_width,y_step-min_pin_width/2))
            prev_y = y_step+min_pin_width/2
            y_step += pin_pitch
        y_step += group_pitch-pin_pitch
        for i in range(int(addr_width)) :
            fid.write('    RECT 0 %.3f %.3f %.3f ;\n' % (prev_y,min_pin_width,y_step-min_pin_width/2))
            prev_y = y_step+min_pin_width/2
            y_step += pin_pitch
        y_step += group_pitch-pin_pitch
        for i in range(3):
            fid.write('    RECT 0 %.3f %.3f %.3f ;\n' % (prev_y,min_pin_width,y_step-min_pin_width/2))
            prev_y = y_step+min_pin_width/2
            y_step += pin_pitch

        # Final shapre from top of last pin to top edge
        fid.write('    RECT 0 %.3f %.3f %.3f ;\n' % (prev_y,min_pin_width,h))

    # Overlap layer (full rect)
    fid.write('    LAYER OVERLAP ;\n')
    fid.write('    RECT 0 0 %.3f %.3f ;\n' % (w,h))

    # Finish up LEF file
    fid.write('  END\n')
    fid.write('END %s\n' % name)
    fid.write('\n')
    fid.write('END LIBRARY\n')
    fid.close()

#
# Helper function that adds a signal pin
#
def lef_add_pin( fid, mem, pin_name, is_input, y, pitch ):

  layer = mem.process.metalPrefix + ('3' if mem.process.flipPins.lower() == 'true' else '4')
  pw  = mem.process.pinWidth_um
  hpw = (mem.process.pinWidth_um/2.0) # half pin width
  ph = mem.process.pinHeight_um 

  fid.write('  PIN %s\n' % pin_name)
  fid.write('    DIRECTION %s ;\n' % ('INPUT' if is_input else 'OUTPUT'))
  fid.write('    USE SIGNAL ;\n')
  fid.write('    SHAPE ABUTMENT ;\n')
  fid.write('    PORT\n')
  fid.write('      LAYER %s ;\n' % layer)
  fid.write('      RECT %.3f %.3f %.3f %.3f ;\n' % (0, y-hpw, ph, y+hpw))
  fid.write('    END\n')
  fid.write('  END %s\n' % pin_name)
  
  return y + pitch

