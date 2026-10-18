[![DOI](https://img.shields.io/badge/DOI-10.82901%2Fnemar.nm000443-blue)](https://doi.org/10.82901/nemar.nm000443)

# Subthalamic and thalamic LFPs during DBS in cervical dystonia (Wiest et al. 2022) - DERIVATIVE

Local field potentials (LFPs) from externalised octopolar deep brain stimulation (DBS) leads in 7 patients with isolated
idiopathic (cranio)cervical dystonia (12 hemispheres; leads span the subthalamic nucleus (STN, inferior contacts), the rostral
zona incerta and the ventrolateral thalamus (superior contacts)), recorded 4-7 days after surgery off anti-dystonic medication
at St George's University Hospitals, London, while stimulation was applied through the lead. Scalp EEG, EMG of dystonic neck
muscles and accelerometers were recorded in some patients. The data were first analysed in Wiest et al. (2022/2023),
which reports broadband power suppression, evoked resonant neural activity (ERNA) and finely tuned gamma under STN stimulation.

## Source
- Wiest C, Torrecillos F, Morgante F, Pereira E, Tan H. "Subthalamic and thalamic local field potential recordings from patients
  with cervical dystonia". University of Oxford, MRC Brain Network Dynamics Unit data sharing platform (Cambium). doi:10.5287/bodleian:qrnqjnpv7
- Wiest C, Morgante F, Torrecillos F, Pogosyan A, He S, Baig F, Bertaina I, Hart MG, Edwards MJ, Pereira EA, Tan H (2023).
  Subthalamic Nucleus Stimulation-Induced Local Field Potential Changes in Dystonia. Mov Disord 38(3). doi:10.1002/mds.29302
- Funding (release README and paper): Medical Research Council UK (MC_UU_00003/2, MR/P012272/1, MR/V00655X/1), NIHR Oxford
  Biomedical Research Centre, Rosetrees Trust.
- Ethics (paper): Health Research Authority UK and National Research Ethics Service Local Research Ethics Committee (IRAS 46576);
  written informed consent.

## Licence
CC BY-SA 4.0. The Cambium record page, its download form and the README.txt inside each of the three zips all state
CC BY-SA 4.0 (no other licence file is in the zips). Copyright 2020-2022, University of Oxford. README.txt is in sourcedata/bndu/.

## Recording
TMSi Saga amplifier, 4096 Hz, custom acquisition software (paper); exported via Spike2 to MATLAB (SmrData structs). Boston
Scientific Vercise Standard Lead 2201 (non-directional, 8 ring contacts; level 1 most inferior). Contacts adjacent to the
stimulated level are recorded bipolar (label e.g. L13 when L2 is stimulated); all other contacts and the EEG are unipolar with
common mode rejection (README). The release does not state units, so channels.tsv lists units as n/a; values are unchanged.
THIS IS A DERIVATIVE DATASET. The release README and the paper describe no filtering before release (the paper's 1 Hz
high-pass and 50 Hz notch are later analysis steps), but every released channel, including the head accelerometers, is free of
DC offset: there is no gravity component on the accelerometers, and 10 s window means are small compared with each channel's
standard deviation, although the TMSi Saga is DC-coupled. The Spike2 files also came from a 'processed_data/SMR' folder. An
undocumented DC removal / high-pass was therefore applied before release (cutoff not stated), so the dataset is labelled
derivative. The sampling rate is the acquisition rate (4096 Hz, no resampling). Channels prefixed F-, S- or f are additional
channels that the authors derived (e.g. F-L1 is close to L1); they are kept as MISC.

## Contents
- 68 continuous recordings, 9.65 h in total, 1.9-17.0 min each, all at 4096 Hz.
  One BIDS run per release .mat file; the release file is listed in each sub-*_scans.tsv (source_file).
  - `task-dbsramp` (62 files; release labels 'Testing' and, for participant 2, 'DBS'): continuous 130 Hz
    monopolar DBS of one of the six middle contact levels (2-7; `acq-<L|R><level>`) with the intensity increased in 0.5 mA steps
    up to 4.5 mA or the side-effect threshold. In patient 2 the paper also tested 100/130/150/180 Hz for 2 min each at one contact.
  - `task-singlepulse` (5 files, participants 5-7; `acq-left|right`): 25 single pulses applied to each of the 8
    contact levels in sequence, the remaining contacts recorded unipolar.
  - `task-paired` (1 file, participant 7, release label 'Paired', left contact level 2): not described in the
    release or the paper; kept as released.
- Channels (types in channels.tsv; release labels kept, repeated release labels such as AUX1 get a suffix _2, _3):
  DBS = lead contacts L1-L8/R1-R8 and bipolar pairs (e.g. L13); EEG = scalp electrodes; EMG = neck muscles (e.g. SplL, SCML);
  MISC = accelerometer, stimulation current channels (Cur*/Am*: time stamps and intensity of the applied stimulation, README)
  and any release channel the README does not describe (e.g. F-*, S-*, f*, Rs*/Res*, *Spc, AUX*), kept unchanged.
- events.tsv: Spike2 'Mark' channel time stamps from the release (SmrData.EvData). Stimulation timing and intensity are in
  the Cur/Am channels.
- electrodes.tsv: lead contacts with x, y, z = n/a, hemisphere, contact level and the stated targets; no coordinates are released.
- participants.tsv: age, sex, diagnosis, disease duration and days after surgery from Wiest et al. (2022) Table 1. The release
  numbering is taken to be the paper's patient numbering: the release README says participants 5-7 received single-pulse
  stimulation, as Table 1 does, and participant 5 has only a left single-pulse file, matching Table 1 (single pulse: L).

## sourcedata/bndu
README.txt and the 68 original .mat files. Changed for privacy only: the MAT header 'Created on' day is set to 01; the Spike2
FileName (an internal lab code) and FilePath (lab drive path containing the recording date and hospital/lab codes) strings are
overwritten in place with the release file name and '[path removed]'. WvData (signals) is byte-identical to the release
(checked); SHA-256 of original and edited files in code/conversion_report.json.

## Privacy
No names or hospital numbers remain. Recording dates were only in the removed FilePath strings; scans.tsv acq_time is n/a.

## Units (updated 2026-10-19, version 1.0.3)

DBS, EEG, EMG channels of 68 recordings now say `µV` in channels.tsv and in the BrainVision headers (were `n/a`). MISC channels (online-derived copies, accelerometers, stimulation amplitude, undocumented channels) stay `n/a`. **Unit inferred, not stated in the release** (the Spike2-to-MATLAB `SmrData` export keeps no unit). Evidence: (1) the recordings were made with TMSi amplifiers and exported through Spike2 by the MRC Brain Network Dynamics Unit, the same chain as the unit's essential-tremor release (He & Tan 2025, doi:10.60964/bndu-kshc-a492), whose Spike2 channel headers state the unit as µV; (2) the stored float64 values sit on Spike2 int16 grids of 0.0098-0.0100 per step (TMSi SAGA files), the same grid family as the TMSi SAGA recordings of the companion BNDU release on NEMAR nm000446 (step 0.0100); (3) robust SD after a 1 Hz high-pass DBS 5.8-16, EEG 7.7-15 (3 release files, 19 Oct 2026; 6-14 in the 17 Oct check of the BIDS runs): only µV is physiologically possible (as V or mV the values would be volts or millivolts). Values unchanged.

Reading with MNE: `raw.get_data()` now returns volts (stored µV x 1e-6) for these channels; MISC channels with unit `n/a` are still read as volts with scale 1. Evidence files: fix1019 `out/pubamp/` (Voyager Jobs ieeg-f19-pa-*, 19 Oct 2026).
