export TOP_DIR :=$(shell git rev-parse --show-toplevel)

CONFIG = example_cfgs/example.cfg

### External tool build directories
export CACTI_BUILD_DIR :=$(TOP_DIR)/tools/cacti

run:
	./scripts/run_cacti.py $(CONFIG)

clean:
	rm -rf results

open.%:
	klayout ./results/$*/$*.lef &

################################################################################
## Build External Tools Needed For This Application
################################################################################

tools: $(CACTI_BUILD_DIR)

$(CACTI_BUILD_DIR):
	mkdir -p $(@D)
	git clone https://github.com/HewlettPackard/Cacti.git $@
	cd $@; git checkout v6.5.0
	cd $@; git apply $(TOP_DIR)/patches/cacti.patch
	cd $@; make -j4

clean_tools:
	rm -rf $(CACTI_BUILD_DIR)
