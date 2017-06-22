#!/usr/bin/env python

#ROOT
import ROOT as r
r.gROOT.SetBatch(1)
r.gStyle.SetOptStat(0)
r.PyConfig.IgnoreCommandLineOptions = True
r.gROOT.ProcessLine( "gErrorIgnoreLevel = 3001;")
r.TCanvas.__init__._creates = False
r.TH1F.__init__._creates = False

import sys #exit
import os #abspath

from optparse import OptionParser
import subprocess

class RunParams :
    """
    a little struct to hold the run properties
    """
    def __init__(self) :
        self.gain = 0.0
        self.tac = 0.0
        self.threshold = 0.0
        self.peak_time = 0.0

    def Print(self) :
        print "RunParams    gain: %.2f    tac: %d    threshold: %d    peak_time: %d"%(float(self.gain), int(self.tac), int(self.threshold), int(self.peak_time))

    def summary_text(self) :
        txt = "gain: %.2f  threshold: %d    peak time: %d    tac: %d"%(float(self.gain), int(self.threshold), int(self.peak_time), int(self.tac))
        return txt

class Gap :
    def __init__(self, start, stop, text_height) :
        self.start = start
        self.stop = stop
        self.text_height = text_height
        self.width = (stop - start)

    def description(self) :
        x = "PDO code gap: start=%d stop=%d width=%d"%(self.start, self.stop, self.width)
        return x

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
    return h, filled_pdo
    

def draw_text(x=0.7, y=0.65, font=42, color=r.kBlack, text="", size=0.04, angle=0.0) :
    '''
    Draw text on the current pad
    (coordinates are normalized to the current pad)
    '''
    l = r.TLatex()
    l.SetTextSize(size)
    l.SetTextFont(font)
    l.SetNDC()
    l.SetTextColor(color)
    l.SetTextAngle(angle)
    l.DrawLatex(x, y, text)

def draw_text_on_top(text="", size=0.04, pushright=1.0, pushup=1.0) :
    """
    utility method to write text
    directly above the plot pad
    """

    s = size
    t = text
    top_margin = r.gPad.GetTopMargin()
    left_margin = r.gPad.GetLeftMargin()
    xpos = pushright * left_margin
    ypos = 1.0 - 0.87*top_margin
    ypos *= pushup
    #draw_text(x=xpos, y=1.0-0.85*top_margin, text=t, size=s)
    draw_text(x=xpos, y=ypos, text=t, size=s)
    

def get_non_empty_pdo(tree, channels, step_size) :
    """
    loops over the pdo distribution
    and finds non-empty codes
    """

    print "get_non_empty_pdo    (%d channels to test)"%len(channels)

    pdo_dict = {}
    histo_dict = {}
    bad_channels = []
    for ich, ch in enumerate(channels) :
        print "get_non_empty_pdo    [%02d/%02d] channel # %d"%(ich+1, len(channels), ch)
        pdo_histo, pdo_list = get_pdos(tree, ch)
        if len(pdo_list) > 0 :
            #pdo_dict[ch] = get_pdos(tree, ch)
            pdo_dict[ch] = pdo_list
            histo_dict[ch] = pdo_histo
        else :
            print "get_non_empty_pdo    WARNING List of non-empty PDO codes for channel %d is empty! This channel may be dead -- not considering it further"%ch
            bad_channels.append(str(ch))
    return histo_dict, pdo_dict, bad_channels

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
    range_dict = {}
    for ich, ch in enumerate(channels) :
        #print " > channel %d"%ch

        # we may have removed some channels from the list
        try :
            tmp = pdo_dict[ch]
        except :
            continue

        sorted_pdos = sorted(pdo_dict[ch])
        range_dict[ch] = [sorted_pdos[0], sorted_pdos[-1]]
    
        gaps = get_gaps(pdo_dict[ch])

        gaps = list(window_ranges(list(gaps)))
        gaps = [g for g in gaps if ((g[1] - g[0]) >= min_gap_size)]
        #print gaps
        gap_dict[ch] = gaps
    return gap_dict, range_dict

def make_gap_graph(gap, maxy, highest, lowest) :
    g = r.TGraph(5)

    width = int(gap[1] - gap[0])
    g.SetLineWidth(2)

    in_bulk = ( (gap[1] < 0.95*highest) and (gap[0] > 1.05*lowest) )

    if width < 6 :
        g.SetLineColor(r.kRed)
        g.SetLineWidth(1)
        g.SetLineStyle(2)
        g.SetFillColor(0)
        g.SetFillStyle(0)
    elif width != 64 :
        g.SetLineColor(r.kRed)
        g.SetLineWidth(2)
        g.SetLineStyle(1)
        g.SetFillColor(r.kRed)
        #if not in_bulk :
        g.SetFillStyle(3354)
        #else :
        #    g.SetFillStyle(1001)
    elif width == 64 :
        g.SetLineColor(r.kRed)
        g.SetLineWidth(2)
        g.SetLineStyle(1)
        g.SetFillColor(r.kRed)
        g.SetFillStyle(1001)


    g.SetPoint(0, gap[0]+3, 0)
    g.SetPoint(1, gap[0]+3, 0.1*maxy)
    g.SetPoint(2, gap[1]+3, 0.1*maxy)
    g.SetPoint(3, gap[1]+3, 0)
    g.SetPoint(4, gap[0]+3, 0)

    #text = r.TLatex()
    #text.SetTextSize(0.2*text.GetTextSize())
    #text.SetTextFont(42)
    #text.DrawLatex(gap[0]+3, 0.11*maxy, "%d"%width) 

    gap_struct = Gap(gap[0]+3, gap[1]+3, 0.1*maxy)

    return g, gap_struct

def summary_plot(histo, gaps, ranges, channel, vmm_id, run_params, outdir) :

    c = r.TCanvas("c_pulser_dac_scan_vmm_%s_channel_%d"%(str(vmm_id), int(channel)), "", 800, 600)
    c.SetGrid(1,1)
    c.SetTickx(1)
    c.SetTicky(1)
    c.cd()

    # first make the full pdo spectrum
    h_pdo = histo #r.TH1F("h_pdo_%d_%s"%(channel, str(vmm_id)), "PDO for VMM %s - Channel %d;pdo [counts];Entries"%(str(vmm_id), int(channel)), 1020, 0, 1020)
    h_pdo.SetTitle("PDO for VMM %s - Channel %d"%(str(vmm_id), int(channel)))
    h_pdo.GetXaxis().SetTitle("pdo [counts]")
    h_pdo.GetYaxis().SetTitle("Entries")
    h_pdo.SetLineColor(r.kBlack)
    h_pdo.SetFillColor(38)
    h_pdo.Sumw2()

    #cmd = "pdo>>%s"%h_pdo.GetName()
    #cut = "channel==%d"%channel
    #cut = r.TCut(cut)
    #sel = r.TCut("1")
    #tree.Draw(cmd, cut * sel, "goff")
    #h_pdo.Draw("hist")

    maxy = h_pdo.GetMaximum()
    h_pdo.SetMaximum(1.1*maxy)
    h_pdo.GetXaxis().SetNdivisions(50)
    h_pdo.GetXaxis().SetLabelSize(0.5*h_pdo.GetXaxis().GetLabelSize())

    gap_graphs = []
    gap_structs = []
    lowest_pdo = ranges[0]
    highest_pdo = ranges[1]
    for g in gaps :
        # don't mark places where we don't expect pdos
        if g[0] <= lowest_pdo : continue
        if g[1] >= highest_pdo : continue
        graph, gap_struct = make_gap_graph(g, maxy, highest_pdo, lowest_pdo)
        gap_graphs.append(graph)
        gap_structs.append(gap_struct)
        #gap_graphs.append(make_gap_graph(g, maxy, highest_pdo, lowest_pdo))

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
    text.DrawLatexNDC(0.12,0.85, header)
    text.DrawLatexNDC(0.12,0.82, vmm)
    c.Update()

    gap_text = r.TLatex()
    gap_text.SetTextFont(42)
    gap_text.SetTextSize(0.25*gap_text.GetTextSize())
    for gap in gap_structs :
        #print "   -> gap found : %s"%gap.description()
        gap_text.SetTextSize(0.3*text.GetTextSize())
        gap_text.DrawLatex(gap.start, gap.text_height + 10, "%d"%gap.width)
        c.Update()

    draw_text_on_top(text=run_params.summary_text(), size=0.03)
    c.Update()

    
    #dir_name = "vmm_scans_%s"%(str(vmm_id))
    dir_name = outdir
    mkdir_cmd = "mkdir -p %s"%(str(dir_name))
    subprocess.call(mkdir_cmd, shell=True)

    save_name = "./%s/vmm_pulser_dac_scan_VMM_%s_channel%d.eps"%(dir_name, str(vmm_id), int(channel))
    c.SaveAs(save_name)

    # save for html (only renders png ??)
    save_name = save_name.replace(".eps",".png")
    html_dir = "./" + dir_name + "/for_html/" 
    mkdir_cmd = "mkdir -p %s"%(str(html_dir))
    subprocess.call(mkdir_cmd, shell=True)

    html_save = html_dir + save_name.split("/")[-1]
    #print "HTML save: %s"%html_save
    c.SaveAs(html_save)

    # save the ROOT file to store the objects
    save_name = save_name.replace(".png",".root")
    c.SaveAs(save_name)


def make_summary_plots(histo_dict, gap_dict, range_dict, channels, vmm_id, run_params, outdir) :

    for ich, ch in enumerate(channels) :

        # we may have removed some channels from the list
        try :
            x = gap_dict[ch]
        except :
            continue
        gaps = gap_dict[ch]

        summary_plot(histo_dict[ch], gaps, range_dict[ch], ch, vmm_id, run_params, outdir)

def get_run_params(chain) :
    """
    fill run properties struct using
    first event in the input chain
    """
    rp = RunParams()
    for ievent, event in enumerate(chain) :
        if ievent >=1 : break
        rp.gain = event.gain
        rp.tac = event.tacSlope
        rp.threshold = event.dacCounts
        rp.peak_time = event.peakTime
    #rp.Print()
    return rp

def run_html(outdir, vmm_id, open_html_page, n_channels) :

    html_filename = "%s/vmm_pdo_scans_%s.html"%(outdir, vmm_id)
    html_cmd = "./makeplots.sh %s/ %s 'VMM %s : %d channels'"%(outdir, html_filename, vmm_id, int(n_channels)) 
    subprocess.call(html_cmd, shell=True)

    open_cmd = "open %s"%(html_filename)
    if open_html_page :
        if os.path.exists(html_filename) :
            print "Opening HTML plot dump..."
            subprocess.call(open_cmd, shell=True)
        else :
            print "run_html    HTML file was not found!"

def main() :

    parser = OptionParser()
    parser.add_option("-i", "--input", default="", help="Input ROOT calib file")
    parser.add_option("--step", default="1", help="Step size used in the DAC scan")
    parser.add_option("--dac-start", dest="dac_start", default="0", help="Initial DAC value in the scan")
    parser.add_option("--dac-end", dest="dac_end", default="1023", help="Final DAC value in the scan")
    parser.add_option("--vmm-id", dest="vmm_id", default="X", help="VMM serial number printed on the chip")
    parser.add_option("--channel", dest="spec_chan", default="", help="Choose a set of channels to look at [default: all] (comma separated: e.g., '1,2,3')")
    parser.add_option("--no-html", action="store_true", default=False, help="Do not open up the HTML plot dump")
    parser.add_option("--chip-no", dest="chip_no", default="0", help="Choose a specific chip if on a multi-chip board/readout")
    (options, args) = parser.parse_args()
    input_file = options.input
    step_size = options.step
    dac_start = options.dac_start
    dac_end = options.dac_end
    vmm_id = options.vmm_id
    spec_chan = options.spec_chan
    no_html = options.no_html
    chip_no = options.chip_no

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
    pdo_histo_dict, present_pdo_dict, bad_channels = get_non_empty_pdo(chain, channels, step_size)

    if len(bad_channels) > 0 :

        bad_channel_list = ",".join(bad_channels)
        print "Removing bad channels: %s"%bad_channel_list

        new_channels = []
        for ch in channels :
            if ch not in bad_channels :
                new_channels.append(ch)
        channels = new_channels

    if len(present_pdo_dict.keys()) == 0 :
        print "WARNING No non-empty PDO codes for any channel! Inspect the input file to be sure that everything looks ok. Exiting."
        sys.exit()

    # dictionary of { channel : [ gap bigger than or eqaul to 'min_gap_size' pdo codes ] }
    min_gap_size = 5
    print 55*"- "
    print "Minimum gap size considered: 5 PDO codes"
    print 55*" -"
    pdo_gap_dict, pdo_range_dict = get_pdo_gaps(present_pdo_dict, min_gap_size, channels)

    run_params = get_run_params(chain)

    # where to dump the output plots and root files
    output_dir = "vmm_pdo_scans_%s"%str(vmm_id)

    make_summary_plots(pdo_histo_dict, pdo_gap_dict, pdo_range_dict, channels, vmm_id, run_params, output_dir)

    print 55*"-"
    print "Output plots and root files saved to: %s"%os.path.abspath(output_dir)
    print 55*"-"

    open_html = not no_html
    run_html(os.path.abspath(output_dir), str(vmm_id), open_html, len(channels))


    #x = raw_input("blah")

#_______________________________________
if __name__ == "__main__" :
    main()
