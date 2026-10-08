"""d3-mrc-dystonia (Oxford MRC BNDU / Cambium doi:10.5287/bodleian:qrnqjnpv7; Wiest, Torrecillos, Morgante, Pereira, Tan) -> iEEG-BIDS (raw).

Release (3 zips 'P1,P2', 'P3,P4', 'P5,P6,P7'; identical README.txt in each, CC BY-SA 4.0 = record page/form; no other licence file):
68 MATLAB v7.3 .mat files Participant<k>_<Left|Right>/<P|L><k>_<L|R><n>_<Testing|DBS|Paired>.mat and P<k>_<Left|Right>_Single.mat,
each one Spike2 export struct SmrData {WvData (samples x channels, float64), WvTits, Fs (4096 Hz), EvData/EvTits (Mark times, s),
FileName, FilePath}. Recorded with a TMSi Saga at 4096 Hz (Wiest et al. 2022 Mov Disord, doi:10.1002/mds.29302); the release is
the continuous recording per stimulation block (probe Job ieeg-b3w12-dyst-probe-1008122018: 1.6-17 min per file, no NaN/gaps).
Values are written unchanged (float32; every release value is float32-representable, checked per channel -> round-trip exact).
Privacy: SmrData.FilePath holds the lab path with recording date, hospital/lab codes (e.g. 'SG049_G36_2022_01_22_CD'), FileName the
internal code 'G<nn>'. In the sourcedata copies both are overwritten in place (same dataset length, so no stale bytes remain) and the
MAT header 'Created on' day is set to 01; the converter checks that the original strings no longer occur anywhere in the copy and
that WvData is byte-identical.
Usage: python b3w12_convert_dyst.py <work_dir> <bids_root>
"""
import glob, json, os, re, shutil, sys
from multiprocessing import Pool
import h5py
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b3w3_common import wjson, write_vhdr, wtsv, scrub_mat_header, sha256_file  # noqa: E402

W, OUT = sys.argv[1], sys.argv[2]
EX = os.path.join(W, "extracted")
SRC = sorted(glob.glob(os.path.join(EX, "*", "*", "*", "*.mat")))
assert len(SRC) == 68, len(SRC)
READMES = sorted(glob.glob(os.path.join(EX, "*", "*", "README.txt")))
assert len(READMES) == 3
SD = os.path.join(OUT, "sourcedata", "bndu")
DOI = "10.5287/bodleian:qrnqjnpv7"
PAPER = "10.1002/mds.29302"
FS_EXPECT = 4096.0
DCNOTE = ("Undocumented DC removal / high-pass before release: every released channel, including the head accelerometers, is free of DC offset "
          "(no gravity component; 10 s window means small compared with the channel SD; DC-check Jobs ieeg-b3w12-dyst-dc-1008124055 and "
          "ieeg-b3w12-dyst-dc2-1008124329), whereas the TMSi Saga is DC-coupled; the Spike2 files came from a 'processed_data/SMR' folder. "
          "Cutoff not stated by the source. The sampling rate (4096 Hz) is the acquisition rate (Wiest et al. 2022).")

EEG = {"Fz", "FCz", "Cz", "Pz", "Oz", "C3", "C4", "CP3", "CPz", "CP4", "F3", "F4", "FC3", "FC4", "P3", "P4"}


def ctype(n):
    m = re.fullmatch(r"([LR])([1-8])", n)
    if m:
        return "DBS", "%s DBS lead (Boston Scientific Vercise 2201, 8 ring contacts), contact level %s (1 = most inferior), unipolar with common mode rejection (README)" % (
            "left" if m.group(1) == "L" else "right", m.group(2))
    m = re.fullmatch(r"([LR])([1-8])([1-8])", n)
    if m:
        return "DBS", "%s DBS lead, bipolar recording between contact levels %s and %s adjacent to the stimulated contact (README: 'label e.g. L13 if L2 was stimulated')" % (
            "left" if m.group(1) == "L" else "right", m.group(2), m.group(3))
    if n in EEG:
        return "EEG", "scalp EEG electrode %s, common mode rejection (README)" % n
    if re.match(r"(Spl|SCM|Trap|EMG|Lev|Semi)", n):
        return "EMG", "EMG from a dystonic neck muscle (README: e.g. SplL = left splenius, SCML = left sternocleidomastoid), release label %s" % n
    if re.match(r"(Acc|Ac[XYZ])", n):
        return "MISC", "accelerometer (forehead or vertex; README), release label %s" % n
    if re.fullmatch(r"(Cur|Am)\d", n):
        return "MISC", "stimulation current: README 'The time stamps and intensity of the applied stimulation currents are saved in channel Cur1/Am1' (release label %s)" % n
    return "MISC", "release channel '%s', not described in the release README" % n


def h5str(ds):
    if "MATLAB_empty" in ds.attrs:
        return ""
    return "".join(chr(int(c)) for c in np.asarray(ds[()]).ravel(order="F"))


def h5cell(f, ds):
    out = []
    for r in np.asarray(ds[()]).ravel(order="F"):
        o = f[r]
        if "MATLAB_empty" in o.attrs and o.attrs.get("MATLAB_class", b"") not in (b"char", "char"):
            out.append(np.zeros(0))
            continue
        out.append(h5str(o) if o.attrs.get("MATLAB_class", b"") in (b"char", "char") else np.asarray(o[()]).ravel())
    return out


def ident(fn):
    """release file -> (subject number, hemisphere folder side, task, acq, release label)"""
    folder = os.path.basename(os.path.dirname(fn))
    m = re.fullmatch(r"(?:Participant|Patient)(\d)_(Left|Right)", folder)
    assert m, folder
    k, side = int(m.group(1)), m.group(2)
    b = os.path.basename(fn)[:-4]
    m2 = re.fullmatch(r"[PL](\d)_([LR])(\d)_(Testing|DBS|Paired)", b)
    if m2:
        assert int(m2.group(1)) == k and m2.group(2) == side[0], fn
        task = {"Testing": "dbsramp", "DBS": "dbsramp", "Paired": "paired"}[m2.group(4)]
        return k, side, task, "%s%s" % (m2.group(2), m2.group(3)), m2.group(4), int(m2.group(3))
    m3 = re.fullmatch(r"[PL](\d)_(Left|Right)_Single", b)
    assert m3 and int(m3.group(1)) == k and m3.group(2) == side, fn
    return k, side, "singlepulse", side.lower(), "Single", None


def uniq(labels):
    seen, out = {}, []
    for n in labels:
        seen[n] = seen.get(n, 0) + 1
        out.append(n if seen[n] == 1 else "%s_%d" % (n, seen[n]))
    return out


def scrub_copy(fn, dst):
    """sourcedata copy: header day->01, FileName/FilePath overwritten in place (same length), verify."""
    b = open(fn, "rb").read()
    nb, ch = scrub_mat_header(b)
    open(dst, "wb").write(nb)
    del b, nb
    rel = os.path.basename(fn)[:-4]
    olds = {}
    with h5py.File(dst, "r+") as f:
        for k, newtxt in (("FileName", rel + ".smr"), ("FilePath", "[path removed]")):
            ds = f["SmrData"][k]
            assert ds.chunks is None and ds.compression is None, (fn, k, ds.chunks, ds.compression)  # in-place overwrite leaves no stale copy
            old = h5str(ds)
            olds[k] = old
            n = ds.size
            t = newtxt if len(newtxt) <= n else "[removed]"[:n]
            t = t.ljust(n)
            ds[...] = np.array([ord(c) for c in t], dtype=ds.dtype).reshape(ds.shape, order="F")
    raw = open(dst, "rb").read()
    leaks = []
    for k, old in olds.items():
        for tok in set([old] + [p for p in re.split(r"[\\/]", old) if re.search(r"\d", p) and len(p) >= 3]):
            if k == "FileName" and tok == old and old == rel + ".smr":
                continue
            for enc in ("utf-16-le", "latin1"):
                if tok.encode(enc) in raw:
                    leaks.append((k, tok, enc))
    for pat in (rb"Recordings_20", rb"StGeorges", "StGeorges".encode("utf-16-le"), "Recordings_".encode("utf-16-le")):
        if pat in raw:
            leaks.append(("pattern", pat.decode("latin1"), "raw"))
    del raw
    with h5py.File(fn, "r") as a, h5py.File(dst, "r") as c:
        same = np.array_equal(a["SmrData/WvData"][()], c["SmrData/WvData"][()]) and sorted(a["SmrData"].keys()) == sorted(c["SmrData"].keys())
        fn2, fp2 = h5str(c["SmrData/FileName"]), h5str(c["SmrData/FilePath"])
    return dict(file=os.path.relpath(fn, EX), header_changed=ch, filename_new=fn2.strip(), filepath_new=fp2.strip(),
                old_had_date=bool(re.search(r"20\d\d_\d\d_\d\d", olds["FilePath"])), leaks=[list(map(str, l)) for l in leaks],
                signal_identical=bool(same), src_sha256=sha256_file(fn), sourcedata_sha256=sha256_file(dst))


def one(fn):
    k, side, task, acq, rlabel, level = ident(fn)
    sub = "sub-%02d" % k
    with h5py.File(fn, "r") as f:
        S = f["SmrData"]
        lab_src = h5cell(f, S["WvTits"])
        fs = float(np.asarray(S["Fs"][()]).ravel()[0])
        D = S["WvData"][()]
        evt = h5cell(f, S["EvTits"]) if "EvTits" in S else []
        evd = h5cell(f, S["EvData"]) if "EvData" in S else []
    X = D.T if D.shape[1] == len(lab_src) else D  # (nch, ns)
    del D
    assert X.shape[0] == len(lab_src), (fn, X.shape, len(lab_src))
    assert fs == FS_EXPECT, fs
    lab = uniq(lab_src)
    stem = f"{sub}_task-{task}_acq-{acq}"
    Dd = os.path.join(OUT, sub, "ieeg")
    os.makedirs(Dd, exist_ok=True)
    X32 = np.ascontiguousarray(X.T.astype("<f4"))
    exact32 = [bool(np.array_equal(X32[:, j].astype(np.float64), X[j], equal_nan=True)) for j in range(X.shape[0])]
    X32.tofile(os.path.join(Dd, stem + "_ieeg.eeg"))
    del X32
    write_vhdr(os.path.join(Dd, stem + "_ieeg"), len(lab), fs, lab, ["n/a"] * len(lab),
               comment="b3w12_convert_dyst.py: SmrData.WvData of %s, values unchanged as float32 (unit not stated in the release)" % os.path.basename(fn))
    back = np.fromfile(os.path.join(Dd, stem + "_ieeg.eeg"), dtype="<f4").reshape(-1, len(lab)).T
    rt_ch = [bool(np.array_equal(back[j].astype(np.float64), X[j], equal_nan=True)) for j in range(X.shape[0])]
    del back
    types = [ctype(n) for n in lab_src]
    rows = []
    for n, n0, (t, d) in zip(lab, lab_src, types):
        if n != n0:
            d += " (duplicate release label '%s'; occurrence renamed %s)" % (n0, n)
        grp = ("left lead" if n0[0] == "L" else "right lead") if t == "DBS" else "n/a"
        rows.append([n, t, "n/a", "n/a", "n/a", fs, grp, "good", "n/a", d])
    wtsv(os.path.join(Dd, stem + "_channels.tsv"), ["name", "type", "units", "low_cutoff", "high_cutoff", "sampling_frequency", "group", "status", "status_description", "description"], rows)
    ev = []
    for t, d in zip(evt, evd):
        if isinstance(d, str):
            continue
        for s in np.asarray(d, dtype=np.float64).ravel():
            if np.isfinite(s):
                ev.append([round(float(s), 6), 0.0, "spike2_" + re.sub(r"\W", "", str(t)), int(round(float(s) * fs))])
    ev.sort(key=lambda r: r[0])
    wtsv(os.path.join(Dd, stem + "_events.tsv"), ["onset", "duration", "trial_type", "sample"], ev)
    ncnt = {kk: sum(1 for t, _ in types if t == kk) for kk in ("DBS", "EEG", "EMG", "MISC")}
    if task == "dbsramp":
        tdesc = ("Continuous 130 Hz monopolar DBS of the %s lead at contact level %d with the intensity increased in 0.5 mA steps from 0.5 mA up to 4.5 mA "
                 "or the side-effect threshold (README; Wiest et al. 2022: blocks of ~47 s separated by ~28 s rest; in patient 2 also 100/130/150/180 Hz for 2 min each "
                 "at one contact). LFPs from the adjacent levels recorded bipolar, all other contacts unipolar. Release file label '%s'.") % (side.lower(), level, rlabel)
        stim = {"Description": "monopolar 130 Hz DBS at %s contact level %d, intensity ramp 0.5-4.5 mA in 0.5 mA steps (README; Wiest et al. 2022); timing and intensity in the Cur/Am channels" % (side.lower(), level)}
    elif task == "singlepulse":
        tdesc = ("Single-pulse stimulation (25 pulses) applied in sequence to all 8 contact levels of the %s lead, the remaining seven contacts recorded unipolar "
                 "(README; Wiest et al. 2022: 2 mA in patient 5, 4 mA in patients 6 and 7).") % side.lower()
        stim = {"Description": "single pulses, 25 per contact level, all 8 levels in sequence (README; Wiest et al. 2022)"}
    else:
        tdesc = "Release file label 'Paired' (contact level %d, %s lead); this recording type is not described in the release README or in Wiest et al. 2022." % (level, side.lower())
        stim = {"Description": "not described in the release (file label 'Paired', contact level %d)" % level}
    wjson(os.path.join(Dd, stem + "_ieeg.json"), {
        "TaskName": task, "TaskDescription": tdesc,
        "SamplingFrequency": fs, "PowerLineFrequency": 50,
        "SoftwareFilters": {"DCRemoval": {"Description": DCNOTE}}, "HardwareFilters": "n/a",
        "Manufacturer": "TMSi", "ManufacturersModelName": "Saga",
        "RecordingSoftware": "custom software written in C (Wiest et al. 2022); exported to Spike2 .smr and then to MATLAB (SmrData)",
        "iEEGReference": "unipolar contacts and EEG: common mode rejection (README); contacts adjacent to the stimulated level: bipolar (labels like L13)",
        "iEEGPlacementScheme": "%s externalised octopolar DBS lead(s) spanning STN (inferior contacts), rostral zona incerta and ventrolateral thalamus (superior contacts); recorded 4-7 days after surgery off anti-dystonic medication (Wiest et al. 2022)" % ("bilateral" if any(n.startswith("L") for n in lab_src) and any(n.startswith("R") for n in lab_src) else "unilateral"),
        "ElectrodeManufacturer": "Boston Scientific", "ElectrodeManufacturersModelName": "Vercise Standard Lead 2201 (non-directional, 8 ring contacts)",
        "RecordingType": "continuous", "RecordingDuration": round(X.shape[1] / fs, 4),
        "DBSChannelCount": ncnt["DBS"], "EEGChannelCount": ncnt["EEG"], "EMGChannelCount": ncnt["EMG"], "MiscChannelCount": ncnt["MISC"],
        "ECOGChannelCount": 0, "SEEGChannelCount": 0,
        "ElectricalStimulation": True, "ElectricalStimulationParameters": stim["Description"],
    })
    dst = os.path.join(SD, os.path.relpath(fn, EX).split(os.sep, 1)[1])
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    sc = scrub_copy(fn, dst)
    contacts = sorted({c for n in lab_src if re.fullmatch(r"[LR][1-8]{1,2}", n) for c in ([n] if len(n) == 2 else [n[0] + n[1], n[0] + n[2]])})
    mean = X.mean(axis=1)
    rec = dict(src=os.path.relpath(fn, EX), sub=sub, side_folder=side, task=task, acq=acq, release_label=rlabel, stim_level=level, stem=stem,
               n_ch=len(lab), labels_src=lab_src, labels=lab, sfreq=fs, n_samples=int(X.shape[1]), duration_s=X.shape[1] / fs,
               n_nan=int(np.isnan(X).sum()), types=ncnt, n_events=len(ev), event_titles=[str(t) for t in evt],
               dbs_channel_mean_abs_max=float(max([abs(mean[j]) for j, (t, _) in enumerate(types) if t == "DBS"] or [0])),
               float32_exact=all(exact32), roundtrip_ok=all(rt_ch) and all(exact32), contacts=contacts, scrub=sc)
    print(stem, len(lab), X.shape[1], round(X.shape[1] / fs, 1), "rt", rec["roundtrip_ok"], "scrub_ok", sc["signal_identical"] and not sc["leaks"], flush=True)
    return rec


if __name__ == "__main__":
    os.makedirs(SD, exist_ok=True)
    with Pool(int(os.environ.get("NPROC", "4"))) as P:
        recs = P.map(one, SRC, chunksize=1)
    rep = {"recordings": recs}
    # README identical across zips -> one copy
    txt = [open(r, "rb").read() for r in READMES]
    assert all(t == txt[0] for t in txt)
    shutil.copy(READMES[0], os.path.join(SD, "README.txt"))
    # scans.tsv per subject
    bysub = {}
    for r in recs:
        bysub.setdefault(r["sub"], []).append(r)
    for sub, rs in bysub.items():
        wtsv(os.path.join(OUT, sub, f"{sub}_scans.tsv"), ["filename", "acq_time", "source_file", "release_label", "stimulated_hemisphere_folder", "stimulated_contact_level"],
             [[f"ieeg/{r['stem']}_ieeg.vhdr", "n/a", r["src"].split(os.sep, 1)[1], r["release_label"], r["side_folder"], r["stim_level"] if r["stim_level"] else "n/a"]
              for r in sorted(rs, key=lambda r: r["stem"])])
        con = sorted({c for r in rs for c in r["contacts"]}, key=lambda c: (c[0], int(c[1])))
        Dd = os.path.join(OUT, sub, "ieeg")
        wtsv(os.path.join(Dd, f"{sub}_space-Other_electrodes.tsv"), ["name", "x", "y", "z", "size", "group", "hemisphere", "contact_level", "region_stated", "manufacturer", "model"],
             [[c, "n/a", "n/a", "n/a", "n/a", "left lead" if c[0] == "L" else "right lead", c[0], int(c[1]),
               "lead spans STN (inferior contacts), rostral zona incerta and ventrolateral thalamus (superior contacts) (Wiest et al. 2022); per-contact localisation not released",
               "Boston Scientific", "Vercise 2201"] for c in con])
        wjson(os.path.join(Dd, f"{sub}_space-Other_electrodes.json"), {
            "SpatialReference": "none: no electrode coordinates are included in the source release (x, y, z = n/a); Wiest et al. 2022 Fig. 1A shows Lead-DBS reconstructions but they are not released",
            "hemisphere": {"Description": "Hemisphere of the lead (L/R, from the release channel label)"},
            "contact_level": {"Description": "Contact level 1-8 (1 = most inferior, Wiest et al. 2022 naming C1-C8)"},
            "region_stated": {"Description": "Target structures stated by the source for the lead as a whole"},
            "manufacturer": {"Description": "Lead manufacturer (Wiest et al. 2022)"}, "model": {"Description": "Lead model (Wiest et al. 2022)"}})
        wjson(os.path.join(Dd, f"{sub}_space-Other_coordsystem.json"), {"iEEGCoordinateSystem": "Other", "iEEGCoordinateUnits": "n/a",
              "iEEGCoordinateSystemDescription": "No contact coordinates are released. Contacts are listed with x, y, z = n/a under the release names L1-L8/R1-R8 (level 1 most inferior)."})
    # participants (Wiest et al. 2022 Table 1; release numbering = paper numbering, see README)
    T1 = {1: ("F", 64, "segmental dystonia: cervical dystonia, upper limb", 28, 4), 2: ("F", 49, "cervical dystonia", 6, 4),
          3: ("F", 68, "craniocervical dystonia", 55, 4), 4: ("F", 59, "cervical dystonia", 5, 5),
          5: ("F", 45, "segmental dystonia: cervical dystonia, upper limb", 25, 7), 6: ("M", 52, "cervical dystonia", 8, 7),
          7: ("M", 51, "segmental dystonia: cervical dystonia, trunk", 10, 7)}
    parts = []
    for sub in sorted(bysub):
        k = int(sub[4:])
        s, a, dx, dd, po = T1[k]
        parts.append([sub, "P%d" % k, a, s, dx, dd, po, ",".join(sorted({r["side_folder"] for r in bysub[sub]}))])
    wtsv(os.path.join(OUT, "participants.tsv"), ["participant_id", "release_id", "age", "sex", "diagnosis", "disease_duration", "days_post_op", "hemisphere_folders"], parts)
    wjson(os.path.join(OUT, "participants.json"), {
        "release_id": {"Description": "Participant number in the release (folders Participant<k>_/Patient<k>_)"},
        "age": {"Description": "Age in years (Wiest et al. 2022 Table 1)", "Units": "year"},
        "sex": {"Description": "Sex (Wiest et al. 2022 Table 1, 'Gender (m/f)')", "Levels": {"F": "female", "M": "male"}},
        "diagnosis": {"Description": "Diagnosis (Wiest et al. 2022 Table 1; CD = cervical dystonia)"},
        "disease_duration": {"Description": "Disease duration (Wiest et al. 2022 Table 1)", "Units": "year"},
        "days_post_op": {"Description": "Time of recording after surgery (Wiest et al. 2022 Table 1)", "Units": "day"},
        "hemisphere_folders": {"Description": "Release hemisphere folders present for this participant (side whose lead was stimulated)"}})
    evtit = sorted({"spike2_" + re.sub(r"\W", "", t) for r in recs for t in r["event_titles"]})
    for t in sorted({r["task"] for r in recs}):
        wjson(os.path.join(OUT, f"task-{t}_events.json"), {
            "trial_type": {"Description": "Spike2 event channel of the release (SmrData.EvTits/EvData)",
                           "Levels": {e: "time stamp of the Spike2 event channel '%s' (not described further in the release)" % e[7:] for e in evtit}},
            "sample": {"Description": "0-based sample index at 4096 Hz"}})
    stems = [r["stem"] for r in recs]
    assert len(set(stems)) == len(stems), "duplicate BIDS stems"
    os.makedirs(os.path.join(OUT, "code"), exist_ok=True)
    for fn in (os.path.abspath(__file__), os.path.join(os.path.dirname(os.path.abspath(__file__)), "b3w3_common.py")):
        shutil.copy(fn, os.path.join(OUT, "code", os.path.basename(fn)))
    json.dump(rep, open(os.path.join(OUT, "code", "conversion_report.json"), "w"), indent=1)
    hrs = sum(r["duration_s"] for r in recs) / 3600
    durs = [r["duration_s"] for r in recs]
    ntask = {t: sum(1 for r in recs if r["task"] == t) for t in ("dbsramp", "singlepulse", "paired")}
    wjson(os.path.join(OUT, "dataset_description.json"), {
        "Name": "Subthalamic and thalamic local field potentials during DBS in cervical dystonia (Wiest et al. 2022; derivative, DC-removed release at 4096 Hz)",
        "BIDSVersion": "1.10.0", "DatasetType": "derivative", "License": "CC-BY-SA-4.0",
        "Authors": ["Christoph Wiest", "Flavie Torrecillos", "Francesca Morgante", "Erlick Pereira", "Huiling Tan"],
        "Acknowledgements": "Data collected and shared by the MRC Brain Network Dynamics Unit, University of Oxford (Tan group), with St George's University Hospitals NHS Foundation Trust, London. Copyright 2020-2022, University of Oxford.",
        "HowToAcknowledge": "Cite the dataset (Wiest C, Torrecillos F, Morgante F, Pereira E, Tan H. University of Oxford, doi:10.5287/bodleian:qrnqjnpv7) and Wiest C, Morgante F, Torrecillos F, Pogosyan A, He S, Baig F, Bertaina I, Hart MG, Edwards MJ, Pereira EA, Tan H (2023). Subthalamic Nucleus Stimulation-Induced Local Field Potential Changes in Dystonia. Mov Disord 38(3), doi:10.1002/mds.29302.",
        "Funding": ["Medical Research Council UK (MC_UU_00003/2, MR/P012272/1, MR/V00655X/1)", "National Institute for Health Research (NIHR) Oxford Biomedical Research Centre", "Rosetrees Trust (PGL21/10115)"],
        "EthicsApprovals": ["Health Research Authority UK and National Research Ethics Service Local Research Ethics Committee (IRAS: 46576) (Wiest et al. 2022)"],
        "ReferencesAndLinks": ["https://doi.org/" + DOI, "https://doi.org/" + PAPER, "https://data.mrc.ox.ac.uk/"],
        "Keywords": ["dystonia", "cervical dystonia", "subthalamic nucleus", "zona incerta", "thalamus", "local field potential", "deep brain stimulation", "evoked resonant neural activity", "single-pulse stimulation"],
        "SourceDatasets": [{"DOI": "doi:" + DOI, "URL": "https://doi.org/" + DOI, "Version": "Cambium release (zips 'P1,P2', 'P3,P4', 'P5,P6,P7')"}],
        "GeneratedBy": [{"Name": "Authors' processing", "Description": "TMSi Saga recordings at 4096 Hz exported to Spike2 .smr and MATLAB SmrData structs; the released signals have no DC offset on any channel (undocumented DC removal/high-pass, cutoff not stated); derived channels (F-*, S-*, f*) included by the authors."},
                        {"Name": "b3w12_convert_dyst.py", "Description": "Repackaging of the Spike2/MATLAB exports to BrainVision float32 with values unchanged (exact); Spike2 Mark events; code in code/."}],
    })
    open(os.path.join(OUT, "README"), "w").write(f"""# Subthalamic and thalamic LFPs during DBS in cervical dystonia (Wiest et al. 2022) - DERIVATIVE

Local field potentials (LFPs) from externalised octopolar deep brain stimulation (DBS) leads in 7 patients with isolated
idiopathic (cranio)cervical dystonia (12 hemispheres; leads span the subthalamic nucleus (STN, inferior contacts), the rostral
zona incerta and the ventrolateral thalamus (superior contacts)), recorded 4-7 days after surgery off anti-dystonic medication
at St George's University Hospitals, London, while stimulation was applied through the lead. Scalp EEG, EMG of dystonic neck
muscles and accelerometers were recorded in some patients. The data were first analysed in Wiest et al. (2022/2023),
which reports broadband power suppression, evoked resonant neural activity (ERNA) and finely tuned gamma under STN stimulation.

## Source
- Wiest C, Torrecillos F, Morgante F, Pereira E, Tan H. "Subthalamic and thalamic local field potential recordings from patients
  with cervical dystonia". University of Oxford, MRC Brain Network Dynamics Unit data sharing platform (Cambium). doi:{DOI}
- Wiest C, Morgante F, Torrecillos F, Pogosyan A, He S, Baig F, Bertaina I, Hart MG, Edwards MJ, Pereira EA, Tan H (2023).
  Subthalamic Nucleus Stimulation-Induced Local Field Potential Changes in Dystonia. Mov Disord 38(3). doi:{PAPER}
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
- {len(recs)} continuous recordings, {hrs:.2f} h in total, {min(durs)/60:.1f}-{max(durs)/60:.1f} min each, all at 4096 Hz.
  One BIDS run per release .mat file; the release file is listed in each sub-*_scans.tsv (source_file).
  - `task-dbsramp` ({ntask['dbsramp']} files; release labels 'Testing' and, for participant 2, 'DBS'): continuous 130 Hz
    monopolar DBS of one of the six middle contact levels (2-7; `acq-<L|R><level>`) with the intensity increased in 0.5 mA steps
    up to 4.5 mA or the side-effect threshold. In patient 2 the paper also tested 100/130/150/180 Hz for 2 min each at one contact.
  - `task-singlepulse` ({ntask['singlepulse']} files, participants 5-7; `acq-left|right`): 25 single pulses applied to each of the 8
    contact levels in sequence, the remaining contacts recorded unipolar.
  - `task-paired` ({ntask['paired']} file, participant 7, release label 'Paired', left contact level 2): not described in the
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
""")
    open(os.path.join(OUT, "CHANGES"), "w").write("1.0.0 2026-10-08\n  - Repackaging of Cambium doi:10.5287/bodleian:qrnqjnpv7 for NEMAR.\n")
    open(os.path.join(OUT, ".bidsignore"), "w").write("code/\n")
    scrub_ok = all(r["scrub"]["signal_identical"] and not r["scrub"]["leaks"] for r in recs)
    print(json.dumps({"recordings": len(recs), "hours": hrs, "min_s": min(durs), "max_s": max(durs), "tasks": ntask,
                      "rt_all": all(r["roundtrip_ok"] for r in recs) and scrub_ok, "float32_exact_all": all(r["float32_exact"] for r in recs),
                      "scrub_ok": scrub_ok, "n_nan": sum(r["n_nan"] for r in recs)}))
    print("CONVERT_DONE")
