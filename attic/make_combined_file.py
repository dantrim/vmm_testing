#!/usr/bin/env python

import ROOT as r
r.gStyle.SetOptStat(0)
r.gROOT.SetBatch(0)

import sys

import glob

def get_channel_number(filename) :
    filename = filename.split("/")[-1]
    ch = filename.split("channel")[-1].replace(".root","")
    return int(ch)

def main() :

    vmm_number = int(sys.argv[1])

    print "getting files for VMM # %d"%vmm_number

    dirname = "./vmm_pdo_scans_%d/"%vmm_number
    files = glob.glob(dirname + "vmm_pulser_dac_scan_VMM_%d_channel*.root"%vmm_number)

    outfilename = "combined_vmm_%d_pdo.root"%vmm_number
    rfile = r.TFile(outfilename, "RECREATE")

    channels = []
    for f in files :
        ch_number = get_channel_number(f)
        channels.append(ch_number)

    channels = sorted(channels)

    for ch in channels :
        for f in files :
            if not (ch == get_channel_number(f)) : continue
            hfile = r.TFile.Open(f)
            c_name = "c_pulser_dac_scan_vmm_%d_channel_%d"%(vmm_number, ch) 
            c = hfile.Get(c_name)

            h = None
            hname = "h_pdo_ch_%d"%ch
            for x in c.GetListOfPrimitives() :
                if x.GetName() == hname :
                    h = x

            hnew = h.Clone("PDOCH%d"%ch)
            rfile.cd()
            hnew.Write()

            #c.ls()
            
    

    
    


#____
if __name__ == "__main__" :
    main()
