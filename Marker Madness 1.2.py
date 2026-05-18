#!/usr/bin/env python3
"""
Marker Madness 1.2 — DaVinci Resolve Marker Manager
====================================================
A GUI tool to view, add, edit, delete, and export both timeline markers
and clip-based markers in your current DaVinci Resolve timeline.

Compatible with DaVinci Resolve 18 and 19.

Installation:
  Copy this file to your DaVinci Resolve scripts folder, then run it
  from Workspace > Scripts > Utility inside DaVinci Resolve.

  macOS:   /Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Utility/
  Windows: C:\\ProgramData\\Blackmagic Design\\DaVinci Resolve\\Fusion\\Scripts\\Utility\\
  Linux:   /opt/resolve/Fusion/Scripts/Utility/
"""

import sys
import os
import csv
import glob
import json
import shutil
import tempfile
import time
import datetime
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# ---------------------------------------------------------------------------
# DaVinci Resolve API connection
# ---------------------------------------------------------------------------

RESOLVE_SCRIPT_PATHS = {
    "darwin": "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules",
    "win32":  os.path.join(
        os.environ.get("PROGRAMDATA", "C:\\ProgramData"),
        "Blackmagic Design", "DaVinci Resolve", "Support", "Developer", "Scripting", "Modules",
    ),
    "linux": "/opt/resolve/Developer/Scripting/Modules",
}

def _add_resolve_path():
    p   = sys.platform
    key = "darwin" if p == "darwin" else "win32" if p.startswith("win") else "linux"
    path = RESOLVE_SCRIPT_PATHS.get(key, "")
    if path and path not in sys.path:
        sys.path.append(path)

def get_resolve():
    _add_resolve_path()
    try:
        import DaVinciResolveScript as dvr
        return dvr.scriptapp("Resolve")
    except Exception:
        return None

# ---------------------------------------------------------------------------
# Marker colours
# ---------------------------------------------------------------------------

MARKER_COLORS = [
    "Blue", "Cyan", "Green", "Yellow", "Red", "Pink",
    "Purple", "Fuchsia", "Rose", "Lavender", "Sky", "Mint",
    "Lemon", "Sand", "Cocoa", "Cream",
]

COLOR_HEX = {
    "Blue": "#3A7BD5", "Cyan": "#00BFFF", "Green": "#32CD32",
    "Yellow": "#FFD700", "Red": "#E53935", "Pink": "#FF69B4",
    "Purple": "#8A2BE2", "Fuchsia": "#FF00FF", "Rose": "#FF007F",
    "Lavender": "#9B72CF", "Sky": "#87CEEB", "Mint": "#98FF98",
    "Lemon": "#FFF44F", "Sand": "#C2B280", "Cocoa": "#7B3F00",
    "Cream": "#FFFDD0",
}



# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------

BG      = "#2d2d2d"
PANEL   = "#333333"
TEXT    = "#E2E2E2"
ACCENT  = "#ffa500"
BTN     = "#404040"
BTN_HOV = "#505050"
ENTRY_BG= "#1e1e1e"
SEL_BG  = "#505050"
RED     = "#E05C5C"
GREEN   = "#6DBF87"
ORANGE  = "#ffa500"
PURPLE  = "#B07CC6"
DIM     = "#707070"

F_MAIN  = ("Avenir Next", 12)
F_BOLD  = ("Avenir Next", 13, "bold")
F_SMALL = ("Avenir Next", 10)
F_MONO  = ("Courier", 11)
F_TITLE = ("Avenir Next", 20, "bold")
F_STATUS = ("Avenir Next", 10, "italic")

# ---------------------------------------------------------------------------
# Table columns
# (id, heading, width, anchor, stretch, inline_editable)
# ---------------------------------------------------------------------------

COLUMNS = [
    ("mtype",      "Type",      62,  "center", False, False),
    ("frame",      "Frame",     75,  "center", False, False),
    ("timecode",   "Marker TC",     110, "center", False, False),
    ("color",      "Color",          90, "center", False, False),
    ("name",       "Name",          200, "w",      False, False),
    ("note",       "Note",          260, "w",      False, False),
    ("clip",       "Clip",          160, "w",      False, False),
    ("duration",   "Marker Dur",     80, "center", False, False),
    ("clip_in",    "Clip In",       110, "center", False, False),
    ("clip_out",   "Clip Out",      110, "center", False, False),
    ("clip_dur_f", "Clip Dur (f)",   80, "center", False, False),
    ("clip_dur_t", "Clip Dur (TC)", 100, "center", False, False),
]

COL_IDS      = [c[0] for c in COLUMNS]
EDITABLE_COLS = {c[0] for c in COLUMNS if c[5]}
COL_NUM      = {c[0]: f"#{i+1}" for i, c in enumerate(COLUMNS)}
NUM_COL      = {f"#{i+1}": c[0] for i, c in enumerate(COLUMNS)}

SORT_KEY = {
    "mtype":    lambda r: r.get("type", ""),
    "frame":    lambda r: r.get("timeline_frame", 0),
    "timecode": lambda r: r.get("timeline_frame", 0),
    "color":    lambda r: r.get("color", ""),
    "name":     lambda r: r.get("name", "").lower(),
    "note":     lambda r: r.get("note", "").lower(),
    "clip":     lambda r: r.get("clip_name", "").lower(),
    "duration":   lambda r: r.get("duration", 0),
    "clip_in":    lambda r: r.get("clip_in_frame",  -1),
    "clip_out":   lambda r: r.get("clip_out_frame", -1),
    "clip_dur_f": lambda r: r.get("clip_dur_frames", -1),
    "clip_dur_t": lambda r: r.get("clip_dur_frames", -1),
}

HTML_COLUMNS = [
    ("thumbnail", "Thumbnail"),
    ("type",      "Type"),
    ("timecode",  "Marker Timecode"),
    ("color",     "Color"),
    ("name",      "Name"),
    ("note",      "Note"),
    ("clip",      "Clip"),
    ("clip_in",   "Clip In"),
    ("clip_out",  "Clip Out"),
    ("dur_f",     "Clip Dur (f)"),
    ("dur_t",     "Clip Dur (TC)"),
]

# Maps display-column IDs to HTML_COLUMNS keys (columns with no HTML equivalent are absent)
DISPLAY_TO_HTML = {
    "mtype":      "type",
    "timecode":   "timecode",
    "color":      "color",
    "name":       "name",
    "note":       "note",
    "clip":       "clip",
    "clip_in":    "clip_in",
    "clip_out":   "clip_out",
    "clip_dur_f": "dur_f",
    "clip_dur_t": "dur_t",
}

THUMB_SIZES = [
    ("Original",     None),
    ("HD  (1920px)", 1920),
    ("Web (1280px)", 1280),
    ("Mid  (960px)", 960),
    ("Small (640px)", 640),
]

EXPORT_FORMATS = [
    ("PNG",  "png"),
    ("TIFF", "tif"),
    ("JPEG", "jpg"),
]

# sips format name for each Resolve export format string
SIPS_FMT = {"png": "png", "tif": "tiff", "jpg": "jpeg"}

# ---------------------------------------------------------------------------
# Preferences  (persistent JSON file, survives sessions)
# ---------------------------------------------------------------------------

try:
    PREFS_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    PREFS_DIR = os.path.expanduser("~/Library/Application Support/Marker Madness")
    os.makedirs(PREFS_DIR, exist_ok=True)
PREFS_FILE = os.path.join(PREFS_DIR, "prefs.json")


def _load_prefs() -> dict:
    try:
        with open(PREFS_FILE, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def _save_prefs(data: dict):
    try:
        with open(PREFS_FILE, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# CSV column definitions  (used by display-order-aware export)
# Maps Treeview column ID → (CSV header label, value extractor)
# Extractors receive (rec, fps, start_frame) and return a scalar.
# ---------------------------------------------------------------------------

CSV_COL_DEF = {
    "mtype":      ("Type",          lambda r, fps, sf: r["type"]),
    "frame":      ("Frame",         lambda r, fps, sf: r["timeline_frame"] + sf),
    "timecode":   ("Timecode",      lambda r, fps, sf: frames_to_tc(r["timeline_frame"] + sf, fps)),
    "color":      ("Color",         lambda r, fps, sf: r["color"]),
    "name":       ("Name",          lambda r, fps, sf: r["name"]),
    "note":       ("Note",          lambda r, fps, sf: r["note"]),
    "clip":       ("Clip",          lambda r, fps, sf: r["clip_name"]),
    "duration":   ("Marker Dur",    lambda r, fps, sf: r["duration"]),
    "clip_in":    ("Clip In",       lambda r, fps, sf: frames_to_tc(r["clip_in_frame"] + sf, fps) if r["clip_in_frame"] is not None else ""),
    "clip_out":   ("Clip Out",      lambda r, fps, sf: frames_to_tc(r["clip_out_frame"] + sf, fps) if r["clip_out_frame"] is not None else ""),
    "clip_dur_f": ("Clip Dur (f)",  lambda r, fps, sf: r["clip_dur_frames"] if r["clip_dur_frames"] is not None else ""),
    "clip_dur_t": ("Clip Dur (TC)", lambda r, fps, sf: frames_to_tc(r["clip_dur_frames"], fps) if r["clip_dur_frames"] is not None else ""),
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def frames_to_tc(frame: int, fps: float) -> str:
    fps_i = round(fps)
    if fps_i < 1:
        fps_i = 1
    ff   = frame % fps_i
    secs = frame // fps_i
    return f"{secs // 3600:02d}:{(secs // 60) % 60:02d}:{secs % 60:02d}:{ff:02d}"

def tc_to_frames(tc: str, fps: float) -> int:
    parts = tc.replace(";", ":").split(":")
    if len(parts) != 4:
        return 0
    try:
        hh, mm, ss, ff = [int(p) for p in parts]
        return ((hh * 3600 + mm * 60 + ss) * round(fps)) + ff
    except ValueError:
        return 0


# ---------------------------------------------------------------------------
# Marker Renamer — transformation engine (ported from Batch Renamer Pro logic)
# ---------------------------------------------------------------------------

def _renamer_transform(text, *, find="", replace="", add="", add_pos="After",
                        replace_all=False, trim=False, trim_begin=0, trim_end=0,
                        counter=0, counter_enabled=False, counter_digits=2,
                        counter_pos="After", counter_step=1, upper=False, lower=False,
                        title_case=False, remove_digits=False):
    n = text
    if trim and (trim_begin > 0 or trim_end > 0):
        end_idx = len(n) - trim_end if trim_end > 0 else len(n)
        n = n[trim_begin:end_idx] if trim_begin < end_idx else ""
    if replace_all:
        n = add
    else:
        if find:
            n = n.replace(find, replace)
        if add and add_pos != "After counter":
            n = (add + n) if add_pos == "Before" else (n + add)
    if upper:
        n = n.upper()
    elif lower:
        n = n.lower()
    elif title_case:
        n = n.title()
    if remove_digits:
        n = "".join(c for c in n if not c.isdigit())
    if counter_enabled and counter_digits > 0:
        cs = str(counter).zfill(counter_digits)
        if counter_pos == "Before":
            n = cs + n
        else:
            n = n + cs
            if add_pos == "After counter" and add:
                n = n + add
    return n


# ---------------------------------------------------------------------------
# Marker Renamer dialog
# ---------------------------------------------------------------------------

class MarkerRenamerDialog(tk.Toplevel):

    def __init__(self, app):
        super().__init__(app.root)
        self.withdraw()
        self.transient(app.root)
        self._app        = app
        self._undo_stack = []   # list of [(rec, old_name, old_note), …]
        self._preview_job = None

        self.title("Marker Renamer")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.protocol("WM_DELETE_WINDOW", self.withdraw)

        self._build()
        self._schedule_preview()
        self.bind("<FocusIn>", self._on_focus_in)

        # Position left of main window
        self.update_idletasks()
        rx = app.root.winfo_rootx()
        ry = app.root.winfo_rooty()
        w  = self.winfo_reqwidth()
        self.geometry(f"+{max(0, rx - w - 8)}+{ry}")
        self.deiconify()
        self.lift()
        self.attributes("-topmost", True)

    # ── UI ────────────────────────────────────────────────────────────────

    def _build(self):
        DLG   = "#343434"
        FIELD = "#1e1e1e"

        self.configure(bg=DLG)

        # ── Title bar ─────────────────────────────────────────────────────
        tk.Label(self, text="  MARKER RENAMER  ", fg=ACCENT, bg=DLG,
                 font=("Avenir Next", 14, "bold")).pack(fill="x", ipady=8)

        body = tk.Frame(self, bg=DLG)
        body.pack(fill="both", expand=True, padx=12, pady=(8, 4))

        def section(parent, label):
            f = tk.LabelFrame(parent, text=f"  {label}  ", fg=ACCENT, bg=DLG,
                              font=F_SMALL, relief="flat",
                              highlightbackground=BTN_HOV, highlightthickness=1)
            f.pack(fill="x", pady=(6, 2))
            return f

        # ── Apply To ──────────────────────────────────────────────────────
        sf = section(body, "APPLY TO")
        self._field_var = tk.StringVar(value="name")
        fr = tk.Frame(sf, bg=DLG)
        fr.pack(fill="x", padx=8, pady=6)
        for val, lbl in [("name", "Name"), ("note", "Note"), ("both", "Both")]:
            tk.Radiobutton(fr, text=lbl, variable=self._field_var, value=val,
                           fg=TEXT, bg=DLG, activeforeground=TEXT,
                           activebackground=DLG, selectcolor=ENTRY_BG,
                           font=F_MAIN, command=self._schedule_preview).pack(side="left", padx=8)

        # ── Scope ─────────────────────────────────────────────────────────
        sc = section(body, "SCOPE")
        self._scope_var = tk.StringVar(value="selected")
        sr = tk.Frame(sc, bg=DLG)
        sr.pack(fill="x", padx=8, pady=6)
        for val, lbl in [("selected", "Selected markers"), ("visible", "All visible markers")]:
            tk.Radiobutton(sr, text=lbl, variable=self._scope_var, value=val,
                           fg=TEXT, bg=DLG, activeforeground=TEXT,
                           activebackground=DLG, selectcolor=ENTRY_BG,
                           font=F_MAIN, command=self._schedule_preview).pack(side="left", padx=8)

        # ── Rename Operations ─────────────────────────────────────────────
        # ── Copy Field ────────────────────────────────────────────────────
        cf = section(body, "COPY FIELD")
        cf_row = tk.Frame(cf, bg=DLG)
        cf_row.pack(fill="x", padx=8, pady=6)
        TBtn(cf_row, text="Name  →  Note", command=lambda: self._copy_field("name_to_note"),
             bg=ACCENT, fg=BG, padx=10, pady=4).pack(side="left", padx=(0, 6))
        TBtn(cf_row, text="Note  →  Name", command=lambda: self._copy_field("note_to_name"),
             bg=ACCENT, fg=BG, padx=10, pady=4).pack(side="left", padx=(0, 6))
        TBtn(cf_row, text="Clip Name  →  Marker Name", command=self._copy_clip_name,
             bg=ACCENT, fg=BG, padx=10, pady=4).pack(side="left")

        ops = section(body, "RENAME OPERATIONS")

        def lbl_entry_row(parent, label):
            r = tk.Frame(parent, bg=DLG)
            r.pack(fill="x", padx=8, pady=3)
            tk.Label(r, text=label, fg=DIM, bg=DLG,
                     font=F_SMALL, width=9, anchor="w").pack(side="left")
            v = tk.StringVar()
            tk.Entry(r, textvariable=v, bg=FIELD, fg=TEXT,
                     insertbackground=TEXT, relief="flat",
                     font=F_MAIN).pack(side="left", fill="x", expand=True)
            v.trace_add("write", lambda *_: self._schedule_preview())
            return v

        self._find_var    = lbl_entry_row(ops, "Find:")
        self._replace_var = lbl_entry_row(ops, "Replace:")

        # Add row + Replace All checkbox
        add_row = tk.Frame(ops, bg=DLG)
        add_row.pack(fill="x", padx=8, pady=3)
        tk.Label(add_row, text="Add:", fg=DIM, bg=DLG,
                 font=F_SMALL, width=9, anchor="w").pack(side="left")
        self._add_var = tk.StringVar()
        tk.Entry(add_row, textvariable=self._add_var, bg=FIELD, fg=TEXT,
                 insertbackground=TEXT, relief="flat", font=F_MAIN,
                 width=16).pack(side="left", fill="x", expand=True, padx=(0, 6))
        self._add_pos_var = tk.StringVar(value="After")
        ttk.Combobox(add_row, textvariable=self._add_pos_var,
                     values=["After", "Before"], state="readonly",
                     width=7, font=F_SMALL).pack(side="left")
        self._add_var.trace_add("write", lambda *_: self._schedule_preview())
        self._add_pos_var.trace_add("write", lambda *_: self._schedule_preview())

        rep_row = tk.Frame(ops, bg=DLG)
        rep_row.pack(fill="x", padx=8, pady=(0, 4))
        self._replace_all_var   = tk.BooleanVar(value=False)
        self._after_counter_var = tk.BooleanVar(value=False)
        tk.Checkbutton(rep_row, text="Replace entire name with Add text",
                       variable=self._replace_all_var,
                       fg=TEXT, bg=DLG, activeforeground=TEXT,
                       activebackground=DLG, selectcolor=ENTRY_BG,
                       font=F_SMALL,
                       command=self._schedule_preview).pack(side="left", padx=(75, 0))
        tk.Checkbutton(rep_row, text="After counter",
                       variable=self._after_counter_var,
                       fg=TEXT, bg=DLG, activeforeground=TEXT,
                       activebackground=DLG, selectcolor=ENTRY_BG,
                       font=F_SMALL,
                       command=self._schedule_preview).pack(side="left", padx=(16, 0))

        tk.Frame(ops, bg=BTN_HOV, height=1).pack(fill="x", padx=8, pady=2)

        # Trim + Counter — shared grid so columns align perfectly
        tc = tk.Frame(ops, bg=DLG)
        tc.pack(fill="x", padx=8, pady=4)

        def _spinbox(parent, var, lo, hi):
            sb = tk.Spinbox(parent, from_=lo, to=hi, textvariable=var,
                            width=5, bg=FIELD, fg=TEXT, insertbackground=TEXT,
                            buttonbackground=BTN, relief="flat", font=F_MAIN,
                            command=self._schedule_preview)
            var.trace_add("write", lambda *_: self._schedule_preview())
            return sb

        def _chk(parent, text, var, row):
            tk.Checkbutton(parent, text=text, variable=var,
                           fg=TEXT, bg=DLG, activeforeground=TEXT,
                           activebackground=DLG, selectcolor=ENTRY_BG,
                           font=F_SMALL, anchor="w",
                           command=self._schedule_preview).grid(
                               row=row, column=0, sticky="w", pady=3)

        def _lbl(parent, text, row, col):
            tk.Label(parent, text=text, fg=DIM, bg=DLG,
                     font=F_SMALL, anchor="e", width=7).grid(
                         row=row, column=col, sticky="e", padx=(6, 2))

        self._trim_var       = tk.BooleanVar(value=False)
        self._trim_begin_var = tk.IntVar(value=0)
        self._trim_end_var   = tk.IntVar(value=0)

        _chk(tc, "Trim",    self._trim_var,    row=0)
        _lbl(tc, "Begin:",  row=0, col=1)
        _spinbox(tc, self._trim_begin_var, 0, 999).grid(row=0, column=2)
        _lbl(tc, "End:",    row=0, col=3)
        _spinbox(tc, self._trim_end_var,   0, 999).grid(row=0, column=4)

        self._counter_var    = tk.BooleanVar(value=False)
        self._ctr_digits_var = tk.IntVar(value=2)
        self._ctr_start_var  = tk.IntVar(value=1)
        self._ctr_step_var   = tk.IntVar(value=1)
        self._ctr_pos_var    = tk.StringVar(value="After")

        _chk(tc, "Counter", self._counter_var, row=1)
        _lbl(tc, "Digits:", row=1, col=1)
        _spinbox(tc, self._ctr_digits_var, 1, 6).grid(row=1, column=2)
        _lbl(tc, "Start:",  row=1, col=3)
        _spinbox(tc, self._ctr_start_var,  0, 9999).grid(row=1, column=4)
        tk.Label(tc, text="Pos:", fg=DIM, bg=DLG,
                 font=F_SMALL, anchor="e", width=4).grid(row=1, column=5, sticky="e", padx=(6,2))
        cb = ttk.Combobox(tc, textvariable=self._ctr_pos_var,
                          values=["After", "Before"], state="readonly",
                          width=6, font=F_SMALL)
        cb.grid(row=1, column=6)
        self._ctr_pos_var.trace_add("write", lambda *_: self._schedule_preview())

        # Step row — indented under Counter
        _lbl(tc, "Step:",   row=2, col=1)
        _spinbox(tc, self._ctr_step_var, 1, 9999).grid(row=2, column=2)
        tk.Label(tc, text="e.g. 10 → 010, 020, 030  for VFX sequencing", fg=TEXT, bg=DLG,
                 font=("Avenir Next", 11, "italic")).grid(
                     row=2, column=3, columnspan=4, sticky="w", padx=(4, 0))

        tk.Frame(ops, bg=BTN_HOV, height=1).pack(fill="x", padx=8, pady=2)

        # Case + Remove digits — 2×2 grid
        cg = tk.Frame(ops, bg=DLG)
        cg.pack(fill="x", padx=8, pady=(4, 6))

        def _cb(parent, text, var, row, col):
            tk.Checkbutton(parent, text=text, variable=var,
                           fg=TEXT, bg=DLG, activeforeground=TEXT,
                           activebackground=DLG, selectcolor=ENTRY_BG,
                           font=F_SMALL, anchor="w", width=14,
                           command=self._schedule_preview).grid(
                               row=row, column=col, sticky="w", padx=(0, 4), pady=2)

        self._upper_var = tk.BooleanVar()
        self._lower_var = tk.BooleanVar()
        self._title_var = tk.BooleanVar()
        self._nodig_var = tk.BooleanVar()

        _cb(cg, "UPPERCASE",     self._upper_var, 0, 0)
        _cb(cg, "lowercase",     self._lower_var, 0, 1)
        _cb(cg, "Title Case",    self._title_var, 1, 0)
        _cb(cg, "Remove digits", self._nodig_var, 1, 1)

        # ── Preview ───────────────────────────────────────────────────────
        pf = section(body, "PREVIEW")

        style = ttk.Style()
        style.configure("Renamer.Treeview",
                         background=ENTRY_BG, fieldbackground=ENTRY_BG,
                         foreground=TEXT, rowheight=24, font=F_SMALL, borderwidth=0)
        style.configure("Renamer.Treeview.Heading",
                         background=BTN, foreground=ACCENT,
                         font=("Avenir Next", 10, "bold"), relief="flat")
        style.map("Renamer.Treeview",
                  background=[("selected", SEL_BG)],
                  foreground=[("selected", TEXT)])

        pf_inner = tk.Frame(pf, bg=DLG)
        pf_inner.pack(fill="both", expand=True, padx=8, pady=6)

        self._preview_tree = ttk.Treeview(pf_inner, columns=("before", "after"),
                                           show="headings", height=8,
                                           style="Renamer.Treeview",
                                           selectmode="none")
        self._preview_tree.heading("before", text="Before")
        self._preview_tree.heading("after",  text="After")
        self._preview_tree.column("before", width=200, anchor="w")
        self._preview_tree.column("after",  width=200, anchor="w")

        vsb = ttk.Scrollbar(pf_inner, orient="vertical",
                             command=self._preview_tree.yview)
        self._preview_tree.configure(yscrollcommand=vsb.set)
        self._preview_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # ── Bottom buttons ────────────────────────────────────────────────
        bf = tk.Frame(self, bg=DLG)
        bf.pack(fill="x", padx=12, pady=(4, 12))

        TBtn(bf, text="Clear",   command=self._clear,            bg=ACCENT, fg=BG,
             padx=10, pady=5).pack(side="left", padx=(0, 4))
        TBtn(bf, text="Refresh", command=self._schedule_preview, bg=BTN,
             padx=10, pady=5).pack(side="left", padx=(0, 4))
        self._undo_btn = TBtn(bf, text="↩  Undo", command=self._undo,
                              bg=BTN_HOV, fg=DIM, padx=10, pady=5)
        self._undo_btn.pack(side="left", padx=4)
        self._apply_btn = TBtn(bf, text="▶  Apply Changes",
                               command=self._apply, bg=ACCENT, fg=BG,
                               padx=14, pady=5)
        self._apply_btn.pack(side="right")

        self._status_var = tk.StringVar(value="")
        tk.Label(self, textvariable=self._status_var, fg=DIM, bg=DLG,
                 font=F_STATUS).pack(pady=(0, 6))

    # ── Helpers ───────────────────────────────────────────────────────────

    def _get_params(self, counter=0):
        add_pos = "After counter" if self._after_counter_var.get() else self._add_pos_var.get()
        return dict(
            find=self._find_var.get(),
            replace=self._replace_var.get(),
            add=self._add_var.get(),
            add_pos=add_pos,
            replace_all=self._replace_all_var.get(),
            trim=self._trim_var.get(),
            trim_begin=self._trim_begin_var.get(),
            trim_end=self._trim_end_var.get(),
            counter=counter,
            counter_enabled=self._counter_var.get(),
            counter_digits=self._ctr_digits_var.get(),
            counter_pos=self._ctr_pos_var.get(),
            counter_step=self._ctr_step_var.get(),
            upper=self._upper_var.get(),
            lower=self._lower_var.get(),
            title_case=self._title_var.get(),
            remove_digits=self._nodig_var.get(),
        )

    def _get_targets(self):
        """Return list of rec dicts to operate on, in display order."""
        app = self._app
        if self._scope_var.get() == "selected":
            ids = app._tree.selection()
        else:
            ids = app._tree.get_children()
        return [app._by_id[i] for i in ids if i in app._by_id]

    def _on_focus_in(self, event):
        if event.widget is self:
            self._schedule_preview()

    def _schedule_preview(self, *_):
        if self._preview_job:
            self.after_cancel(self._preview_job)
        self._preview_job = self.after(120, self._update_preview)

    def _update_preview(self):
        self._preview_job = None
        for row in self._preview_tree.get_children():
            self._preview_tree.delete(row)

        targets = self._get_targets()
        field   = self._field_var.get()
        counter = self._ctr_start_var.get() * self._ctr_step_var.get()

        for rec in targets:
            p = self._get_params(counter)
            if field == "name":
                before = rec["name"]
                after  = _renamer_transform(before, **p)
                label  = before
            elif field == "note":
                before = rec["note"]
                after  = _renamer_transform(before, **p)
                label  = before
            else:
                before = rec["name"]
                after  = _renamer_transform(before, **p)
                label  = before

            tag = "changed" if after != before else "same"
            self._preview_tree.insert("", "end", values=(label, after), tags=(tag,))
            if self._counter_var.get():
                counter += self._ctr_step_var.get()

        self._preview_tree.tag_configure("changed", foreground=ACCENT)
        self._preview_tree.tag_configure("same",    foreground=DIM)

        count = len(targets)
        scope = "selected" if self._scope_var.get() == "selected" else "visible"
        self._status_var.set(f"{count} {scope} marker{'s' if count != 1 else ''}")

    # ── Actions ───────────────────────────────────────────────────────────

    def _copy_field(self, direction):
        targets = self._get_targets()
        if not targets:
            self._status_var.set("No markers to copy.")
            return
        undo_batch = []
        errors     = []
        for rec in targets:
            if direction == "name_to_note":
                new_name, new_note = rec["name"], rec["name"]
            else:
                new_name, new_note = rec["note"], rec["note"]
            if new_name == rec["name"] and new_note == rec["note"]:
                continue
            undo_batch.append((rec, rec["name"], rec["note"]))
            ok, err = self._app._write_marker(rec, rec["color"], new_name,
                                               new_note, rec["duration"], "")
            if ok:
                rec["name"] = new_name
                rec["note"] = new_note
            else:
                errors.append(err)
        if undo_batch:
            self._undo_stack.append(undo_batch)
            self._undo_btn.config(bg=ACCENT, fg=BG)
        self._app._populate_table()
        self._update_preview()
        label = "Name → Note" if direction == "name_to_note" else "Note → Name"
        self._status_var.set(f"Copied {label} on {len(undo_batch)} marker{'s' if len(undo_batch) != 1 else ''}.")

    def _copy_clip_name(self):
        targets = [r for r in self._get_targets() if r.get("clip_name")]
        if not targets:
            self._status_var.set("No clip markers with a clip name in scope.")
            return
        undo_batch = []
        for rec in targets:
            new_name = rec["clip_name"]
            if new_name == rec["name"]:
                continue
            undo_batch.append((rec, rec["name"], rec["note"]))
            ok, _ = self._app._write_marker(rec, rec["color"], new_name,
                                             rec["note"], rec["duration"], "")
            if ok:
                rec["name"] = new_name
        if undo_batch:
            self._undo_stack.append(undo_batch)
            self._undo_btn.config(bg=ACCENT, fg=BG)
        self._app._populate_table()
        self._update_preview()
        self._status_var.set(f"Clip Name → Marker Name on {len(undo_batch)} marker{'s' if len(undo_batch) != 1 else ''}.")

    def _apply(self):
        targets = self._get_targets()
        if not targets:
            self._status_var.set("No markers to apply to.")
            return

        field   = self._field_var.get()
        counter = self._ctr_start_var.get() * self._ctr_step_var.get()
        undo_batch = []
        errors     = []

        for rec in targets:
            p        = self._get_params(counter)
            new_name = _renamer_transform(rec["name"], **p) if field in ("name", "both") else rec["name"]
            new_note = _renamer_transform(rec["note"], **p) if field in ("note", "both") else rec["note"]

            if new_name == rec["name"] and new_note == rec["note"]:
                if self._counter_var.get():
                    counter += 1
                continue

            undo_batch.append((rec, rec["name"], rec["note"]))
            ok, err = self._app._write_marker(rec, rec["color"], new_name,
                                               new_note, rec["duration"], "")
            if ok:
                rec["name"] = new_name
                rec["note"] = new_note
                if self._counter_var.get():
                    counter += 1
            else:
                errors.append(err)

        if undo_batch:
            self._undo_stack.append(undo_batch)
            self._undo_btn.config(bg=ACCENT, fg=BG)

        self._app._populate_table()
        self._update_preview()

        changed = len(undo_batch)
        if errors:
            self._status_var.set(f"Applied {changed}, {len(errors)} error(s).")
        else:
            self._status_var.set(f"Applied to {changed} marker{'s' if changed != 1 else ''}.")

    def _undo(self):
        if not self._undo_stack:
            return
        batch = self._undo_stack.pop()
        for rec, old_name, old_note in reversed(batch):
            ok, _ = self._app._write_marker(rec, rec["color"], old_name,
                                             old_note, rec["duration"], "")
            if ok:
                rec["name"] = old_name
                rec["note"] = old_note

        if not self._undo_stack:
            self._undo_btn.config(bg=BTN_HOV, fg=DIM)

        self._app._populate_table()
        self._update_preview()
        self._status_var.set(f"Undone {len(batch)} change{'s' if len(batch) != 1 else ''}.")

    def _clear(self):
        self._find_var.set("")
        self._replace_var.set("")
        self._add_var.set("")
        self._add_pos_var.set("After")
        self._replace_all_var.set(False)
        self._after_counter_var.set(False)
        self._trim_var.set(False)
        self._trim_begin_var.set(0)
        self._trim_end_var.set(0)
        self._counter_var.set(False)
        self._ctr_digits_var.set(2)
        self._ctr_start_var.set(1)
        self._ctr_step_var.set(1)
        self._ctr_pos_var.set("After")
        self._upper_var.set(False)
        self._lower_var.set(False)
        self._title_var.set(False)
        self._nodig_var.set(False)
        self._schedule_preview()


# ---------------------------------------------------------------------------
# Themed button
# ---------------------------------------------------------------------------

class TBtn(tk.Button):
    def __init__(self, parent, bg=BTN, fg=TEXT, padx=12, pady=6, font=F_MAIN, **kw):
        super().__init__(parent, bg=bg, fg=fg, relief="flat",
                         activebackground=BTN_HOV, activeforeground=TEXT,
                         padx=padx, pady=pady, cursor="hand2", font=font, **kw)
        _bg = bg
        self.bind("<Enter>", lambda _: self.config(bg=BTN_HOV))
        self.bind("<Leave>", lambda _: self.config(bg=_bg))

# ---------------------------------------------------------------------------
# Marker detail dialog
# ---------------------------------------------------------------------------

def center_on_parent(dialog: tk.Toplevel, parent: tk.Misc):
    """Center a Toplevel dialog over its parent window."""
    dialog.update_idletasks()
    pw   = parent.winfo_rootx()
    py   = parent.winfo_rooty()
    pw_w = parent.winfo_width()
    pw_h = parent.winfo_height()
    # Use req dimensions — winfo_width returns 1 before the window is mapped
    dw = dialog.winfo_reqwidth()
    dh = dialog.winfo_reqheight()
    x = pw + (pw_w - dw) // 2
    y = py + (pw_h - dh) // 2
    dialog.geometry(f"+{max(0, x)}+{max(0, y)}")


class MarkerDialog(tk.Toplevel):
    """Add / Edit marker dialog.

    For Add mode pass get_tc_fn (a zero-arg callable that returns the current
    playhead timecode string) to enable the Refresh Position button and the
    target radio buttons (Timeline Ruler / Clip / Pick Track).
    For Edit mode leave get_tc_fn=None; target row is hidden.
    """

    def __init__(self, parent, title: str, fps: float, marker_type: str = "Timeline",
                 frame=0, color="Blue", name="", note="", duration=1,
                 get_tc_fn=None):
        super().__init__(parent)
        self.withdraw()
        self.transient(parent)
        self.title(title)
        self.resizable(False, False)
        self.configure(bg=BG)
        # No grab_set() — lets user interact with Resolve while dialog is open.
        self.result = None
        self._fps = fps
        self._get_tc_fn = get_tc_fn
        self._is_add = get_tc_fn is not None

        DLG  = "#424242"
        DFLD = "#323232"
        self.configure(bg=DLG)
        pad = {"padx": 16, "pady": 6}

        row = 0

        # ── Target selector (Add mode only) ──────────────────────────────
        if self._is_add:
            self._target_var = tk.StringVar(value="timeline")
            tgt_frame = tk.Frame(self, bg=DLG)
            tgt_frame.grid(row=row, column=0, columnspan=2, sticky="ew",
                           padx=16, pady=(14, 2))
            tk.Label(tgt_frame, text="Add to:", fg=DIM, bg=DLG,
                     font=F_SMALL).pack(side="left", padx=(0, 10))
            for val, lbl in [("timeline",  "Timeline Ruler"),
                             ("clip_auto", "Clip (auto)"),
                             ("clip_pick", "Pick Track")]:
                tk.Radiobutton(tgt_frame, text=lbl, variable=self._target_var,
                               value=val, fg=TEXT, bg=DLG, activeforeground=TEXT,
                               activebackground=DLG, selectcolor=DFLD,
                               font=F_SMALL).pack(side="left", padx=6)
            row += 1

        # ── Type badge (Edit mode only) ───────────────────────────────────
        if not self._is_add:
            badge_color = ACCENT if marker_type == "Timeline" else PURPLE
            tk.Label(self, text=f"  {marker_type} Marker  ", fg=BG, bg=badge_color,
                     font=F_BOLD).grid(row=row, column=0, columnspan=2, sticky="w",
                                       padx=16, pady=(8, 4))
            row += 1

        # ── Field labels ──────────────────────────────────────────────────
        for lbl in ["Timecode  (HH:MM:SS:FF)", "Color", "Name", "Note",
                    "Duration (frames)"]:
            tk.Label(self, text=lbl, fg=TEXT, bg=DLG,
                     font=F_SMALL).grid(row=row, column=0, sticky="nw", **pad)
            row += 1
        tc_row, color_row, name_row, note_row, dur_row = range(row - 5, row)

        # ── Timecode + Refresh Position ───────────────────────────────────
        tc_cell = tk.Frame(self, bg=DLG)
        tc_cell.grid(row=tc_row, column=1, sticky="ew", **pad)
        self._tc_var    = tk.StringVar(value=frames_to_tc(frame, fps))
        self._frame_var = tk.IntVar(value=frame)
        tc_e = tk.Entry(tc_cell, textvariable=self._tc_var, width=18,
                        bg=DFLD, fg=TEXT, insertbackground=TEXT,
                        relief="flat", font=F_MONO)
        tc_e.pack(side="left")
        self._tc_var.trace_add("write", self._tc_changed)

        if self._is_add:
            TBtn(tc_cell, text="↺ Refresh Position",
                 command=self._refresh_position,
                 bg=BTN, fg=DIM, padx=6, pady=2).pack(side="left", padx=(8, 0))

        if marker_type == "Clip":
            tc_e.config(state="disabled", disabledforeground=DIM)

        # ── Color ─────────────────────────────────────────────────────────
        self._color_var = tk.StringVar(value=color)
        ttk.Combobox(self, textvariable=self._color_var, values=MARKER_COLORS,
                     state="readonly", width=16).grid(row=color_row, column=1,
                                                      sticky="ew", **pad)

        # ── Name ──────────────────────────────────────────────────────────
        self._name_var = tk.StringVar(value=name)
        tk.Entry(self, textvariable=self._name_var, width=36,
                 bg=DFLD, fg=TEXT, insertbackground=TEXT,
                 relief="flat", font=F_MAIN).grid(row=name_row, column=1,
                                                   sticky="ew", **pad)

        # ── Note ──────────────────────────────────────────────────────────
        self._note_text = tk.Text(self, width=36, height=4,
                                  bg=DFLD, fg=TEXT, insertbackground=TEXT,
                                  relief="flat", font=F_MAIN, wrap="word")
        self._note_text.insert("1.0", note)
        self._note_text.grid(row=note_row, column=1, sticky="ew", **pad)

        # ── Duration ──────────────────────────────────────────────────────
        self._dur_var = tk.IntVar(value=duration)
        tk.Spinbox(self, from_=1, to=999999, textvariable=self._dur_var, width=10,
                   bg=DFLD, fg=TEXT, insertbackground=TEXT,
                   buttonbackground=BTN, relief="flat",
                   font=F_MAIN).grid(row=dur_row, column=1, sticky="w", **pad)

        # ── Buttons ───────────────────────────────────────────────────────
        bf = tk.Frame(self, bg=DLG)
        bf.grid(row=dur_row + 1, column=0, columnspan=2, pady=12)
        TBtn(bf, text="Cancel", command=self.destroy, bg=ACCENT, fg=BG).pack(side="left", padx=8)
        TBtn(bf, text="Save",   command=self._save,   bg=ACCENT, fg=BG).pack(side="left", padx=8)

        self.columnconfigure(1, weight=1)
        self.bind("<Return>",   lambda _: self._save())
        self.bind("<KP_Enter>", lambda _: self._save())

        center_on_parent(self, parent)
        self.deiconify()
        self.lift()
        # Always stay on top — user needs this dialog visible while clicking
        # in Resolve to position the playhead or refresh position.
        self.attributes("-topmost", True)

    def _refresh_position(self):
        """Update timecode/frame from current Resolve playhead position."""
        if not self._get_tc_fn:
            return
        try:
            tc_str = self._get_tc_fn()
            if tc_str:
                self._tc_var.set(tc_str)
        except Exception:
            pass

    def _tc_changed(self, *_):
        tc = self._tc_var.get().strip()
        if len(tc) < 8:
            return
        f = tc_to_frames(tc, self._fps)
        if f > 0:
            self._frame_var.set(f)

    def _save(self):
        try:
            dur = max(1, int(self._dur_var.get()))
        except (tk.TclError, ValueError):
            dur = 1
        self.result = {
            "frame":    self._frame_var.get(),
            "color":    self._color_var.get(),
            "name":     self._name_var.get().strip(),
            "note":     self._note_text.get("1.0", "end-1c").strip(),
            "duration": dur,
            "target":   self._target_var.get() if self._is_add else "timeline",
        }
        self.destroy()

# ---------------------------------------------------------------------------
# Bulk colour-change dialog
# ---------------------------------------------------------------------------

class ColorPickDialog(tk.Toplevel):
    def __init__(self, parent, count: int):
        super().__init__(parent)
        self.withdraw()
        self.transient(parent)
        self.title("Change Color")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.result = None

        tk.Label(self, text=f"New color for {count} marker{'s' if count != 1 else ''}:",
                 fg=TEXT, bg=BG, font=F_MAIN).pack(padx=20, pady=(16, 8))
        self._color_var = tk.StringVar(value="Blue")
        ttk.Combobox(self, textvariable=self._color_var, values=MARKER_COLORS,
                     state="readonly", width=18).pack(padx=20, pady=4)
        bf = tk.Frame(self, bg=BG)
        bf.pack(pady=12)
        TBtn(bf, text="Apply",  command=self._apply, bg=ACCENT, fg=BG).pack(side="left", padx=8)
        TBtn(bf, text="Cancel", command=self.destroy, bg=ACCENT, fg=BG).pack(side="left", padx=8)
        center_on_parent(self, parent)
        self.deiconify()
        self.lift()
        self.attributes("-topmost", True)

    def _apply(self):
        self.result = self._color_var.get()
        self.destroy()

# ---------------------------------------------------------------------------
# Track picker dialog  (used by demote: ruler → clip)
# ---------------------------------------------------------------------------

class TrackPickDialog(tk.Toplevel):
    """Track picker with Video/Audio grouping, scrollable list, clip-name
    toggle, and an optional frame offset.

    tracks : list of (track_type, track_index, clip_count, clip_names_list)
    result : (track_type, track_index, offset_frames) or None
    """

    def __init__(self, parent, tracks: list):
        super().__init__(parent)
        self.withdraw()
        self.transient(parent)
        self.title("Choose Target Track")
        self.resizable(False, True)
        self.configure(bg=BG)
        self.result = None

        tk.Label(self, text="Apply marker(s) to which track?",
                 fg=TEXT, bg=BG, font=F_BOLD).pack(padx=20, pady=(16, 6))
        tk.Label(self, text="Only tracks with clips at the selected frame(s) are shown.",
                 fg=DIM, bg=BG, font=F_SMALL).pack(padx=20, pady=(0, 6))

        # ── Show names toggle ─────────────────────────────────────────────
        self._show_names = tk.BooleanVar(value=False)
        tk.Checkbutton(self, text="Show clip names", variable=self._show_names,
                       fg=DIM, bg=BG, activeforeground=TEXT, activebackground=BG,
                       selectcolor=ENTRY_BG, font=F_SMALL,
                       command=self._refresh_labels).pack(anchor="w", padx=20, pady=(0, 4))

        # ── Scrollable track list ─────────────────────────────────────────
        list_outer = tk.Frame(self, bg=BG, bd=0)
        list_outer.pack(fill="both", expand=True, padx=20)

        canvas = tk.Canvas(list_outer, bg=BG, highlightthickness=0, bd=0)
        vsb    = ttk.Scrollbar(list_outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self._inner = tk.Frame(canvas, bg=BG)
        win_id = canvas.create_window((0, 0), window=self._inner, anchor="nw")

        def _on_inner_resize(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(win_id, width=canvas.winfo_width())
        self._inner.bind("<Configure>", _on_inner_resize)
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win_id, width=e.width))

        # ── Build radio buttons grouped by type ───────────────────────────
        self._var       = tk.StringVar()
        self._rb_data   = []   # (widget, ttype, tidx, clip_count, clip_names)
        first_val       = None

        for section, label in (("video", "VIDEO"), ("audio", "AUDIO")):
            section_tracks = [(tt, ti, cnt, names)
                              for (tt, ti, cnt, names) in tracks
                              if tt == section]
            if not section_tracks:
                continue
            tk.Label(self._inner, text=label, fg=ACCENT, bg=BG,
                     font=("Avenir Next", 9, "bold")).pack(
                         anchor="w", padx=4, pady=(8, 2))
            for (ttype, tidx, clip_count, clip_names) in section_tracks:
                prefix = "V" if ttype == "video" else "A"
                val    = f"{ttype}:{tidx}"
                if first_val is None:
                    first_val = val
                rb = tk.Radiobutton(self._inner, variable=self._var, value=val,
                                    fg=TEXT, bg=BG, activeforeground=TEXT,
                                    activebackground=BG, selectcolor=ENTRY_BG,
                                    font=F_MAIN, anchor="w", justify="left",
                                    wraplength=340)
                rb.pack(fill="x", padx=4, pady=1)
                self._rb_data.append((rb, prefix, tidx, clip_count, clip_names))

        if first_val:
            self._var.set(first_val)
        self._refresh_labels()

        # Cap scrollable area height at 300px
        self._inner.update_idletasks()
        canvas.configure(height=min(300, self._inner.winfo_reqheight()))

        # ── Options grid (offset + color) ─────────────────────────────────
        opt = tk.Frame(self, bg=BG)
        opt.pack(fill="x", padx=20, pady=(10, 4))

        tk.Label(opt, text="Offset (frames):", fg=TEXT, bg=BG,
                 font=F_MAIN).grid(row=0, column=0, sticky="w")
        self._offset_var = tk.IntVar(value=0)
        self._offset_sb  = tk.Spinbox(opt, from_=-9999, to=9999,
                                      textvariable=self._offset_var,
                                      width=7, bg=ENTRY_BG, fg=TEXT,
                                      insertbackground=TEXT,
                                      buttonbackground=BTN, relief="flat",
                                      font=F_MAIN)
        self._offset_sb.grid(row=0, column=1, sticky="w", padx=(8, 0))
        tk.Label(opt, text="+ = forward into clip", fg=DIM, bg=BG,
                 font=F_SMALL).grid(row=0, column=2, sticky="w", padx=(8, 0))

        tk.Label(opt, text="Color:", fg=TEXT, bg=BG,
                 font=F_MAIN).grid(row=1, column=0, sticky="w", pady=(6, 0))
        self._color_var = tk.StringVar(value="Original")
        ttk.Combobox(opt, textvariable=self._color_var,
                     values=["Original"] + MARKER_COLORS,
                     state="readonly", width=14,
                     font=F_MAIN).grid(row=1, column=1, sticky="w",
                                        padx=(8, 0), pady=(6, 0))
        tk.Label(opt, text="keep original color or pick new",
                 fg=DIM, bg=BG, font=F_SMALL).grid(row=1, column=2, sticky="w",
                                                    padx=(8, 0), pady=(6, 0))

        # ── Buttons ───────────────────────────────────────────────────────
        bf = tk.Frame(self, bg=BG)
        bf.pack(pady=(8, 16))
        TBtn(bf, text="OK",     command=self._ok,     bg=ACCENT, fg=BG).pack(side="left", padx=8)
        TBtn(bf, text="Cancel", command=self.destroy, bg=ACCENT, fg=BG).pack(side="left", padx=8)

        self.bind("<Return>",   lambda _: self._ok())
        self.bind("<KP_Enter>", lambda _: self._ok())
        self.bind("<Tab>",      lambda _: (self._offset_sb.focus_set(), "break"))
        center_on_parent(self, parent)
        self.deiconify()
        self.lift()
        self.attributes("-topmost", True)

    def _refresh_labels(self):
        show = self._show_names.get()
        for (rb, prefix, tidx, clip_count, clip_names) in self._rb_data:
            noun = "clip" if clip_count == 1 else "clips"
            text = f"{prefix}{tidx}  —  {clip_count} {noun}"
            if show and clip_names:
                names_str = ", ".join(clip_names[:10])
                if len(clip_names) > 10:
                    names_str += f" +{len(clip_names)-10} more"
                text += f":  {names_str}"
            rb.config(text=text)

    def _ok(self):
        val = self._var.get()
        if val:
            ttype, tidx = val.split(":")
            try:
                offset = int(self._offset_var.get())
            except (ValueError, tk.TclError):
                offset = 0
            color = self._color_var.get()
            self.result = (ttype, int(tidx), offset, color)
        self.destroy()


# ---------------------------------------------------------------------------
# Promote (clip → timeline) options dialog — offset + color, no track picker
# ---------------------------------------------------------------------------

class PromoteOptionsDialog(tk.Toplevel):
    """Lightweight dialog for Copy/Move → Timeline: frame offset + color.

    result : (offset_frames, color_str) or None on cancel.
    """

    def __init__(self, parent, action_label="Copy to Timeline"):
        super().__init__(parent)
        self.withdraw()
        self.transient(parent)
        self.title(action_label)
        self.resizable(False, False)
        self.configure(bg=BG)
        self.result = None

        tk.Label(self, text=action_label,
                 fg=TEXT, bg=BG, font=F_BOLD).pack(padx=24, pady=(16, 4))
        tk.Label(self, text="Place selected clip marker(s) onto the timeline.",
                 fg=DIM, bg=BG, font=F_SMALL).pack(padx=24, pady=(0, 12))

        opts = tk.Frame(self, bg=BG)
        opts.pack(padx=24, pady=(0, 8))

        tk.Label(opts, text="Frame offset:", fg=DIM, bg=BG,
                 font=F_SMALL).grid(row=0, column=0, sticky="w", pady=4)
        self._offset_var = tk.IntVar(value=0)
        tk.Spinbox(opts, from_=-9999, to=9999, textvariable=self._offset_var,
                   width=7, bg=ENTRY_BG, fg=TEXT, insertbackground=TEXT,
                   buttonbackground=BTN, relief="flat",
                   font=F_MAIN).grid(row=0, column=1, padx=(8, 0), pady=4, sticky="w")

        tk.Label(opts, text="Color:", fg=DIM, bg=BG,
                 font=F_SMALL).grid(row=1, column=0, sticky="w", pady=4)
        self._color_var = tk.StringVar(value="Original")
        ttk.Combobox(opts, textvariable=self._color_var,
                     values=["Original"] + MARKER_COLORS,
                     state="readonly", width=14).grid(row=1, column=1, padx=(8, 0),
                                                      pady=4, sticky="w")

        bf = tk.Frame(self, bg=BG)
        bf.pack(pady=(4, 16))
        TBtn(bf, text="OK",     command=self._ok,     bg=ACCENT, fg=BG).pack(side="left", padx=8)
        TBtn(bf, text="Cancel", command=self.destroy, bg=ACCENT, fg=BG).pack(side="left", padx=8)

        self.bind("<Return>",   lambda _: self._ok())
        self.bind("<KP_Enter>", lambda _: self._ok())
        center_on_parent(self, parent)
        self.deiconify()
        self.lift()
        self.attributes("-topmost", True)

    def _ok(self):
        try:
            offset = int(self._offset_var.get())
        except (ValueError, tk.TclError):
            offset = 0
        self.result = (offset, self._color_var.get())
        self.destroy()


# ---------------------------------------------------------------------------
# Batch frame-export progress dialog
# ---------------------------------------------------------------------------

class BatchExportDialog(tk.Toplevel):
    """Non-blocking progress window shown during batch frame export."""

    def __init__(self, parent, total: int):
        super().__init__(parent)
        self.withdraw()
        self.transient(parent)
        self.title("Batch Export Frames")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.grab_set()
        self.cancelled = False

        self._phase_var = tk.StringVar(value="Grabbing frames…")
        self._phase_lbl = tk.Label(self, textvariable=self._phase_var,
                                   fg=ACCENT, bg=BG, font=F_BOLD)
        self._phase_lbl.pack(padx=24, pady=(16, 6))

        self._msg_var = tk.StringVar(value="Starting…")
        tk.Label(self, textvariable=self._msg_var, fg=TEXT, bg=BG,
                 font=F_SMALL, width=52, anchor="w").pack(padx=24)

        self._bar = ttk.Progressbar(self, orient="horizontal",
                                    length=360, mode="determinate",
                                    maximum=total)
        self._bar.pack(padx=24, pady=10)

        self._count_var = tk.StringVar(value=f"0 / {total}")
        tk.Label(self, textvariable=self._count_var, fg=DIM, bg=BG,
                 font=F_SMALL).pack()

        TBtn(self, text="Cancel", command=self._cancel,
             bg=RED, fg=BG).pack(pady=12)

        self._total = total
        center_on_parent(self, parent)
        self.deiconify()
        self.lift()
        self.attributes("-topmost", True)

    def set_phase(self, phase: str):
        """Switch header label between 'Grabbing frames…' and 'Exporting frames…'."""
        self._phase_var.set(phase)
        self.update()

    def update_progress(self, n: int, msg: str):
        self._bar["value"] = n
        self._count_var.set(f"{n} / {self._total}")
        self._msg_var.set(msg[:60])
        self.update()  # full repaint, not just idle tasks

    def _cancel(self):
        self.cancelled = True


# ---------------------------------------------------------------------------
# Rename dialog  (right-click on Name column)
# ---------------------------------------------------------------------------

class RenameDialog(tk.Toplevel):
    def __init__(self, parent, current_name: str):
        super().__init__(parent)
        self.withdraw()
        self.transient(parent)
        self.title("Rename Marker")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.result = None

        tk.Label(self, text="New name:", fg=TEXT, bg=BG,
                 font=F_MAIN).pack(padx=20, pady=(16, 6))
        self._var = tk.StringVar(value=current_name)
        entry = tk.Entry(self, textvariable=self._var, width=36,
                         bg=ENTRY_BG, fg=TEXT, insertbackground=TEXT,
                         relief="flat", font=F_MAIN)
        entry.pack(padx=20, pady=4)
        entry.select_range(0, "end")
        entry.focus_set()
        entry.bind("<Return>", lambda _: self._save())
        entry.bind("<Escape>", lambda _: self.destroy())

        bf = tk.Frame(self, bg=BG)
        bf.pack(pady=12)
        TBtn(bf, text="Rename", command=self._save, bg=ACCENT, fg=BG).pack(side="left", padx=8)
        TBtn(bf, text="Cancel", command=self.destroy, bg=ACCENT, fg=BG).pack(side="left", padx=8)
        center_on_parent(self, parent)
        self.deiconify()
        self.lift()
        self.attributes("-topmost", True)

    def _save(self):
        self.result = self._var.get().strip()
        self.destroy()


# ---------------------------------------------------------------------------
# Export options dialog
# ---------------------------------------------------------------------------

class ExportOptionsDialog(tk.Toplevel):
    def __init__(self, parent, visible_count: int, selected_count: int):
        super().__init__(parent)
        self.withdraw()
        self.transient(parent)
        self.title("Export Options")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.result = None

        tk.Label(self, text="Export Markers to CSV", fg=ACCENT, bg=BG,
                 font=F_BOLD).pack(fill="x", pady=(18, 4))

        # ── Scope ──────────────────────────────────────────────────────
        scope_frame = tk.LabelFrame(self, text=" Scope ", fg=DIM, bg=BG,
                                    font=F_SMALL, relief="flat",
                                    highlightbackground=BTN_HOV, highlightthickness=1)
        scope_frame.pack(fill="x", padx=20, pady=(10, 6))

        self._scope_var = tk.StringVar(value="selected" if selected_count > 0 else "visible")

        tk.Radiobutton(scope_frame,
                       text=f"All visible markers  ({visible_count})",
                       variable=self._scope_var, value="visible",
                       fg=TEXT, bg=BG, activeforeground=TEXT,
                       activebackground=BG, selectcolor=ENTRY_BG,
                       font=F_MAIN).pack(anchor="w", padx=12, pady=(8, 2))

        tk.Radiobutton(scope_frame,
                       text=f"Selected markers only  ({selected_count})",
                       variable=self._scope_var, value="selected",
                       fg=TEXT if selected_count > 0 else DIM,
                       bg=BG, activeforeground=TEXT,
                       activebackground=BG, selectcolor=ENTRY_BG,
                       font=F_MAIN,
                       state="normal" if selected_count > 0 else "disabled"
                       ).pack(anchor="w", padx=12, pady=(2, 8))

        # ── Thumbnails ─────────────────────────────────────────────────
        thumb_frame = tk.LabelFrame(self, text=" Thumbnails ", fg=DIM, bg=BG,
                                    font=F_SMALL, relief="flat",
                                    highlightbackground=BTN_HOV, highlightthickness=1)
        thumb_frame.pack(fill="x", padx=20, pady=(6, 6))

        self._thumb_var = tk.BooleanVar(value=False)
        tk.Checkbutton(thumb_frame,
                       text="Include still frames\n(saved to 'thumbnails' subfolder next to CSV)",
                       variable=self._thumb_var,
                       command=self._on_thumb_toggle,
                       fg=TEXT, bg=BG, activeforeground=TEXT,
                       activebackground=BG, selectcolor=ENTRY_BG,
                       font=F_MAIN, justify="left", anchor="w").pack(anchor="w", padx=12, pady=(8, 4))

        # Thumbnail size
        size_row = tk.Frame(thumb_frame, bg=BG)
        size_row.pack(anchor="w", padx=28, pady=(0, 4))
        tk.Label(size_row, text="Size:", fg=DIM, bg=BG, font=F_SMALL).pack(side="left")
        self._size_var = tk.StringVar(value=THUMB_SIZES[0][0])
        self._size_menu = ttk.Combobox(size_row, textvariable=self._size_var,
                                       values=[lbl for lbl, _ in THUMB_SIZES],
                                       state="disabled", width=14)
        self._size_menu.pack(side="left", padx=(6, 0))

        # Thumbnail format
        fmt_row = tk.Frame(thumb_frame, bg=BG)
        fmt_row.pack(anchor="w", padx=28, pady=(0, 4))
        tk.Label(fmt_row, text="Format:", fg=DIM, bg=BG, font=F_SMALL).pack(side="left")
        self._thumb_fmt_var = tk.StringVar(value=EXPORT_FORMATS[0][0])
        self._thumb_fmt_menu = ttk.Combobox(fmt_row, textvariable=self._thumb_fmt_var,
                                            values=[lbl for lbl, _ in EXPORT_FORMATS],
                                            state="disabled", width=8)
        self._thumb_fmt_menu.pack(side="left", padx=(6, 0))

        # JPEG quality (always visible, enabled only when thumbnails on + JPEG selected)
        q_row = tk.Frame(thumb_frame, bg=BG)
        q_row.pack(anchor="w", padx=28, pady=(0, 8))
        tk.Label(q_row, text="Quality:", fg=DIM, bg=BG, font=F_SMALL).pack(side="left")
        self._thumb_q_var = tk.IntVar(value=85)
        self._thumb_q_scale = tk.Scale(q_row, from_=0, to=100, orient="horizontal",
                                       variable=self._thumb_q_var,
                                       bg=BG, fg=DIM, troughcolor=ENTRY_BG,
                                       highlightthickness=0, length=100, state="disabled")
        self._thumb_q_scale.pack(side="left", padx=(6, 0))
        tk.Label(q_row, text="(JPEG only)", fg=DIM, bg=BG, font=F_SMALL).pack(side="left", padx=(6, 0))
        self._thumb_fmt_var.trace_add("write", self._on_thumb_fmt_change)

        self._keep_drx_var = tk.BooleanVar(value=False)
        self._keep_drx_cb = tk.Checkbutton(thumb_frame,
                       text="Keep .DRX sidecar files",
                       variable=self._keep_drx_var,
                       fg=DIM, bg=BG, activeforeground=TEXT,
                       activebackground=BG, selectcolor=ENTRY_BG,
                       font=F_MAIN, justify="left", anchor="w",
                       state="disabled")
        self._keep_drx_cb.pack(anchor="w", padx=12, pady=(0, 8))

        # ── HTML Report Columns ────────────────────────────────────────
        col_frame = tk.LabelFrame(self, text=" HTML Report Columns ", fg=DIM, bg=BG,
                                  font=F_SMALL, relief="flat",
                                  highlightbackground=BTN_HOV, highlightthickness=1)
        col_frame.pack(fill="x", padx=20, pady=(6, 10))

        self._col_vars   = {}
        self._col_checks = []
        grid = tk.Frame(col_frame, bg=BG)
        grid.pack(padx=12, pady=8)
        for i, (key, label) in enumerate(HTML_COLUMNS):
            var = tk.BooleanVar(value=True)
            self._col_vars[key] = var
            cb = tk.Checkbutton(grid, text=label, variable=var,
                                fg=DIM, bg=BG, activeforeground=TEXT,
                                activebackground=BG, selectcolor=ENTRY_BG,
                                font=F_SMALL, state="disabled")
            cb.grid(row=i // 4, column=i % 4, sticky="w", padx=(0, 14), pady=1)
            self._col_checks.append(cb)

        # Custom label for the Name column
        name_row = tk.Frame(col_frame, bg=BG)
        name_row.pack(anchor="w", padx=12, pady=(4, 2))
        tk.Label(name_row, text="Label for 'Name' column:", fg=DIM, bg=BG,
                 font=F_SMALL).pack(side="left")
        self._name_label_var = tk.StringVar(value="Name")
        self._name_label_entry = tk.Entry(name_row, textvariable=self._name_label_var,
                                          width=14, bg=ENTRY_BG, fg=TEXT,
                                          insertbackground=TEXT, relief="flat",
                                          font=F_SMALL, state="disabled")
        self._name_label_entry.pack(side="left", padx=(6, 0))
        self._col_checks.append(self._name_label_entry)

        tk.Label(col_frame, text="(only applies when thumbnails are included)",
                 fg=DIM, bg=BG, font=F_SMALL).pack(pady=(2, 6))

        # ── Buttons ────────────────────────────────────────────────────
        bf = tk.Frame(self, bg=BG)
        bf.pack(pady=(4, 16))
        TBtn(bf, text="Cancel", command=self.destroy, bg=ACCENT, fg=BG).pack(side="left", padx=8)
        TBtn(bf, text="Export", command=self._export, bg=ACCENT, fg=BG).pack(side="left", padx=8)
        center_on_parent(self, parent)
        self.deiconify()
        self.lift()
        self.attributes("-topmost", True)

    def _on_thumb_toggle(self):
        enabled  = self._thumb_var.get()
        state    = "readonly" if enabled else "disabled"
        cb_state = "normal"   if enabled else "disabled"
        self._size_menu.config(state=state)
        self._thumb_fmt_menu.config(state=state)
        self._keep_drx_cb.config(state=cb_state, fg=TEXT if enabled else DIM)
        self._name_label_entry.config(state=cb_state)
        for cb in self._col_checks:
            try:
                cb.config(state=cb_state, fg=TEXT if enabled else DIM)
            except tk.TclError:
                cb.config(state=cb_state)  # Entry widgets don't have fg in disabled config
        self._on_thumb_fmt_change()

    def _on_thumb_fmt_change(self, *_):
        is_jpeg = self._thumb_fmt_var.get() == "JPEG"
        enabled = self._thumb_var.get()
        active  = is_jpeg and enabled
        self._thumb_q_scale.config(state="normal" if active else "disabled",
                                   fg=TEXT if active else DIM)

    def _export(self):
        size_label   = self._size_var.get()
        thumb_max_px = next((px for lbl, px in THUMB_SIZES if lbl == size_label), None)
        fmt_label    = self._thumb_fmt_var.get()
        thumb_fmt    = next((f for lbl, f in EXPORT_FORMATS if lbl == fmt_label), "png")
        jpeg_quality = self._thumb_q_var.get() if thumb_fmt == "jpg" else None
        self.result = {
            "scope":          self._scope_var.get(),
            "include_frames": self._thumb_var.get(),
            "keep_drx":       self._keep_drx_var.get(),
            "thumb_max_px":   thumb_max_px,
            "thumb_fmt":      thumb_fmt,
            "jpeg_quality":   jpeg_quality,
            "html_columns":   {k for k, v in self._col_vars.items() if v.get()},
            "name_label":     self._name_label_var.get().strip() or "Name",
        }
        self.destroy()


# ---------------------------------------------------------------------------
# Batch frame export options dialog
# ---------------------------------------------------------------------------

class BatchExportOptionsDialog(tk.Toplevel):
    def __init__(self, parent, visible_count: int, selected_count: int, default_name_only: bool = False):
        super().__init__(parent)
        self.withdraw()
        self.transient(parent)
        self.title("Batch Export Options")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.result = None   # {"scope": "visible"|"selected", "name_only": bool}

        tk.Label(self, text="Batch Export Frames", fg=ACCENT, bg=BG,
                 font=F_BOLD).pack(fill="x", pady=(18, 4))

        # ── Scope ──────────────────────────────────────────────────────────
        scope_frame = tk.LabelFrame(self, text=" Scope ", fg=DIM, bg=BG,
                                    font=F_SMALL, relief="flat",
                                    highlightbackground=BTN_HOV, highlightthickness=1)
        scope_frame.pack(fill="x", padx=20, pady=(10, 6))

        self._scope_var = tk.StringVar(value="selected" if selected_count > 0 else "visible")
        tk.Radiobutton(scope_frame,
                       text=f"All visible markers  ({visible_count})",
                       variable=self._scope_var, value="visible",
                       fg=TEXT, bg=BG, activeforeground=TEXT,
                       activebackground=BG, selectcolor=ENTRY_BG,
                       font=F_MAIN).pack(anchor="w", padx=12, pady=(8, 2))
        tk.Radiobutton(scope_frame,
                       text=f"Selected markers only  ({selected_count})",
                       variable=self._scope_var, value="selected",
                       fg=TEXT if selected_count > 0 else DIM,
                       bg=BG, activeforeground=TEXT,
                       activebackground=BG, selectcolor=ENTRY_BG,
                       font=F_MAIN,
                       state="normal" if selected_count > 0 else "disabled"
                       ).pack(anchor="w", padx=12, pady=(2, 8))

        # ── Format ─────────────────────────────────────────────────────────
        fmt_frame = tk.LabelFrame(self, text=" Format ", fg=DIM, bg=BG,
                                  font=F_SMALL, relief="flat",
                                  highlightbackground=BTN_HOV, highlightthickness=1)
        fmt_frame.pack(fill="x", padx=20, pady=(6, 6))

        fmt_row = tk.Frame(fmt_frame, bg=BG)
        fmt_row.pack(anchor="w", padx=12, pady=(8, 4))
        self._fmt_var = tk.StringVar(value=EXPORT_FORMATS[0][0])
        for label, _ in EXPORT_FORMATS:
            tk.Radiobutton(fmt_row, text=label, variable=self._fmt_var, value=label,
                           fg=TEXT, bg=BG, activeforeground=TEXT, activebackground=BG,
                           selectcolor=ENTRY_BG, font=F_MAIN).pack(side="left", padx=(0, 12))

        # JPEG quality
        q_row = tk.Frame(fmt_frame, bg=BG)
        q_row.pack(anchor="w", padx=12, pady=(0, 8))
        tk.Label(q_row, text="Quality:", fg=DIM, bg=BG, font=F_SMALL).pack(side="left")
        self._jpeg_q_var = tk.IntVar(value=85)
        self._jpeg_q_scale = tk.Scale(q_row, from_=0, to=100, orient="horizontal",
                                      variable=self._jpeg_q_var,
                                      bg=BG, fg=DIM, troughcolor=ENTRY_BG,
                                      highlightthickness=0, length=100, state="disabled")
        self._jpeg_q_scale.pack(side="left", padx=(6, 0))
        tk.Label(q_row, text="(JPEG only)", fg=DIM, bg=BG, font=F_SMALL).pack(side="left", padx=(6, 0))
        self._fmt_var.trace_add("write", self._on_fmt_change)

        # ── Filename ───────────────────────────────────────────────────────
        fname_frame = tk.LabelFrame(self, text=" Filename ", fg=DIM, bg=BG,
                                    font=F_SMALL, relief="flat",
                                    highlightbackground=BTN_HOV, highlightthickness=1)
        fname_frame.pack(fill="x", padx=20, pady=(6, 6))

        self._name_only_var = tk.BooleanVar(value=default_name_only)
        tk.Checkbutton(fname_frame,
                       text="Marker name only  (e.g. My Marker.png)",
                       variable=self._name_only_var,
                       fg=TEXT, bg=BG, activeforeground=TEXT,
                       activebackground=BG, selectcolor=ENTRY_BG,
                       font=F_MAIN).pack(anchor="w", padx=12, pady=(8, 2))
        tk.Label(fname_frame,
                 text="Default: 0001_TL_00-00-10-00_My Marker.png",
                 fg=DIM, bg=BG, font=F_SMALL).pack(anchor="w", padx=12, pady=(0, 8))

        # ── DRX sidecar ────────────────────────────────────────────────────
        drx_frame = tk.LabelFrame(self, text=" Sidecar Files ", fg=DIM, bg=BG,
                                   font=F_SMALL, relief="flat",
                                   highlightbackground=BTN_HOV, highlightthickness=1)
        drx_frame.pack(fill="x", padx=20, pady=(6, 10))

        self._keep_drx_var = tk.BooleanVar(value=False)
        tk.Checkbutton(drx_frame,
                       text="Keep .DRX sidecar files",
                       variable=self._keep_drx_var,
                       fg=TEXT, bg=BG, activeforeground=TEXT,
                       activebackground=BG, selectcolor=ENTRY_BG,
                       font=F_MAIN, justify="left", anchor="w").pack(anchor="w", padx=12, pady=8)

        # ── Buttons ────────────────────────────────────────────────────────
        bf = tk.Frame(self, bg=BG)
        bf.pack(pady=(4, 16))
        TBtn(bf, text="Cancel", command=self.destroy, bg=ACCENT, fg=BG).pack(side="left", padx=8)
        TBtn(bf, text="Export", command=self._export, bg=ACCENT, fg=BG).pack(side="left", padx=8)
        center_on_parent(self, parent)
        self.deiconify()
        self.lift()
        self.attributes("-topmost", True)

    def _on_fmt_change(self, *_):
        is_jpeg = self._fmt_var.get() == "JPEG"
        self._jpeg_q_scale.config(state="normal" if is_jpeg else "disabled",
                                  fg=TEXT if is_jpeg else DIM)

    def _export(self):
        fmt_label    = self._fmt_var.get()
        fmt          = next((f for lbl, f in EXPORT_FORMATS if lbl == fmt_label), "png")
        jpeg_quality = self._jpeg_q_var.get() if fmt == "jpg" else None
        self.result = {
            "scope":        self._scope_var.get(),
            "name_only":    self._name_only_var.get(),
            "keep_drx":     self._keep_drx_var.get(),
            "fmt":          fmt,
            "jpeg_quality": jpeg_quality,
        }
        self.destroy()


# ---------------------------------------------------------------------------
# Export Frame options dialog  (pre-dialog before the OS save sheet)
# ---------------------------------------------------------------------------

class ExportFrameOptionsDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()
        self.transient(parent)
        self.title("Export Frame")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.result = None   # {"fmt": "png"|"tif"|"jpg", "jpeg_quality": int|None}

        tk.Label(self, text="Export Frame", fg=ACCENT, bg=BG,
                 font=F_BOLD).pack(fill="x", pady=(18, 4))

        # ── Format ─────────────────────────────────────────────────────────
        fmt_frame = tk.LabelFrame(self, text=" Format ", fg=DIM, bg=BG,
                                  font=F_SMALL, relief="flat",
                                  highlightbackground=BTN_HOV, highlightthickness=1)
        fmt_frame.pack(fill="x", padx=20, pady=(10, 6))

        fmt_row = tk.Frame(fmt_frame, bg=BG)
        fmt_row.pack(anchor="w", padx=12, pady=(10, 6))
        self._fmt_var = tk.StringVar(value=EXPORT_FORMATS[0][0])
        for label, _ in EXPORT_FORMATS:
            tk.Radiobutton(fmt_row, text=label, variable=self._fmt_var, value=label,
                           fg=TEXT, bg=BG, activeforeground=TEXT, activebackground=BG,
                           selectcolor=ENTRY_BG, font=F_MAIN,
                           command=self._on_fmt_change).pack(side="left", padx=(0, 16))

        # JPEG quality slider
        q_row = tk.Frame(fmt_frame, bg=BG)
        q_row.pack(anchor="w", padx=12, pady=(0, 10))
        tk.Label(q_row, text="Quality:", fg=DIM, bg=BG, font=F_SMALL).pack(side="left")
        self._jpeg_q_var = tk.IntVar(value=85)
        self._jpeg_q_scale = tk.Scale(q_row, from_=0, to=100, orient="horizontal",
                                      variable=self._jpeg_q_var,
                                      bg=BG, fg=DIM, troughcolor=ENTRY_BG,
                                      highlightthickness=0, length=140, state="disabled")
        self._jpeg_q_scale.pack(side="left", padx=(6, 0))
        self._jpeg_q_label = tk.Label(q_row, text="(JPEG only)", fg=DIM, bg=BG, font=F_SMALL)
        self._jpeg_q_label.pack(side="left", padx=(8, 0))

        # ── Filename ───────────────────────────────────────────────────────
        fname_frame = tk.LabelFrame(self, text=" Filename ", fg=DIM, bg=BG,
                                    font=F_SMALL, relief="flat",
                                    highlightbackground=BTN_HOV, highlightthickness=1)
        fname_frame.pack(fill="x", padx=20, pady=(6, 6))

        self._name_only_var = tk.BooleanVar(value=False)
        tk.Checkbutton(fname_frame,
                       text="Marker name only  (e.g. My Marker.png)",
                       variable=self._name_only_var,
                       fg=TEXT, bg=BG, activeforeground=TEXT,
                       activebackground=BG, selectcolor=ENTRY_BG,
                       font=F_MAIN).pack(anchor="w", padx=12, pady=(8, 2))
        tk.Label(fname_frame,
                 text="Default: My Marker_00-00-10-00.png",
                 fg=DIM, bg=BG, font=F_SMALL).pack(anchor="w", padx=12, pady=(0, 8))

        # ── Buttons ────────────────────────────────────────────────────────
        bf = tk.Frame(self, bg=BG)
        bf.pack(pady=(6, 16))
        TBtn(bf, text="Cancel",   command=self.destroy,  bg=ACCENT, fg=BG).pack(side="left", padx=8)
        TBtn(bf, text="Continue", command=self._confirm, bg=ACCENT, fg=BG).pack(side="left", padx=8)

        center_on_parent(self, parent)
        self.deiconify()
        self.lift()
        self.attributes("-topmost", True)

    def _on_fmt_change(self):
        is_jpeg = self._fmt_var.get() == "JPEG"
        self._jpeg_q_scale.config(state="normal" if is_jpeg else "disabled",
                                  fg=TEXT if is_jpeg else DIM)
        self._jpeg_q_label.config(fg=TEXT if is_jpeg else DIM)

    def _confirm(self):
        fmt_label    = self._fmt_var.get()
        fmt          = next((f for lbl, f in EXPORT_FORMATS if lbl == fmt_label), "png")
        jpeg_quality = self._jpeg_q_var.get() if fmt == "jpg" else None
        self.result  = {
            "fmt":          fmt,
            "jpeg_quality": jpeg_quality,
            "name_only":    self._name_only_var.get(),
        }
        self.destroy()


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

APP_TITLE   = "Marker Madness"
APP_VERSION = "1.2"

class MarkerMadness:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.configure(bg=BG)
        self.root.after_idle(lambda: self.root.minsize(
            1100, max(self._side_panel.winfo_reqheight(), 630)))

        self._resolve      = None
        self._project      = None
        self._timeline     = None
        self._fps          = 24.0
        self._start_frame  = 0     # timeline start timecode expressed in frames

        self._all_markers  = []   # list of marker dicts
        self._by_id        = {}   # iid -> marker dict
        self._tl_frames    = set()  # set of timeline frame ints

        # Marker clipboard for cross-timeline copy/paste
        self._marker_clipboard = []  # list of {color, name, note, duration, frame_offset}

        # Column drag-reorder state
        self._drag_col_id   = None
        self._drag_start_x  = 0
        self._dragging      = False
        self._drag_occurred = False

        # Load persisted preferences before creating BooleanVars so their
        # default values are restored from the last session.
        self._prefs = _load_prefs()

        self._sort_col     = self._prefs.get("sort_col",     "frame")
        self._sort_reverse = self._prefs.get("sort_reverse", False)

        # Inline editor
        self._inline_widget = None
        self._inline_item   = None
        self._inline_col    = None
        self._click_job     = None

        # Preview / playhead
        self._preview_img  = None
        self._grab_path    = None
        self._autograb_job = None
        self._autojump_var    = tk.BooleanVar(value=self._prefs.get("auto_jump",        True))
        self._keep_gallery_var = tk.BooleanVar(value=self._prefs.get("keep_gallery",    False))
        self._click_edit_var  = tk.BooleanVar(value=self._prefs.get("click_edit",       False))
        self._stay_on_top_var    = tk.BooleanVar(value=self._prefs.get("stay_on_top",   True))
        self._topmost_check_job  = None
        self.root.attributes("-topmost", True)
        self.root.bind("<FocusIn>",  self._on_root_focus_in)
        self.root.bind("<FocusOut>", self._on_root_focus_out)
        self._no_prompt_delete_var = tk.BooleanVar(value=self._prefs.get("no_prompt_delete", False))
        self._search_var       = tk.StringVar()
        self._search_job       = None
        self._main_undo_stack  = []

        self._build_ui()
        self.root.bind("<Command-z>", lambda e: self._main_undo())
        self.root.bind("<Control-z>", lambda e: self._main_undo())

        # Apply persisted column order and widths now that the tree exists
        self._apply_prefs_to_ui()

        # Save prefs when the window is closed
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._connect()
        self._raise_window()

    # ── Window focus ─────────────────────────────────────────────────────

    def _raise_window(self):
        """Bring the window to the front on all platforms."""
        self.root.lift()
        self.root.attributes("-topmost", True)
        if not self._stay_on_top_var.get():
            self.root.after(250, lambda: self.root.attributes("-topmost", False))
        self.root.focus_force()

    def _on_stay_on_top_changed(self, *_):
        if self._stay_on_top_var.get():
            self.root.attributes("-topmost", True)
            self.root.bind("<FocusIn>",  self._on_root_focus_in)
            self.root.bind("<FocusOut>", self._on_root_focus_out)
        else:
            self.root.attributes("-topmost", False)
            try:
                self.root.unbind("<FocusIn>")
                self.root.unbind("<FocusOut>")
            except Exception:
                pass

    def _on_root_focus_in(self, event):
        """Restore topmost and trigger a debounced auto-refresh when returning to the window."""
        if event.widget != self.root:
            return
        if self._stay_on_top_var.get():
            self.root.attributes("-topmost", True)
        # Auto-refresh after a short delay — catches timeline switches in Resolve
        if hasattr(self, "_focus_refresh_job") and self._focus_refresh_job:
            self.root.after_cancel(self._focus_refresh_job)
        self._focus_refresh_job = self.root.after(500, self._auto_refresh_on_focus)

    def _auto_refresh_on_focus(self):
        self._focus_refresh_job = None
        self._refresh()

    def _on_root_focus_out(self, event):
        """When we lose focus, check which app is now frontmost.
        Keep topmost if it's Resolve; drop it for everything else."""
        if event.widget != self.root or not self._stay_on_top_var.get():
            return
        # Debounce: ignore rapid in/out pairs (e.g. dialog opening)
        if self._topmost_check_job:
            self.root.after_cancel(self._topmost_check_job)
        self._topmost_check_job = self.root.after(120, self._check_frontmost_app)

    def _check_frontmost_app(self):
        """Run an AppleScript query in a background thread to avoid blocking the UI."""
        self._topmost_check_job = None
        if not self._stay_on_top_var.get():
            return
        # If focus moved to one of our own windows (e.g. a dialog opened),
        # don't drop topmost — the main window should stay above Resolve.
        try:
            if self.root.focus_displayof() is not None:
                return
        except Exception:
            pass
        def _query():
            try:
                result = subprocess.run(
                    ["osascript", "-e",
                     "tell application \"System Events\" to name of "
                     "first application process whose frontmost is true"],
                    capture_output=True, text=True, timeout=1.0
                )
                active = result.stdout.strip()
                keep = "Resolve" in active
            except Exception:
                keep = True  # on any error, stay topmost to be safe
            self.root.after(0, lambda: self.root.attributes("-topmost", keep))
        threading.Thread(target=_query, daemon=True).start()

    def _mb(self, fn, *args, **kwargs):
        """Call a messagebox function with topmost temporarily disabled so it
        appears in front of the main window rather than behind it."""
        if self._stay_on_top_var.get():
            self.root.attributes("-topmost", False)
        try:
            return fn(*args, parent=self.root, **kwargs)
        finally:
            if self._stay_on_top_var.get():
                self.root.attributes("-topmost", True)

    # ── UI construction ───────────────────────────────────────────────────

    def _build_ui(self):
        # Shift+Command+A is a default macOS system shortcut ("Search Man Page Index
        # in Terminal") that fires at the OS level and cannot be intercepted by Tkinter.
        # We do not bind it — Escape is the deselect-all shortcut instead.

        # Top bar — right-side widgets packed FIRST so they claim space before left items expand
        top = tk.Frame(self.root, bg=PANEL, pady=10)
        top.pack(fill="x")
        tk.Label(top, text=APP_TITLE, fg=ACCENT, bg=PANEL, font=F_TITLE).pack(side="left", padx=(16, 4))
        tk.Label(top, text=f"v{APP_VERSION}", fg=DIM, bg=PANEL,
                 font=("Avenir Next", 10)).pack(side="left", pady=(4, 0))

        # Pack right-side buttons before status_area so they're never squeezed out
        TBtn(top, text="⟳  Refresh", command=self._refresh, bg=ACCENT, fg=BG).pack(side="right", padx=8)
        self._main_undo_btn = TBtn(top, text="↩ Undo",
                                   command=self._main_undo,
                                   bg=BTN_HOV, fg=DIM)
        self._main_undo_btn.pack(side="right", padx=(0, 4))
        tk.Frame(top, bg=BTN_HOV, width=1).pack(side="right", fill="y", padx=8)
        self._paste_btn = TBtn(top, text="⎗ Paste Markers", command=self._paste_markers,
                               bg=BTN_HOV, fg=DIM)
        self._paste_btn.pack(side="right", padx=(0, 4))
        self._copy_btn = TBtn(top, text="⎘ Copy Markers", command=self._copy_markers,
                              bg=ACCENT, fg=BG)
        self._copy_btn.pack(side="right", padx=(0, 4))

        status_area = tk.Frame(top, bg=PANEL)
        status_area.pack(side="left", padx=8)

        # Shown when disconnected / error
        self._warn_frame = tk.Frame(status_area, bg=PANEL)
        self._warn_var = tk.StringVar(value="Connecting…")
        tk.Label(self._warn_frame, textvariable=self._warn_var,
                 fg=DIM, bg=PANEL, font=F_STATUS).pack(side="left")
        self._warn_frame.pack(side="left")

        # Shown when connected
        self._info_frame = tk.Frame(status_area, bg=PANEL)
        tk.Label(self._info_frame, text="Project", fg=DIM, bg=PANEL, font=F_STATUS).pack(side="left")
        self._proj_var = tk.StringVar(value="")
        tk.Label(self._info_frame, textvariable=self._proj_var,
                 fg=TEXT, bg=PANEL, font=F_MAIN).pack(side="left", padx=(5, 0))
        tk.Label(self._info_frame, text="   ·   ", fg=DIM, bg=PANEL, font=F_STATUS).pack(side="left")
        tk.Label(self._info_frame, text="Timeline", fg=DIM, bg=PANEL, font=F_STATUS).pack(side="left")
        self._tl_var = tk.StringVar(value="")
        tk.Label(self._info_frame, textvariable=self._tl_var,
                 fg=TEXT, bg=PANEL, font=F_MAIN).pack(side="left", padx=(5, 0))
        tk.Label(self._info_frame, text="   ·   ", fg=DIM, bg=PANEL, font=F_STATUS).pack(side="left")
        self._fps_var = tk.StringVar(value="")
        tk.Label(self._info_frame, textvariable=self._fps_var,
                 fg=TEXT, bg=PANEL, font=F_MAIN).pack(side="left")

        # Hint row — above the main toolbar
        hint_row = tk.Frame(self.root, bg=BG)
        hint_row.pack(fill="x", padx=12, pady=(6, 0))
        tk.Label(hint_row, text="⌥  Right-click Color to batch change",
                 fg=ACCENT, bg=BG, font=F_SMALL).pack(side="left")

        # Toolbar row 1 — actions
        tb1 = tk.Frame(self.root, bg=BG, pady=4)
        tb1.pack(fill="x", padx=12)

        TBtn(tb1, text="+ Add",            command=self._add_marker,
             bg=ACCENT, fg=BG).pack(side="left", padx=3)
        TBtn(tb1, text="✎ Edit",           command=self._edit_marker,
             bg=ACCENT, fg=BG).pack(side="left", padx=3)
        TBtn(tb1, text="⚡ Batch Rename",   command=self._open_renamer,
             bg=PURPLE, fg=BG, font=("Avenir Next", 13, "bold")).pack(side="left", padx=3)

        TBtn(tb1, text="✕ Delete",         command=self._delete_marker,
             bg=RED, fg=BG).pack(side="left", padx=3)
        TBtn(tb1, text="✕✕ Delete All",   command=self._delete_all,
             bg=RED, fg=BG).pack(side="left", padx=3)

        # Transfer section — stacked pairs: top row ⬆Timeline, bottom row ⬇Clip
        tk.Frame(tb1, bg=BTN_HOV, width=1).pack(side="left", fill="y", padx=8)
        tk.Label(tb1, text="Transfer:", fg=DIM, bg=BG, font=F_SMALL).pack(side="left", padx=(0, 4))

        # Outer frame holds two sub-columns side by side
        transfer_frame = tk.Frame(tb1, bg=BG)
        transfer_frame.pack(side="left")

        # Copy column
        copy_col = tk.Frame(transfer_frame, bg=BG)
        copy_col.pack(side="left", padx=3)
        self._btn_copy = TBtn(copy_col, text="⬆ Copy→Timeline",
                              command=lambda: self._promote(move=False),
                              bg=PURPLE, fg=BG)
        self._btn_copy.pack(fill="x", pady=(0, 2))
        self._btn_copy_clip = TBtn(copy_col, text="⬇ Copy→Clip",
                                   command=lambda: self._demote(move=False),
                                   bg=PURPLE, fg=BG)
        self._btn_copy_clip.pack(fill="x")

        # Move column
        move_col = tk.Frame(transfer_frame, bg=BG)
        move_col.pack(side="left", padx=3)
        self._btn_move = TBtn(move_col, text="⬆ Move→Timeline",
                              command=lambda: self._promote(move=True),
                              bg=PURPLE, fg=BG)
        self._btn_move.pack(fill="x", pady=(0, 2))
        self._btn_move_clip = TBtn(move_col, text="⬇ Move→Clip",
                                   command=lambda: self._demote(move=True),
                                   bg=PURPLE, fg=BG)
        self._btn_move_clip.pack(fill="x")

        # Nudge + Undo section
        tk.Frame(tb1, bg=BTN_HOV, width=1).pack(side="left", fill="y", padx=8)
        tk.Label(tb1, text="Nudge:", fg=DIM, bg=BG, font=F_SMALL).pack(side="left", padx=(0, 4))
        self._nudge_var = tk.IntVar(value=0)
        tk.Spinbox(tb1, from_=-9999, to=9999, textvariable=self._nudge_var,
                   width=6, bg=ENTRY_BG, fg=TEXT, insertbackground=TEXT,
                   buttonbackground=BTN, relief="flat",
                   font=F_MAIN).pack(side="left")
        tk.Label(tb1, text="f", fg=DIM, bg=BG, font=F_SMALL).pack(side="left", padx=(2, 6))
        TBtn(tb1, text="Apply", command=self._nudge_markers,
             bg=ACCENT, fg=BG).pack(side="left", padx=(0, 6))
        self._nudge_auto_var = tk.BooleanVar(value=False)
        tk.Checkbutton(tb1, text="Skip Confirm", variable=self._nudge_auto_var,
                       fg=TEXT, bg=BG, activeforeground=TEXT, activebackground=BG,
                       selectcolor=ENTRY_BG, font=F_SMALL).pack(side="left")


        # Toolbar row 2 — filters & import/export
        tb2 = tk.Frame(self.root, bg=BG, pady=4)
        tb2.pack(fill="x", padx=12)

        tk.Label(tb2, text="Color:", fg=DIM, bg=BG, font=F_SMALL).pack(side="left", padx=(0, 3))
        self._filter_color = tk.StringVar(value="All")
        fcb = ttk.Combobox(tb2, textvariable=self._filter_color,
                           values=["All"] + MARKER_COLORS, state="readonly", width=11)
        fcb.pack(side="left")
        fcb.bind("<<ComboboxSelected>>", lambda _: self._populate_table())

        tk.Label(tb2, text="Type:", fg=DIM, bg=BG, font=F_SMALL).pack(side="left", padx=(16, 3))
        self._filter_type = tk.StringVar(value="All Types")
        ttk.Combobox(tb2, textvariable=self._filter_type,
                     values=["All Types", "Timeline", "Clip"],
                     state="readonly", width=11).pack(side="left")
        self._filter_type.trace_add("write", lambda *_: self._populate_table())

        # Search field
        tk.Label(tb2, text="🔍 Search:", fg=DIM, bg=BG, font=F_SMALL).pack(side="left", padx=(16, 3))
        self._search_entry = tk.Entry(tb2, textvariable=self._search_var, width=20,
                                bg=ENTRY_BG, fg=TEXT, insertbackground=TEXT,
                                relief="flat", font=F_MAIN)
        self._search_entry.pack(side="left")
        self._search_var.trace_add("write", self._on_search_changed)
        TBtn(tb2, text="✕", command=self._clear_search,
             bg=BTN, fg=DIM, padx=5, pady=2).pack(side="left", padx=(2, 0))

        # Search filter checkboxes
        sf = tk.Frame(tb2, bg=BG)
        sf.pack(side="left", padx=(10, 0))
        tk.Label(sf, text="Search in:", fg=DIM, bg=BG,
                 font=("Avenir Next", 9)).pack(anchor="w")
        cb_row = tk.Frame(sf, bg=BG)
        cb_row.pack(anchor="w")
        self._search_name_var = tk.BooleanVar(value=True)
        self._search_note_var = tk.BooleanVar(value=True)
        self._search_clip_var = tk.BooleanVar(value=True)
        for label, var in [("Name", self._search_name_var),
                            ("Note", self._search_note_var),
                            ("Clip", self._search_clip_var)]:
            tk.Checkbutton(cb_row, text=label, variable=var,
                           fg=TEXT, bg=BG, activeforeground=TEXT,
                           activebackground=BG, selectcolor=ENTRY_BG,
                           font=("Avenir Next", 9),
                           command=self._populate_table).pack(side="left", padx=(0, 4))

        TBtn(tb2, text="⬇ Export CSV", command=self._export_csv,
             bg=GREEN, fg=BG).pack(side="right", padx=3)
        TBtn(tb2, text="⬆ Import CSV", command=self._import_csv,
             bg=GREEN, fg=BG).pack(side="right", padx=3)
        tk.Frame(tb2, bg=BTN_HOV, width=1).pack(side="right", fill="y", padx=8)
        TBtn(tb2, text="↺ Reset Column Layout", command=self._reset_layout,
             bg=BTN, fg=DIM, padx=6, pady=2).pack(side="right", padx=3)

        # Main area: table + preview
        # Preview must be packed first (side="right") so expand=True on the
        # table frame doesn't crowd it out when column widths are wide.
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True, padx=12, pady=(4, 4))
        self._build_preview(main)
        self._build_table(main)

        # Status bar
        sb = tk.Frame(self.root, bg=PANEL, pady=4)
        sb.pack(fill="x")
        self._count_var = tk.StringVar(value="")
        tk.Label(sb, textvariable=self._count_var, fg=TEXT, bg=PANEL,
                 font=F_SMALL).pack(side="left", padx=12)
        tk.Label(sb, text="Right-click Name/Note to edit  ·  Right-click Color to change (select multiple to batch change)  ·  Double-click for full editor  ·  Esc to deselect all",
                 fg=DIM, bg=PANEL, font=F_SMALL).pack(side="right", padx=12)

    def _build_table(self, parent):
        frame = tk.Frame(parent, bg=BG)
        frame.pack(side="left", fill="both", expand=True)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                         background=PANEL, fieldbackground=PANEL,
                         foreground=TEXT, rowheight=28, font=F_MAIN, borderwidth=0)
        style.configure("Treeview.Heading",
                         background=BTN, foreground=ACCENT, font=F_BOLD, relief="flat")
        style.map("Treeview",
                  background=[("selected", SEL_BG)],
                  foreground=[("selected", TEXT)])

        # Build per-color swatch images (12×12 solid squares) for the tree column
        self._color_imgs = {}
        for color_name, hex_val in COLOR_HEX.items():
            img = tk.PhotoImage(width=12, height=12)
            row_str = "{" + " ".join([hex_val] * 12) + "}"
            img.put(" ".join([row_str] * 12))
            self._color_imgs[color_name] = img
        self._color_imgs[""] = tk.PhotoImage(width=12, height=12)  # transparent fallback

        ids = [c[0] for c in COLUMNS]
        self._tree = ttk.Treeview(frame, columns=ids, show="tree headings",
                                   selectmode="extended")

        # Tree column (#0) — colored dot, no heading text
        self._tree.column("#0", width=30, minwidth=30, anchor="center", stretch=False)
        self._tree.heading("#0", text="")

        for cid, heading, width, anchor, stretch, _ in COLUMNS:
            self._tree.heading(cid, text=heading, anchor=anchor,
                               command=lambda c=cid: self._on_sort_column(c))
            self._tree.column(cid, width=width, anchor=anchor, stretch=stretch)

        vsb = ttk.Scrollbar(frame, orient="vertical",   command=self._tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal",  command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        self._tree.bind("<ButtonRelease-1>",  self._on_click)
        self._tree.bind("<Double-1>",         self._on_double_click)
        self._tree.bind("<Delete>",           lambda _: self._delete_marker())
        self._tree.bind("<BackSpace>",        lambda _: self._delete_marker())
        self._tree.bind("<<TreeviewSelect>>", self._on_sel_change)
        self._tree.bind("<Button-2>",         self._on_right_click)  # macOS
        self._tree.bind("<Button-3>",         self._on_right_click)  # Windows/Linux
        self._tree.bind("<Command-a>",        self._select_all)
        self._tree.bind("<Escape>", self._deselect_all)

        # Column drag-to-reorder — detect heading drags, suppress sort when drag occurs
        self._tree.bind("<ButtonPress-1>",   self._col_drag_start,  add="+")
        self._tree.bind("<B1-Motion>",       self._col_drag_motion, add="+")
        self._tree.bind("<ButtonRelease-1>", self._col_drag_end,    add="+")

        # Row tags — no foreground override; dot image carries the color
        self._tree.tag_configure("tl_row")
        self._tree.tag_configure("clip_row")

    def _build_preview(self, parent):
        panel = tk.Frame(parent, bg=PANEL, width=310)
        panel.pack(side="right", fill="y", padx=(8, 0))
        panel.pack_propagate(False)
        self._side_panel = panel

        tk.Label(panel, text="Frame Preview", fg=ACCENT, bg=PANEL,
                 font=F_BOLD).pack(pady=(12, 4))

        self._img_canvas = tk.Canvas(panel, bg=ENTRY_BG, width=286, height=161,
                                      relief="flat", highlightthickness=0)
        self._img_canvas.pack(padx=10, pady=4)
        self._img_canvas.create_text(143, 80,
                                      text="Select a marker\nthen click\nGrab Frame",
                                      fill=DIM, font=F_SMALL, justify="center",
                                      tags="placeholder")

        self._prev_info = tk.StringVar(value="")
        tk.Label(panel, textvariable=self._prev_info, fg=TEXT, bg=PANEL,
                 font=F_SMALL, wraplength=286, justify="left",
                 height=3, anchor="nw").pack(padx=10, pady=4)

        # Checkboxes — 2 columns × 2 rows
        cb_grid = tk.Frame(panel, bg=PANEL)
        cb_grid.pack(fill="x", padx=10, pady=(0, 4))
        cb_grid.columnconfigure(0, weight=1)
        cb_grid.columnconfigure(1, weight=1)

        def _cb(parent, text, var, row, col):
            tk.Checkbutton(parent, text=text, variable=var,
                           fg=TEXT, bg=PANEL, activeforeground=TEXT,
                           activebackground=PANEL, selectcolor=ENTRY_BG,
                           font=F_SMALL, anchor="w").grid(
                row=row, column=col, sticky="w", padx=6, pady=2)

        _cb(cb_grid, "Auto-jump on select",    self._autojump_var,          0, 0)
        _cb(cb_grid, "Keep stills in gallery", self._keep_gallery_var,      0, 1)
        _cb(cb_grid, "One click edit field",   self._click_edit_var,        1, 0)
        _cb(cb_grid, "Float above Resolve",    self._stay_on_top_var,       1, 1)
        _cb(cb_grid, "Delete without prompt",  self._no_prompt_delete_var,  2, 0)
        self._stay_on_top_var.trace_add("write", self._on_stay_on_top_changed)

        TBtn(panel, text="⏎  Jump to Marker", command=self._jump_to_marker,
             bg=ACCENT, fg=BG).pack(fill="x", padx=10, pady=(0, 4))
        TBtn(panel, text="📷  Grab Frame",    command=self._grab_frame,
             bg=ACCENT, fg=BG).pack(fill="x", padx=10, pady=(0, 4))
        TBtn(panel, text="⬇  Export Frame",   command=self._export_frame,
             bg=GREEN, fg=BG).pack(fill="x", padx=10, pady=(0, 4))
        TBtn(panel, text="📷  Batch Export High Res Frames", command=self._batch_export_full_res_frames,
             bg=ORANGE, fg=BG).pack(fill="x", padx=10, pady=(0, 6))

        tk.Label(panel, text="Shift or ⌘-click to select\nmultiple markers for batch changes",
                 fg=TEXT, bg=PANEL, font=("Avenir Next", 11, "italic"),
                 justify="center").pack(pady=(0, 8))

    # ── Column drag-to-reorder ────────────────────────────────────────────

    def _col_drag_start(self, event):
        region = self._tree.identify_region(event.x, event.y)
        if region != "heading":
            self._drag_col_id = None
            return
        col = self._tree.identify_column(event.x)
        if col == "#0":   # tree column — not draggable
            self._drag_col_id = None
            return
        self._drag_col_id  = col
        self._drag_start_x = event.x
        self._dragging     = False

    def _col_drag_motion(self, event):
        if not self._drag_col_id:
            return
        if abs(event.x - self._drag_start_x) > 12:
            if not self._dragging:
                self._dragging = True
                self._tree.config(cursor="sb_h_double_arrow")
                # Highlight the column being dragged
                try:
                    src_idx = int(self._drag_col_id[1:]) - 1
                    cols = list(self._tree["displaycolumns"])
                    if cols == ["#all"]:
                        cols = list(COL_IDS)
                    if 0 <= src_idx < len(cols):
                        self._tree.heading(cols[src_idx], text=f"↔ {self._tree.heading(cols[src_idx], 'text')}")
                except Exception:
                    pass
        # Highlight the target column heading so user sees drop destination
        if self._dragging:
            target = self._tree.identify_column(event.x)
            style = ttk.Style()
            style.configure("Treeview.Heading", background=BTN, foreground=ACCENT)
            if target and target != "#0" and target != self._drag_col_id:
                try:
                    tgt_idx = int(target[1:]) - 1
                    cols = list(self._tree["displaycolumns"])
                    if cols == ["#all"]:
                        cols = list(COL_IDS)
                    if 0 <= tgt_idx < len(cols):
                        self._tree.heading(cols[tgt_idx], background=BTN_HOV)
                except Exception:
                    pass

    def _col_drag_end(self, event):
        self._tree.config(cursor="")
        # Restore any modified heading text
        if self._dragging and self._drag_col_id:
            try:
                src_idx = int(self._drag_col_id[1:]) - 1
                cols = list(self._tree["displaycolumns"])
                if cols == ["#all"]:
                    cols = list(COL_IDS)
                if 0 <= src_idx < len(cols):
                    col_id = cols[src_idx]
                    orig = next((c[1] for c in COLUMNS if c[0] == col_id), col_id)
                    self._tree.heading(col_id, text=orig)
            except Exception:
                pass
        if not self._dragging or not self._drag_col_id:
            self._drag_col_id = None
            self._dragging    = False
            return
        self._drag_occurred = True
        target_col = self._tree.identify_column(event.x)
        self._reorder_column(self._drag_col_id, target_col)
        self._drag_col_id = None
        self._dragging    = False

    def _reorder_column(self, src_col: str, dst_col: str):
        """Move src_col to dst_col position in displaycolumns and save prefs."""
        if dst_col == "#0":
            return
        try:
            src_idx = int(src_col[1:]) - 1
            dst_idx = int(dst_col[1:]) - 1
        except ValueError:
            return
        cols = list(self._tree["displaycolumns"])
        if cols == ["#all"]:
            cols = list(COL_IDS)
        if src_idx < 0 or dst_idx < 0 or src_idx == dst_idx:
            return
        if src_idx >= len(cols) or dst_idx >= len(cols):
            return
        col_id = cols.pop(src_idx)
        cols.insert(dst_idx, col_id)
        self._tree.configure(displaycolumns=cols)
        _save_prefs(self._collect_prefs())

    # ── Preferences: apply / collect / save ──────────────────────────────

    def _apply_prefs_to_ui(self):
        """Apply saved column order, widths, filter state, etc. after UI is built."""
        p = self._prefs

        # Column order
        saved_order = p.get("col_order", [])
        valid = [c for c in saved_order if c in COL_IDS]
        for c in COL_IDS:
            if c not in valid:
                valid.append(c)
        if valid:
            self._tree.configure(displaycolumns=valid)

        # Column widths
        for col_id, width in p.get("col_widths", {}).items():
            if col_id in COL_IDS:
                try:
                    self._tree.column(col_id, width=int(width))
                except Exception:
                    pass

        # Filter and nudge state
        try:
            self._filter_color.set(p.get("filter_color", "All"))
            self._filter_type.set(p.get("filter_type", "All Types"))
            self._nudge_var.set(p.get("nudge_amount", 0))
        except Exception:
            pass

    def _reset_layout(self):
        """Restore columns to default order and widths."""
        self._tree.configure(displaycolumns=COL_IDS)
        for col_id, heading, width, anchor, stretch, _ in COLUMNS:
            try:
                self._tree.column(col_id, width=width)
            except Exception:
                pass
        _save_prefs(self._collect_prefs())

    def _collect_prefs(self) -> dict:
        """Gather all saveable state into a dict."""
        cols = list(self._tree["displaycolumns"])
        if cols == ["#all"]:
            cols = list(COL_IDS)
        widths = {}
        for col_id in COL_IDS:
            try:
                widths[col_id] = self._tree.column(col_id, "width")
            except Exception:
                pass
        return {
            "window_geometry":  self.root.geometry(),
            "col_order":        cols,
            "col_widths":       widths,
            "sort_col":         self._sort_col,
            "sort_reverse":     self._sort_reverse,
            "auto_jump":        self._autojump_var.get(),
            "keep_gallery":     self._keep_gallery_var.get(),
            "click_edit":       self._click_edit_var.get(),
            "stay_on_top":      self._stay_on_top_var.get(),
            "no_prompt_delete": self._no_prompt_delete_var.get(),
            "nudge_amount":     self._nudge_var.get(),
        }

    def _on_close(self):
        """Save preferences then close the window."""
        _save_prefs(self._collect_prefs())
        self.root.destroy()

    # ── Cross-timeline copy / paste ───────────────────────────────────────

    def _copy_markers(self):
        sel = self._tree.selection()
        if not sel:
            self._mb(messagebox.showinfo, "Copy Markers",
                     "Select one or more markers to copy.")
            return
        recs = [self._by_id[iid] for iid in sel if iid in self._by_id]
        if not recs:
            return
        min_frame = min(r["timeline_frame"] for r in recs)
        self._marker_clipboard = [
            {
                "color":        r["color"],
                "name":         r["name"],
                "note":         r["note"],
                "duration":     r["duration"],
                "frame_offset": r["timeline_frame"] - min_frame,
            }
            for r in recs
        ]
        count = len(self._marker_clipboard)
        # Light up the paste button
        self._paste_btn.config(fg=BG, bg=ACCENT)
        cur = self._count_var.get().split("  ·  copied")[0]
        self._count_var.set(cur + f"  ·  {count} marker{'s' if count != 1 else ''} copied")

    def _paste_markers(self):
        if not self._marker_clipboard:
            self._mb(messagebox.showinfo, "Paste Markers",
                     "Nothing in clipboard. Select markers and use Copy first.")
            return

        # Refresh first so we're connected to whichever timeline is now active
        self._refresh()

        timeline, err = self._fresh_timeline()
        if not timeline:
            self._mb(messagebox.showwarning, "Not connected", err)
            return

        try:
            tc_str = timeline.GetCurrentTimecode() or ""
            if not tc_str:
                self._mb(messagebox.showwarning, "Paste Markers",
                         "Could not read playhead position from Resolve.")
                return
            playhead_abs   = tc_to_frames(tc_str, self._fps)
            playhead_frame = playhead_abs - self._start_frame
        except Exception as exc:
            self._mb(messagebox.showerror, "Paste Markers",
                     f"Error reading playhead position:\n{exc}")
            return

        count    = len(self._marker_clipboard)
        tc_label = frames_to_tc(playhead_abs, self._fps)
        if not self._mb(messagebox.askyesno, "Paste Markers",
                        f"Paste {count} marker{'s' if count != 1 else ''} to the current timeline\n"
                        f"starting at playhead  {tc_label}?\n\n"
                        "Markers land as timeline markers relative to the playhead.\n"
                        "Tip: make sure your playhead is positioned before confirming.\n"
                        "Conflicts (existing marker at same frame) are skipped."):
            return

        added = skipped = failed = 0
        undo_batch = []

        for entry in self._marker_clipboard:
            tl_frame = playhead_frame + entry["frame_offset"]
            if tl_frame < 0:
                skipped += 1
                continue
            if tl_frame in self._tl_frames:
                skipped += 1
                continue
            ok, _err = self._resolve_add_marker(
                timeline, tl_frame,
                entry["color"], entry["name"], entry["note"], entry["duration"], ""
            )
            if ok:
                added += 1
                self._tl_frames.add(tl_frame)
                undo_batch.append((timeline, tl_frame))
            else:
                failed += 1

        if undo_batch:
            self._main_undo_stack.append(("add_timeline", undo_batch))
            self._main_undo_btn.config(bg=ACCENT, fg=BG)

        self._refresh()
        msg = f"Pasted {added} marker{'s' if added != 1 else ''}."
        if skipped:
            msg += f"\nSkipped {skipped} (conflict or out of range)."
        if failed:
            msg += f"\nFailed: {failed}."
        self._mb(messagebox.showinfo, "Paste Complete", msg)

    # ── Resolve connection ────────────────────────────────────────────────

    def _connect(self):
        self._resolve = get_resolve()
        if not self._resolve:
            self._show_status_warning("⚠  Not connected — launch DaVinci Resolve first")
            return
        self._reset_filters()
        self._refresh()
        self._start_timeline_poll()

    def _reset_filters(self):
        self._filter_color.set("All")
        self._filter_type.set("All Types")

    def _start_timeline_poll(self):
        """Poll Resolve every 4 seconds and auto-refresh if the timeline has changed."""
        self._poll_timeline()

    def _poll_timeline(self):
        try:
            if self._resolve:
                pm = self._resolve.GetProjectManager()
                if pm:
                    proj = pm.GetCurrentProject()
                    if proj:
                        tl = proj.GetCurrentTimeline()
                        if tl:
                            name = tl.GetName()
                            current = self._timeline.GetName() if self._timeline else None
                            if name != current:
                                self._reset_filters()
                                self._refresh()
        except Exception:
            pass
        self.root.after(4000, self._poll_timeline)

    def _show_status_warning(self, msg: str):
        self._info_frame.pack_forget()
        self._warn_var.set(msg)
        self._warn_frame.pack(side="left")

    def _show_status_connected(self, proj: str, tl: str, fps: float):
        self._warn_frame.pack_forget()
        self._proj_var.set(proj)
        self._tl_var.set(tl)
        self._fps_var.set(f"{fps} fps")
        self._info_frame.pack(side="left")

    def _get_timeline(self):
        if not self._resolve:
            return None
        try:
            pm = self._resolve.GetProjectManager()
            if not pm:
                return None
            self._project = pm.GetCurrentProject()
            if not self._project:
                self._show_status_warning("⚠  No project open")
                return None
            self._timeline = self._project.GetCurrentTimeline()
            if not self._timeline:
                self._show_status_warning("⚠  No timeline selected")
                return None
            try:
                self._fps = float(self._timeline.GetSetting("timelineFrameRate"))
            except Exception:
                self._fps = 24.0
            # Read the timeline start timecode so frame numbers display correctly
            # for timelines that start at 01:00:00:00 etc.
            try:
                start_tc = self._timeline.GetStartTimecode()
                self._start_frame = tc_to_frames(start_tc, self._fps)
            except Exception:
                self._start_frame = 0
            self._show_status_connected(
                self._project.GetName(),
                self._timeline.GetName(),
                self._fps
            )
            return self._timeline
        except Exception as exc:
            self._show_status_warning(f"Error: {exc}")
            return None

    # ── Data loading ──────────────────────────────────────────────────────

    def _refresh(self):
        self._close_inline()
        if not self._get_timeline():
            self._all_markers = []
            self._by_id       = {}
            self._tl_frames   = set()
            self._populate_table()
            return

        markers = []

        # Timeline (ruler) markers
        try:
            tl_raw = self._timeline.GetMarkers() or {}
        except Exception:
            tl_raw = {}
        for frame_id, m in tl_raw.items():
            rec = self._make_record(
                mtype="Timeline",
                timeline_frame=frame_id,
                marker_frame=frame_id,
                color=m.get("color", "Blue"),
                name=m.get("name", ""),
                note=m.get("note", ""),
                duration=m.get("duration", 1),
                clip_name="",
                track_type="",
                track_index=0,
                timeline_item=None,
            )
            markers.append(rec)

        self._tl_frames = {r["timeline_frame"] for r in markers}

        # Clip markers — iterate every track
        # Use a seen set to deduplicate: synced clips share the same markers
        # across their video and audio track instances.
        # tl_end guards against source/master-clip markers whose frame offsets
        # fall outside the actual timeline range — those jump to nowhere.
        try:
            tl_end = self._timeline.GetEndFrame()
        except Exception:
            tl_end = None
        seen_clip_markers = set()
        try:
            for track_type in ("video", "audio"):
                track_count = self._timeline.GetTrackCount(track_type)
                for ti in range(1, track_count + 1):
                    items = self._timeline.GetItemListInTrack(track_type, ti)
                    if not items:
                        continue
                    for ci, item in enumerate(items):
                        try:
                            clip_markers = item.GetMarkers() or {}
                            clip_start   = item.GetStart()
                            clip_name    = item.GetName()
                            try:
                                left_offset = item.GetLeftOffset()
                            except Exception:
                                left_offset = 0
                        except Exception:
                            continue
                        clip_end = item.GetEnd()
                        for mf, m in clip_markers.items():
                            # clip_start / GetEnd() are absolute frames (include
                            # the timecode offset). Validate in absolute space,
                            # then normalize to 0-based for consistent storage.
                            tl_pos_abs = clip_start + mf - left_offset
                            # Tight filter: must fall within this clip's own
                            # range. Source/media-pool markers that happen to
                            # land in the timeline range are caught here.
                            if not (clip_start <= tl_pos_abs < clip_end):
                                continue
                            if tl_end is not None and not (self._start_frame <= tl_pos_abs <= tl_end):
                                continue
                            tl_pos = tl_pos_abs - self._start_frame
                            dedup_key = (clip_name, tl_pos, mf)
                            if dedup_key in seen_clip_markers:
                                continue
                            seen_clip_markers.add(dedup_key)
                            uid = f"c_{track_type}_{ti}_{ci}_{mf}"
                            rec = self._make_record(
                                mtype="Clip",
                                timeline_frame=tl_pos,
                                marker_frame=mf,
                                color=m.get("color", "Blue"),
                                name=m.get("name", ""),
                                note=m.get("note", ""),
                                duration=m.get("duration", 1),
                                clip_name=clip_name,
                                track_type=track_type,
                                track_index=ti,
                                timeline_item=item,
                                uid=uid,
                            )
                            markers.append(rec)
        except Exception as clip_exc:
            # Surface the error in the status bar rather than silently ignoring it
            self._fps_var.set(self._fps_var.get() + f"  ⚠ clip scan: {clip_exc}")

        self._all_markers = markers
        self._by_id       = {r["id"]: r for r in markers}
        self._populate_table()

    def _make_record(self, *, mtype, timeline_frame, marker_frame,
                     color, name, note, duration,
                     clip_name, track_type, track_index, timeline_item,
                     uid=None) -> dict:
        if uid is None:
            uid = f"t_{timeline_frame}"

        clip_in_frame = clip_out_frame = clip_dur_frames = None
        if timeline_item is not None:
            try:
                clip_in_frame    = timeline_item.GetStart() - self._start_frame
                clip_out_frame   = timeline_item.GetEnd()   - self._start_frame
                clip_dur_frames  = timeline_item.GetDuration()
            except Exception:
                pass

        return {
            "id":              uid,
            "type":            mtype,
            "timeline_frame":  timeline_frame,
            "marker_frame":    marker_frame,
            "color":           color,
            "name":            name,
            "note":            note,
            "duration":        duration,
            "clip_name":       clip_name,
            "track_type":      track_type,
            "track_index":     track_index,
            "timeline_item":   timeline_item,
            "clip_in_frame":   clip_in_frame,
            "clip_out_frame":  clip_out_frame,
            "clip_dur_frames": clip_dur_frames,
        }

    # ── Search ────────────────────────────────────────────────────────────

    def _on_search_changed(self, *_):
        """Debounce search input so _populate_table isn't called every keystroke."""
        if self._search_job:
            self.root.after_cancel(self._search_job)
        self._search_job = self.root.after(150, self._populate_table)

    def _clear_search(self):
        self._search_var.set("")

    # ── Table population ──────────────────────────────────────────────────

    def _on_sort_column(self, col_id):
        if self._drag_occurred:
            self._drag_occurred = False
            return  # heading click was actually the end of a drag — skip sort
        if self._sort_col == col_id:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_col     = col_id
            self._sort_reverse = False
        self._populate_table()

    def _populate_table(self):
        self._close_inline()
        for row in self._tree.get_children():
            self._tree.delete(row)

        for cid, heading, _, anchor, _, _ in COLUMNS:
            arrow = (" ▼" if self._sort_reverse else " ▲") if cid == self._sort_col else ""
            self._tree.heading(cid, text=heading + arrow, anchor=anchor)

        color_f  = self._filter_color.get()
        type_f   = self._filter_type.get()
        search_f = self._search_var.get().strip().lower()
        shown    = 0

        # Cache search field flags once — not on every row
        srch_name = self._search_name_var.get()
        srch_note = self._search_note_var.get()
        srch_clip = self._search_clip_var.get()

        key_fn = SORT_KEY.get(self._sort_col, lambda r: r["timeline_frame"])
        for rec in sorted(self._all_markers, key=key_fn, reverse=self._sort_reverse):
            if color_f != "All" and rec["color"] != color_f:
                continue
            if type_f == "Timeline" and rec["type"] != "Timeline":
                continue
            if type_f == "Clip" and rec["type"] != "Clip":
                continue
            if search_f:
                haystack = " ".join([
                    rec["name"]      if srch_name else "",
                    rec["note"]      if srch_note else "",
                    rec["clip_name"] if srch_clip else "",
                ]).lower()
                if search_f not in haystack:
                    continue

            tc  = frames_to_tc(rec["timeline_frame"] + self._start_frame, self._fps)
            tag_color = f"c_{rec['color'].lower()}"
            tag_type  = "tl_row" if rec["type"] == "Timeline" else "clip_row"
            label     = "TL" if rec["type"] == "Timeline" else "Clip"

            cif = rec["clip_in_frame"]
            cof = rec["clip_out_frame"]
            cdf = rec["clip_dur_frames"]
            clip_in_tc  = frames_to_tc(cif + self._start_frame, self._fps) if cif is not None else ""
            clip_out_tc = frames_to_tc(cof + self._start_frame, self._fps) if cof is not None else ""
            clip_dur_f  = cdf if cdf is not None else ""
            clip_dur_t  = frames_to_tc(cdf, self._fps)                     if cdf is not None else ""

            self._tree.insert("", "end", iid=rec["id"],
                              text="",
                              image=self._color_imgs.get(rec["color"], self._color_imgs[""]),
                              values=(label, rec["timeline_frame"] + self._start_frame, tc,
                                      rec["color"], rec["name"], rec["note"],
                                      rec["clip_name"], rec["duration"],
                                      clip_in_tc, clip_out_tc, clip_dur_f, clip_dur_t),
                              tags=(tag_type, tag_color))
            shown += 1

        total = len(self._all_markers)
        tl_count   = sum(1 for r in self._all_markers if r["type"] == "Timeline")
        clip_count = total - tl_count
        sel_count  = len(self._tree.selection())
        base = f"{shown} shown  ·  {tl_count} timeline, {clip_count} clip"
        self._count_var.set(base + (f"  ·  {sel_count} selected" if sel_count else ""))

    # ── Selection helpers ─────────────────────────────────────────────────

    def _select_all(self, _=None):
        self._tree.selection_set(self._tree.get_children())
        return "break"

    def _deselect_all(self, _=None):
        self._tree.selection_remove(self._tree.selection())
        return "break"

    def _open_renamer(self):
        if not hasattr(self, "_renamer_dlg") or not self._renamer_dlg.winfo_exists():
            self._renamer_dlg = MarkerRenamerDialog(self)
        else:
            self._renamer_dlg.deiconify()
            self._renamer_dlg.lift()
            self._renamer_dlg._schedule_preview()

    def _on_shift_click(self, event):
        item = self._tree.identify_row(event.y)
        if not item:
            return "break"
        if item in self._tree.selection():
            self._tree.selection_remove(item)
        else:
            self._tree.selection_add(item)
        return "break"

    # ── Inline editing ────────────────────────────────────────────────────

    def _on_click(self, event):
        self._close_inline()
        if not self._click_edit_var.get():
            return
        region = self._tree.identify_region(event.x, event.y)
        col_id = NUM_COL.get(self._tree.identify_column(event.x), "")
        item   = self._tree.identify_row(event.y)
        if region != "cell" or col_id not in ("name", "note") or not item:
            return
        if self._click_job:
            self.root.after_cancel(self._click_job)
        self._click_job = self.root.after(
            280, lambda: self._start_inline(item, col_id)
        )

    def _on_double_click(self, event):
        if self._click_job:
            self.root.after_cancel(self._click_job)
            self._click_job = None
        self._close_inline()
        self._edit_marker()

    def _on_right_click(self, event):
        """Right-click context menu:
           - Color column: color picker list
           - Name / Note columns: 'Edit' option that opens inline editor
        """
        col_id = NUM_COL.get(self._tree.identify_column(event.x), "")
        item   = self._tree.identify_row(event.y)
        if not item:
            return

        if col_id == "color":
            # Keep existing selection logic for color
            current_sel = self._tree.selection()
            if item not in current_sel:
                self._tree.selection_set(item)

            rec = self._by_id.get(item)
            if not rec:
                return

            menu = tk.Menu(self.root, tearoff=0, bg=PANEL, fg=TEXT,
                           activebackground=SEL_BG, activeforeground=TEXT,
                           relief="flat", bd=0, font=F_MAIN)

            current_color = rec["color"]
            for color in MARKER_COLORS:
                hex_col = COLOR_HEX.get(color, TEXT)
                label   = f"✓  {color}" if color == current_color else f"    {color}"
                menu.add_command(
                    label=label,
                    foreground=hex_col,
                    command=lambda c=color: self._apply_color_from_menu(item, c)
                )
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()

        elif col_id in ("name", "note"):
            # Select the row, show a small context menu with Edit option
            self._tree.selection_set(item)
            label = "Edit Name" if col_id == "name" else "Edit Note"
            menu = tk.Menu(self.root, tearoff=0, bg=PANEL, fg=TEXT,
                           activebackground=SEL_BG, activeforeground=TEXT,
                           relief="flat", bd=0, font=F_MAIN)
            menu.add_command(
                label=f"✎  {label}",
                command=lambda: self._start_inline(item, col_id)
            )
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()

    def _apply_color_from_menu(self, clicked_item: str, new_color: str):
        """Apply a color chosen from the right-click context menu to all selected markers."""
        sel = self._tree.selection()
        # Fall back to just the clicked item if selection is somehow empty
        if not sel:
            sel = (clicked_item,)

        errors = []
        for item in sel:
            if not self._tree.exists(item):
                continue
            rec = self._by_id.get(item)
            if not rec or new_color == rec["color"]:
                continue
            ok, err = self._write_marker(rec, new_color, rec["name"],
                                         rec["note"], rec["duration"], "")
            if ok:
                rec["color"] = new_color
                col_idx = COL_IDS.index("color")
                values  = list(self._tree.item(item, "values"))
                values[col_idx] = new_color
                tag_type  = "tl_row" if rec["type"] == "Timeline" else "clip_row"
                tag_color = f"c_{new_color.lower()}"
                self._tree.item(item, image=self._color_imgs.get(new_color, self._color_imgs[""]),
                                values=values, tags=(tag_type, tag_color))
            else:
                errors.append(f"Frame {rec['timeline_frame']}: {err}")

        if errors:
            detail = "\n".join(errors[:5])
            if len(errors) > 5:
                detail += f"\n… and {len(errors) - 5} more"
            self._mb(messagebox.showerror, "Error", f"Could not update some markers:\n\n{detail}")
            self._refresh()

    def _start_inline(self, item: str, col_id: str):
        self._click_job = None
        if not self._tree.exists(item):
            return
        bbox = self._tree.bbox(item, COL_NUM[col_id])
        if not bbox:
            return
        x, y, w, h = bbox
        col_idx = COL_IDS.index(col_id)
        current = self._tree.item(item, "values")[col_idx]

        self._inline_item = item
        self._inline_col  = col_id

        var = tk.StringVar(value=current)

        if col_id == "color":
            # Color column — show a readonly Combobox that drops down immediately
            widget = ttk.Combobox(self._tree, textvariable=var,
                                  values=MARKER_COLORS, state="readonly",
                                  font=F_MAIN)
            widget.place(x=x, y=y, width=max(w, 110), height=h)
            widget.focus_set()
            widget.bind("<<ComboboxSelected>>", lambda _: self._save_inline(var.get()))
            widget.bind("<Escape>", lambda _: self._close_inline())
            widget.bind("<FocusOut>",
                        lambda _: self.root.after(150, lambda: self._close_inline()))
            # Auto-open the dropdown after the widget is placed
            self.root.after(10, lambda: widget.event_generate("<Down>"))
        else:
            # Text columns — plain Entry
            original = current
            widget = tk.Entry(self._tree, textvariable=var, relief="flat",
                              bg=ENTRY_BG, fg=TEXT, insertbackground=TEXT,
                              font=F_MAIN, bd=0)
            widget.place(x=x, y=y, width=w, height=h)
            widget.select_range(0, "end")
            widget.focus_set()
            widget.bind("<Return>",    lambda e: self._save_inline(var.get()))
            widget.bind("<KP_Enter>",  lambda e: self._save_inline(var.get()))
            widget.bind("<Tab>",       lambda e: self._save_inline(var.get()))
            widget.bind("<Escape>",    lambda e: self._close_inline())
            widget.bind("<Up>",   lambda e: widget.icursor(0) or widget.xview_moveto(0) or "break")
            widget.bind("<Down>", lambda e: widget.icursor("end") or widget.xview_moveto(1) or "break")
            widget.bind("<Command-z>", lambda e: (var.set(original), widget.icursor("end")))
            widget.bind("<FocusOut>",
                        lambda e: self.root.after(50, lambda: self._save_inline(var.get())))

        self._inline_widget = widget

    def _save_inline(self, new_value: str):
        item   = self._inline_item
        col_id = self._inline_col
        self._close_inline()
        if not item or not col_id:
            return
        if not self._tree.exists(item):
            return

        rec = self._by_id.get(item)
        if not rec:
            return

        col_idx = COL_IDS.index(col_id)
        values  = list(self._tree.item(item, "values"))
        if new_value == values[col_idx]:
            return
        values[col_idx] = new_value
        self._tree.item(item, values=values)

        # Determine the new field values for each editable column
        note      = values[COL_IDS.index("note")]
        new_color = new_value if col_id == "color" else rec["color"]
        new_name  = new_value if col_id == "name"  else rec["name"]
        new_note  = note      if col_id == "note"   else rec["note"]

        ok, err = self._write_marker(rec,
                                     color=new_color, name=new_name,
                                     note=new_note, duration=rec["duration"],
                                     custom="")
        if ok:
            rec["color"] = new_color
            rec["name"]  = new_name
            rec["note"]  = new_note
            if col_id == "color":
                tag_type  = "tl_row" if rec["type"] == "Timeline" else "clip_row"
                tag_color = f"c_{new_color.lower()}"
                self._tree.item(item,
                                image=self._color_imgs.get(new_color, self._color_imgs[""]),
                                tags=(tag_type, tag_color))
        else:
            self._mb(messagebox.showerror, "Error", f"Could not update marker in Resolve.\n\n{err}")
            self._refresh()

    def _close_inline(self):
        if self._inline_widget:
            try:
                self._inline_widget.destroy()
            except Exception:
                pass
            self._inline_widget = None
        self._inline_item = None
        self._inline_col  = None
        # Don't steal focus from the search entry while the user is typing
        try:
            if self.root.focus_displayof() is not self._search_entry:
                self._tree.focus_set()
        except Exception:
            self._tree.focus_set()

    # ── Selection → preview info ──────────────────────────────────────────

    def _on_sel_change(self, _=None):
        sel = self._tree.selection()
        if len(sel) == 1:
            rec = self._by_id.get(sel[0], {})
            tc  = frames_to_tc(rec.get("timeline_frame", 0) + self._start_frame, self._fps)
            info = f"{rec.get('type','')}  ·  {tc}"
            if rec.get("name"):
                info += f"\n{rec['name']}"
            if rec.get("clip_name"):
                info += f"\nClip: {rec['clip_name']}"
            self._prev_info.set(info)
            if self._autojump_var.get():
                self._seek_to_marker(rec)
        else:
            self._prev_info.set(f"{len(sel)} markers selected" if sel else "")

        # Cancel any pending auto-grab (kept so it can't fire from a stale click)
        if self._autograb_job:
            self.root.after_cancel(self._autograb_job)
            self._autograb_job = None

        # Update promote/demote buttons
        has_clip = has_tl = False
        for i in sel:
            t = self._by_id.get(i, {}).get("type")
            if t == "Clip":     has_clip = True
            elif t == "Timeline": has_tl = True
            if has_clip and has_tl:
                break
        self._btn_copy.config(state="normal" if has_clip else "disabled")
        self._btn_move.config(state="normal" if has_clip else "disabled")
        self._btn_copy_clip.config(state="normal" if has_tl else "disabled")
        self._btn_move_clip.config(state="normal" if has_tl else "disabled")

        # Refresh selected count in status bar
        cur = self._count_var.get()
        base = cur.split("  ·  selected")[0] if "  ·  selected" in cur else cur
        # Strip any previous "· N selected" suffix
        parts = base.split("  ·  ")
        base = "  ·  ".join(p for p in parts if "selected" not in p)
        self._count_var.set(base + (f"  ·  {len(sel)} selected" if sel else ""))

    # ── Low-level marker write ────────────────────────────────────────────

    def _resolve_delete_marker(self, obj, frame_id):
        """Try all known Resolve API spellings for deleting a marker by frame.
        Resolve 21 uses DeleteMarkerAtFrame; older builds use other names.
        Returns (success, error_string)."""
        last_err = "no delete method found"
        for method_name in ("DeleteMarkerAtFrame", "DeleteMarkerByFrameId", "DeleteMarkerAtTime"):
            fn = getattr(obj, method_name, None)
            if fn is None:
                continue
            try:
                fn(frame_id)
                return True, ""
            except Exception as exc:
                last_err = str(exc)
        return False, f"Delete failed (tried all known method names): {last_err}"

    def _resolve_add_marker(self, obj, frame_id, color, name, note, duration, custom):
        """Call AddMarker on a timeline or clip item object.
        Returns (success, error_string)."""
        fn = getattr(obj, "AddMarker", None)
        if fn is None:
            return False, "AddMarker method not found on object — check Resolve scripting API."
        try:
            result = fn(frame_id, color, name, note, int(duration), custom)
            return bool(result), ("" if result else "AddMarker returned False")
        except Exception as exc:
            return False, str(exc)

    def _fresh_timeline(self):
        """Re-fetch a live timeline proxy every time. Returns (timeline, error_str)."""
        if not self._resolve:
            return None, "Not connected to Resolve."
        try:
            pm = self._resolve.GetProjectManager()
            if pm is None:
                return None, "GetProjectManager() returned None."
            proj = pm.GetCurrentProject()
            if proj is None:
                return None, "GetCurrentProject() returned None — is a project open?"
            tl = proj.GetCurrentTimeline()
            if tl is None:
                return None, "GetCurrentTimeline() returned None — is a timeline open?"
            self._timeline = tl
            self._project  = proj
            return tl, ""
        except Exception as exc:
            return None, str(exc)

    def _write_marker(self, rec, color, name, note, duration, custom):
        """Delete and recreate a marker (Resolve has no direct update API).
        Always re-fetches fresh proxies. Returns (success, error_message)."""
        timeline, err = self._fresh_timeline()
        if not timeline:
            return False, err

        if rec["type"] == "Timeline":
            frame_id = rec["timeline_frame"]
            self._resolve_delete_marker(timeline, frame_id)
            ok, err = self._resolve_add_marker(
                timeline, frame_id, color, name, note, duration, custom
            )
            return ok, err

        else:
            # Clip marker — re-scan tracks for a fresh item proxy
            tl_frame     = rec["timeline_frame"]
            marker_frame = rec["marker_frame"]
            target_item  = self._find_clip_at_frame(timeline, tl_frame)
            if target_item is None:
                return False, (
                    f"No clip found at timeline frame {tl_frame}. "
                    "Try Refresh and retry."
                )
            self._resolve_delete_marker(target_item, marker_frame)
            ok, err = self._resolve_add_marker(
                target_item, marker_frame, color, name, note, duration, custom
            )
            if ok:
                rec["timeline_item"] = target_item
            return ok, err

    def _find_clip_at_frame(self, timeline, tl_frame, track_type=None, track_index=None):
        """Return the first TimelineItem spanning tl_frame.
        If track_type and track_index are given, only that track is searched."""
        try:
            types = [track_type] if track_type else ["video", "audio"]
            for ttype in types:
                start = track_index if track_index else 1
                end   = (track_index + 1) if track_index else (timeline.GetTrackCount(ttype) + 1)
                for ti in range(start, end):
                    items = timeline.GetItemListInTrack(ttype, ti)
                    if not items:
                        continue
                    for item in items:
                        try:
                            abs_frame = tl_frame + self._start_frame
                            if item.GetStart() <= abs_frame < item.GetEnd():
                                return item
                        except Exception:
                            continue
        except Exception:
            pass
        return None

    def _get_tracks_at_frames(self, timeline, tl_frames: set) -> list:
        """Return list of (track_type, track_index, clip_count, clip_names_list)
        for every track that has a clip covering at least one frame in tl_frames."""
        results = []
        try:
            for ttype in ("video", "audio"):
                count = timeline.GetTrackCount(ttype)
                for ti in range(1, count + 1):
                    items = timeline.GetItemListInTrack(ttype, ti)
                    if not items:
                        continue
                    names = []
                    for item in items:
                        try:
                            if any(item.GetStart() <= f + self._start_frame < item.GetEnd()
                                   for f in tl_frames):
                                n = item.GetName()
                                if n not in names:
                                    names.append(n)
                        except Exception:
                            continue
                    if names:
                        results.append((ttype, ti, len(names), names))
        except Exception:
            pass
        return results



    def _current_tc(self):
        """Return the current playhead timecode string from Resolve, or ''."""
        try:
            tl, _ = self._fresh_timeline()
            return tl.GetCurrentTimecode() or "" if tl else ""
        except Exception:
            return ""

    def _add_marker(self):
        timeline, err = self._fresh_timeline()
        if not timeline:
            self._mb(messagebox.showwarning, "Not connected", err)
            return

        # Pass a live callable so the dialog's Refresh Position button works.
        try:
            tc_str = timeline.GetCurrentTimecode() or ""
            abs_frame = tc_to_frames(tc_str, self._fps) if tc_str else self._start_frame
        except Exception:
            abs_frame = self._start_frame

        dlg = MarkerDialog(self.root, "Add Marker", self._fps,
                           frame=abs_frame, get_tc_fn=self._current_tc)
        self.root.wait_window(dlg)
        if dlg.result is None:
            return

        r = dlg.result
        tl_frame = r["frame"] - self._start_frame  # 0-based timeline frame

        # Always re-fetch a fresh timeline after dialog interaction — the
        # Refresh Position button internally calls _fresh_timeline(), which
        # can invalidate the proxy we fetched before the dialog opened.
        timeline, err = self._fresh_timeline()
        if not timeline:
            self._mb(messagebox.showwarning, "Not connected", err)
            return

        if r["target"] == "timeline":
            self._add_marker_to_timeline(timeline, tl_frame, r)
        elif r["target"] == "clip_auto":
            self._add_marker_to_clip_auto(timeline, tl_frame, r)
        else:  # clip_pick
            self._add_marker_to_clip_pick(timeline, tl_frame, r)

    def _add_marker_to_timeline(self, timeline, tl_frame, r):
        ok, err = self._resolve_add_marker(
            timeline, tl_frame, r["color"], r["name"], r["note"], r["duration"], ""
        )
        if ok:
            self._main_undo_stack.append(("add_timeline", [(timeline, tl_frame)]))
            self._main_undo_btn.config(bg=ACCENT, fg=BG)
            self._refresh()
        else:
            if tl_frame in self._tl_frames:
                self._mb(messagebox.showerror, "Conflict",
                    "A timeline marker already exists at that position.\n"
                    "Delete it first or move the playhead.")
            else:
                self._mb(messagebox.showerror, "Error",
                    f"Resolve could not add the marker.\n\n{err}")

    def _add_marker_to_clip_auto(self, timeline, tl_frame, r):
        """Add marker to the first clip found at tl_frame (V1 → VN scan)."""
        item = self._find_clip_at_frame(timeline, tl_frame, track_type="video")
        if item is None:
            item = self._find_clip_at_frame(timeline, tl_frame, track_type="audio")
        if item is None:
            self._mb(messagebox.showwarning, "No Clip Found",
                "No clip at the current playhead position.\n"
                "Try 'Pick Track' to choose a specific track.")
            return
        self._add_marker_to_clip_item(item, tl_frame, r)

    def _add_marker_to_clip_pick(self, timeline, tl_frame, r):
        """Show TrackPickDialog then add marker to the chosen clip."""
        available = self._get_tracks_at_frames(timeline, {tl_frame})
        if not available:
            self._mb(messagebox.showwarning, "No Clips Found",
                "No clips at the current playhead position.")
            return
        dlg = TrackPickDialog(self.root, available)
        self.root.wait_window(dlg)
        if dlg.result is None:
            return
        chosen_type, chosen_idx, frame_offset, chosen_color = dlg.result

        # Re-fetch a fresh timeline proxy — the original may be stale after
        # the user interacted with the dialog (Resolve can invalidate proxies).
        timeline, err = self._fresh_timeline()
        if not timeline:
            self._mb(messagebox.showwarning, "Not connected", err)
            return

        item = self._find_clip_at_frame(timeline, tl_frame,
                                        track_type=chosen_type, track_index=chosen_idx)
        if item is None:
            self._mb(messagebox.showwarning, "Not Found",
                "No clip on that track at the playhead position.")
            return
        if chosen_color != "Original":
            r = dict(r, color=chosen_color)
        self._add_marker_to_clip_item(item, tl_frame, r, frame_offset=frame_offset)

    def _add_marker_to_clip_item(self, item, tl_frame, r, frame_offset=0):
        """Common tail: compute clip_offset, optionally apply frame_offset, add marker."""
        try:
            left_offset = item.GetLeftOffset()
        except Exception:
            left_offset = 0
        try:
            abs_frame   = tl_frame + self._start_frame
            clip_offset = abs_frame - item.GetStart() + left_offset
        except Exception as exc:
            self._mb(messagebox.showerror, "Error",
                f"Could not read clip position — this clip type may not support markers.\n\n{exc}")
            return
        if frame_offset != 0:
            try:
                clip_dur       = item.GetDuration()
                frames_from_in = clip_offset - left_offset
                frames_from_in = max(0, min(frames_from_in + frame_offset, clip_dur - 1))
                clip_offset    = left_offset + frames_from_in
            except Exception:
                clip_offset = max(left_offset, clip_offset + frame_offset)
        ok, err = self._resolve_add_marker(
            item, clip_offset, r["color"], r["name"], r["note"], r["duration"], ""
        )
        if ok:
            self._main_undo_stack.append(("add_clip", [(item, clip_offset)]))
            self._main_undo_btn.config(bg=ACCENT, fg=BG)
            self._refresh()
        else:
            self._mb(messagebox.showerror, "Error",
                f"Could not add clip marker — this clip type may not support markers.\n\n{err}")

    def _edit_marker(self):
        sel = self._tree.selection()
        if not sel:
            self._mb(messagebox.showinfo, "Edit Marker", "Select a marker to edit first.")
            return
        rec = self._by_id.get(sel[0])
        if not rec:
            return
        dlg = MarkerDialog(self.root, f"Edit {rec['type']} Marker", self._fps,
                           marker_type=rec["type"],
                           frame=rec["timeline_frame"] + self._start_frame,
                           color=rec["color"], name=rec["name"],
                           note=rec["note"], duration=rec["duration"])
        self.root.wait_window(dlg)
        if dlg.result is None:
            return
        r = dlg.result
        ok, err = self._write_marker(rec, r["color"], r["name"],
                                     r["note"], r["duration"], "")
        if ok:
            self._refresh()
        else:
            self._mb(messagebox.showerror, "Error", f"Resolve could not update the marker.\n\n{err}")

    def _toolbar_color_selected(self, _=None):
        """Called when the user picks a color from the toolbar combobox."""
        new_color = self._toolbar_color_var.get()
        # Reset the display text after a short delay so it doesn't look "stuck"
        self.root.after(200, lambda: self._toolbar_color_var.set("Select Color"))
        sel = self._tree.selection()
        if not sel:
            self._mb(messagebox.showinfo, "Change Color", "Select one or more markers first.")
            return
        errors = []
        for iid in list(sel):
            rec = self._by_id.get(iid)
            if not rec:
                continue
            ok, err = self._write_marker(rec, new_color, rec["name"],
                                         rec["note"], rec["duration"], "")
            if not ok:
                errors.append(f"Frame {rec['timeline_frame']}: {err}")
        self._refresh()
        if errors:
            detail = "\n".join(errors[:5])
            if len(errors) > 5:
                detail += f"\n… and {len(errors) - 5} more"
            self._mb(messagebox.showwarning, "Color Change — Partial Failure",
                     f"{len(errors)} marker(s) could not be updated:\n\n{detail}")

    def _delete_marker(self):
        sel = self._tree.selection()
        if not sel:
            self._mb(messagebox.showinfo, "Delete", "Select one or more markers to delete.")
            return
        count = len(sel)
        if not self._no_prompt_delete_var.get():
            label = (f"marker \"{self._by_id.get(sel[0], {}).get('name', sel[0])}\""
                     if count == 1 else f"{count} markers")
            if not self._mb(messagebox.askyesno, "Delete",
                            f"Delete {label}?\n\nThis cannot be undone."):
                return

        timeline, err = self._fresh_timeline()
        if not timeline:
            self._mb(messagebox.showwarning, "Not connected", err)
            return

        phantom = 0
        for iid in sel:
            rec = self._by_id.get(iid)
            if not rec:
                continue
            if rec["type"] == "Timeline":
                self._resolve_delete_marker(timeline, rec["timeline_frame"])
            else:
                # Use the stored timeline_item reference — it knows exactly
                # which track (video or audio) owns this marker.
                item = rec.get("timeline_item")
                if item is None:
                    item = self._find_clip_at_frame(timeline, rec["timeline_frame"])
                if item:
                    existing = {}
                    try:
                        existing = item.GetMarkers() or {}
                    except Exception:
                        pass
                    if rec["marker_frame"] in existing:
                        self._resolve_delete_marker(item, rec["marker_frame"])
                    else:
                        phantom += 1
                else:
                    phantom += 1
        if phantom:
            self._mb(messagebox.showinfo, "Delete",
                f"{phantom} marker{'s' if phantom > 1 else ''} could not be deleted — "
                f"likely a source media marker not owned by this timeline.")
        self._refresh()

    def _delete_all(self):
        if not self._all_markers:
            self._mb(messagebox.showinfo, "Delete All", "No markers to delete.")
            return
        color_f = self._filter_color.get()
        type_f  = self._filter_type.get()
        targets = [
            r for r in self._all_markers
            if (color_f == "All" or r["color"] == color_f)
            and (type_f == "All Types" or r["type"] == type_f)
        ]
        if not targets:
            self._mb(messagebox.showinfo, "Delete All", "No markers match the current filters.")
            return
        tl_n   = sum(1 for r in targets if r["type"] == "Timeline")
        clip_n = len(targets) - tl_n
        detail = []
        if tl_n:
            detail.append(f"{tl_n} timeline")
        if clip_n:
            detail.append(f"{clip_n} clip")
        if not self._mb(messagebox.askyesno, "Delete All",
                        f"Delete {' + '.join(detail)} marker(s)?\n"
                        "This cannot be undone."):
            return

        timeline, err = self._fresh_timeline()
        if not timeline:
            self._mb(messagebox.showwarning, "Not connected", err)
            return

        for rec in targets:
            if rec["type"] == "Timeline":
                self._resolve_delete_marker(timeline, rec["timeline_frame"])
            else:
                item = rec.get("timeline_item") or self._find_clip_at_frame(timeline, rec["timeline_frame"])
                if item:
                    self._resolve_delete_marker(item, rec["marker_frame"])
        self._refresh()

    # ── Promote: copy / move clip markers to timeline ─────────────────────

    def _promote(self, move: bool):
        sel = self._tree.selection()
        clips = [self._by_id[iid] for iid in sel
                 if self._by_id.get(iid, {}).get("type") == "Clip"]
        if not clips:
            self._mb(messagebox.showinfo, "Promote", "Select one or more clip markers first.")
            return

        timeline, err = self._fresh_timeline()
        if not timeline:
            self._mb(messagebox.showwarning, "Not connected", err)
            return

        # Show offset + color picker
        label = "Move to Timeline" if move else "Copy to Timeline"
        dlg = PromoteOptionsDialog(self.root, action_label=label)
        self.root.wait_window(dlg)
        if dlg.result is None:
            return
        frame_offset, chosen_color = dlg.result

        conflicts = [r for r in clips
                     if (r["timeline_frame"] + frame_offset) in self._tl_frames]
        overwrite = False
        if conflicts:
            ans = self._mb(messagebox.askyesnocancel,
                "Conflicts Found",
                f"{len(conflicts)} frame position(s) already have a timeline marker.\n\n"
                "Yes  = overwrite the existing timeline marker\n"
                "No   = skip conflicting frames\n"
                "Cancel = abort"
            )
            if ans is None:
                return
            overwrite = ans

        action = "Moving" if move else "Copying"
        added = skipped = failed = 0
        undo_batch = []

        for rec in clips:
            tl_frame = rec["timeline_frame"] + frame_offset
            if tl_frame in self._tl_frames:
                if not overwrite:
                    skipped += 1
                    continue
                self._resolve_delete_marker(timeline, tl_frame)
                self._tl_frames.discard(tl_frame)

            use_color = rec["color"] if chosen_color == "Original" else chosen_color
            ok, _err = self._resolve_add_marker(
                timeline, tl_frame, use_color, rec["name"],
                rec["note"], rec["duration"], ""
            )
            if ok:
                added += 1
                self._tl_frames.add(tl_frame)
                clip_item = rec.get("timeline_item")
                if move and clip_item:
                    self._resolve_delete_marker(clip_item, rec["marker_frame"])
                undo_batch.append(("tl_marker", timeline, tl_frame, move,
                                   clip_item, rec["marker_frame"], rec))
            else:
                failed += 1

        if undo_batch:
            self._main_undo_stack.append(("promote", undo_batch))
            self._main_undo_btn.config(bg=ACCENT, fg=BG)

        self._refresh()
        msg = f"{action} complete.\n\nAdded to timeline: {added}"
        if skipped:
            msg += f"\nSkipped (conflict): {skipped}"
        if failed:
            msg += f"\nFailed: {failed}"
        self._mb(messagebox.showinfo, f"{action} Complete", msg)

    # ── Demote: copy / move timeline markers to a clip ────────────────────

    def _demote(self, move: bool):
        """Copy or move selected timeline markers onto a clip in a chosen track."""
        sel = self._tree.selection()
        tl_markers = [self._by_id[iid] for iid in sel
                      if self._by_id.get(iid, {}).get("type") == "Timeline"]
        if not tl_markers:
            self._mb(messagebox.showinfo, "Demote", "Select one or more timeline markers first.")
            return

        timeline, err = self._fresh_timeline()
        if not timeline:
            self._mb(messagebox.showwarning, "Not connected", err)
            return

        # ── Find which tracks actually have clips at the selected frames ──
        tl_frames = {r["timeline_frame"] for r in tl_markers}
        available_tracks = self._get_tracks_at_frames(timeline, tl_frames)

        if not available_tracks:
            self._mb(messagebox.showwarning,
                "No Clips Found",
                "None of the selected marker positions have a clip on any track.\n"
                "Make sure your timeline has clips at those timecodes."
            )
            return

        # ── Show the single upfront track picker ─────────────────────────
        dlg = TrackPickDialog(self.root, available_tracks)
        self.root.wait_window(dlg)
        if dlg.result is None:
            return
        chosen_type, chosen_idx, frame_offset, chosen_color = dlg.result

        action = "Moving" if move else "Copying"
        added = skipped = failed = 0
        undo_batch = []

        for rec in tl_markers:
            tl_frame = rec["timeline_frame"]
            item = self._find_clip_at_frame(timeline, tl_frame,
                                            track_type=chosen_type,
                                            track_index=chosen_idx)
            if item is None:
                skipped += 1
                continue

            try:
                left_offset = item.GetLeftOffset()
            except Exception:
                left_offset = 0

            clip_offset = (tl_frame + self._start_frame - item.GetStart()) + left_offset

            # Apply user-requested frame offset.
            # clip_offset is in source-frame space; clamp within [left_offset,
            # left_offset + clip_dur - 1] to stay inside the clip's in/out.
            if frame_offset != 0:
                try:
                    clip_dur        = item.GetDuration()
                    frames_from_in  = clip_offset - left_offset
                    frames_from_in  = max(0, min(frames_from_in + frame_offset,
                                                  clip_dur - 1))
                    clip_offset     = left_offset + frames_from_in
                except Exception:
                    clip_offset = max(left_offset, clip_offset + frame_offset)

            # Skip if clip already has a marker at this offset
            try:
                existing = item.GetMarkers() or {}
            except Exception:
                existing = {}
            if clip_offset in existing:
                skipped += 1
                continue

            use_color = rec["color"] if chosen_color == "Original" else chosen_color
            ok, _err = self._resolve_add_marker(
                item, clip_offset, use_color, rec["name"],
                rec["note"], rec["duration"], ""
            )
            if ok:
                added += 1
                undo_batch.append(("clip_marker", item, clip_offset, move,
                                   timeline, tl_frame, rec))
                if move:
                    self._resolve_delete_marker(timeline, tl_frame)
            else:
                failed += 1

        if undo_batch:
            self._main_undo_stack.append(("demote", undo_batch))
            self._main_undo_btn.config(bg=ACCENT, fg=BG)

        self._refresh()
        track_label = f"{'V' if chosen_type == 'video' else 'A'}{chosen_idx}"
        msg = f"{action} complete  →  Track {track_label}\n\nAdded to clip: {added}"
        if skipped:
            msg += f"\nSkipped (no clip on track / conflict): {skipped}"
        if failed:
            msg += f"\nFailed: {failed}"
        self._mb(messagebox.showinfo, f"{action} Complete", msg)

    # ── Nudge markers ─────────────────────────────────────────────────────

    def _nudge_markers(self):
        """Move selected markers forward or backward by the nudge spinbox value."""
        offset = self._nudge_var.get()
        if offset == 0:
            return
        sel = self._tree.selection()
        if not sel:
            self._mb(messagebox.showinfo, "Nudge", "Select one or more markers first.")
            return
        timeline, err = self._fresh_timeline()
        if not timeline:
            self._mb(messagebox.showwarning, "Not connected", err)
            return

        moved = skipped = 0
        undo_batch = []

        for iid in sel:
            rec = self._by_id.get(iid)
            if not rec:
                continue

            if rec["type"] == "Timeline":
                old_frame = rec["timeline_frame"]
                new_frame = old_frame + offset
                if new_frame < 0:
                    skipped += 1
                    continue
                if new_frame in self._tl_frames and new_frame != old_frame:
                    skipped += 1
                    continue
                ok, _ = self._resolve_add_marker(
                    timeline, new_frame, rec["color"], rec["name"],
                    rec["note"], rec["duration"], ""
                )
                if ok:
                    self._resolve_delete_marker(timeline, old_frame)
                    undo_batch.append(("tl", old_frame, new_frame, rec))
                    moved += 1
                else:
                    skipped += 1

            else:  # Clip marker
                item = rec.get("timeline_item")
                if item is None:
                    skipped += 1
                    continue
                old_mf = rec["marker_frame"]
                new_mf = old_mf + offset
                new_mf = max(0, new_mf)
                try:
                    existing = item.GetMarkers() or {}
                except Exception:
                    existing = {}
                if new_mf in existing and new_mf != old_mf:
                    skipped += 1
                    continue
                ok, _ = self._resolve_add_marker(
                    item, new_mf, rec["color"], rec["name"],
                    rec["note"], rec["duration"], ""
                )
                if ok:
                    self._resolve_delete_marker(item, old_mf)
                    undo_batch.append(("clip", old_mf, new_mf, rec, item))
                    moved += 1
                else:
                    skipped += 1

        if undo_batch:
            self._main_undo_stack.append(("nudge", undo_batch))
            self._main_undo_btn.config(bg=ACCENT, fg=BG)

        self._refresh()
        if not self._nudge_auto_var.get():
            msg = f"Nudged {moved} marker{'s' if moved != 1 else ''} by {offset:+d} frames."
            if skipped:
                msg += f"\nSkipped {skipped} (conflict or out of range)."
            self._mb(messagebox.showinfo, "Nudge Complete", msg)

    # ── Main window undo ──────────────────────────────────────────────────

    def _main_undo(self):
        if not self._main_undo_stack:
            return
        timeline, err = self._fresh_timeline()
        if not timeline:
            self._mb(messagebox.showwarning, "Not connected", err)
            return

        op_type, batch = self._main_undo_stack.pop()

        if op_type == "demote":
            for (_, item, clip_offset, was_move, tl, tl_frame, rec) in batch:
                self._resolve_delete_marker(item, clip_offset)
                if was_move:
                    self._resolve_add_marker(
                        tl, tl_frame, rec["color"], rec["name"],
                        rec["note"], rec["duration"], ""
                    )

        elif op_type == "promote":
            for (_, tl, tl_frame, was_move, clip_item, clip_mf, rec) in batch:
                self._resolve_delete_marker(tl, tl_frame)
                if was_move and clip_item:
                    self._resolve_add_marker(
                        clip_item, clip_mf, rec["color"], rec["name"],
                        rec["note"], rec["duration"], ""
                    )

        elif op_type == "add_timeline":
            for (tl, tl_frame) in batch:
                self._resolve_delete_marker(tl, tl_frame)

        elif op_type == "add_clip":
            for (item, clip_offset) in batch:
                self._resolve_delete_marker(item, clip_offset)

        elif op_type == "nudge":
            for entry in batch:
                if entry[0] == "tl":
                    _, old_frame, new_frame, rec = entry
                    self._resolve_add_marker(
                        timeline, old_frame, rec["color"], rec["name"],
                        rec["note"], rec["duration"], ""
                    )
                    self._resolve_delete_marker(timeline, new_frame)
                else:
                    _, old_mf, new_mf, rec, item = entry
                    self._resolve_add_marker(
                        item, old_mf, rec["color"], rec["name"],
                        rec["note"], rec["duration"], ""
                    )
                    self._resolve_delete_marker(item, new_mf)

        if not self._main_undo_stack:
            self._main_undo_btn.config(bg=BTN_HOV, fg=DIM)
        self._refresh()

    # ── Batch frame export ────────────────────────────────────────────────

    def _grab_then_export_stills(self, targets, dest_dir, prefix_base, progress, fmt="png"):
        """
        Two-phase still export:
          Phase 1 — seek to each marker and grab a still into the gallery (fast).
          Phase 2 — export each still one at a time with retry, return-value
                    checking, and a 2-second pause between exports (reliable).

        Returns:
          results: list of (rec, idx, found_file_path_or_None, still_or_None)
          album:   the gallery still album used (so caller can DeleteStills)
        """
        total = len(targets)
        album = None
        try:
            album = self._project.GetGallery().GetCurrentStillAlbum()
        except Exception:
            pass

        if not album:
            return [(rec, i, None, None) for i, rec in enumerate(targets)], None

        # ── Phase 1: grab all stills quickly ───────────────────────────────
        grabbed = []   # list of (rec, idx, still_or_None)
        for i, rec in enumerate(targets):
            if progress.cancelled:
                grabbed.append((rec, i, None))
                continue
            progress.update_progress(i, f"Grabbing {i+1} / {total}  {rec.get('name', '')[:40]}")
            self._seek_to_marker(rec)
            try:
                still = self._timeline.GrabStill()
            except Exception:
                still = None
            grabbed.append((rec, i, still))

        progress.set_phase("Exporting frames…")
        # ── Phase 2: export each still one at a time, slowly ───────────────
        results = []
        for j, (rec, i, still) in enumerate(grabbed):
            if progress.cancelled or not still:
                results.append((rec, i, None, still))
                continue

            progress.update_progress(j + 1, f"Exporting {j+1} / {total}  {rec.get('name', '')[:40]}")

            unique_prefix = f"{prefix_base}{i:04d}_"
            found_file = None

            for attempt in range(2):   # one initial try + one retry
                try:
                    ok = album.ExportStills([still], dest_dir, unique_prefix, fmt)
                except Exception:
                    ok = False

                if ok is False:
                    self.root.update()
                    time.sleep(0.6)
                    continue

                deadline = time.time() + 10.0
                while time.time() < deadline:
                    matches = glob.glob(os.path.join(dest_dir, f"{unique_prefix}*.{fmt}"))
                    if not matches and fmt == "tif":
                        matches = glob.glob(os.path.join(dest_dir, f"{unique_prefix}*.tiff"))
                    if matches:
                        found_file = matches[0]
                        break
                    self.root.update()
                    time.sleep(0.15)

                if found_file:
                    break

            results.append((rec, i, found_file, still))

            # 0.7-second pause before next export (skip after last)
            if j < len(grabbed) - 1 and not progress.cancelled:
                elapsed = 0.0
                while elapsed < 0.7:
                    if progress.cancelled:
                        break
                    self.root.update()
                    time.sleep(0.1)
                    elapsed += 0.1

        return results, album

    def _get_filtered_markers(self):
        """Return (visible, selected) marker lists respecting current filters and search."""
        color_f  = self._filter_color.get()
        type_f   = self._filter_type.get()
        search_f = self._search_var.get().strip().lower()
        sel_ids  = set(self._tree.selection())

        visible = [
            r for r in sorted(self._all_markers, key=lambda r: r["timeline_frame"])
            if (color_f == "All" or r["color"] == color_f)
            and (type_f == "All Types" or r["type"] == type_f)
            and (not search_f or search_f in " ".join([
                r.get("name", ""), r.get("note", ""), r.get("clip_name", "")
            ]).lower())
        ]
        selected = [r for r in visible if r["id"] in sel_ids]
        return visible, selected

    def _batch_export_full_res_frames(self):
        """Grab and export a PNG frame for every visible or selected marker."""
        if not self._all_markers:
            self._mb(messagebox.showinfo, "Batch Export", "No markers to export.")
            return
        if not self._timeline or not self._project:
            self._mb(messagebox.showwarning, "Not connected", "No timeline is active.")
            return

        visible, selected = self._get_filtered_markers()

        if not visible:
            self._mb(messagebox.showinfo, "Batch Export", "No markers match the current filters.")
            return

        dlg = BatchExportOptionsDialog(self.root, len(visible), len(selected),
                                       )
        self.root.wait_window(dlg)
        if dlg.result is None:
            return

        targets      = selected if dlg.result["scope"] == "selected" else visible
        name_only    = dlg.result["name_only"]
        keep_drx     = dlg.result["keep_drx"]
        fmt          = dlg.result.get("fmt", "png")
        jpeg_quality = dlg.result.get("jpeg_quality")
        ext          = fmt  # file extension matches Resolve's format string

        if not targets:
            self._mb(messagebox.showinfo, "Batch Export", "No markers in the selected scope.")
            return

        if self._stay_on_top_var.get():
            self.root.attributes("-topmost", False)
        out_dir = filedialog.askdirectory(title="Choose folder for exported frames")
        if self._stay_on_top_var.get():
            self.root.attributes("-topmost", True)
        if not out_dir:
            return

        total    = len(targets)
        progress = BatchExportDialog(self.root, total)
        self.root.update_idletasks()

        current_page = None
        try:
            current_page = self._resolve.GetCurrentPage()
        except Exception:
            pass

        results, album = self._grab_then_export_stills(
            targets, out_dir, "mm_batch", progress, fmt=fmt)

        exported = failed = 0
        failed_names = []
        stills_to_delete = [s for _, _, _, s in results if s]

        for rec, i, found_file, _still in results:
            if not found_file:
                failed += 1
                failed_names.append(rec.get("name", "").strip()
                                    or f"frame {rec['timeline_frame']}")
                continue

            tc_label = frames_to_tc(rec["timeline_frame"] + self._start_frame, self._fps)
            if name_only:
                raw   = rec.get("name", "").strip() or f"frame_{rec['timeline_frame']}"
                slug  = "".join(c if c.isalnum() or c in " -_" else "_" for c in raw)
                fname = f"{slug}.{ext}"
            else:
                tc_safe = tc_label.replace(":", "-")
                slug    = rec.get("name", "").strip() or f"frame_{rec['timeline_frame']}"
                slug    = "".join(c if c.isalnum() or c in " -_" else "_" for c in slug)
                mtype   = "TL" if rec["type"] == "Timeline" else "Clip"
                fname   = f"{i+1:04d}_{mtype}_{tc_safe}_{slug}.{ext}"

            dest = os.path.join(out_dir, fname)
            try:
                shutil.move(found_file, dest)
                if fmt == "jpg" and jpeg_quality is not None:
                    try:
                        subprocess.run(
                            ["sips", "-s", "format", "jpeg",
                             "-s", "formatOptions", str(jpeg_quality),
                             dest, "--out", dest],
                            capture_output=True, timeout=30
                        )
                    except Exception:
                        pass
                exported += 1
            except Exception:
                failed += 1
                failed_names.append(rec.get("name", "").strip()
                                    or f"frame {rec['timeline_frame']}")

        # Clean up gallery all at once
        if not self._keep_gallery_var.get() and stills_to_delete and album:
            try:
                album.DeleteStills(stills_to_delete)
            except Exception:
                pass

        # Remove .DRX sidecar files unless the user asked to keep them
        if not keep_drx:
            for f in glob.glob(os.path.join(out_dir, "*.drx")):
                try:
                    os.remove(f)
                except Exception:
                    pass

        self._restore_page(current_page)
        progress.destroy()

        msg = f"Batch export complete.\n\nExported: {exported} / {total}"
        if failed:
            msg += f"\nFailed / skipped: {failed}"
            if failed_names:
                msg += "\n  • " + "\n  • ".join(failed_names[:8])
                if len(failed_names) > 8:
                    msg += f"\n  • … and {len(failed_names) - 8} more"
        if progress.cancelled:
            msg += "\n\n(Cancelled by user)"
        msg += f"\n\nSaved to:\n{out_dir}"
        self._mb(messagebox.showinfo, "Batch Export Complete", msg)

    def _export_csv(self):
        if not self._all_markers:
            self._mb(messagebox.showinfo, "Export", "No markers to export.")
            return

        visible, selected = self._get_filtered_markers()

        if not visible:
            self._mb(messagebox.showinfo, "Export", "No markers match the current filters.")
            return

        # Show export options dialog
        dlg = ExportOptionsDialog(self.root, len(visible), len(selected))
        self.root.wait_window(dlg)
        if dlg.result is None:
            return

        targets        = selected if dlg.result["scope"] == "selected" else visible
        include_frames = dlg.result["include_frames"]
        keep_drx       = dlg.result["keep_drx"]
        thumb_max_px   = dlg.result.get("thumb_max_px")
        thumb_fmt      = dlg.result.get("thumb_fmt", "png")
        jpeg_quality   = dlg.result.get("jpeg_quality")
        html_columns   = dlg.result.get("html_columns", {k for k, _ in HTML_COLUMNS})
        name_label     = dlg.result.get("name_label", "Name")

        if not targets:
            self._mb(messagebox.showinfo, "Export", "No markers in the selected scope.")
            return

        # File picker
        safe = "markers"
        if self._timeline:
            safe = "".join(c if c.isalnum() or c in " -_" else "_"
                           for c in self._timeline.GetName()) + "_markers"
        if self._stay_on_top_var.get():
            self.root.attributes("-topmost", False)
        path = filedialog.asksaveasfilename(
            title="Export Markers as CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"{safe}.csv",
        )
        if self._stay_on_top_var.get():
            self.root.attributes("-topmost", True)
        if not path:
            return

        # Set up thumbnails subfolder if requested
        thumb_dir = None
        thumb_map = {}
        if include_frames:
            if not self._timeline or not self._project:
                self._mb(messagebox.showwarning, "Not connected",
                         "No active timeline — cannot grab frames.")
                include_frames = False
            else:
                thumb_dir = os.path.join(os.path.dirname(path), "thumbnails")
                os.makedirs(thumb_dir, exist_ok=True)

        if include_frames and thumb_dir:
            # Re-fetch a fresh timeline proxy — the dialog chain above can stale the old one
            fresh_tl, tl_err = self._fresh_timeline()
            if fresh_tl:
                self._timeline = fresh_tl

            total    = len(targets)
            progress = BatchExportDialog(self.root, total)
            self.root.update_idletasks()

            current_page = None
            try:
                current_page = self._resolve.GetCurrentPage()
            except Exception:
                pass

            results, album = self._grab_then_export_stills(
                targets, thumb_dir, "mm_exp", progress, fmt=thumb_fmt)

            stills_to_delete = [s for _, _, _, s in results if s]

            for rec, i, found_file, _still in results:
                if not found_file:
                    continue
                tc_label = frames_to_tc(rec["timeline_frame"] + self._start_frame, self._fps)
                tc_safe  = tc_label.replace(":", "-")
                slug     = rec.get("name", "").strip() or f"frame_{rec['timeline_frame']}"
                slug     = "".join(c if c.isalnum() or c in " -_" else "_" for c in slug)
                mtype    = "TL" if rec["type"] == "Timeline" else "Clip"
                fname    = f"{i+1:04d}_{mtype}_{tc_safe}_{slug}.{thumb_fmt}"
                dest     = os.path.join(thumb_dir, fname)
                try:
                    shutil.move(found_file, dest)
                    sips_cmd = ["sips"]
                    if thumb_max_px:
                        sips_cmd += ["-Z", str(thumb_max_px)]
                    if thumb_fmt == "jpg" and jpeg_quality is not None:
                        sips_cmd += ["-s", "format", "jpeg",
                                     "-s", "formatOptions", str(jpeg_quality)]
                    if len(sips_cmd) > 1:
                        try:
                            subprocess.run(sips_cmd + [dest, "--out", dest],
                                           capture_output=True, timeout=30)
                        except Exception:
                            pass
                    thumb_map[rec["id"]] = os.path.join("thumbnails", fname)
                except Exception:
                    pass

            if not self._keep_gallery_var.get() and stills_to_delete and album:
                try:
                    album.DeleteStills(stills_to_delete)
                except Exception:
                    pass

            # Remove .DRX sidecar files unless the user asked to keep them
            if not keep_drx:
                for f in glob.glob(os.path.join(thumb_dir, "*.drx")):
                    try:
                        os.remove(f)
                    except Exception:
                        pass

            self._restore_page(current_page)
            progress.destroy()

        # Write CSV — column order follows the current display order in the table
        count = 0
        try:
            disp_cols = list(self._tree["displaycolumns"])
            if disp_cols == ["#all"]:
                disp_cols = list(COL_IDS)
            active_defs = [(cid, CSV_COL_DEF[cid]) for cid in disp_cols if cid in CSV_COL_DEF]

            with open(path, "w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                headers = [hdr for _, (hdr, _) in active_defs]
                if include_frames:
                    headers.append("ThumbnailPath")
                w.writerow(headers)
                for rec in targets:
                    row = [fn(rec, self._fps, self._start_frame) for _, (_, fn) in active_defs]
                    if include_frames:
                        row.append(thumb_map.get(rec["id"], ""))
                    w.writerow(row)
                    count += 1
            msg = f"Exported {count} marker{'s' if count != 1 else ''} to:\n{path}"
            if include_frames:
                grabbed = len(thumb_map)
                msg += f"\n\nThumbnails: {grabbed} / {count} saved to:\n{thumb_dir}"
                if thumb_map:
                    html_path = os.path.splitext(path)[0] + ".html"
                    tl_name = self._timeline.GetName() if self._timeline else "Markers"
                    # Build ordered HTML key list from display column order
                    disp = list(self._tree["displaycolumns"])
                    if disp == ["#all"]:
                        disp = list(COL_IDS)
                    ordered_html = []
                    if "thumbnail" in html_columns:
                        ordered_html.append("thumbnail")
                    for cid in disp:
                        hkey = DISPLAY_TO_HTML.get(cid)
                        if hkey and hkey in html_columns:
                            ordered_html.append(hkey)
                    self._write_html_report(html_path, targets, thumb_map, tl_name,
                                            columns=ordered_html,
                                            name_label=name_label)
                    msg += f"\n\nHTML report (open in browser to see images):\n{html_path}"
            self._mb(messagebox.showinfo, "Export Complete", msg)
        except Exception as exc:
            self._mb(messagebox.showerror, "Export Failed", str(exc))

    def _write_html_report(self, html_path, markers, thumb_map, timeline_name="Markers",
                           columns=None, name_label="Name"):
        # columns is an ordered list of HTML column keys; fall back to full default order
        if columns is None:
            columns = [k for k, _ in HTML_COLUMNS]

        html_col_labels = dict(HTML_COLUMNS)
        cell_styles = {
            "timecode": "font-family:monospace",
            "clip_in":  "font-family:monospace",
            "clip_out": "font-family:monospace",
            "dur_f":    "text-align:center",
            "dur_t":    "font-family:monospace",
        }

        def esc(s):
            return str(s).replace("&", "&amp;").replace("<", "&lt;")

        rows_html = []
        for rec in markers:
            thumb_rel = thumb_map.get(rec["id"], "")
            img_tag   = (f'<img src="{thumb_rel}" style="max-height:80px;border-radius:4px;">'
                         if thumb_rel else "")
            color   = rec.get("color", "")
            dot_hex = COLOR_HEX.get(color, "#888888")
            tc      = frames_to_tc(rec["timeline_frame"] + self._start_frame, self._fps)
            cif = rec.get("clip_in_frame")
            cof = rec.get("clip_out_frame")
            cdf = rec.get("clip_dur_frames")
            clip_in_tc  = frames_to_tc(cif + self._start_frame, self._fps) if cif is not None else ""
            clip_out_tc = frames_to_tc(cof + self._start_frame, self._fps) if cof is not None else ""
            clip_dur_f  = str(cdf)                    if cdf is not None else ""
            clip_dur_t  = frames_to_tc(cdf, self._fps) if cdf is not None else ""
            color_cell  = (f"<span style='display:inline-block;width:12px;height:12px;"
                           f"border-radius:50%;background:{dot_hex};margin-right:6px;"
                           f"vertical-align:middle'></span>{esc(color)}")
            cell_content = {
                "thumbnail": img_tag,
                "type":      esc(rec.get("type", "")),
                "timecode":  tc,
                "color":     color_cell,
                "name":      esc(rec.get("name", "")),
                "note":      esc(rec.get("note", "")),
                "clip":      esc(rec.get("clip_name", "")),
                "clip_in":   clip_in_tc,
                "clip_out":  clip_out_tc,
                "dur_f":     clip_dur_f,
                "dur_t":     clip_dur_t,
            }
            row = ""
            for key in columns:
                content = cell_content.get(key, "")
                style   = cell_styles.get(key, "")
                s = f" style='{style}'" if style else ""
                row += f"<td{s}>{content}</td>"
            rows_html.append(f"<tr>{row}</tr>")

        tl_safe  = esc(timeline_name)
        rows_str = "\n".join(rows_html)
        date_str = datetime.datetime.now().strftime("%B %d, %Y")
        headers  = "".join(
            f"<th>{name_label if key == 'name' else html_col_labels.get(key, key)}</th>"
            for key in columns
        )
        html = (
            "<!DOCTYPE html>\n<html lang='en'>\n<head>\n"
            "<meta charset='utf-8'>\n"
            f"<title>{tl_safe} — Marker Report</title>\n"
            "<style>\n"
            "body{background:#fff;color:#111;font-family:Helvetica,Arial,sans-serif;"
            "padding:32px 40px;margin:0}\n"
            "header{margin-bottom:24px}\n"
            "header h1{margin:0 0 4px;font-size:22px;font-weight:700;color:#111}\n"
            "header p{margin:0;font-size:13px;color:#666}\n"
            "table{border-collapse:collapse;width:100%;font-size:13px}\n"
            "th{background:#f4f4f4;padding:8px 12px;text-align:center;"
            "font-weight:600;color:#333;border:1px solid #ddd}\n"
            "td{padding:7px 12px;border:1px solid #ddd;vertical-align:middle;color:#222}\n"
            "tr:nth-child(even) td{background:#fafafa}\n"
            "tr:hover td{background:#f0f4ff}\n"
            "footer{margin-top:24px;font-size:11px;color:#aaa;text-align:right}\n"
            "@media print{"
            "body{padding:16px}"
            "tr:hover td{background:inherit}"
            "}\n"
            "</style>\n</head>\n<body>\n"
            "<header>\n"
            f"<h1>{tl_safe}</h1>\n"
            f"<p>Marker report &nbsp;·&nbsp; {date_str}</p>\n"
            "</header>\n"
            + f"<table>\n<tr>{headers}</tr>\n"
            + f"{rows_str}\n"
            + "</table>\n"
            + "<footer>Generated by Marker Madness</footer>\n"
            + "</body>\n</html>"
        )
        with open(html_path, "w", encoding="utf-8") as fh:
            fh.write(html)

    # ── CSV import ────────────────────────────────────────────────────────

    def _import_csv(self):
        timeline, err = self._fresh_timeline()
        if not timeline:
            self._mb(messagebox.showwarning, "Not connected", err)
            return
        if self._stay_on_top_var.get():
            self.root.attributes("-topmost", False)
        path = filedialog.askopenfilename(
            title="Import Markers from CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if self._stay_on_top_var.get():
            self.root.attributes("-topmost", True)
        if not path:
            return
        rows = []
        try:
            with open(path, newline="", encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
        except Exception as exc:
            self._mb(messagebox.showerror, "Import Failed", f"Could not read file:\n{exc}")
            return
        if not rows:
            self._mb(messagebox.showinfo, "Import", "The CSV file is empty.")
            return

        conflicts = [r for r in rows if int(r.get("Frame", 0)) in self._tl_frames]
        overwrite = False
        if conflicts:
            ans = self._mb(messagebox.askyesnocancel,
                "Conflicts Found",
                f"{len(conflicts)} frame(s) already have timeline markers.\n\n"
                "Yes = overwrite  ·  No = skip  ·  Cancel = abort"
            )
            if ans is None:
                return
            overwrite = ans

        added = skipped = failed = 0
        for row in rows:
            try:
                frame_id = int(row.get("Frame", 0))
                color    = row.get("Color", "Blue")
                if color not in MARKER_COLORS:
                    color = "Blue"
                name     = row.get("Name",     "")
                note     = row.get("Note",     "")
                duration = int(row.get("Marker Dur") or row.get("Duration") or 1)

                if frame_id in self._tl_frames:
                    if not overwrite:
                        skipped += 1
                        continue
                    self._resolve_delete_marker(timeline, frame_id)

                ok, _e = self._resolve_add_marker(
                    timeline, frame_id, color, name, note, duration, ""
                )
                if ok:
                    added += 1
                    self._tl_frames.add(frame_id)
                else:
                    failed += 1
            except Exception:
                failed += 1

        self._refresh()
        msg = f"Import complete.\n\nAdded: {added}"
        if skipped:
            msg += f"\nSkipped: {skipped}"
        if failed:
            msg += f"\nFailed: {failed}"
        self._mb(messagebox.showinfo, "Import Complete", msg)

    # ── Playhead seek ─────────────────────────────────────────────────────

    def _seek_to_marker(self, rec: dict):
        """Move the Resolve playhead to the marker's timeline position."""
        if not self._timeline:
            return
        tc = frames_to_tc(rec["timeline_frame"] + self._start_frame, self._fps)
        try:
            self._timeline.SetCurrentTimecode(tc)
        except Exception:
            pass

    def _jump_to_marker(self):
        """Manual Jump to Marker button — seeks regardless of the auto-jump toggle."""
        sel = self._tree.selection()
        if not sel:
            self._mb(messagebox.showinfo, "Jump to Marker", "Select a marker first.")
            return
        rec = self._by_id.get(sel[0])
        if not rec:
            return
        if not self._timeline:
            self._mb(messagebox.showwarning, "Not connected", "No timeline is active.")
            return
        self._seek_to_marker(rec)

    # ── Frame grab & preview ──────────────────────────────────────────────

    def _grab_frame(self, rec=None):
        """Grab the frame at the selected (or supplied) marker and show a preview.

        When called by the button, rec=None and the selection is used.
        When called by auto-grab, rec is passed directly so no dialog is shown
        on failure — silent errors are used instead to avoid pop-up spam.
        """
        silent = rec is not None   # auto-grab: don't show error dialogs

        if rec is None:
            sel = self._tree.selection()
            if not sel:
                self._mb(messagebox.showinfo, "Grab Frame", "Select a marker first.")
                return
            rec = self._by_id.get(sel[0])
            if not rec:
                return

        if not self._timeline or not self._project:
            if not silent:
                self._mb(messagebox.showwarning, "Not connected", "No timeline is active.")
            return

        # Always seek to the marker before grabbing so we capture the right frame
        self._seek_to_marker(rec)

        # ── Save the current page so we can restore it after the grab ──────
        current_page = None
        try:
            current_page = self._resolve.GetCurrentPage()
        except Exception:
            pass

        # Grab the still
        try:
            still = self._timeline.GrabStill()
        except Exception as exc:
            if not silent:
                self._mb(messagebox.showerror,
                    "Grab Failed",
                    f"Could not grab frame.\nMake sure the Edit or Color page "
                    f"is active in Resolve.\n\n{exc}"
                )
            self._restore_page(current_page)
            return

        if not still:
            if not silent:
                self._mb(messagebox.showerror,
                    "Grab Failed",
                    "No still was returned.\n"
                    "Make sure the Edit or Color page is active in Resolve."
                )
            self._restore_page(current_page)
            return

        # Export the still to temp storage
        tmp_dir    = tempfile.gettempdir()
        tmp_prefix = "mm_preview"
        try:
            album = self._project.GetGallery().GetCurrentStillAlbum()
            album.ExportStills([still], tmp_dir, tmp_prefix, "png")
            # Clean up the still from the gallery unless the user wants to keep it
            if not self._keep_gallery_var.get():
                try:
                    album.DeleteStills([still])
                except Exception:
                    pass
        except Exception as exc:
            if not silent:
                self._mb(messagebox.showerror, "Export Failed", f"Could not export still:\n{exc}")
            self._restore_page(current_page)
            return

        # ── Restore the original page immediately ──────────────────────────
        self._restore_page(current_page)

        matches = sorted(glob.glob(os.path.join(tmp_dir, f"{tmp_prefix}*.png")),
                         key=os.path.getmtime, reverse=True)
        if not matches:
            if not silent:
                self._mb(messagebox.showerror, "File Not Found",
                         "Still exported but PNG file could not be located.")
            return

        self._grab_path = matches[0]
        self._show_preview(self._grab_path)

    def _restore_page(self, page):
        """Switch Resolve back to the given page if it changed during a grab."""
        if not page or not self._resolve:
            return
        try:
            current = self._resolve.GetCurrentPage()
            if current and current.lower() != page.lower():
                self._resolve.OpenPage(page.lower())
        except Exception:
            pass

    def _show_preview(self, path: str):
        try:
            img = tk.PhotoImage(file=path)
        except Exception as exc:
            self._img_canvas.delete("all")
            self._img_canvas.create_text(143, 80,
                                          text=f"Preview error:\n{exc}",
                                          fill=RED, font=F_SMALL, justify="center")
            return
        cw, ch = 286, 161
        iw, ih = img.width(), img.height()
        scale  = min(cw / iw, ch / ih)
        if scale < 1:
            f = max(1, round(1 / scale))
            img = img.subsample(f, f)
        elif scale > 1:
            f = max(1, round(scale))
            img = img.zoom(f, f)
        self._preview_img = img
        self._img_canvas.delete("all")
        self._img_canvas.create_image(cw // 2, ch // 2, image=img, anchor="center")

    def _export_frame(self):
        if not self._grab_path:
            self._mb(messagebox.showinfo, "Export Frame",
                     "Click Grab Frame first to capture a preview.")
            return

        # Format + quality pre-dialog
        opt_dlg = ExportFrameOptionsDialog(self.root)
        self.root.wait_window(opt_dlg)
        if opt_dlg.result is None:
            return
        fmt          = opt_dlg.result["fmt"]       # "png", "tif", "jpg"
        jpeg_quality = opt_dlg.result["jpeg_quality"]
        name_only    = opt_dlg.result["name_only"]

        ext_map = {"png": ".png", "tif": ".tif", "jpg": ".jpg"}
        ftypes  = {
            "png": [("PNG image",  "*.png"), ("All files", "*.*")],
            "tif": [("TIFF image", "*.tif *.tiff"), ("All files", "*.*")],
            "jpg": [("JPEG image", "*.jpg *.jpeg"), ("All files", "*.*")],
        }
        def_ext = ext_map.get(fmt, ".png")

        sel  = self._tree.selection()
        name = "frame"
        if sel:
            rec  = self._by_id.get(sel[0], {})
            tc   = frames_to_tc(rec.get("timeline_frame", 0) + self._start_frame, self._fps).replace(":", "-")
            slug = rec.get("name", "").strip() or f"frame_{rec.get('timeline_frame','')}"
            slug = "".join(c if c.isalnum() or c in " -_" else "_" for c in slug)
            name = slug if name_only else f"{slug}_{tc}"

        if self._stay_on_top_var.get():
            self.root.attributes("-topmost", False)
        path = filedialog.asksaveasfilename(
            title="Export Frame",
            defaultextension=def_ext,
            filetypes=ftypes.get(fmt, ftypes["png"]),
            initialfile=f"{name}{def_ext}",
        )
        if self._stay_on_top_var.get():
            self.root.attributes("-topmost", True)
        if not path:
            return

        sips_fmt = SIPS_FMT.get(fmt)
        try:
            shutil.copy2(self._grab_path, path)
            if sips_fmt and fmt != "png":
                cmd = ["sips", "-s", "format", sips_fmt]
                if fmt == "jpg" and jpeg_quality is not None:
                    cmd += ["-s", "formatOptions", str(jpeg_quality)]
                cmd += [path, "--out", path]
                subprocess.run(cmd, capture_output=True, timeout=30)
            self._mb(messagebox.showinfo, "Exported", f"Frame saved to:\n{path}")
        except Exception as exc:
            self._mb(messagebox.showerror, "Export Failed", str(exc))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    root = tk.Tk()
    root.withdraw()                  # hide before anything renders
    root.title(APP_TITLE)
    app = MarkerMadness(root)

    # Temporarily lift pack_propagate(False) so the panel's true content height
    # flows up to the root — then measure, then lock it back down.
    app._side_panel.pack_propagate(True)
    root.update_idletasks()
    app._side_panel.pack_propagate(False)

    saved_geom = app._prefs.get("window_geometry")
    if saved_geom:
        try:
            root.geometry(saved_geom)
        except Exception:
            saved_geom = None
    if not saved_geom:
        w  = 1500
        h  = max(root.winfo_reqheight(), 800)
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    root.deiconify()                 # reveal at the correct position
    root.mainloop()


if __name__ == "__main__":
    main()
