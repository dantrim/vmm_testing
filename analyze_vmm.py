#!/usr/bin/env python

from optparse import OptionParser

import sys
import os

import ROOT as r
r.PyConfig.IgnoreCommandLineOptions = True
r.gROOT.ProcessLine("gErrorIgnoreLevel = 3001;")
r.gStyle.SetOptStat(0)
r.gROOT.SetBatch(1)


output_dir = ""
vmm_id = ""

class ChannelGap :
    def __init__(self, channel, left, right, width) :
        self.channel_ = channel
        self.left_ = left
        self.right_ = right
        self.width_ = width
        self.vmm_ = ""

    def set_vmm(self, vmm) :
        self.vmm_ = vmm

    def vmm(self) :
        return self.vmm_
        

    def channel(self) :
        return self.channel_

    def left(self) :
        return self.left_

    def right(self) :
        return self.right_

    def width(self) :
        return self.width_

    def Print(self) :
        print "ChannelGap for VMM %s CH %02d :  [%d,%d] = %d"%(self.vmm(), self.channel(), self.left(), self.right(), self.width())

def vmm_id_from_file(input_file) :
    out = ""
    test = input_file.split("/")[-1]
    try :
        out = test.split("_")[-1].replace(".txt","")
    except :
        out = ""
    return out

def valid_input_file(input_file) :

    test = input_file.split("/")[-1]
    if not test.endswith(".txt") :
        print "ERROR Provided input file is not a text file"
        return False

    if not test.startswith("pdo_gaps_VMM_") :
        print "ERROR Provided input file is not correct format"
        return False

    if vmm_id_from_file(input_file) == "" :
        print "ERROR Cannot determine VMM ID from input file"
        return False

    return True

def get_dump_file(vmm_id) :

    test_dir = "./"
    test = "%spdo_dump_VMM_%s.root"%(test_dir, vmm_id)
    if not os.path.isfile(test) :
        print "ERROR Cannot find file containing PDO histograms"
        sys.exit()
    return test

def get_available_channels(rfile) :

    out = []

    for key in rfile.GetListOfKeys() :
        obj = key.ReadObj()
        if obj.InheritsFrom("TH1F") :
            name = obj.GetName()

            # expect histograms named PDOCHXX
            if "PDOCH" not in name : continue
            channel = name.replace("PDOCH","")
            channel = int(channel)
            out.append(channel)

    return out

def get_channel_spec_from_available(channels, channel_spec) :

    out = []
    cs = channel_spec.split(",")
    for c in cs :
        if "-" in c :
            cd = c.split("-")
            lower = int(cd[0])
            upper = int(cd[1])
            cdr = range(lower, upper+1)
            for d in cdr :
                if d in channels :
                    out.append(d)
                else :
                    print "WARNING Requested channel %d not found in channels from input file"%d
        else :
            if int(c) in channels :
                out.append(int(c))
            else :
                print "WARNING Requested channel %d not found in channels from input file"%int(c)
    return out

def gaps_for_channel(channel_request, list_of_gaps) :
    out = []
    for cg in list_of_gaps :
        if int(cg.channel()) == int(channel_request) :
            out.append(cg)
    return out

def get_gaps(input_file, vmm_id_in) :

    print "Collecting gaps from input file '%s'"%input_file

    lines = open(input_file).readlines()

    out = {}

    gaps = []
    channels_found = []
    #skip first line, it is a header
    for iline, line in enumerate(lines[1:]) :
        if not line : continue
        line = line.strip()
        line = line.split()
        ch = int(line[0])
        if ch not in channels_found :
            channels_found.append(ch)
        left = int(line[1])
        right = int(line[2])
        width = int(line[3])
        cg = ChannelGap(ch, left, right, width)
        cg.set_vmm(vmm_id_in)
        gaps.append(cg)

    channels_found = sorted(channels_found)

    for c in channels_found :
        out[c] = gaps_for_channel(c, gaps)

    return out

def is_valid_gap(gap) :

    is_valid = True

    if gap.left() == 0 or gap.left() == 1 :
        is_valid = False

    if gap.right() == 1023 or gap.right() == 1024 :
        is_valid = False

    if gap.right() < 200 and gap.width() > 10 :
        is_valid = False

    if gap.right() > 850 and gap.width() > 10 :
        is_valid = False

    return is_valid

def remove_spurious(glist) :

    # ignore gaps at the edges of the DAC window that are separated by a single code value
    
    out = []

    for ig, g in enumerate(glist) :
        if g.right() < 800 and g.left() > 200 :
            out.append(g)
            continue

        if g.right() > 800 and ig != (len(glist)-1) :
            next_gap_right = glist[ig+1]
            delta = (next_gap_right.left() - (g.right()+1))
            if not (delta < 3) :
                out.append(g)

        if g.left() < 180 and ig != 0 :
            prev_gap_left = glist[ig-1]
            delta = (g.left() - (prev_gap_left.right()+1))
            if not (delta < 3) :
                out.append(g)

    return out

def get_relevant_gaps(gaps) :
    out = {}
    for channel in gaps.keys() :
        glist = []
        gs = gaps[channel]

        gs = remove_spurious(gs)
        for g in gs :
            if is_valid_gap(g) :
                glist.append(g)

        out[channel] = glist
    return out
        

def get_gap_graphs(gaps, maxy) :

    out = []

    for gap in gaps :
        if not (gap.width() > 5) : continue

        if gap.left() == 0 or gap.left() == 1 : continue

        if gap.right() == 1023 or gap.right() == 1024 : continue

        g = r.TGraph(4)
        height = 0.5*maxy
        points = [ [gap.left(), 0], [gap.left(), height], [gap.right()+1, height], [gap.right()+1, 0] ]
        for ip, p in enumerate(points) :
            g.SetPoint(ip, p[0], p[1])
        g.SetFillStyle(3144)
        g.SetFillColor(r.kRed)
        out.append(g)

    return out


def make_overlay(channel, rfile, gaps) :

    global output_dir

    valid_gaps = []

    hc = rfile.Get("PDOCH%d"%channel)
    if not hc :
        print "ERROR Could not grab histogram for channel %d from input root file '%s'"%(channel, rfile.GetName())
    c = r.TCanvas("c_overlay_%d"%channel, "", 1200, 600)
    c.SetGrid(1,1)
    c.cd()

    hc.SetLineColor(r.kBlack)
    hc.SetFillColor(36)

    maxy = hc.GetMaximum()
    gap_graphs = get_gap_graphs(gaps, maxy)

    hc.Draw("hist")
    c.Update()
    for gg in gap_graphs :
        gg.Draw("f same")
    c.Update()

    oname = output_dir
    oname += "pulser_dac_scan_VMM_%s_CH_%02d"%(vmm_id, channel)
    c.SaveAs(oname + ".root")
    c.SaveAs(oname + ".pdf")


def make_overlay_plots(rfile, gap_map, channels) :

    for channel in gap_map.keys() :
        if channel in channels :
            make_overlay(channel, rfile, gap_map[channel])

def global_gap_summary(gap_map) :

    global output_dir
    global vmm_id

    c = r.TCanvas("c_global_gap_summary_VMM_%s"%vmm_id, "", 800, 600)
    c.SetGrid(1,1)
    c.SetLogy()
    c.cd()

    max_x = -1
    for ch, glist in gap_map.iteritems() :
        for g in glist :
            if g.width() > max_x : max_x = g.width()

    max_x = int(1.65*max_x)

    h = r.TH1F("h_global_gaps_VMM_%s"%vmm_id, "Gap Widths for VMM %s (global);Width [counts];Entries"%vmm_id, max_x, 0, max_x)
    h.SetLineWidth(r.kBlack)
    h.SetLineWidth(2)
    h.SetFillColor(46)

    for ch, glist in gap_map.iteritems() :
        for g in glist :
            h.Fill(g.width())
    c.Update()

    h.SetMaximum(10*h.GetMaximum())
    h.Draw("hist")
    c.Update()

    oname = output_dir
    oname += "global_gaps_VMM_%s"%vmm_id

    c.SaveAs(oname + ".pdf")
    c.SaveAs(oname + ".root")

    return max_x

def channel_gap_width_summary(xmax, channels, gap_map) :

    global output_dir
    global vmm_id

    c = r.TCanvas("c_channel_gap_width_summary_VMM_%s"%vmm_id, "", 800, 600)
    c.SetGrid(1,1)
    c.SetRightMargin(1.15*c.GetRightMargin())
    c.cd()

    #axis = r.TH2F("axis", "Channel Gap Summary VMM %s;Gap Width [counts]; Channel"%vmm_id, max_x, 0, max_x, 64, 0, 64)

    h = r.TH2F("h_channel_gap_width_summary_VMM_%s"%vmm_id, "Channel Gap Width Summary VMM %s;Gap Width [counts]; Channel"%vmm_id, xmax, 0, xmax, 64, 0, 64) 

    for ch, gaps in gap_map.iteritems() :
        for g in gaps :
            x = g.width()
            h.Fill(x, ch)
    c.Update()
    h.Draw("colz")
    c.Update()

    oname = output_dir
    oname += "channel_gap_width_VMM_%s"%vmm_id
    c.SaveAs(oname + ".pdf")
    c.SaveAs(oname + ".root")

def channel_gap_location_summary(xmax, channels, gap_map) :

    global output_dir
    global vmm_id

    c = r.TCanvas("c_channel_gap_location_summary_VMM_%s"%vmm_id, "", 800, 600)
    c.SetGrid(1,1)
    c.SetTickx(1)
    c.SetTicky(1)
    c.SetRightMargin(1.15*c.GetRightMargin())
    c.cd()

    h = r.TH2F("h_channel_gap_location_summary_VMM_%s"%vmm_id, "Channel Gap Location Summary VMM %s;Gap Location [counts];Channel"%vmm_id, 1023, 0, 1023, 64, 0, 64)


    n_gaps = {}
    n_gaps1 = {}
    n_gaps5 = {}
    
    for ch, gaps in gap_map.iteritems() :
        #ht = r.TH1F("h_tmp_gap_%s_%d"%(vmm_id, ch), "", 1023, 0, 1023)
        #print "GAPS FOR CHAN %d"%ch
        n_gaps[ch] = 0
        n_gaps1[ch] = 0
        n_gaps5[ch] = 0
        for g in gaps :
            n_gaps[ch] += 1
            if g.width() > 1 :
                n_gaps1[ch] += 1
            if g.width() > 5 :
                n_gaps5[ch] += 1

            #print "   >   [%d,%d] - %d"%(g.left(), g.right(), g.width())
            for i in xrange(g.left(), g.right()+2) :
                h.Fill(i, ch, g.width())

    h.Draw("colz")
    c.Update()

    hlines = []
    for i in xrange(64) :
        if i == 0 : continue
        if not i%2==0 : continue
        l = r.TLine(0, i, 1023, i) 
        l.SetLineStyle(2)
        l.SetLineWidth(1)
        hlines.append(l)
    for hl in hlines :
        hl.Draw()
        c.Update()

    oname = output_dir
    oname += "channel_gaps_location_VMM_%s"%vmm_id
    c.SaveAs(oname + ".pdf")
    c.SaveAs(oname + ".root") 

    # project
    cx = r.TCanvas("c_projx_VMM_%s"%vmm_id, "", 800, 600)
    cx.SetGrid(1,1)
    hx = r.TH1F("h_channels_n_gaps_VMM_%s"%vmm_id, "# Gaps Per Channel VMM %s;Channel;# Gaps"%vmm_id, 64, 0, 64)
    hx.SetLineColor(r.kBlack)

    h1 = r.TH1F("h_channels_n_gaps_1_VMM_%s"%vmm_id, "# Gaps Per Channel VMM %s;Channel;# Gaps"%vmm_id, 64, 0, 64)
    h1.SetLineColor(r.kBlue)
    h1.SetLineWidth(1)
    h1.SetLineStyle(1)

    h5 = r.TH1F("h_channels_n_gaps_5_VMM_%s"%vmm_id, "# Gaps Per Channel VMM %s;Channel;# Gaps"%vmm_id, 64, 0, 64)
    h5.SetLineColor(r.kRed)
    h5.SetLineWidth(1)
    h5.SetLineStyle(1)

    for ch, n in n_gaps.iteritems() :
        hx.SetBinContent(ch+1, n)
    hx.Draw("hist")
    cx.Update()

    for ch, n in n_gaps1.iteritems() :
        h1.SetBinContent(ch+1, n)
    h1.Draw("hist same")
    cx.Update()

    for ch, n in n_gaps5.iteritems() :
        h5.SetBinContent(ch+1, n)
    h5.Draw("hist same")
    cx.Update()

    leg = r.TLegend(0.75,0.74, 0.89, 0.89)
    leg.SetFillStyle(0)
    leg.AddEntry(hx, "Width > 0", "l")
    leg.AddEntry(h1, "Width > 1", "l")
    leg.AddEntry(h5, "Width > 5", "l")
    leg.Draw()

    oname = output_dir
    oname += "channels_n_gaps_VMM_%s"%vmm_id
    cx.SaveAs(oname + ".pdf")
    cx.SaveAs(oname + ".root")


def channel_gap_width_per_chan(xmax, channels, gap_map) :

    global vmm_id
    global output_dir

    for c in channels :
        gaps = gap_map[c]
        can = r.TCanvas("c_gap_widths_VMM_%s_CHAN_%d"%(vmm_id, c), "", 800, 600)
        can.SetGrid(1,1)
        can.cd()
        maxx = -1
        for g in gaps :
            if g.width() > maxx : maxx = g.width()
        maxx = int(3*maxx)

        h = r.TH1F("h_gap_widths_VMM_%s_CHAN_%d"%(vmm_id, c), "Gap Widths for VMM %s CHAN %d;Width [counts];Entries"%(vmm_id, c), maxx, 0, maxx)
        h.SetLineWidth(1)
        h.SetLineColor(r.kBlack)
        h.SetFillColor(31)

        for g in gaps :
            h.Fill(g.width())

        h.SetMaximum(1.6*h.GetMaximum())

        h.Draw("hist")
        can.Update()

        oname = output_dir
        oname += "gap_widths_VMM_%s_CHAN_%02d"%(vmm_id, c)
        can.SaveAs(oname + ".pdf")
        can.SaveAs(oname + ".root")


def make_gap_summary(channels, gap_map) :

    max_width = global_gap_summary(gap_map)

    channel_gap_width_summary(max_width, channels, gap_map)

    channel_gap_width_per_chan(max_width, channels, gap_map) 

    channel_gap_location_summary(max_width, channels, gap_map)

##########################################
# multi VMM ana

def make_multi_channel_gap_location_summary(channels, gaps_in) :

    c = r.TCanvas("c_multi_channel_gap_location_summary", "", 800, 600)
    c.SetGrid(1,1)
    c.SetTickx(1)
    c.SetTicky(1)
    c.SetRightMargin(1.15*c.GetRightMargin())
    c.cd()

    h = r.TH2F("h_multi_channel_gap_location_summary", "Channel Gap Location Summary (MULTI VMM);Gap Location [counts];Channel", 1023, 0, 1023, 64, 0, 64)
    n_gaps = {}
    n_gaps1 = {}
    n_gaps5 = {}

    for i in xrange(64) :
        n_gaps[i] = 0
        n_gaps1[i] = 0
        n_gaps5[i] = 0


    for vmm_id in gaps_in.keys() :
        gap_map = gaps_in[vmm_id]
        for ch, gaps in gap_map.iteritems() :
            for g in gaps :
                n_gaps[ch] += 1
                if g.width() > 1 :
                    n_gaps1[ch] += 1
                if g.width() > 5 :
                    n_gaps5[ch] += 1
                if g.width() > 50 :
                    g.Print()
                for i in xrange(g.left(), g.right()+2) :
                    h.Fill(i, ch, g.width())

    h.Draw("colz")
    c.Update()

    hlines = []
    for i in xrange(64) :
        if i == 0 : continue
        if not i%2==0 : continue
        l = r.TLine(0, i, 1023, i)
        l.SetLineStyle(2)
        l.SetLineWidth(1)
        hlines.append(l)
    for hl in hlines :
        hl.Draw()
        c.Update()

    oname = "./"
    oname += "multi_vmm_channel_gaps_location"
    c.SaveAs(oname + ".pdf")
    c.SaveAs(oname + ".root")

    # project
    cx = r.TCanvas("c_multi_projx", "", 800, 600)
    cx.SetGrid(1,1)
    h = r.TH1F("h_chan_n_gaps_multi_VMM", "# Gaps Per Channel (MULTI VMM);Channel;# Gaps", 64, 0, 64)
    h.SetLineColor(r.kBlack)

    h1 = r.TH1F("h_chan_n_gaps1_multi_VMM", "# Gaps Per Channel (MULTI VMM);Channel;# Gaps", 64, 0, 64)
    h1.SetLineColor(r.kBlue)

    h5 = r.TH1F("h_chan_n_gaps5_multi_VMM", "# Gaps Per Channel (MULTI VMM);Channel;# Gaps", 64, 0, 64)
    h5.SetLineColor(r.kRed)

    n_vmms = len(gaps_in.keys())
    for ch, n in n_gaps.iteritems() :
        h.SetBinContent(ch+1, n/n_vmms) 
    h.Draw("hist")
    cx.Update()

    for ch, n in n_gaps1.iteritems() :
        h1.SetBinContent(ch+1, n/n_vmms)
    h1.Draw("hist same")
    cx.Update()

    for ch, n in n_gaps5.iteritems() :
        h5.SetBinContent(ch+1, n/n_vmms)
    h5.Draw("hist same")
    cx.Update()

    leg = r.TLegend(0.75, 0.74, 0.89, 0.89)
    leg.SetFillStyle(0)
    leg.AddEntry(h, "Width > 0", "l")
    leg.AddEntry(h1, "Width > 1", "l")
    leg.AddEntry(h5, "Width > 5", "l")
    leg.Draw()

    oname = "./"
    oname += "multi_vmm_channels_n_gaps"
    cx.SaveAs(oname + ".pdf")
    cx.SaveAs(oname + ".root")

def make_multi_gap_width_summary(gaps_in) :

    c = r.TCanvas("c_multi_gap_width", "", 800, 600)
    c.SetRightMargin(1.15*c.GetRightMargin())
    c.SetGrid(1,1)
    c.SetLogy()
    c.cd()

    xmax = -1
    for vmm_id, gaplist in gaps_in.iteritems() :
        for ch, gaps in gaplist.iteritems() :
            for g in gaps :
                if g.width() > xmax : xmax = g.width()

    xmax = xmax + 10
   # xmax = int(2*xmax)

    h = r.TH1F("h_multi_gap_width", "Gap Width (MULTI VMM);Width [counts];Entries", xmax, 0, xmax) 
    h.SetLineColor(r.kBlack)
    h.SetFillColor(46)

    for vmm_id, gaplist in gaps_in.iteritems() :
        for ch, gaps in gaplist.iteritems() :
            for g in gaps :
                h.Fill(g.width())

    h.Draw("hist")
    c.Update()

    oname = "./"
    oname += "multi_vmm_gap_width_summary"
    c.SaveAs(oname + ".pdf")
    c.SaveAs(oname + ".root")

    return xmax

def make_multi_width_v_vmm(gaps_in, xmax) :

    c = r.TCanvas("c_multi_width_v_vmm", "", 800, 600)
    c.SetRightMargin(1.18*c.GetRightMargin())
    c.SetGrid(1,1)
    c.cd()

    widths = {}
    vmms = []

    for vmm_id, gaplist in gaps_in.iteritems() :
        widths[vmm_id] = []
        vmms.append(vmm_id)
        for ch, gaps in gaplist.iteritems() :
            for g in gaps :
                widths[vmm_id].append(g.width())

    n_y = len(gaps_in.keys())
    h = r.TH2F("h_multi_vmm_width_v_vmm", "Gap Widths vs VMM (MULTI VMM);Width [counts];VMM ID", xmax, 0, xmax, n_y, 0, n_y) 

    for ivmm, vmm in enumerate(vmms) :
        h.GetYaxis().SetBinLabel(ivmm+1, vmm)

    for ivmm, vmm in enumerate(vmms) :
        wlist = widths[vmm]
        for w in wlist :
            h.Fill(w, ivmm)

    h.Draw("colz")
    c.Update()

    oname = "./"
    oname += "multi_vmm_width_v_vmm_summary"
    c.SaveAs(oname + ".pdf")
    c.SaveAs(oname + ".root")
        

    

def summarize_multiple(multi_list) :

    global output_dir

    vmm_ids = multi_list.split(",")
    rfiles = {}
    gaps = {}
    channels = []

    for vmm_id in vmm_ids :
        pdo_dump = get_dump_file(vmm_id)
        rfile = r.TFile.Open(pdo_dump)
        if len(channels) == 0 :
            channels = get_available_channels(rfile)
        rfiles[vmm_id] = rfile

        fname = "pdo_gaps_VMM_%s.txt"%vmm_id
        chgaps = get_gaps(fname, vmm_id)
        chgaps = get_relevant_gaps(chgaps)
        gaps[vmm_id] = chgaps
    channels = sorted(channels)

    make_multi_channel_gap_location_summary(channels, gaps)

    maxx = make_multi_gap_width_summary(gaps)

    make_multi_width_v_vmm(gaps, maxx)

    return


def main() :

    global output_dir
    global vmm_id

    parser = OptionParser()
    parser.add_option("-i", "--input", help="Provide in put text file containing VMM channel gaps", default="")
    parser.add_option("-c", "--channel", help="Provide a specific channel (multiple can be separated by commas or dashes, e.g. 1,2,3 or 1-3)", default="")
    parser.add_option("-m", "--multi", help="Provide multiple VMM IDs (comma separated)", default="")
    (options, args) = parser.parse_args()

    input_file = options.input
    channel_spec = options.channel
    do_multi = options.multi

    if not (do_multi == "") :
        summarize_multiple(do_multi)
        return

    if input_file == "" :
        print "ERROR You did not provide an input file, exiting"
        sys.exit()

    if not valid_input_file(input_file) :
        sys.exit()

    vmm_id = vmm_id_from_file(input_file)

    print "Analyzing data from VMM %s"%vmm_id

    output_dir = "./vmm_pdo_scans_%s/"%vmm_id

    pdo_dump_file = get_dump_file(vmm_id)
    rfile = r.TFile.Open(pdo_dump_file)

    channels = get_available_channels(rfile)
    channels = sorted(channels)

    print 55 * "-"
    print "Found these channels in input file: "
    print channels

    if channel_spec != "" :
        channels = get_channel_spec_from_available(channels, channel_spec)

    channel_gaps = get_gaps(input_file, vmm_id)

    # remove gaps at the edges of the bulk of the PDO distribution
    channel_gaps_original = channel_gaps
    channel_gaps = get_relevant_gaps(channel_gaps)

    for cr in channels :
        if cr not in channel_gaps.keys() : 
            print "WARNING Did not find requested channel %d after collecting channel gaps from text file"%int(cg)
    make_overlay_plots(rfile, channel_gaps, channels)

    make_gap_summary(channels, channel_gaps)

#__________________________________________________________________
if __name__ == "__main__" :
    main()
