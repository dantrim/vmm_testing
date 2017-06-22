# vmm_testing

Scripts to perform the analysis of the calibration ntuples from pulser DAC scans of VMM3.

# Requirements

- Python >= 2.7
- PyROOT

If you do not have PyROOT you can run this code on lxplus. To test whether or not you have PyROOT you should open up a Python interactive session and try importing the ROOT module. From a command line, do:

```
$ python
>> import ROOT
```
 
If you get a `No module named 'ROOT'` response then you do not have PyROOT.

# How to run

The python script `test_vmm.py` will take in a calibration ntuple that has the pulser DAC scans performed and will find gaps in the PDO distribution for each VMM channel's PDO spectrum. There are several command line options that you need to provide and several optional ones. Here is the list of all of them:

## required arguments
* `-i` : this is the input ROOT file
* `--vmm-id` : this is the serial number printed on the VMM itself

## optional arguments
* `--channel` : comma separated list (with no spaces) of channel numbers that you want to consider (if you do not provide this argument the script will consider all non-dead channels in the file) [example: `--channel 1,4,6` to analyze VMM channels 1, 4, and 6 only]
* `--no-html` : do not automatically open up the HTML plot dump at the end of the analysis (this may be useful if you are on a remote machine and opening up a browser would be slow, e.g.)

# Example run

In typical pulser DAC scans, in order to get the full pulser DAC scan sampled there may be several individual calibration ROOT files, each with different scan windows and/or run parameters (like the gain). In order to combine these into a **single** input file for `test_vmm.py` you can use ROOT's *hadd* command from the command-line. For example, if you have two files `calib_run_0001.root` and `calib_run_0002.root` you can combine them into a single file `pulser_dac_scan_10043.root` (where `10043` is the VMM serial number) by calling from the command line:

```
hadd -f pulser_dac_scan_10043.root calib_run_0001.root calib_run_0002.root
```

The file `pulser_dac_scan_10043.root` is the merger of the two calib ntuples.

With this **single** pulser DAC scan file, and assuming a VMM serial number `10043`, the script can be run using the following command:

```
./test_vmm.py -i pulser_dac_scan_10043.root --vmm-id "10043"
```

The result of running this program is:

* a new directory named `vmm_pdo_scans_10043` which will contain `eps` files that hold the plots of the PDO distribution for each channel. There will also be `.root` files which contain the ROOT objects (canvas, histograms) that are used to make the plots. These are named as follows: `vmm_pulser_dac_scan_VMM_10043_channel46.{eps,root}`, e.g. for channel 46 of VMM 10043. The ROOT files can be combined (again using *hadd*) to have a single ROOT file that has the canvases for every single channel. The ROOT files are useful for being able to **zoom** on the distributions, etc... whereas the `eps` files are static.
* a new directory named `vmm_pdo_scans_10043/for_html/` which will contain `png` files used for producing the `.html` file in `vmm_pdo_scans_10043/`
* inside of `vmm_pdo_scans_10043/` there is also an `.html` file that contains a dump of all of the PDO histograms.

# Interpretting the output plots

The output plots are the PDO distributions for each channel. There will also be **red hashed** areas OR **solid red** areas. These red marked areas mark the gaps in the PDO spectrum. Gaps are only considered if they are at least 5 PDO codes wide. This can easily be changed. The meaning of the hash vs solid is described here:

* **red hashed gaps** : the gap is *not* 64 PDO codes wide
* **solid red gaps** : the gap is exactly 64 PDO codes wide

Just above each of the red gaps is printed the width of the gap in small font. You can use the `eps` files which are of higher resolution to inspect these values or zoom in on the respected regions using the output `root` files.

You must use some thought when considering the gaps. There will typically be gaps at the beginning of the PDO distribution and at the end of the PDO distribution where the full range is not accessed. If there is a large peak at ~40 PDO codes (the pedestal) there is typically a wide gap beyond that until the "bulk" PDO distribution begins. This gap will still be marked with red. Using the output `html` file in a browser to inspect the distributions is relatively easy, and the spurious markings of the gaps beyond the pedestal and at the end of the distributions can be done with relative easy and speed.
