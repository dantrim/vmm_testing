# makefile for generic c++ project
# generated with `makeproject` on Mon Feb 27 14:42:26 CET 2017
# Author: Dan Guest <dguest@cern.ch>

# _______________________________________________________________
# Basic Setup

# --- set dirs
BUILD        := build
SRC          := src
INC          := include
DICT         := dict
OUTPUT       := bin
LIB          := lib

#  set search path
vpath %.cxx  $(SRC)
vpath %.hh   $(INC)
vpath %.h    $(INC)
vpath %.hpp  $(INC)
vpath %Dict.h $(DICT)
vpath %Dict.cxx $(DICT)

# --- set compiler and flags (roll c options and include paths together)
CXX          ?= g++
CXXFLAGS     := -O2 -Wall -fPIC -I$(INC) -g -std=c++11
LIBS         := # blank, more will be added below
LDFLAGS      := # blank, more will be added below

# ---- define objects from files in the SRC directory
GEN_OBJ_SRC   := $(wildcard $(SRC)/*.cxx)
GEN_OBJ       := $(notdir $(GEN_OBJ_SRC:%.cxx=%.o))

# this list may be manipulated in other segments further down
GEN_OBJ_PATHS := $(GEN_OBJ:%=$(BUILD)/%)

# --- all top level (added further down)
ALL_TOP_LEVEL := # blank, more will be added below

# _______________________________________________________________
# Add Top Level Objects

# --- stuff used for the c++ executable
# everything with this prefix will be built as an executable
EXE_PREFIX   := vmmtest_

ALL_EXE_SRC   := $(wildcard $(SRC)/$(EXE_PREFIX)*.cxx)
ALL_EXE       := $(notdir $(ALL_EXE_SRC:%.cxx=%))
ALL_EXE_PATHS := $(ALL_EXE:%=$(OUTPUT)/%)

# filter out the general objects
GEN_OBJ_PATHS := $(filter-out $(BUILD)/$(EXE_PREFIX)%.o,$(GEN_OBJ_PATHS))

# add to all top level
ALL_TOP_LEVEL += $(ALL_EXE_PATHS)

# _______________________________________________________________
# Add ROOT dicts

# Edit `DICT_FILES` if you want to add more dictionaries
#DICT_FILES     := $(INC)/Stl.h
#TDICTS         := $(notdir $(DICT_FILES:.h=Dict.o))
#TDICT_PATHS    := $(TDICTS:%=$(BUILD)/%)
#GEN_OBJ_PATHS  += $(TDICT_PATHS)
## prevent auto-deletion of dictionary objects
#.SECONDARY: $(TDICT_PATHS)

# _______________________________________________________________
# Add Libraries

# --- load in root config
ROOTCFLAGS    := $(shell root-config --cflags)
ROOTLIBS      := $(shell root-config --libs)
# ROOTLIBS      += -lCore -lTree -lRIO
ROOTLDFLAGS   := $(shell root-config --ldflags)

CXXFLAGS     += $(ROOTCFLAGS)
LDFLAGS      += $(ROOTLDFLAGS)
LIBS         += $(ROOTLIBS)
LIBS         += ./lib/StlLib.so

# --- first call here
all: $(ALL_TOP_LEVEL)

# _______________________________________________________________
# Add Build Rules

# build exe
$(OUTPUT)/$(EXE_PREFIX)%: $(GEN_OBJ_PATHS) $(BUILD)/$(EXE_PREFIX)%.o
	@mkdir -p $(OUTPUT)
	@echo "linking $^ --> $@"
	@$(CXX) -o $@ $^ $(LIBS) $(LDFLAGS)

# compile rule
$(BUILD)/%.o: %.cxx
	@echo compiling $<
	@mkdir -p $(BUILD)
	@$(CXX) -c $(CXXFLAGS) $< -o $@

# --- ROOT dictionary generation
LINKDEF := $(INC)/LinkDef.h
SEDSTR  := 's,\\\#include "\$(INC)/\(.*\)",\\\#include "\1",g'
ROOT_DICT_TMP := /tmp/rootbuild
TMPDIR  := $(shell mktemp -d $(ROOT_DICT_TMP).XXXX)
#$(DICT)/%Dict.cxx: %.h $(LINKDEF)
#	@echo making dict $@
#	@mkdir -p $(DICT)
#	@rm -f $(DICT)/$*Dict.h $(DICT)/$*Dict.cxx
#	@rootcint $@ -c $(INC)/$*.h $(LINKDEF)
#	@sed $(SEDSTR) $(DICT)/$*Dict.h > $(TMPDIR)/$*Dict.h
#	@mv -f -- $(TMPDIR)/$*Dict.h $(DICT)/$*Dict.h

#$(BUILD)/%Dict.o: $(DICT)/%Dict.cxx
#	@mkdir -p $(BUILD)
#	@echo compiling dict $@
#	@$(CXX) $(CXXFLAGS) $(ROOTCFLAGS) -c $< -o $@ 2> /dev/null

# use auto dependency generation
ALLOBJ       := $(GEN_OBJ)
DEP          := $(BUILD)

ifneq ($(MAKECMDGOALS),clean)
ifneq ($(MAKECMDGOALS),rmdep)
include  $(ALLOBJ:%.o=$(DEP)/%.d)
endif
endif

DEPTARGSTR = -MT $(BUILD)/$*.o -MT $(DEP)/$*.d
$(DEP)/%.d: %.cxx
	@echo making dependencies for $<
	@mkdir -p $(DEP)
	@$(CXX) -MM -MP $(DEPTARGSTR) $(CXXFLAGS) $(PY_FLAGS) $< -o $@

# clean
.PHONY : clean rmdep all
CLEANLIST     = *~ *.o *.o~ *.d core
clean:
	rm -fr $(CLEANLIST) $(CLEANLIST:%=$(BUILD)/%) $(CLEANLIST:%=$(DEP)/%)
	rm -fr $(BUILD) $(DICT) $(OUTPUT) $(ROOT_DICT_TMP).*

rmdep:
	rm -f $(DEP)/*.d
