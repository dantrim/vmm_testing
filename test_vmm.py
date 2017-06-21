#!/usr/bin/env python

import ROOT as r
r.gROOT.SetBatch(1)
r.gStyle.SetOptStat(0)
r.PyConfig.IgnoreCommandLineOptions = True

import sys

from optparse import OptionParser
import subprocess

def channels_tested(tree) :
    """
    find the channels that we pulsed
    """

    h = r.TH1F("h_chan", "", 64, 0, 64)
    cmd = "channel>>h_chan"

    tree.Draw(cmd, "1", "goff")

    n_bins = h.GetNbinsX()

    filled_channels = []
    for ibin in xrange(n_bins) :
        is_filled = (int(h.GetBinContent(ibin+1)) > 0)
        if is_filled :
            filled_channels.append(ibin)

    return filled_channels

def get_pdos(tree, channel) :
    """
    get the non-empty pdo codes
    for the given channel
    """

    h = r.TH1F("h_pdo_ch_%d"%channel, "", 505, 10, 1020)

    cmd = "pdo>>%s"%h.GetName()
    cut = "channel==%s"%channel
    sel = r.TCut("1")
    cut = r.TCut(cut)

    tree.Draw(cmd, cut * sel, "goff")

    filled_pdo = []
    n_bins = h.GetNbinsX()
    for ibin in xrange(n_bins) :
        is_filled = (int(h.GetBinContent(ibin+1)) > 0)
        if is_filled :
            filled_pdo.append(int(h.GetBinLowEdge(ibin)))
            #lower_edge = int(h.GetBinLowEdge(ibin))
            #upper_edge = int(h.GetBinLowEdge(ibin)) + h.GetBinWidth(ibin)
            #test_width = (upper_edge - lower_edge)
            #h_width = h.GetBinWidth(ibin)
            #print "test_width = %d    h_width = %d"%(test_width, h_width)
            #if test_width != h_width :
            #    print " > WIDTHS DIFFER"
            #if h.GetBinWidth(ibin) != 1 :
            #    filled_pdo.append(int(filled_pdo[-1]) + int(h.GetBinWidth(ibin)))
            #filled_pdo.append(ibin)
    return filled_pdo
    
    

def get_non_empty_pdo(tree, channels, step_size) :
    """
    loops over the pdo distribution
    and finds non-empty codes
    """

    print "get_non_empty_pdo    (%d channels to test)"%len(channels)

    pdo_dict = {}
    for ich, ch in enumerate(channels) :
        print "get_non_empty_pdo    [%02d/%02d] channel # %d"%(ich+1, len(channels), ch)
        pdo_list = get_pdos(tree, ch)
        if len(pdo_list) > 0 :
            pdo_dict[ch] = get_pdos(tree, ch)
        else :
            print "get_non_empty_pdo    WARNING List of non-empty PDO codes for channel %d is empty! This channel may be dead -- not considering it further"%ch
    return pdo_dict

def get_gaps(pdo_list) :

    return set(range(pdo_list[len(pdo_list)-1])[1:]) - set(pdo_list)

def window_ranges(list_to_test) :
    start, end = list_to_test[0], list_to_test[0]
    count = start
    for item in list_to_test :
        if not count == item :
            yield start, end
            start, end = item, item
            count = item
        end = item
        count += 1
    yield start, end

def get_pdo_gaps(pdo_dict, min_gap_size, channels) :

    print 40 * "- "
    print "get_pdo_gaps"

    gap_dict = {}
    for ich, ch in enumerate(channels) :
        print "channel %d"%ch

        # we may have removed some channels from the list
        try :
            tmp = pdo_dict[ch]
        except :
            continue
        gaps = get_gaps(pdo_dict[ch])

        gaps = list(window_ranges(list(gaps)))
        gaps = [g for g in gaps if ((g[1] - g[0]) >= min_gap_size)]
        print gaps
        gap_dict[ch] = gaps
    return gap_dict

def make_gap_graph(gap, maxy) :

    
    g = r.TGraph(5)

    width = int(gap[1] - gap[0])
    g.SetLineWidth(2)
    if width < 6 :
        g.SetLineColor(r.kRed)
        g.SetLineWidth(1)
        g.SetLineStyle(2)
        g.SetFillColor(0)
    else :
        g.SetLineColor(r.kRed)
        g.SetLineWidth(2)
        g.SetLineStyle(1)
        g.SetFillColor(r.kRed)

    g.SetPoint(0, gap[0], 0)
    g.SetPoint(1, gap[0], 0.1*maxy)
    g.SetPoint(2, gap[1], 0.1*maxy)
    g.SetPoint(3, gap[1], 0)
    g.SetPoint(4, gap[0], 0)

    return g

def summary_plot(tree, gaps, channel, vmm_id) :

    c = r.TCanvas("c_pulser_dac_scan_vmm_%s_channel_%d"%(str(vmm_id), int(channel)), "", 800, 600)
    c.SetGrid(1,1)
    c.cd()

    # first make the full pdo spectrum
    h_pdo = r.TH1F("h_pdo_%d_%s"%(channel, str(vmm_id)), "PDO for VMM %s - Channel %d;pdo [counts];Entries"%(str(vmm_id), int(channel)), 1020, 0, 1020)
    h_pdo.SetLineColor(r.kBlack)
    h_pdo.SetFillColor(38)
    h_pdo.Sumw2()

    cmd = "pdo>>%s"%h_pdo.GetName()
    cut = "channel==%d"%channel
    cut = r.TCut(cut)
    sel = r.TCut("1")
    tree.Draw(cmd, cut * sel, "goff")
    h_pdo.Draw("hist")

    maxy = h_pdo.GetMaximum()
    h_pdo.SetMaximum(1.1*maxy)
    h_pdo.GetXaxis().SetNdivisions(50)
    h_pdo.GetXaxis().SetLabelSize(0.5*h_pdo.GetXaxis().GetLabelSize())

    gap_graphs = []
    for g in gaps :
        gap_graphs.append(make_gap_graph(g, maxy))

    c.cd()
    h_pdo.Draw("hist")
    c.Update()
    for g in gap_graphs :
        g.Draw("lf same")
        c.Update()


    text = r.TLatex()
    text.SetTextFont(42)
    text.SetTextSize(0.8*text.GetTextSize())

    header = "#bf{ATLAS} #it{Preliminary}"
    vmm = "#bf{VMM3} - ID %s - Channel %d"%(str(vmm_id), int(channel))
    text.DrawLatex(35,maxy, header)
    text.DrawLatex(35,0.95*maxy, vmm)
    c.Update()

    
    dir_name = "vmm_scans_%s"%(str(vmm_id))
    mkdir_cmd = "mkdir -p %s"%(str(dir_name))
    subprocess.call(mkdir_cmd, shell=True)

    save_name = "./%s/vmm_pulser_dac_scan_VMM_%s_channel%d.png"%(dir_name, str(vmm_id), int(channel))
    c.SaveAs(save_name)
    save_name = save_name.replace(".png",".root")
    c.SaveAs(save_name)

def make_summary_plots(tree, gap_dict, channels, vmm_id) :

    for ich, ch in enumerate(channels) :

        # we may have removed some channels from the list
        try :
            x = gap_dict[ch]
        except :
            continue
        gaps = gap_dict[ch]

        summary_plot(tree, gaps, ch, vmm_id)

def main() :

    parser = OptionParser()
    parser.add_option("-i", "--input", default="")
    parser.add_option("--step", default="1")
    parser.add_option("--dac-start", dest="dac_start", default="0")
    parser.add_option("--dac-end", dest="dac_end", default="1023")
    parser.add_option("--vmm-id", dest="vmm_id", default="X")
    parser.add_option("--channel", dest="spec_chan", default="")
    (options, args) = parser.parse_args()
    input_file = options.input
    step_size = options.step
    dac_start = options.dac_start
    dac_end = options.dac_end
    vmm_id = options.vmm_id
    spec_chan = options.spec_chan

    if vmm_id == "X" :
        print "You must provide a vmm id, exiting"
        sys.exit()
    if input_file == "" :
        print "No input file provided, exiting"
        sys.exit()

    rfile = r.TFile.Open(input_file)
    check_tree = rfile.Get("calib")
    if not check_tree :
        print "ERROR Input file '%s' does not contain the calib ntuple!"%input_file
        sys.exit()

    chain = r.TChain("calib")
    chain.AddFile(input_file) 

    # get a list of non-empty channels
    channels = channels_tested(chain)

    if spec_chan != "" :
        spec_chan = spec_chan.split(",")
        new_channels = []
        for ch in channels :
            if str(ch) in spec_chan :
                new_channels.append(ch)
        channels = new_channels

    if len(channels) == 0 :
        print "No channels found in input file, exiting"
        sys.exit()

    # dictionary of { channel : [list of non-empty pdo codes] }
    present_pdo_dict = get_non_empty_pdo(chain, channels, step_size)

    if len(present_pdo_dict.keys()) == 0 :
        print "WARNING No non-empty PDO codes for any channel! Inspect the input file to be sure that everything looks ok. Exiting."
        sys.exit()

    # dictionary of { channel : [ gap bigger than or eqaul to 'min_gap_size' pdo codes ] }
    min_gap_size = 5
    print 55*"- "
    print "Minimum gap size considered: 5 PDO codes"
    print 55*" -"
    pdo_gap_dict = get_pdo_gaps(present_pdo_dict, min_gap_size, channels)

    make_summary_plots(chain, pdo_gap_dict, channels, vmm_id)


#_______________________________________
if __name__ == "__main__" :
    main()
