export TOP_DIR :=$(shell git rev-parse --show-toplevel)

export CACTI_BUILD_DIR := $(TOP_DIR)/tools/cacti

CONFIG := $(TOP_DIR)/example_cfgs/freepdk45.cfg

run:
	./scripts/run.py $(CONFIG)

view.%:
	klayout ./results/$*/$*.lef &

clean:
	rm -rf ./results

#=======================================
# TOOLS
#=======================================

tools: $(CACTI_BUILD_DIR)

$(CACTI_BUILD_DIR):
	mkdir -p $(@D)
	git clone https://github.com/HewlettPackard/Cacti.git $@
	cd $@; git checkout v6.5.0
	cd $@; git apply $(TOP_DIR)/patches/cacti.patch
	cd $@; make -j4

clean_tools:
	rm -rf $(CACTI_BUILD_DIR)

