# BSG Black-box SRAM Generator

This project is desgined to generate black-boxed SRAMs for use in CAD flows where either an SRAM generator is not avaible or doesn't exist.

## Setup

The black-box SRAM generator depends on lightly modified version of [Cacti](https://github.com/HewlettPackard/cacti) for area, power, and timing modeling. To build this version of Cacti, simply run:

```
$ make tools
```

## Usage

### Configuration File

The input to the BSG Black-box SRAM generator is a simple JSON file that contains some information about the technology node you are targeting as well as the size and names of SRAMs you would like to generate. Below is an example JSON file that can be found in `./example_cfgs/example.cfg`:

```
{
  "tech_nm":     45,
  "minWidth_nm": 50,
  "minSpace_nm": 50,
  "metalPrefix": "metal",
  "srams": [
    {"name": "sram_32x32_1rw",  "width":  32, "depth":  32},
    {"name": "sram_116x64_1rw", "width": 116, "depth":  64},
    {"name": "sram_32x512_1rw", "width":  32, "depth": 512}
  ]
}
```

`tech_nm` - The name of the target technology node (in nm). Used in Cacti for modeling PPA of the SRAM.

`minWidth_nm` - The minimum width for metal 1 for the target technology node (in nm). Used in the lef file generation for pin sizing.

`minSpace_nm` - The minimum space for metal 1 for the target technology node (in nm). Used in the LEF view generation for pin feasibility checking.

`metalPrefix` - The string that prefixes metal layers.

`srams` - A list of SRAMs to generate. Each sram should have a `name`, `width` (or the number of bits per word), and `depth` (or number of words). 


### Running the Generator

Now that you have a configuration file, it is time to run the generator. The main makefile target is:

```
$ make run CONFIG=<path to config file>
```

If you'd perfer, you can open up the Makefile and set `CONFIG` rather than setting it on the command line.

All of the generated files can be found in the `./results` directory. Inside this directory will be a directory for each SRAM which contains the .lef, .lib and v file (as well as some intermediate files used for Cacti).

## Feedback

Feedback is always welcome! We ask that you submit a GitHub issue for any bugs, improvements, or new features you would like to see. We are also receptive to outside contributions but please be mindful of sensitive information that is commonly associated with licensed IP.

