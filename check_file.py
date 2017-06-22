#!/usr/bin/env python

import ROOT as r
r.gROOT.SetBatch(0)
r.gStyle.SetOptStat(0)

import sys


def main() :

    infile = sys.argv[1]
    chain = r.TChain("calib")
    chain.AddFile(infile)

    c = r.TCanvas("c","",1200,600)
    c.Divide(1,2)

    c.cd(1)
    h = r.TH1F("h_pulser", "Pulser DAC;counts;entries", 510,0,1020)
    h.SetLineWidth(1)
    chain.Draw("pulserCounts>>%s"%h.GetName())
    c.Update()

    c.cd(2)
    h2 = r.TH2F("h2", "PDO vs Pulser DAC;Pulser DAC;PDO",80,0,1020,80,0,1020)
    chain.Draw("pdo:pulserCounts>>%s"%h2.GetName(), "", "colz")
    c.Update()
    c.Draw()

    x = raw_input("Press any key to exit")

    

#_____
if __name__ == "__main__" :
    main()
