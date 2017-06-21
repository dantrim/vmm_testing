#!/usr/bin/env python

import ROOT as r
r.gROOT.SetBatch(1)
r.PyConfig.IgnoreCommandLineOptions = True

import sys

from optparse import OptionParser
import subprocess

def main() :

    parser = OptionParser()
    parser.add_option("-i", "--input", default="")
    parser.add_option("--step", default="")
    parser.add_option("--dac-start", dest="dac_start", default="")
    parser.add_option("--dac-end", dest="dac_end", default="")
    (options, args) = parser.parse_args()
    input_file = options.input
    step_size = options.step
    dac_start = options.dac_start
    dac_end = options.dac_end

    rfile = r.TFile.Open(input_file)
    check_tree = rfile.Get("calib")
    if not check_tree :
        print "ERROR Input file '%s' does not contain the calib ntuple!"%input_file
        sys.exit()

    chain = r.TChain("calib")
    chain.AddFile(input_file) 


#_______________________________________
if __name__ == "__main__" :
    main()
