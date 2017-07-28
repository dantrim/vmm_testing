#!/bin/bash

rootcint -f StlDict.cxx -c StlDict.cxx -c ./include/Stl.h ./include/Stl.h ./include/LinkDef.h
mkdir -p ./lib/
g++ -o ./lib/StlLib.so StlDict.cxx `root-config --cflags --libs` -shared -fPIC
