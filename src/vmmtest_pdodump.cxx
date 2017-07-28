
//std/stl
#include <string>
#include <iostream>
#include <sstream>
#include <fstream>
#include <iomanip>
#include <map>
#include <set> // set_difference
#include <algorithm>
using namespace std;

//ROOT
#include "TROOT.h"
#include "TStyle.h"
#include "TFile.h"
#include "TH1F.h"
#include "TCut.h"
#include "TBranch.h"
#include "TTree.h"

///////////////////////////////////////////////////////////////////////////////
//
// pdo_dump
//
// script to make the histograms of PDO for each channel
// in the input ROOT file
//
// daniel.joseph.antrim@cern.ch
// July 2017
//
///////////////////////////////////////////////////////////////////////////////


void help()
{

    cout << "-----------------------------------------------------------------" << endl;
    cout << " PDO dump " << endl;
    cout << endl;
    cout << " Usage: ./vmmtest_pdodump -i <input-calib-file> -v <vmm-id>" << endl;
    cout << endl;
    cout << " Options:" << endl;
    cout << "  -i|--input           input ROOT ntuple [REQUIRED]" << endl;
    cout << "  -v|--vmm             VMM serial number (5-digit number on VMM) [REQUIRED]" << endl;
    cout << "  -h|--help            print this help message" << endl;
    cout << endl;
    cout << "-----------------------------------------------------------------" << endl;
}

struct Gap {
    Gap(){};
    int left;
    int right;
    int width() {
        return (right - left) + 1;
    }
};

vector<int> get_channels(TTree* tree)
{

    TH1F* h = new TH1F("h_chan", "", 64,0,64);
    string cmd = "channel>>h_chan";
    tree->Draw(cmd.c_str(), "", "goff");

    float integral = h->Integral();

    cout << "channel integral = " << integral << endl;

    int nbins = h->GetNbinsX();

    vector<int> empty_channels;
    vector<int> filled_channels;
    for(int i = 0; i < nbins; i++) {
        float content = h->GetBinContent(i+1);
        if(content==0) {
            empty_channels.push_back(i); 
        }
        else {
            filled_channels.push_back(i);
        }
    }

    delete h;

    cout << "- - - - - - - - - - - - - - -" << endl;
    cout << empty_channels.size() << "  empty channels   : ";
    for(auto c : empty_channels) cout << " " << c;
    cout << endl;
    cout << filled_channels.size() << "  filled channels : ";
    for(auto c : filled_channels) cout << " " << c;
    cout << endl;

    return filled_channels;

}

void get_pdo(int channel, string vmm_id, TTree* tree)
{
    stringstream name;
    stringstream title;

    name << "PDOCH" << channel;
    title << "PDO dump for VMM " << vmm_id << "  CHAN " << channel; 
    TH1F* h = new TH1F(name.str().c_str(), title.str().c_str(), 1024, 0,1024);

    stringstream draw;
    stringstream cut;
    draw << "pdo>>" << h->GetName();
    cut << "channel==" << channel;
    TCut tcut(cut.str().c_str());
    tree->Draw(draw.str().c_str(), tcut, "goff"); 

}

map<int, TH1F*> initialize_histograms(vector<int> channels, string vmm_id)
{
    stringstream name;
    stringstream title;

    map<int, TH1F*> histos;
    for(auto c : channels) {
        name.str("");
        title.str("");
        name << "PDOCH" << c;
        //name << c;
        title << "PDO dump for VMM " << vmm_id << "  CHAN " << c << ";PDO[counts];Entries";
        TH1F* h = new TH1F(name.str().c_str(), title.str().c_str(), 1024, 0, 1024);
        //histos.push_back(h);
        histos[c] = h;
    } // ch
    return histos;
}

vector<int> filled_pdos(TH1F* h)
{
    int n_bins = h->GetNbinsX();
    vector<int> filled;
    for(int i = 0; i < n_bins; i++) {
        int pdo = h->GetBinCenter(i+1);
        if(h->GetBinContent(i+1) > 0) {
            filled.push_back(pdo);
        }
    }
    return filled;
}

map<int, vector<Gap> > get_gaps(map<int,TH1F*> histos)
{
    int start = 0;
    int end = 1024;
    vector<int> expected;
    for(int i = start; i <=end; i++) expected.push_back(i);

    map<int, vector<Gap> > channel_gap_map;
    for(auto h : histos) {
        vector<Gap> out;

    
        int ch = h.first;
        TH1F* hist = h.second;

        vector<int> filled = filled_pdos(hist);
        vector<int> gap_bits(expected.size());

        vector<int>::iterator it;
        it = set_difference(expected.begin(), expected.end(), filled.begin(), filled.end(), gap_bits.begin()); 
        gap_bits.resize(it - gap_bits.begin());

        int left_end = gap_bits.at(0);
        int right_end = gap_bits.at(1);

        int test_tail = left_end;
        int test_head = right_end;
        int last = gap_bits.at(gap_bits.size()-1);
        int left_idx = 0;
        int right_idx = 1;
        for(int i = 1; i < gap_bits.size()-1; i++) {
            int left_val = gap_bits.at(i);
            int right_val = gap_bits.at(i+1);
            int delta = (right_val - left_val);
            if(delta == 1) {
                left_idx=i+1;
                right_idx=i+2;
            }
            else {
                Gap g;
                g.left = left_end;
                g.right = left_val; 
                out.push_back(g);

                left_end = right_val;

                left_idx=i+1;
                right_idx=i+2;
            }
        } // i
        Gap g;
        g.left = left_end;
        g.right = last;
        out.push_back(g);

        //if(ch<5) {
        //    cout << "ch " << ch << "   gap bits : ";
        //    for(auto gb : gap_bits) cout << " " << gb;
        //    cout << endl;
        //    cout << "stored -> " << endl;
        //    for(auto gap : out) {
        //       cout << "      [" << gap.left << ", " << gap.right << "] = " << gap.width() << endl; 
        //    }
        //    cout << endl;
        //}

        channel_gap_map[ch] = out;
    } // h

    return channel_gap_map;
}

void store_gaps_as_text(map<int, vector<Gap> > gap_map, string vmm_id)
{

    stringstream oname;
    oname << "pdo_gaps_VMM_" << vmm_id << ".txt"; 
    std::ofstream of;
    of.open(oname.str(), std::ofstream::out);

    string dsplit = "\t";
    of << "CHANNEL" << dsplit << "GAPLEFT" << dsplit << "GAPRIGHT" << dsplit << "WIDTH\n";
    for(auto gv : gap_map) {
        int channel = gv.first;
        vector<Gap> gaps = gv.second;

        for(auto g : gaps) {
            of << channel << dsplit << g.left << dsplit << g.right << dsplit << g.width() << "\n";
        }
    }
    of.close();

    cout << "Storing gap text file: " << oname.str() << endl;
}

void dump_pdo_plots(string input_file, string vmm_id)
{

    TFile* rfile = TFile::Open(input_file.c_str());
    TTree* tree = static_cast<TTree*>(rfile->Get("calib"));

    vector<int> channels_tested = get_channels(tree);
    if(channels_tested.size()==0) {
        cout << "No non-empty VMM channels found for VMM '" << vmm_id << "' in file '" << input_file << "', exiting" << endl;
        return;
    }

    map<int, TH1F*> histos = initialize_histograms(channels_tested, vmm_id);
    cout << "initialized " << histos.size() << "  histograms" << endl;

    // output file
    stringstream name;
    name << "pdo_dump_VMM_" << vmm_id << ".root";
    TFile* outfile = new TFile(name.str().c_str(), "RECREATE");
    outfile->cd();

    //////////////////////////////////////////////////
    // storage for the tree's branch variables
    //////////////////////////////////////////////////
    vector< vector<unsigned int> > *pdoin;
    vector< vector<int > > *channelin;
    TBranch* pdobr;
    TBranch* channelbr;
    tree->SetBranchAddress("pdo", &pdoin, &pdobr);
    tree->SetBranchAddress("channel", &channelin, &channelbr);

    //////////////////////////////////////////////////
    // begin loop to get PDO
    //////////////////////////////////////////////////
    Long64_t nentries = tree->GetEntries();
    Long64_t current_entry = 0;
    vector< int> channels;
    vector< unsigned int> pdo;
    stringstream testname;

    int update_level = nentries / 20;
    Long64_t for_update = 0;
    int n_checks = 0;

    for(Long64_t entry = 0; entry < nentries; entry++) {
        Long64_t nb = tree->GetEntry(entry);
        if(entry%update_level==0 || entry==(nentries-1)) {
            for_update = (entry + 1);
            cout << " *** Processing entry " << std::setw(14) << for_update << "/" << nentries << " ["
                    << std::setw(3) << n_checks*5 << "\%] *** " << endl;
            n_checks++;
        }
        channels = (*channelin).at(0);
        pdo = (*pdoin).at(0);
        for(unsigned int ichan = 0; ichan < channels.size(); ichan++) {
            testname.str("");
            testname << "PDOCH" << ichan;
            int chan = channels.at(ichan);
            int p4chan = pdo.at(ichan);
            histos[chan]->Fill(p4chan);
        }
    }

    //////////////////////////////////////////////////
    // get gaps
    //////////////////////////////////////////////////
    map<int, vector<Gap> > gap_map = get_gaps(histos);

    // store
    store_gaps_as_text(gap_map, vmm_id);
    
    //////////////////////////////////////////////////
    // save histograms
    //////////////////////////////////////////////////

    for(auto c : channels_tested) histos[c]->Write();

    outfile->Write();
    outfile->Close();
    
}

int main(int argc, char* argv[])
{
    gStyle->SetOptStat(0);
    gROOT->SetBatch(1);

    string input_file = "";
    string vmm_id = "";

    int optin(1);
    while(optin < argc) {
        string in = argv[optin];
        if          (in == "-i" || in == "--input") { input_file = argv[++optin]; }
        else if     (in == "-v" || in == "--vmm")   { vmm_id = argv[++optin]; }
        else if     (in == "-h" || in == "--help")  { help(); return 0; }
        else {
            cout << "vmmtest_main    Unknown command line argument provided '" << in << "'" << endl;
            help();
            exit(1);
        }
        optin++;
    }

    // require the input command line arguments be provided
    if(input_file=="") {
        cout << "vmmtest_pdodump    ERROR You did not provide an input file" << endl;
        exit(1);
    }
    if(vmm_id=="") {
        cout << "vmmtest_pdodump    ERROR You did not provide a VMM ID" << endl;
        exit(1);
    }

    // check that we can find the input file provided
    std::ifstream fs(input_file);
    if(!fs.good()) {
        cout << "vmmtest_pdodump    Cannot successfully find input file '" << input_file << "'" << endl;
        exit(1);
    }

    dump_pdo_plots(input_file, vmm_id);

  return 0;
}
