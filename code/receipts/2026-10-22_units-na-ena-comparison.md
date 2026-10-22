# Receipt: DBS units stay n/a; paper comparison as supporting evidence

**Claim**: README Units section: units stay n/a in all 68 channels.tsv (1,100 DBS rows) because no source states them; how
MNE reads the values; single-pulse ENA amplitudes vs Wiest et al. (2022) Fig. 4C-F as supporting evidence of a µV scale.

**Source**
- NEMAR files read at `origin/main` `0a84072dff50fba0c95cd8b12a53cee65d0e5667`
  (`/checkpoint/brainai2/shared/studies/Wiest2022Subthalamic/download/nm000443/`, refreshed 2026-10-22). The sha256 of each
  of the 136 `_ieeg.eeg`/`_ieeg.vhdr` files read equals its SHA256E git-annex key at that commit (136/136). The 68
  `channels.tsv` read have the same git blob hash as at `origin/main` (68/68), and this commit restores them unchanged
  (the PR's µV edit is reverted), so the table below is the PR head.
- Upstream: University of Oxford ORA / MRC BNDU, doi:10.5287/bodleian:qrnqjnpv7 (68 .mat files; source file and sha256 of
  original and scrubbed copy per recording in `code/conversion_report.json`).
- Searched for a statement of the recording unit (none found):
  - `sourcedata/bndu/README.txt` (sha256 `126323e2...85de93`, same text as the record page "Documentation"): no unit.
  - Record page (https://ora.ox.ac.uk/objects/uuid:9cb9a6fb-d35c-4350-a4a7-10b999fedbf3): no unit.
  - SmrData fields of all 68 `sourcedata/bndu` .mat files (annex objects at `origin/main`, h5py over the public NEMAR S3
    URLs): `EvData, EvTits, FileName, FilePath, Fs, WvData, WvTits` (63) or without `EvData/EvTits` (5); no unit or scale
    field (68/68).
  - Wiest et al. (2022) Mov Disord 38(3):423, doi:10.1002/mds.29302, full text PMC7614354 (Europe PMC JATS XML): methods
    give the amplifier (TMSi Saga, 4096 Hz) but no unit or gain for the data; text and captions have no µV. µV appears
    only on figure axes (Fig. 3B scale bar, Fig. 3C colour bar, Fig. 4A-F amplitude axes), i.e. on analysis outputs.
- Paper reference values: box-plot medians of "ENA Amplitude (µV)" in Fig. 4B-F (figure image `MDS-38-423-g005.jpg` from the
  Europe PMC supplementary files of PMC7614354), read off the plots to the nearest 5 µV (`PAPER` in the script).

**Method**
- Tables: rows per `type` and the set of `units` values in each `channels.tsv`; unit and resolution of every channel in
  the `.vhdr`. Reader check per recording: MNE `read_raw_brainvision(preload=True)` and MNE-BIDS `read_raw_bids` (MNE 1.13.2,
  MNE-BIDS 0.20.0); `get_data()` compared for exact equality with the stored float32 samples (i.e. no scaling applied);
  channel types and the FIFF unit MNE gives the DBS channels.
- ENA (5 `task-singlepulse` recordings, contacts L1-L8/R1-R8): artifact onsets where the largest |first difference| over the
  8 contacts exceeds 50 robust SDs (1.4826 x median |difference|, flat channels skipped), merged within 5 ms; pulses kept if
  isolated (> 0.3 s from neighbours) and only the Fig. 4 stimulated contact is exactly 0 over +-100 ms (the stimulated
  contact is zeroed in the release). Per pulse and recorded contact: samples 1.5-10 ms after onset, linear detrend, 4th-order
  Butterworth 700 Hz low-pass (zero phase), peak = maximum in 3.5-6.5 ms, amplitude = peak minus the minimum in the following
  3 ms (Fig. 3B definition); median over pulses, ratio = median / paper value. Stored numbers are used unscaled.

**Result** (script output, unedited)

mne 1.13.2, mne_bids 0.20.0

| recording | rows | DBS | EEG | EMG | MISC | units | vhdr unit | vhdr resolution | brainvision types | brainvision == stored | read_raw_bids dbs | read_raw_bids dbs unit | read_raw_bids == stored |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sub-01_task-dbsramp_acq-R2 | 33 | 16 | 6 | 0 | 11 | n/a | n/a | 1.0 | misc | True | 16 | FIFF_UNIT_V | True |
| sub-01_task-dbsramp_acq-R3 | 33 | 16 | 6 | 0 | 11 | n/a | n/a | 1.0 | misc | True | 16 | FIFF_UNIT_V | True |
| sub-02_task-dbsramp_acq-L2 | 31 | 14 | 6 | 2 | 9 | n/a | n/a | 1.0 | misc | True | 14 | FIFF_UNIT_V | True |
| sub-02_task-dbsramp_acq-L3 | 31 | 14 | 6 | 2 | 9 | n/a | n/a | 1.0 | misc | True | 14 | FIFF_UNIT_V | True |
| sub-02_task-dbsramp_acq-L4 | 31 | 14 | 6 | 2 | 9 | n/a | n/a | 1.0 | misc | True | 14 | FIFF_UNIT_V | True |
| sub-02_task-dbsramp_acq-L5 | 31 | 14 | 6 | 2 | 9 | n/a | n/a | 1.0 | misc | True | 14 | FIFF_UNIT_V | True |
| sub-02_task-dbsramp_acq-L6 | 31 | 14 | 6 | 2 | 9 | n/a | n/a | 1.0 | misc | True | 14 | FIFF_UNIT_V | True |
| sub-02_task-dbsramp_acq-L7 | 31 | 14 | 6 | 2 | 9 | n/a | n/a | 1.0 | misc | True | 14 | FIFF_UNIT_V | True |
| sub-02_task-dbsramp_acq-R2 | 31 | 14 | 6 | 0 | 11 | n/a | n/a | 1.0 | misc | True | 14 | FIFF_UNIT_V | True |
| sub-02_task-dbsramp_acq-R3 | 31 | 14 | 6 | 0 | 11 | n/a | n/a | 1.0 | misc | True | 14 | FIFF_UNIT_V | True |
| sub-02_task-dbsramp_acq-R4 | 31 | 14 | 6 | 0 | 11 | n/a | n/a | 1.0 | misc | True | 14 | FIFF_UNIT_V | True |
| sub-02_task-dbsramp_acq-R5 | 31 | 14 | 6 | 0 | 11 | n/a | n/a | 1.0 | misc | True | 14 | FIFF_UNIT_V | True |
| sub-02_task-dbsramp_acq-R6 | 31 | 14 | 6 | 0 | 11 | n/a | n/a | 1.0 | misc | True | 14 | FIFF_UNIT_V | True |
| sub-02_task-dbsramp_acq-R7 | 31 | 14 | 6 | 0 | 11 | n/a | n/a | 1.0 | misc | True | 14 | FIFF_UNIT_V | True |
| sub-03_task-dbsramp_acq-L2 | 35 | 16 | 6 | 2 | 11 | n/a | n/a | 1.0 | misc | True | 16 | FIFF_UNIT_V | True |
| sub-03_task-dbsramp_acq-L3 | 35 | 16 | 6 | 2 | 11 | n/a | n/a | 1.0 | misc | True | 16 | FIFF_UNIT_V | True |
| sub-03_task-dbsramp_acq-L4 | 35 | 16 | 6 | 2 | 11 | n/a | n/a | 1.0 | misc | True | 16 | FIFF_UNIT_V | True |
| sub-03_task-dbsramp_acq-L5 | 35 | 16 | 6 | 2 | 11 | n/a | n/a | 1.0 | misc | True | 16 | FIFF_UNIT_V | True |
| sub-03_task-dbsramp_acq-L6 | 35 | 16 | 6 | 2 | 11 | n/a | n/a | 1.0 | misc | True | 16 | FIFF_UNIT_V | True |
| sub-03_task-dbsramp_acq-L7 | 35 | 16 | 6 | 2 | 11 | n/a | n/a | 1.0 | misc | True | 16 | FIFF_UNIT_V | True |
| sub-03_task-dbsramp_acq-R2 | 35 | 16 | 6 | 2 | 11 | n/a | n/a | 1.0 | misc | True | 16 | FIFF_UNIT_V | True |
| sub-03_task-dbsramp_acq-R3 | 35 | 16 | 6 | 2 | 11 | n/a | n/a | 1.0 | misc | True | 16 | FIFF_UNIT_V | True |
| sub-03_task-dbsramp_acq-R4 | 35 | 16 | 6 | 2 | 11 | n/a | n/a | 1.0 | misc | True | 16 | FIFF_UNIT_V | True |
| sub-03_task-dbsramp_acq-R5 | 35 | 16 | 6 | 2 | 11 | n/a | n/a | 1.0 | misc | True | 16 | FIFF_UNIT_V | True |
| sub-03_task-dbsramp_acq-R6 | 35 | 16 | 6 | 2 | 11 | n/a | n/a | 1.0 | misc | True | 16 | FIFF_UNIT_V | True |
| sub-03_task-dbsramp_acq-R7 | 35 | 16 | 6 | 2 | 11 | n/a | n/a | 1.0 | misc | True | 16 | FIFF_UNIT_V | True |
| sub-04_task-dbsramp_acq-L2 | 31 | 17 | 6 | 0 | 8 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-04_task-dbsramp_acq-L3 | 31 | 17 | 6 | 0 | 8 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-04_task-dbsramp_acq-L4 | 31 | 17 | 6 | 0 | 8 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-04_task-dbsramp_acq-L5 | 31 | 17 | 6 | 0 | 8 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-04_task-dbsramp_acq-L6 | 31 | 17 | 6 | 0 | 8 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-04_task-dbsramp_acq-L7 | 31 | 17 | 6 | 0 | 8 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-04_task-dbsramp_acq-R2 | 31 | 17 | 6 | 0 | 8 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-04_task-dbsramp_acq-R3 | 31 | 17 | 6 | 0 | 8 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-04_task-dbsramp_acq-R4 | 31 | 17 | 6 | 0 | 8 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-04_task-dbsramp_acq-R5 | 31 | 17 | 6 | 0 | 8 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-04_task-dbsramp_acq-R6 | 31 | 17 | 6 | 0 | 8 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-04_task-dbsramp_acq-R7 | 31 | 17 | 6 | 0 | 8 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-05_task-singlepulse_acq-left | 42 | 16 | 6 | 0 | 20 | n/a | n/a | 1.0 | misc | True | 16 | FIFF_UNIT_V | True |
| sub-06_task-dbsramp_acq-L2 | 39 | 17 | 6 | 0 | 16 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-06_task-dbsramp_acq-L3 | 39 | 17 | 6 | 0 | 16 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-06_task-dbsramp_acq-L4 | 39 | 17 | 6 | 0 | 16 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-06_task-dbsramp_acq-L5 | 39 | 17 | 6 | 0 | 16 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-06_task-dbsramp_acq-L6 | 39 | 17 | 6 | 0 | 16 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-06_task-dbsramp_acq-L7 | 39 | 17 | 6 | 0 | 16 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-06_task-dbsramp_acq-R2 | 39 | 17 | 6 | 0 | 16 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-06_task-dbsramp_acq-R3 | 39 | 17 | 6 | 0 | 16 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-06_task-dbsramp_acq-R4 | 39 | 17 | 6 | 0 | 16 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-06_task-dbsramp_acq-R5 | 39 | 17 | 6 | 0 | 16 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-06_task-dbsramp_acq-R6 | 39 | 17 | 6 | 0 | 16 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-06_task-dbsramp_acq-R7 | 39 | 17 | 6 | 0 | 16 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-06_task-singlepulse_acq-left | 30 | 16 | 6 | 0 | 8 | n/a | n/a | 1.0 | misc | True | 16 | FIFF_UNIT_V | True |
| sub-06_task-singlepulse_acq-right | 30 | 16 | 6 | 0 | 8 | n/a | n/a | 1.0 | misc | True | 16 | FIFF_UNIT_V | True |
| sub-07_task-dbsramp_acq-L2 | 37 | 17 | 6 | 0 | 14 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-07_task-dbsramp_acq-L3 | 37 | 17 | 6 | 0 | 14 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-07_task-dbsramp_acq-L4 | 37 | 17 | 6 | 0 | 14 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-07_task-dbsramp_acq-L5 | 37 | 17 | 6 | 0 | 14 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-07_task-dbsramp_acq-L6 | 37 | 17 | 6 | 0 | 14 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-07_task-dbsramp_acq-L7 | 37 | 17 | 6 | 0 | 14 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-07_task-dbsramp_acq-R2 | 37 | 17 | 6 | 0 | 14 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-07_task-dbsramp_acq-R3 | 37 | 17 | 6 | 0 | 14 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-07_task-dbsramp_acq-R4 | 37 | 17 | 6 | 0 | 14 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-07_task-dbsramp_acq-R5 | 37 | 17 | 6 | 0 | 14 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-07_task-dbsramp_acq-R6 | 37 | 17 | 6 | 0 | 14 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-07_task-dbsramp_acq-R7 | 37 | 17 | 6 | 0 | 14 | n/a | n/a | 1.0 | misc | True | 17 | FIFF_UNIT_V | True |
| sub-07_task-paired_acq-L2 | 36 | 16 | 6 | 0 | 14 | n/a | n/a | 1.0 | misc | True | 16 | FIFF_UNIT_V | True |
| sub-07_task-singlepulse_acq-left | 28 | 16 | 6 | 0 | 6 | n/a | n/a | 1.0 | misc | True | 16 | FIFF_UNIT_V | True |
| sub-07_task-singlepulse_acq-right | 28 | 16 | 6 | 0 | 6 | n/a | n/a | 1.0 | misc | True | 16 | FIFF_UNIT_V | True |

68 tables, 2336 rows, 1100 DBS rows; units values: ['n/a']

| recording | Fig. 4 stim | flat contacts (whole file) | artifacts | median artifact interval (s) | isolated (> 0.3 s) | pulses used |
|---|---|---|---|---|---|---|
| sub-05 left | C1 | C1 | 73117 | 0.008 | 0 | 0 |
| sub-06 left | C3 |  | 242 | 2.552 | 214 | 25 |
| sub-06 right | C2 |  | 227 | 2.553 | 219 | 25 |
| sub-07 left | C2 |  | 226 | 2.563 | 217 | 25 |
| sub-07 right | C3 |  | 249 | 2.514 | 215 | 25 |

| recording | stim | contact | paper µV | stored median | ratio |
|---|---|---|---|---|---|
| sub-06 left | C3 | C1 | 95 | 91.3 | 0.96 |
| sub-06 left | C3 | C2 | 230 | 230.6 | 1.0 |
| sub-06 left | C3 | C4 | 290 | 299.3 | 1.03 |
| sub-06 left | C3 | C5 | 70 | 72.4 | 1.03 |
| sub-06 left | C3 | C6 | 50 | 48.4 | 0.97 |
| sub-06 left | C3 | C7 | 90 | 90.8 | 1.01 |
| sub-06 left | C3 | C8 | 95 | 95.1 | 1.0 |
| sub-06 right | C2 | C1 | 30 | 39.4 | 1.31 |
| sub-06 right | C2 | C3 | 190 | 212.2 | 1.12 |
| sub-06 right | C2 | C4 | 130 | 134.5 | 1.03 |
| sub-06 right | C2 | C5 | 45 | 46.7 | 1.04 |
| sub-06 right | C2 | C6 | 45 | 46.5 | 1.03 |
| sub-06 right | C2 | C7 | 65 | 70.2 | 1.08 |
| sub-06 right | C2 | C8 | 85 | 85.3 | 1.0 |
| sub-07 left | C2 | C1 | 50 | 42.0 | 0.84 |
| sub-07 left | C2 | C3 | 85 | 80.4 | 0.95 |
| sub-07 left | C2 | C4 | 40 | 36.7 | 0.92 |
| sub-07 left | C2 | C5 | 40 | 44.2 | 1.11 |
| sub-07 left | C2 | C6 | 55 | 59.9 | 1.09 |
| sub-07 left | C2 | C7 | 60 | 71.5 | 1.19 |
| sub-07 left | C2 | C8 | 55 | 73.7 | 1.34 |
| sub-07 right | C3 | C1 | 45 | 39.8 | 0.89 |
| sub-07 right | C3 | C2 | 55 | 48.9 | 0.89 |
| sub-07 right | C3 | C4 | 110 | 106.6 | 0.97 |
| sub-07 right | C3 | C5 | 45 | 44.5 | 0.99 |
| sub-07 right | C3 | C6 | 40 | 48.7 | 1.22 |
| sub-07 right | C3 | C7 | 60 | 75.0 | 1.25 |
| sub-07 right | C3 | C8 | 70 | 83.9 | 1.2 |

ratio stored/paper over 28 contacts: median 1.03, IQR 0.97-1.11, range 0.84-1.34

**Coverage**: 68 of 68 channels.tsv (2,336 rows, 1,100 DBS) and 68 of 68 `.vhdr`/`.eeg`; 5 of 5 single-pulse recordings
examined, 4 compared (sub-05 left: artifacts every ~8 ms throughout and C1 flat for the whole file, no isolated pulses).

Run: `python 2026-10-22_units-na-ena-comparison.py <bids_root>` with mne, mne_bids, numpy, pandas, scipy (Slurm job 13448867).
