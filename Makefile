ifeq ($(OS), Windows_NT)
	CONFIG_SOURCE_PATH="W:FID-Projekte/Team Retro-Scan/retrokat_configs"
else
	CONFIG_SOURCE_PATH="/mnt/ZE020110/FID-Projekte/Team Retro-Scan/retrokat_configs"
endif

ifndef NAME
$(error NAME ist nicht definiert; Bitte mit '$(MAKE) NAME=...' erneut versuchen)
endif

CONFIG_TARGET_PATH:=$(shell pwd)

.PHONY: all install install_configs

all: install

install: install_configs

install_configs:
	$(MAKE) -C $(CONFIG_SOURCE_PATH) install


