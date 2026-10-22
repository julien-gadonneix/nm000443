import argparse
import pathlib
import re

import mne
import mne_bids
import numpy as np
import pandas as pd
import scipy.signal

FS = 4096.0
SOS = scipy.signal.butter(4, 700, "lowpass", fs=FS, output="sos")
# Wiest et al. 2022 Fig. 4B-F: box-plot median ENA amplitude (µV) per recorded contact, read off the plots to 5 µV
PAPER = {
    ("sub-05", "left", 1): {2: 105, 3: 35, 4: 40, 5: 50, 6: 40, 7: 30, 8: 25},
    ("sub-06", "left", 3): {1: 95, 2: 230, 4: 290, 5: 70, 6: 50, 7: 90, 8: 95},
    ("sub-06", "right", 2): {1: 30, 3: 190, 4: 130, 5: 45, 6: 45, 7: 65, 8: 85},
    ("sub-07", "left", 2): {1: 50, 3: 85, 4: 40, 5: 40, 6: 55, 7: 60, 8: 55},
    ("sub-07", "right", 3): {1: 45, 2: 55, 4: 110, 5: 45, 6: 40, 7: 60, 8: 70},
}


def markdown(df: pd.DataFrame) -> str:
    lines = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    lines += ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(lines)


def vhdr_channels(vhdr: pathlib.Path) -> list[tuple[str, str, str]]:
    return re.findall(r"^Ch\d+=([^,]*),[^,]*,([^,]*),(.*)$", vhdr.read_text(encoding="utf-8"), re.M)


def tables(root: pathlib.Path) -> pd.DataFrame:
    rows = []
    for tsv in sorted(root.glob("sub-*/ieeg/*_channels.tsv")):
        stem = tsv.name.removesuffix("_channels.tsv")
        vhdr = tsv.with_name(f"{stem}_ieeg.vhdr")
        ch = pd.read_csv(tsv, sep="\t", keep_default_na=False)
        hdr = vhdr_channels(vhdr)
        assert [h[0] for h in hdr] == ch.name.tolist(), stem
        stored = np.fromfile(vhdr.with_suffix(".eeg"), dtype="<f4").reshape(-1, len(hdr)).T
        bv = mne.io.read_raw_brainvision(vhdr, preload=True, verbose="error")
        bids = mne_bids.read_raw_bids(mne_bids.get_bids_path_from_fname(vhdr), verbose="error")
        n_type = ch.type.value_counts()
        bids_types = pd.Series(bids.get_channel_types()).value_counts()
        dbs = mne.pick_types(bids.info, dbs=True)
        rows.append(
            {
                "recording": stem,
                "rows": len(ch),
                **{t: int(n_type.get(t, 0)) for t in ("DBS", "EEG", "EMG", "MISC")},
                "units": "/".join(sorted(set(ch.units))),
                "vhdr unit": "/".join(sorted({h[2] for h in hdr})),
                "vhdr resolution": "/".join(sorted({h[1] for h in hdr})),
                "brainvision types": "/".join(sorted(set(bv.get_channel_types()))),
                "brainvision == stored": np.array_equal(bv.get_data(), stored),
                "read_raw_bids dbs": int(bids_types.get("dbs", 0)),
                "read_raw_bids dbs unit": "/".join(sorted({bids.info["chs"][i]["unit"]._name for i in dbs})),
                "read_raw_bids == stored": np.array_equal(bids.get_data(), stored),
            }
        )
    return pd.DataFrame(rows)


def ena_amplitude(trace: np.ndarray) -> float:
    t = np.arange(len(trace)) / FS * 1e3
    keep = (t >= 1.5) & (t <= 10)
    seg = scipy.signal.sosfiltfilt(SOS, scipy.signal.detrend(trace[keep]), padlen=10)
    t = t[keep]
    window = (t >= 3.5) & (t <= 6.5)
    peak = np.flatnonzero(window)[np.argmax(seg[window])]
    return float(seg[peak] - seg[(t > t[peak]) & (t <= t[peak] + 3)].min())


def ena(root: pathlib.Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    recordings, contacts = [], []
    for (sub, hemi, stim), paper in PAPER.items():
        vhdr = root / sub / "ieeg" / f"{sub}_task-singlepulse_acq-{hemi}_ieeg.vhdr"
        names = [h[0] for h in vhdr_channels(vhdr)]
        x = np.memmap(vhdr.with_suffix(".eeg"), dtype="<f4", mode="r").reshape(-1, len(names))
        lead = np.asarray(x[:, [names.index(f"{hemi[0].upper()}{k}") for k in range(1, 9)]], dtype=float)
        jump = np.abs(np.diff(lead, axis=0))
        mad = 1.4826 * np.median(jump, axis=0)
        z = np.max(jump[:, mad > 0] / mad[mad > 0], axis=1)
        hits = np.flatnonzero(z > 50)
        onsets = hits[np.r_[True, np.diff(hits) > 0.005 * FS]] + 1
        gap = np.diff(onsets) / FS
        isolated = onsets[np.r_[True, gap > 0.3] & np.r_[gap > 0.3, True]]
        half = int(0.1 * FS)
        flat = np.array([np.all(lead[max(0, p - half) : p + half] == 0, axis=0) for p in isolated], dtype=bool)
        flat = flat.reshape(-1, 8)
        pulses = isolated[flat[:, stim - 1] & (flat.sum(axis=1) == 1)]
        recording = f"{sub} {hemi}"
        recordings.append(
            {
                "recording": recording,
                "Fig. 4 stim": f"C{stim}",
                "flat contacts (whole file)": ",".join(f"C{k + 1}" for k in range(8) if np.all(lead[:, k] == 0)),
                "artifacts": len(onsets),
                "median artifact interval (s)": round(float(np.median(gap)), 3),
                "isolated (> 0.3 s)": len(isolated),
                "pulses used": len(pulses),
            }
        )
        for k, ref in paper.items():
            if len(pulses) == 0:
                continue
            med = float(np.median([ena_amplitude(lead[p : p + int(0.012 * FS), k - 1]) for p in pulses]))
            contacts.append({"recording": recording, "stim": f"C{stim}", "contact": f"C{k}", "paper µV": ref,
                             "stored median": round(med, 1), "ratio": round(med / ref, 2)})
    return pd.DataFrame(recordings), pd.DataFrame(contacts)


parser = argparse.ArgumentParser()
parser.add_argument("root", type=pathlib.Path)
root = parser.parse_args().root
print(f"mne {mne.__version__}, mne_bids {mne_bids.__version__}\n")
tab = tables(root)
print(markdown(tab))
print(f"\n{len(tab)} tables, {tab.rows.sum()} rows, {tab.DBS.sum()} DBS rows; units values: {sorted(set(tab.units))}\n")
recordings, contacts = ena(root)
print(markdown(recordings) + "\n")
print(markdown(contacts))
r = contacts.ratio
print(f"\nratio stored/paper over {len(r)} contacts: median {r.median():.2f}, IQR {r.quantile(0.25):.2f}-{r.quantile(0.75):.2f}, "
      f"range {r.min():.2f}-{r.max():.2f}")
