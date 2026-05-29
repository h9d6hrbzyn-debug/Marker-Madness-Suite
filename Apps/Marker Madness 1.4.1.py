#!/usr/bin/env python3
"""
Marker Madness 1.4.1 — DaVinci Resolve Marker Manager
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
import webbrowser

# ---------------------------------------------------------------------------
# App icon (embedded Base64 PNG — no external file required)
# ---------------------------------------------------------------------------

APP_ICON_B64 = (
    "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"
)

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
    ("clip_dur_f", "Clip Dur frames",  130, "center", False, False),
    ("clip_dur_t", "Clip Duration", 100, "center", False, False),
]

COL_IDS      = [c[0] for c in COLUMNS]
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
    ("dur_f",     "Clip Dur frames"),
    ("dur_t",     "Clip Duration"),
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
    "clip_dur_f": ("Clip Dur frames",  lambda r, fps, sf: r["clip_dur_frames"] if r["clip_dur_frames"] is not None else ""),
    "clip_dur_t": ("Clip Duration", lambda r, fps, sf: frames_to_tc(r["clip_dur_frames"], fps) if r["clip_dur_frames"] is not None else ""),
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
        # self.transient(app.root) omitted — causes macOS focus-stealing on dialogs.
        self._app        = app
        self._undo_stack = []   # list of [(rec, old_name, old_note), …]
        self._redo_stack = []   # list of [(rec, redo_name, redo_note), …]
        self._preview_job = None

        self.title("Marker Renamer")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.protocol("WM_DELETE_WINDOW", self.withdraw)

        self._build()
        self._schedule_preview()
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<Command-Shift-z>", lambda e: self._redo())
        self.bind("<Command-Shift-Z>", lambda e: self._redo())
        self.bind("<Control-Shift-z>", lambda e: self._redo())
        self.bind("<Control-Shift-Z>", lambda e: self._redo())

        # Center over the main window on every first open
        center_on_parent(self, app.root)
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
                            highlightthickness=1, highlightbackground=BTN_HOV,
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
        _spinbox(tc, self._trim_begin_var, 0, 999).grid(row=0, column=2, padx=(0, 4))
        _lbl(tc, "End:",    row=0, col=3)
        _spinbox(tc, self._trim_end_var,   0, 999).grid(row=0, column=4, padx=(0, 4))

        self._counter_var    = tk.BooleanVar(value=False)
        self._ctr_digits_var = tk.IntVar(value=2)
        self._ctr_start_var  = tk.IntVar(value=1)
        self._ctr_step_var   = tk.IntVar(value=1)
        self._ctr_pos_var    = tk.StringVar(value="After")

        _chk(tc, "Counter", self._counter_var, row=1)
        _lbl(tc, "Digits:", row=1, col=1)
        _spinbox(tc, self._ctr_digits_var, 1, 6).grid(row=1, column=2, padx=(0, 4))
        _lbl(tc, "Start:",  row=1, col=3)
        _spinbox(tc, self._ctr_start_var,  0, 9999).grid(row=1, column=4, padx=(0, 4))
        tk.Label(tc, text="Pos:", fg=DIM, bg=DLG,
                 font=F_SMALL, anchor="e", width=4).grid(row=1, column=5, sticky="e", padx=(6,2))
        cb = ttk.Combobox(tc, textvariable=self._ctr_pos_var,
                          values=["After", "Before"], state="readonly",
                          width=6, font=F_SMALL)
        cb.grid(row=1, column=6)
        self._ctr_pos_var.trace_add("write", lambda *_: self._schedule_preview())

        # Step row — indented under Counter
        _lbl(tc, "Step:",   row=2, col=1)
        _spinbox(tc, self._ctr_step_var, 1, 9999).grid(row=2, column=2, padx=(0, 4))
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
        self._redo_btn = TBtn(bf, text="↪  Redo", command=self._redo,
                              bg=BTN_HOV, fg=DIM, padx=10, pady=5)
        self._redo_btn.pack(side="left", padx=(0, 4))
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
        # First counter value = start × step (e.g. start=1, step=10 → 10, 20, 30).
        # This is intentional — do not change to just start.
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
            if len(self._undo_stack) > 10:
                self._undo_stack.pop(0)
            self._redo_stack.clear()
            self._update_undo_btns()
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
            if len(self._undo_stack) > 10:
                self._undo_stack.pop(0)
            self._redo_stack.clear()
            self._update_undo_btns()
        self._app._populate_table()
        self._update_preview()
        self._status_var.set(f"Clip Name → Marker Name on {len(undo_batch)} marker{'s' if len(undo_batch) != 1 else ''}.")

    def _apply(self):
        targets = self._get_targets()
        if not targets:
            self._status_var.set("No markers to apply to.")
            return

        field   = self._field_var.get()
        # First counter value = start × step (e.g. start=1, step=10 → 10, 20, 30).
        # This is intentional — do not change to just start.
        counter = self._ctr_start_var.get() * self._ctr_step_var.get()
        undo_batch = []
        errors     = []

        for rec in targets:
            p        = self._get_params(counter)
            new_name = _renamer_transform(rec["name"], **p) if field in ("name", "both") else rec["name"]
            new_note = _renamer_transform(rec["note"], **p) if field in ("note", "both") else rec["note"]

            if new_name == rec["name"] and new_note == rec["note"]:
                if self._counter_var.get():
                    counter += self._ctr_step_var.get()
                continue

            undo_batch.append((rec, rec["name"], rec["note"]))
            ok, err = self._app._write_marker(rec, rec["color"], new_name,
                                               new_note, rec["duration"], "")
            if ok:
                rec["name"] = new_name
                rec["note"] = new_note
                if self._counter_var.get():
                    counter += self._ctr_step_var.get()
            else:
                errors.append(err)

        if undo_batch:
            self._undo_stack.append(undo_batch)
            if len(self._undo_stack) > 10:
                self._undo_stack.pop(0)
            self._redo_stack.clear()
            self._update_undo_btns()

        self._app._populate_table()
        self._update_preview()

        changed = len(undo_batch)
        if errors:
            self._status_var.set(f"Applied {changed}, {len(errors)} error(s).")
        else:
            self._status_var.set(f"Applied to {changed} marker{'s' if changed != 1 else ''}.")

    def _update_undo_btns(self):
        """Keep Undo/Redo button labels and colours in sync with the stacks."""
        n = len(self._undo_stack)
        m = len(self._redo_stack)
        if n == 0:
            self._undo_btn.config(bg=BTN_HOV, fg=DIM, text="↩  Undo")
        elif n == 1:
            self._undo_btn.config(bg=ACCENT,  fg=BG,  text="↩  Undo")
        else:
            self._undo_btn.config(bg=ACCENT,  fg=BG,  text=f"↩  Undo ({n})")
        if m == 0:
            self._redo_btn.config(bg=BTN_HOV, fg=DIM, text="↪  Redo")
        elif m == 1:
            self._redo_btn.config(bg=ACCENT,  fg=BG,  text="↪  Redo")
        else:
            self._redo_btn.config(bg=ACCENT,  fg=BG,  text=f"↪  Redo ({m})")

    def _undo(self):
        if not self._undo_stack:
            return
        batch = self._undo_stack.pop()
        # Capture current state so redo can re-apply what we're about to undo
        redo_batch = [(rec, rec["name"], rec["note"]) for rec, _, _ in batch]
        for rec, old_name, old_note in reversed(batch):
            ok, _ = self._app._write_marker(rec, rec["color"], old_name,
                                             old_note, rec["duration"], "")
            if ok:
                rec["name"] = old_name
                rec["note"] = old_note
        self._redo_stack.append(redo_batch)
        self._update_undo_btns()
        self._app._populate_table()
        self._update_preview()
        self._status_var.set(f"Undone {len(batch)} change{'s' if len(batch) != 1 else ''}.")

    def _redo(self):
        if not self._redo_stack:
            return
        redo_batch = self._redo_stack.pop()
        # Capture current state so undo can reverse the redo
        undo_batch = [(rec, rec["name"], rec["note"]) for rec, _, _ in redo_batch]
        for rec, redo_name, redo_note in redo_batch:
            ok, _ = self._app._write_marker(rec, rec["color"], redo_name,
                                             redo_note, rec["duration"], "")
            if ok:
                rec["name"] = redo_name
                rec["note"] = redo_note
        self._undo_stack.append(undo_batch)
        self._update_undo_btns()
        self._app._populate_table()
        self._update_preview()
        self._status_var.set(f"Redone {len(redo_batch)} change{'s' if len(redo_batch) != 1 else ''}.")

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

def _attach_entry_menu(widget: tk.Entry):
    """Attach a right-click Cut / Copy / Paste / Select All menu to an Entry."""
    menu = tk.Menu(widget, tearoff=0)
    menu.add_command(label="Cut",        command=lambda: widget.event_generate("<<Cut>>"))
    menu.add_command(label="Copy",       command=lambda: widget.event_generate("<<Copy>>"))
    menu.add_command(label="Paste",      command=lambda: widget.event_generate("<<Paste>>"))
    menu.add_separator()
    menu.add_command(label="Select All", command=lambda: widget.select_range(0, "end"))

    def _show(event):
        widget.focus_set()
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    widget.bind("<Button-2>", _show)
    widget.bind("<Button-3>", _show)

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
                 get_tc_fn=None, track_list=None):
        super().__init__(parent)
        self.withdraw()
        # transient(parent) omitted — on macOS it causes the parent to
        # re-activate when the dialog appears, stealing focus and breaking
        # ttk.Combobox dropdowns. -topmost keeps it above MM instead.
        self.title(title)
        self.resizable(False, False)
        self.configure(bg=BG)
        # No grab_set() — user needs to interact with Resolve to move the
        # playhead and use Refresh Position while this dialog is open.
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
            # Build dropdown options from the provided track_list.
            # "Timeline" is always the first entry; video tracks come before audio.
            _tgt_display = ["Timeline"]
            self._tgt_keys = ["timeline"]
            if track_list:
                for (ttype, tidx) in track_list:
                    _tgt_display.append(f"{'V' if ttype == 'video' else 'A'}{tidx}")
                    self._tgt_keys.append(f"{ttype}:{tidx}")
            self._tgt_display = _tgt_display
            self._target_var  = tk.StringVar(value="Timeline")

            tgt_frame = tk.Frame(self, bg=DLG)
            tgt_frame.grid(row=row, column=0, columnspan=2, sticky="ew",
                           padx=16, pady=(14, 2))
            tk.Label(tgt_frame, text="Add to:", fg=DIM, bg=DLG,
                     font=F_SMALL).pack(side="left", padx=(0, 10))
            ttk.Combobox(tgt_frame, textvariable=self._target_var,
                         values=_tgt_display, state="readonly", width=14,
                         font=F_SMALL).pack(side="left")
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
        self._name_entry = tk.Entry(self, textvariable=self._name_var, width=36,
                 bg=DFLD, fg=TEXT, insertbackground=TEXT,
                 relief="flat", font=F_MAIN)
        self._name_entry.grid(row=name_row, column=1, sticky="ew", **pad)

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
        TBtn(bf, text="Save",   command=self._save,   bg=ACCENT, fg=BG).pack(side="left", padx=8)
        TBtn(bf, text="Cancel", command=self.destroy, bg=ACCENT, fg=BG).pack(side="left", padx=8)

        self.columnconfigure(1, weight=1)
        self.bind("<Return>",   lambda _: self._save())
        self.bind("<KP_Enter>", lambda _: self._save())

        center_on_parent(self, parent)
        self.deiconify()
        self.lift()
        # Always stay on top — user needs this dialog visible while clicking
        # in Resolve to position the playhead or refresh position.
        self.attributes("-topmost", True)
        # Deferred focus grab: give the window manager ~200 ms to finish
        # presenting the window before we steal focus back from Resolve.
        # Without this, Resolve briefly re-takes focus and the dialog opens
        # non-active — clicks land on Resolve instead of the dialog widgets.
        # 200 ms also covers the case where this dialog opens immediately
        # after AddActionDialog closes (which briefly returns focus to the
        # MM main window).
        self.after(200, self._grab_focus)

    def _grab_focus(self):
        """Grab window focus and put the cursor in the Name field."""
        try:
            self.lift()
            self.focus_force()
            self._name_entry.focus_set()
        except Exception:
            pass

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
            "target":   (self._tgt_keys[self._tgt_display.index(self._target_var.get())]
                         if self._is_add else "timeline"),
        }
        self.destroy()

# ---------------------------------------------------------------------------
# Bulk colour-change dialog
# ---------------------------------------------------------------------------

class ColorPickDialog(tk.Toplevel):
    def __init__(self, parent, count: int):
        super().__init__(parent)
        self.withdraw()
        # self.transient(parent) omitted — causes macOS to re-activate the
        # parent when the dialog appears, stealing focus and breaking Comboboxes.
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
        # self.transient(parent) omitted — causes macOS to re-activate the
        # parent when the dialog appears, stealing focus and breaking Comboboxes.
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
# Add-action gateway dialog  (Add at Playhead  vs  Stamp All Clips on Track)
# ---------------------------------------------------------------------------

class AddActionDialog(tk.Toplevel):
    """Two-button gateway shown when the user clicks '+ Add'.

    result: "playhead" | "stamp_track" | None
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()
        # transient(parent) omitted — see StampTrackDialog note above.
        self.title("Add Markers")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.result = None

        tk.Label(self, text="Add Markers",
                 fg=TEXT, bg=BG, font=F_BOLD).pack(padx=36, pady=(18, 14))

        # ── Option 1: single marker at playhead ───────────────────────────
        TBtn(self, text="⊕  Add Single Marker",
             command=lambda: self._pick("playhead"),
             bg=ACCENT, fg=BG, width=26).pack(padx=36, pady=(0, 4))
        tk.Label(self, text="One marker at the current playhead position",
                 fg=DIM, bg=BG, font=F_SMALL).pack(padx=36, pady=(0, 14))

        # ── Separator ─────────────────────────────────────────────────────
        tk.Frame(self, bg=BTN_HOV, height=1).pack(fill="x", padx=24, pady=(0, 14))

        # ── Option 2: stamp every clip on a track ─────────────────────────
        TBtn(self, text="⊹  Batch Stamp Track",
             command=lambda: self._pick("stamp_track"),
             bg=PURPLE, fg=BG, width=26).pack(padx=36, pady=(0, 4))
        tk.Label(self, text="Stamp the same marker on every clip in a track",
                 fg=DIM, bg=BG, font=F_SMALL).pack(padx=36, pady=(0, 18))

        self.bind("<Escape>", lambda _: self.destroy())
        center_on_parent(self, parent)
        self.deiconify()
        self.lift()
        self.attributes("-topmost", True)
        self.focus_force()

    def _pick(self, choice):
        self.result = choice
        self.destroy()


# ---------------------------------------------------------------------------
# Stamp Track dialog  (marker settings + track selector for bulk stamping)
# ---------------------------------------------------------------------------

class StampTrackDialog(tk.Toplevel):
    """Configure a marker to be stamped on every clip in a chosen track.

    track_list : list of (track_type, track_index)  e.g. [("video",1), ("audio",1)]
    timeline   : live Resolve timeline proxy (used by ↺ From Timeline button)
    fps        : project frame rate
    result     : (ttype, tidx, color, name, note, duration, offset,
                  skip_existing, range_frames)
                 range_frames is None (entire track) or (in_frames, out_frames).
                 Entire tuple is None on cancel.
    """

    def __init__(self, parent, track_list: list,
                 timeline=None, fps: float = 24.0):
        super().__init__(parent)
        self.withdraw()
        # transient(parent) intentionally omitted — on macOS it causes the
        # parent to re-activate when the dialog appears, stealing focus and
        # breaking ttk.Combobox dropdowns. -topmost keeps it above MM instead.
        self.title("Stamp All Clips on Track")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.result   = None
        self._tl      = timeline
        self._fps     = fps

        tk.Label(self, text="Stamp All Clips on Track",
                 fg=TEXT, bg=BG, font=F_BOLD).pack(padx=28, pady=(18, 4))
        tk.Label(self, text="Places one marker on every clip in the chosen track.",
                 fg=DIM, bg=BG, font=F_SMALL).pack(padx=28, pady=(0, 14))

        # ── Build track selector data ─────────────────────────────────────
        self._track_labels = []
        self._track_data   = []
        for (ttype, tidx) in track_list:
            prefix = "V" if ttype == "video" else "A"
            self._track_labels.append(f"{prefix}{tidx}")
            self._track_data.append((ttype, tidx))

        # ── Options grid ─────────────────────────────────────────────────
        grid = tk.Frame(self, bg=BG)
        grid.pack(padx=28, pady=(0, 8), fill="x")
        grid.columnconfigure(1, weight=1)

        # Track
        tk.Label(grid, text="Track:", fg=TEXT, bg=BG,
                 font=F_MAIN).grid(row=0, column=0, sticky="w", pady=5)
        self._track_var = tk.StringVar(
            value=self._track_labels[0] if self._track_labels else "")
        ttk.Combobox(grid, textvariable=self._track_var,
                     values=self._track_labels, state="readonly",
                     width=10, font=F_MAIN).grid(
                         row=0, column=1, sticky="w", padx=(10, 0), pady=5)

        # Color
        tk.Label(grid, text="Color:", fg=TEXT, bg=BG,
                 font=F_MAIN).grid(row=1, column=0, sticky="w", pady=5)
        self._color_var = tk.StringVar(value="Blue")
        ttk.Combobox(grid, textvariable=self._color_var,
                     values=MARKER_COLORS, state="readonly",
                     width=14, font=F_MAIN).grid(
                         row=1, column=1, sticky="w", padx=(10, 0), pady=5)

        # Name
        tk.Label(grid, text="Name:", fg=TEXT, bg=BG,
                 font=F_MAIN).grid(row=2, column=0, sticky="w", pady=5)
        self._name_var = tk.StringVar()
        tk.Entry(grid, textvariable=self._name_var, bg=ENTRY_BG, fg=TEXT,
                 insertbackground=TEXT, relief="flat", font=F_MAIN,
                 width=32).grid(row=2, column=1, sticky="ew",
                                padx=(10, 0), pady=5)

        # Note
        tk.Label(grid, text="Note:", fg=TEXT, bg=BG,
                 font=F_MAIN).grid(row=3, column=0, sticky="w", pady=5)
        self._note_var = tk.StringVar()
        tk.Entry(grid, textvariable=self._note_var, bg=ENTRY_BG, fg=TEXT,
                 insertbackground=TEXT, relief="flat", font=F_MAIN,
                 width=32).grid(row=3, column=1, sticky="ew",
                                padx=(10, 0), pady=5)

        # Duration
        tk.Label(grid, text="Duration:", fg=TEXT, bg=BG,
                 font=F_MAIN).grid(row=4, column=0, sticky="w", pady=5)
        dur_row = tk.Frame(grid, bg=BG)
        dur_row.grid(row=4, column=1, sticky="w", padx=(10, 0), pady=5)
        self._dur_var = tk.IntVar(value=1)
        tk.Spinbox(dur_row, from_=1, to=9999, textvariable=self._dur_var,
                   width=7, bg=ENTRY_BG, fg=TEXT, insertbackground=TEXT,
                   buttonbackground=BTN, relief="flat",
                   font=F_MAIN).pack(side="left")
        tk.Label(dur_row, text="frames", fg=DIM, bg=BG,
                 font=F_SMALL).pack(side="left", padx=(6, 0))

        # Position within clip
        tk.Label(grid, text="Position:", fg=TEXT, bg=BG,
                 font=F_MAIN).grid(row=5, column=0, sticky="nw", pady=(10, 5))
        pos_frame = tk.Frame(grid, bg=BG)
        pos_frame.grid(row=5, column=1, sticky="w", padx=(10, 0), pady=(10, 5))
        self._pos_var = tk.StringVar(value="start")
        tk.Radiobutton(pos_frame, text="Start of clip",
                       variable=self._pos_var, value="start",
                       fg=TEXT, bg=BG, activeforeground=TEXT,
                       activebackground=BG, selectcolor=ENTRY_BG,
                       font=F_MAIN,
                       command=self._update_offset_state).pack(anchor="w")
        offset_row = tk.Frame(pos_frame, bg=BG)
        offset_row.pack(anchor="w", pady=(4, 0))
        tk.Radiobutton(offset_row, text="Offset:",
                       variable=self._pos_var, value="offset",
                       fg=TEXT, bg=BG, activeforeground=TEXT,
                       activebackground=BG, selectcolor=ENTRY_BG,
                       font=F_MAIN,
                       command=self._update_offset_state).pack(side="left")
        self._offset_var = tk.IntVar(value=0)
        self._offset_sb  = tk.Spinbox(offset_row, from_=0, to=99999,
                                      textvariable=self._offset_var,
                                      width=6, bg=ENTRY_BG, fg=TEXT,
                                      insertbackground=TEXT,
                                      buttonbackground=BTN, relief="flat",
                                      font=F_MAIN)
        self._offset_sb.pack(side="left", padx=(6, 6))
        tk.Label(offset_row, text="frames from start",
                 fg=DIM, bg=BG, font=F_SMALL).pack(side="left")

        # Conflicts
        tk.Label(grid, text="Conflicts:", fg=TEXT, bg=BG,
                 font=F_MAIN).grid(row=6, column=0, sticky="nw", pady=(10, 5))
        cf_frame = tk.Frame(grid, bg=BG)
        cf_frame.grid(row=6, column=1, sticky="w", padx=(10, 0), pady=(10, 5))
        self._skip_var = tk.StringVar(value="skip")
        tk.Radiobutton(cf_frame,
                       text="Skip clips that already have a marker at that position",
                       variable=self._skip_var, value="skip",
                       fg=TEXT, bg=BG, activeforeground=TEXT,
                       activebackground=BG, selectcolor=ENTRY_BG,
                       font=F_MAIN, wraplength=300,
                       justify="left").pack(anchor="w")
        tk.Radiobutton(cf_frame, text="Overwrite existing",
                       variable=self._skip_var, value="overwrite",
                       fg=TEXT, bg=BG, activeforeground=TEXT,
                       activebackground=BG, selectcolor=ENTRY_BG,
                       font=F_MAIN).pack(anchor="w", pady=(4, 0))

        # ── Range ─────────────────────────────────────────────────────────
        tk.Label(grid, text="Range:", fg=TEXT, bg=BG,
                 font=F_MAIN).grid(row=7, column=0, sticky="nw", pady=(10, 5))
        rng_frame = tk.Frame(grid, bg=BG)
        rng_frame.grid(row=7, column=1, sticky="w", padx=(10, 0), pady=(10, 5))

        self._range_var = tk.StringVar(value="all")
        rb_kw = dict(fg=TEXT, bg=BG, activeforeground=TEXT,
                     activebackground=BG, selectcolor=ENTRY_BG,
                     font=F_MAIN, command=self._on_range_changed)
        tk.Radiobutton(rng_frame, text="Entire track",
                       variable=self._range_var, value="all",
                       **rb_kw).pack(side="left")
        tk.Radiobutton(rng_frame, text="In/Out range",
                       variable=self._range_var, value="inout",
                       **rb_kw).pack(side="left", padx=(14, 0))

        # TC fields — hidden until "In/Out range" is chosen
        self._range_in_var  = tk.StringVar(value="")
        self._range_out_var = tk.StringVar(value="")
        self._tc_frame = tk.Frame(grid, bg=BG)
        self._tc_frame.grid(row=8, column=1, sticky="w", padx=(10, 0), pady=(0, 6))
        self._tc_frame.grid_remove()

        tc_kw = dict(bg=ENTRY_BG, fg=TEXT, insertbackground=TEXT,
                     relief="flat", font=F_MONO, width=12)
        tk.Label(self._tc_frame, text="In:", fg=DIM, bg=BG,
                 font=F_SMALL).pack(side="left", padx=(0, 4))
        tk.Entry(self._tc_frame, textvariable=self._range_in_var,
                 **tc_kw).pack(side="left")
        tk.Label(self._tc_frame, text="Out:", fg=DIM, bg=BG,
                 font=F_SMALL).pack(side="left", padx=(10, 4))
        tk.Entry(self._tc_frame, textvariable=self._range_out_var,
                 **tc_kw).pack(side="left")
        TBtn(self._tc_frame, text="↺ From Timeline",
             command=self._grab_from_tl,
             bg=BTN_HOV, fg=BG, padx=8, pady=3,
             font=F_SMALL).pack(side="left", padx=(10, 0))

        # ── Buttons ───────────────────────────────────────────────────────
        bf = tk.Frame(self, bg=BG)
        bf.pack(pady=(10, 18))
        TBtn(bf, text="Stamp",  command=self._ok,     bg=ACCENT, fg=BG).pack(side="left", padx=8)
        TBtn(bf, text="Cancel", command=self.destroy, bg=ACCENT, fg=BG).pack(side="left", padx=8)

        self._update_offset_state()
        self.bind("<Return>",   lambda _: self._ok())
        self.bind("<KP_Enter>", lambda _: self._ok())
        self.bind("<Escape>",   lambda _: self.destroy())
        center_on_parent(self, parent)
        self.deiconify()
        self.lift()
        self.attributes("-topmost", True)
        self.focus_force()

    def _update_offset_state(self):
        state = "normal" if self._pos_var.get() == "offset" else "disabled"
        self._offset_sb.config(state=state)

    def _on_range_changed(self):
        if self._range_var.get() == "inout":
            self._tc_frame.grid()
        else:
            self._tc_frame.grid_remove()

    def _grab_from_tl(self):
        """Read timeline In/Out points and populate the TC fields.

        Resolve 21+  → GetMarkInOut() returns
                        {'video': {'in': <frame>, 'out': <frame>}, 'audio': ...}
                        where frame is relative to the timeline's start frame.
        Older Resolve → GetCurrentInPoint() / GetCurrentOutPoint() returning
                        either a raw frame count or a packed-decimal TC integer
                        (e.g. 3004219 = 03:00:42:19).
        """
        if not self._tl:
            messagebox.showinfo("Not available",
                "No timeline reference — type timecodes manually (HH:MM:SS:FF).",
                parent=self)
            return

        # Timeline start frame — needed to convert relative frames to TC
        tl_start = 0
        try:
            tl_start = int(self._tl.GetStartFrame() or 0)
        except Exception:
            pass

        def _frame_to_tc(frame):
            return frames_to_tc(int(frame) + tl_start, self._fps)

        def _resolve_val_legacy(val):
            """Handle older API returns: packed-decimal TC int or raw frame count."""
            ifps = int(round(self._fps)) or 24
            if val is None:
                return None
            if isinstance(val, (int, float)):
                ival = int(val)
                if ival < 0:
                    return None
                # Packed decimal TC? e.g. 3004219 → 03:00:42:19
                ff = ival % 100
                ss = (ival // 100)     % 100
                mm = (ival // 10000)   % 100
                hh = (ival // 1000000) % 100
                if mm < 60 and ss < 60 and ff < ifps:
                    return f"{hh:02d}:{mm:02d}:{ss:02d}:{ff:02d}"
                return frames_to_tc(ival, self._fps)
            if isinstance(val, str) and val.strip():
                raw    = val.strip().replace(";", ":").replace(".", ":")
                digits = raw.replace(":", "")
                if digits.isdigit() and len(digits) == 8:
                    ff = int(digits[6:8]); ss = int(digits[4:6])
                    mm = int(digits[2:4]); hh = int(digits[0:2])
                    if mm < 60 and ss < 60 and ff < ifps:
                        return f"{hh:02d}:{mm:02d}:{ss:02d}:{ff:02d}"
                if tc_to_frames(raw, self._fps) >= 0:
                    return raw
            return None

        got_in = got_out = False

        # ── Resolve 21+: GetMarkInOut() ──────────────────────────────────────
        fn_mio = getattr(self._tl, 'GetMarkInOut', None)
        if callable(fn_mio):
            try:
                result = fn_mio()
                in_val = out_val = None
                if isinstance(result, dict):
                    for key in ('video', 'audio', None):
                        section = result.get(key, result) if key else result
                        if isinstance(section, dict) and 'in' in section:
                            in_val  = section['in']
                            out_val = section.get('out')
                            break
                elif isinstance(result, (list, tuple)) and len(result) >= 2:
                    in_val, out_val = result[0], result[1]

                if in_val is not None and int(in_val) >= 0:
                    self._range_in_var.set(_frame_to_tc(in_val))
                    got_in = True
                if out_val is not None and int(out_val) >= 0:
                    self._range_out_var.set(_frame_to_tc(out_val))
                    got_out = True
            except Exception:
                pass

        # ── Older Resolve: individual in/out methods ──────────────────────────
        if not got_in:
            for attr in ("GetCurrentInPoint", "GetInPoint"):
                fn = getattr(self._tl, attr, None)
                if not callable(fn):
                    continue
                try:
                    tc = _resolve_val_legacy(fn())
                    if tc:
                        self._range_in_var.set(tc)
                        got_in = True
                        break
                except Exception:
                    pass

        if not got_out:
            for attr in ("GetCurrentOutPoint", "GetOutPoint"):
                fn = getattr(self._tl, attr, None)
                if not callable(fn):
                    continue
                try:
                    tc = _resolve_val_legacy(fn())
                    if tc:
                        self._range_out_var.set(tc)
                        got_out = True
                        break
                except Exception:
                    pass

        if not (got_in or got_out):
            messagebox.showinfo(
                "Can't Read In/Out Points",
                "Couldn't read the timeline In/Out points automatically.\n\n"
                "This can happen if:\n"
                "  • No In/Out points are set in Resolve yet (press I and O)\n"
                "  • Your Resolve version doesn't expose them via scripting\n\n"
                "Just type the timecodes directly (HH:MM:SS:FF).",
                parent=self)

    def _ok(self):
        if not self._track_var.get() or not self._track_labels:
            return
        idx = self._track_labels.index(self._track_var.get())
        ttype, tidx = self._track_data[idx]
        try:
            dur = max(1, int(self._dur_var.get()))
        except (ValueError, tk.TclError):
            dur = 1
        offset = 0
        if self._pos_var.get() == "offset":
            try:
                offset = max(0, int(self._offset_var.get()))
            except (ValueError, tk.TclError):
                offset = 0
        skip = (self._skip_var.get() == "skip")

        # Range
        range_frames = None
        if self._range_var.get() == "inout":
            in_f  = tc_to_frames(self._range_in_var.get(),  self._fps)
            out_f = tc_to_frames(self._range_out_var.get(), self._fps)
            if in_f >= 0 and out_f > in_f:
                range_frames = (in_f, out_f)
            else:
                messagebox.showwarning(
                    "Invalid Range",
                    "In/Out timecodes are empty or out of order.\n"
                    "Stamping will apply to the entire track instead.",
                    parent=self)

        self.result = (
            ttype, tidx,
            self._color_var.get(),
            self._name_var.get().strip(),
            self._note_var.get().strip(),
            dur, offset, skip, range_frames,
        )
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
        # self.transient(parent) omitted — causes macOS to re-activate the
        # parent when the dialog appears, stealing focus and breaking Comboboxes.
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
        self._offset_sb = tk.Spinbox(opts, from_=-9999, to=9999, textvariable=self._offset_var,
                   width=7, bg=ENTRY_BG, fg=TEXT, insertbackground=TEXT,
                   buttonbackground=BTN, relief="flat",
                   font=F_MAIN)
        self._offset_sb.grid(row=0, column=1, padx=(8, 0), pady=4, sticky="w")

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
        self.bind("<Tab>",      lambda _: (self._offset_sb.focus_set(), "break"))
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
# Paste markers dialog  (confirmation + target-track picker)
# ---------------------------------------------------------------------------

class PasteMarkersDialog(tk.Toplevel):
    """Confirm-and-target dialog for cross-timeline marker paste.

    tracks : list of (track_type, track_index, clip_count, clip_names_list)
             Only tracks that have a clip at one of the paste frames are passed in.
    result : ("ruler", 0) for timeline ruler, or (track_type, track_index) for a
             clip track.  None if the user cancelled.
    """

    def __init__(self, parent, count: int, tc_label: str, tracks: list):
        super().__init__(parent)
        self.withdraw()
        # self.transient(parent) omitted — causes macOS to re-activate the
        # parent when the dialog appears, stealing focus and breaking Comboboxes.
        self.title("Paste Markers")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.result = None

        marker_word = "marker" if count == 1 else "markers"
        tk.Label(self, text=f"Paste {count} {marker_word}",
                 fg=TEXT, bg=BG, font=F_BOLD).pack(padx=24, pady=(16, 2))
        tk.Label(self, text=f"Starting at playhead  {tc_label}",
                 fg=DIM, bg=BG, font=F_SMALL).pack(padx=24)
        tk.Label(self,
                 text="Conflicts (existing marker at same frame) are skipped.",
                 fg=DIM, bg=BG, font=F_SMALL).pack(padx=24, pady=(2, 12))

        opts = tk.Frame(self, bg=BG)
        opts.pack(padx=24, pady=(0, 8))

        tk.Label(opts, text="Paste onto:", fg=DIM, bg=BG,
                 font=F_SMALL).grid(row=0, column=0, sticky="w", pady=4)

        self._track_labels = ["Timeline Ruler"]
        self._track_data   = [("ruler", 0)]
        for (ttype, tidx, _cnt, _names) in tracks:
            prefix = "V" if ttype == "video" else "A"
            self._track_labels.append(f"{prefix}{tidx}")
            self._track_data.append((ttype, tidx))

        self._track_var = tk.StringVar(value=self._track_labels[0])
        ttk.Combobox(opts, textvariable=self._track_var,
                     values=self._track_labels,
                     state="readonly", width=30).grid(row=0, column=1,
                                                      padx=(8, 0), pady=4, sticky="w")

        if len(self._track_labels) == 1:
            tk.Label(opts,
                     text="No clips found at the paste frame(s) — will paste to ruler.",
                     fg=DIM, bg=BG, font=F_SMALL).grid(row=1, column=0, columnspan=2,
                                                         sticky="w", pady=(0, 4))

        bf = tk.Frame(self, bg=BG)
        bf.pack(pady=(4, 16))
        TBtn(bf, text="Paste",  command=self._ok,     bg=ACCENT, fg=BG).pack(side="left", padx=8)
        TBtn(bf, text="Cancel", command=self.destroy, bg=ACCENT, fg=BG).pack(side="left", padx=8)

        self.bind("<Return>",   lambda _: self._ok())
        self.bind("<KP_Enter>", lambda _: self._ok())
        center_on_parent(self, parent)
        self.deiconify()
        self.lift()
        self.attributes("-topmost", True)

    def _ok(self):
        idx = self._track_labels.index(self._track_var.get())
        self.result = self._track_data[idx]
        self.destroy()


# ---------------------------------------------------------------------------
# CSV Import preview dialog
# ---------------------------------------------------------------------------

class ImportPreviewDialog(tk.Toplevel):
    """Preview CSV rows before importing as markers.

    Supports checkbox selection with Shift-click range selection plus
    Check/Uncheck Selected batch buttons.

    result : list of row dicts to import, or None if cancelled.
    """

    COLS = [
        ("check",    "✓",        34),
        ("timecode", "Timecode", 100),
        ("color",    "Color",     80),
        ("name",     "Name",     200),
        ("note",     "Note",     180),
    ]

    def __init__(self, parent, rows, start_frame, tl_frames, filepath,
                 available_tracks=None):
        super().__init__(parent)
        self.withdraw()
        # self.transient(parent) omitted — causes macOS to re-activate the
        # parent when the dialog appears, stealing focus and breaking Comboboxes.
        self.title("Import Markers — Preview")
        self.resizable(True, True)
        self.configure(bg=BG)

        self._rows             = rows
        self._start_frame      = start_frame
        self._tl_frames        = tl_frames
        self._filepath         = filepath
        self._available_tracks = available_tracks or []
        self._checked          = set()
        self._items            = []
        self.result            = None
        self.track_result      = ("ruler", 0)

        style = ttk.Style()
        style.configure("Import.Treeview",         font=("Avenir Next", 14), rowheight=28)
        style.configure("Import.Treeview.Heading", font=F_SMALL)

        self._build_ui()
        self._populate()
        self.minsize(660, 440)
        center_on_parent(self, parent)
        self.deiconify()
        self.lift()
        self.attributes("-topmost", True)

    # ── UI ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        hf = tk.Frame(self, bg=BG)
        hf.pack(fill="x", padx=16, pady=(14, 4))
        tk.Label(hf, text="Import Markers — Preview",
                 fg=TEXT, bg=BG, font=F_BOLD).pack(anchor="w")
        self._header_var = tk.StringVar()
        tk.Label(hf, textvariable=self._header_var,
                 fg=DIM, bg=BG, font=F_SMALL).pack(anchor="w")

        tf = tk.Frame(self, bg=BG)
        tf.pack(fill="both", expand=True, padx=16, pady=(6, 0))
        vsb = ttk.Scrollbar(tf, orient="vertical")
        vsb.pack(side="right", fill="y")
        self._tree = ttk.Treeview(tf, columns=[c[0] for c in self.COLS],
                                  show="headings", selectmode="extended",
                                  yscrollcommand=vsb.set, style="Import.Treeview")
        vsb.config(command=self._tree.yview)
        for col_id, heading, width in self.COLS:
            self._tree.heading(col_id, text=heading)
            anchor  = "center" if col_id == "check" else "w"
            stretch = col_id in ("name", "note")
            self._tree.column(col_id, width=width, anchor=anchor, stretch=stretch)
        self._tree.tag_configure("conflict", foreground="#e6a817")
        self._tree.bind("<Button-1>", self._on_click)
        self._tree.pack(side="left", fill="both", expand=True)

        sf = tk.Frame(self, bg=BG)
        sf.pack(fill="x", padx=16, pady=(6, 2))
        TBtn(sf, text="Check All",        command=self._check_all,
             bg=BTN, fg=DIM, padx=6, pady=2).pack(side="left", padx=(0, 4))
        TBtn(sf, text="Uncheck All",      command=self._uncheck_all,
             bg=BTN, fg=DIM, padx=6, pady=2).pack(side="left", padx=(0, 10))
        tk.Frame(sf, bg=BTN_HOV, width=1).pack(side="left", fill="y", padx=(0, 10))
        TBtn(sf, text="Check Selected",   command=self._check_selected,
             bg=BTN, fg=DIM, padx=6, pady=2).pack(side="left", padx=(0, 4))
        TBtn(sf, text="Uncheck Selected", command=self._uncheck_selected,
             bg=BTN, fg=DIM, padx=6, pady=2).pack(side="left")
        self._conflict_var = tk.StringVar()
        tk.Label(sf, textvariable=self._conflict_var,
                 fg="#e6a817", bg=BG, font=F_SMALL).pack(side="right")

        # ── Paste-onto track row ──────────────────────────────────────────
        tf2 = tk.Frame(self, bg=BG)
        tf2.pack(fill="x", padx=16, pady=(4, 2))
        tk.Label(tf2, text="Paste onto:", fg=DIM, bg=BG,
                 font=F_SMALL).pack(side="left", padx=(0, 8))
        self._track_labels = ["Timeline Ruler"]
        self._track_data   = [("ruler", 0)]
        for (ttype, tidx, _cnt, _names) in self._available_tracks:
            prefix = "V" if ttype == "video" else "A"
            self._track_labels.append(f"{prefix}{tidx}")
            self._track_data.append((ttype, tidx))
        self._track_var = tk.StringVar(value=self._track_labels[0])
        ttk.Combobox(tf2, textvariable=self._track_var,
                     values=self._track_labels,
                     state="readonly", width=20).pack(side="left")
        if len(self._track_labels) == 1:
            tk.Label(tf2, text="(no clips at import frames — will paste to ruler)",
                     fg=DIM, bg=BG, font=F_SMALL).pack(side="left", padx=(8, 0))

        bf = tk.Frame(self, bg=BG)
        bf.pack(fill="x", padx=16, pady=(6, 12))
        TBtn(bf, text="Cancel", command=self.destroy,
             bg=BTN, fg=DIM, padx=8).pack(side="right", padx=(4, 0))
        self._import_btn = TBtn(bf, text="Import", command=self._do_import,
                                bg=ACCENT, fg=BG, padx=8)
        self._import_btn.pack(side="right", padx=4)
        self.bind("<Return>",   lambda _: self._do_import())
        self.bind("<KP_Enter>", lambda _: self._do_import())
        self.bind("<Escape>",   lambda _: self.destroy())

    # ── Population ────────────────────────────────────────────────────────

    def _populate(self):
        self._items.clear()
        self._checked.clear()
        conflicts = 0
        for row in self._rows:
            try:
                rel_frame = int(row.get("Frame", 0)) - self._start_frame
            except (ValueError, TypeError):
                rel_frame = -1
            is_conflict = rel_frame in self._tl_frames
            if is_conflict:
                conflicts += 1
            tags = ("conflict",) if is_conflict else ()
            iid = self._tree.insert("", "end",
                                    values=("☑",
                                            row.get("Timecode", ""),
                                            row.get("Color", ""),
                                            row.get("Name", ""),
                                            row.get("Note", "")),
                                    tags=tags)
            self._checked.add(iid)
            self._items.append((iid, row))

        fname = os.path.basename(self._filepath)
        self._header_var.set(f"{len(self._rows)} markers from {fname}")
        if conflicts:
            self._conflict_var.set(
                f"⚠  {conflicts} conflict{'s' if conflicts != 1 else ''} "
                f"— frame already occupied (shown in amber)"
            )
        self._update_btn()

    # ── Checkbox logic ────────────────────────────────────────────────────

    def _on_click(self, event):
        if self._tree.identify_column(event.x) == "#1":
            item = self._tree.identify_row(event.y)
            if item:
                self._toggle(item)

    def _toggle(self, iid):
        if iid in self._checked:
            self._checked.discard(iid)
            mark = "☐"
        else:
            self._checked.add(iid)
            mark = "☑"
        vals = list(self._tree.item(iid, "values"))
        vals[0] = mark
        self._tree.item(iid, values=vals)
        self._update_btn()

    def _set_state(self, iids, state):
        mark = "☑" if state else "☐"
        for iid in iids:
            vals = list(self._tree.item(iid, "values"))
            vals[0] = mark
            self._tree.item(iid, values=vals)
            if state:
                self._checked.add(iid)
            else:
                self._checked.discard(iid)
        self._update_btn()

    def _check_all(self):       self._set_state([i for i, _ in self._items], True)
    def _uncheck_all(self):     self._set_state([i for i, _ in self._items], False)
    def _check_selected(self):  self._set_state(self._tree.selection(), True)
    def _uncheck_selected(self): self._set_state(self._tree.selection(), False)

    def _update_btn(self):
        n = len(self._checked)
        self._import_btn.config(text=f"Import {n} Marker{'s' if n != 1 else ''}")

    # ── Confirm ───────────────────────────────────────────────────────────

    def _do_import(self):
        selected = [row for iid, row in self._items if iid in self._checked]
        if not selected:
            messagebox.showwarning("Nothing Checked",
                                   "Check at least one marker to import.",
                                   parent=self)
            return
        self.result = selected
        idx = self._track_labels.index(self._track_var.get())
        self.track_result = self._track_data[idx]
        self.destroy()


# ---------------------------------------------------------------------------
# Marker Exchange dialog — bidirectional NLE marker import/export
# ---------------------------------------------------------------------------

class MarkerExchangeDialog(tk.Toplevel):
    """Bidirectional marker exchange between Marker Madness and other NLEs.

    Adobe Premiere Pro — fully functional (CSV format).
    Avid Media Composer — placeholder until locator file format is confirmed.
    """

    def __init__(self, parent, app):
        super().__init__(parent)
        self.withdraw()
        # self.transient(parent) omitted — causes macOS to re-activate the
        # parent when the dialog appears, stealing focus and breaking Comboboxes.
        self.title("Marker Exchange")
        self.resizable(False, False)
        self.configure(bg=BG)
        self._app = app

        self._scope_var       = tk.StringVar(value="all")
        self._offset_var      = tk.StringVar(value="00:00:00:00")
        self._avid_offset_var = tk.StringVar(value="00:00:00:00")

        self._build_ui()
        self.minsize(500, 0)
        center_on_parent(self, parent)
        self.deiconify()
        self.attributes("-topmost", True)
        self.lift()
        self.focus_force()

    def _open_file_dialog(self, fn, *args, **kwargs):
        """Drop topmost on both this dialog and the main window, run a filedialog
        call, then restore everything so we reliably come back to the front."""
        stay = self._app._stay_on_top_var.get()
        if stay:
            self._app.root.attributes("-topmost", False)
        self.attributes("-topmost", False)
        try:
            result = fn(*args, parent=self, **kwargs)
        finally:
            self.attributes("-topmost", True)
            if stay:
                self._app.root.attributes("-topmost", True)
            self.lift()
            self.focus_force()
        return result

    # ── UI ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Title
        tk.Label(self, text="🔄  Marker Exchange", fg=ACCENT, bg=BG,
                 font=("Avenir Next", 16, "bold")).pack(fill="x", padx=20, pady=(18, 2))
        tk.Label(self, text="Move markers between Resolve and other editing applications.",
                 fg=DIM, bg=BG, font=("Avenir Next", 12)).pack(fill="x", padx=20, pady=(0, 14))

        # ── Adobe Premiere Pro ──────────────────────────────────────────────
        pp_frame = tk.LabelFrame(self, text="  Adobe Premiere Pro  ",
                                 fg=ACCENT, bg=BG, font=("Avenir Next", 11),
                                 relief="flat",
                                 highlightbackground=BTN_HOV, highlightthickness=1)
        pp_frame.pack(fill="x", padx=16, pady=(0, 10))

        # Export
        tk.Label(pp_frame, text="Export — Resolve → Premiere Pro",
                 fg=TEXT, bg=BG, font=("Avenir Next", 12, "bold")).pack(
                     anchor="w", padx=14, pady=(12, 2))
        tk.Label(pp_frame,
                 text="Writes a CSV Premiere can open via Markers panel → ☰ → Import Markers.",
                 fg=DIM, bg=BG, font=("Avenir Next", 11)).pack(anchor="w", padx=14, pady=(0, 6))

        scope_f = tk.Frame(pp_frame, bg=BG)
        scope_f.pack(anchor="w", padx=14, pady=(0, 8))
        tk.Label(scope_f, text="Scope:", fg=DIM, bg=BG,
                 font=("Avenir Next", 11)).pack(side="left")
        for val, label in (("all", "All visible"), ("selected", "Selected only")):
            tk.Radiobutton(scope_f, text=label, variable=self._scope_var,
                           value=val, fg=TEXT, bg=BG, selectcolor=BG,
                           activebackground=BG,
                           font=("Avenir Next", 11)).pack(side="left", padx=(8, 0))

        TBtn(pp_frame, text="⬇  Export for Premiere Pro",
             command=self._export_premiere,
             bg=ACCENT, fg=BG, padx=10, pady=5).pack(anchor="w", padx=14, pady=(0, 12))

        # Divider
        tk.Frame(pp_frame, bg=BTN_HOV, height=1).pack(fill="x", padx=14, pady=4)

        # Import
        tk.Label(pp_frame, text="Import — Premiere Pro → Resolve",
                 fg=TEXT, bg=BG, font=("Avenir Next", 12, "bold")).pack(
                     anchor="w", padx=14, pady=(10, 2))
        tk.Label(pp_frame,
                 text="Markers land on the timeline ruler as Red. Recolor in the table afterward.",
                 fg=DIM, bg=BG, font=("Avenir Next", 11)).pack(anchor="w", padx=14, pady=(0, 6))

        off_f = tk.Frame(pp_frame, bg=BG)
        off_f.pack(anchor="w", padx=14, pady=(0, 8))
        tk.Label(off_f, text="TC Offset (optional):",
                 fg=DIM, bg=BG, font=("Avenir Next", 11)).pack(side="left")
        tk.Entry(off_f, textvariable=self._offset_var, width=14,
                 bg=ENTRY_BG, fg=TEXT, insertbackground=TEXT,
                 font=("Avenir Next", 11)).pack(side="left", padx=(8, 0))
        tk.Label(off_f, text="— subtract this from every imported TC",
                 fg=DIM, bg=BG, font=("Avenir Next", 11)).pack(side="left", padx=(6, 0))

        TBtn(pp_frame, text="⬆  Import from Premiere Pro",
             command=self._import_premiere,
             bg=ACCENT, fg=BG, padx=10, pady=5).pack(anchor="w", padx=14, pady=(0, 12))

        # ── Avid Media Composer — Coming Soon ──────────────────────────────
        av_frame = tk.LabelFrame(self, text="  Avid Media Composer  ",
                                 fg=ACCENT, bg=BG, font=("Avenir Next", 11),
                                 relief="flat",
                                 highlightbackground=BTN_HOV, highlightthickness=1)
        av_frame.pack(fill="x", padx=16, pady=(0, 10))

        # Export
        tk.Label(av_frame, text="Export — Resolve → Avid Media Composer",
                 fg=TEXT, bg=BG, font=("Avenir Next", 12, "bold")).pack(
                     anchor="w", padx=14, pady=(12, 2))
        tk.Label(av_frame,
                 text="Writes a tab-delimited locator file. Import in Avid via\n"
                      "Clip menu → Import Locators (or File → Import, filter by .txt).",
                 fg=DIM, bg=BG, font=("Avenir Next", 11), justify="left").pack(
                     anchor="w", padx=14, pady=(0, 6))

        TBtn(av_frame, text="⬇  Export for Avid Media Composer",
             command=self._export_avid,
             bg=ACCENT, fg=BG, padx=10, pady=5).pack(anchor="w", padx=14, pady=(0, 12))

        tk.Frame(av_frame, bg=BTN_HOV, height=1).pack(fill="x", padx=14, pady=4)

        # Import
        tk.Label(av_frame, text="Import — Avid Media Composer → Resolve",
                 fg=TEXT, bg=BG, font=("Avenir Next", 12, "bold")).pack(
                     anchor="w", padx=14, pady=(10, 2))
        tk.Label(av_frame,
                 text="Reads Avid's tab-delimited locator export. Colors are mapped\n"
                      "to the nearest Resolve marker color.",
                 fg=DIM, bg=BG, font=("Avenir Next", 11), justify="left").pack(
                     anchor="w", padx=14, pady=(0, 6))

        av_off_f = tk.Frame(av_frame, bg=BG)
        av_off_f.pack(anchor="w", padx=14, pady=(0, 8))
        tk.Label(av_off_f, text="TC Offset (optional):",
                 fg=DIM, bg=BG, font=("Avenir Next", 11)).pack(side="left")
        tk.Entry(av_off_f, textvariable=self._avid_offset_var, width=14,
                 bg=ENTRY_BG, fg=TEXT, insertbackground=TEXT,
                 font=("Avenir Next", 11)).pack(side="left", padx=(8, 0))
        tk.Label(av_off_f, text="— subtract this from every imported TC",
                 fg=DIM, bg=BG, font=("Avenir Next", 11)).pack(side="left", padx=(6, 0))

        TBtn(av_frame, text="⬆  Import from Avid Media Composer",
             command=self._import_avid,
             bg=ACCENT, fg=BG, padx=10, pady=5).pack(anchor="w", padx=14, pady=(0, 12))

        # ── Close ───────────────────────────────────────────────────────────
        tk.Frame(self, bg=BTN_HOV, height=1).pack(fill="x", padx=16, pady=(4, 0))
        bf = tk.Frame(self, bg=BG)
        bf.pack(fill="x", padx=16, pady=10)
        TBtn(bf, text="Close", command=self.destroy,
             bg=ACCENT, fg=BG, padx=14, pady=5).pack(side="right")

    # ── Export to Premiere Pro ──────────────────────────────────────────────

    def _export_premiere(self):
        app = self._app
        if not app._all_markers:
            messagebox.showinfo("Export", "No markers to export.", parent=self)
            return

        visible, selected = app._get_filtered_markers()
        targets = selected if self._scope_var.get() == "selected" else visible
        if not targets:
            messagebox.showinfo("Export",
                                "No markers in the current scope.", parent=self)
            return

        fps         = app._fps
        start_frame = app._start_frame

        # Build a safe default filename
        safe = "markers"
        if app._timeline:
            safe = "".join(c if c.isalnum() or c in " -_" else "_"
                           for c in app._timeline.GetName()) + "_premiere"

        path = self._open_file_dialog(
            filedialog.asksaveasfilename,
            title="Export Markers for Premiere Pro",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"{safe}.csv",
        )
        if not path:
            return

        # Drop-frame detection — Premiere uses ; as the frame separator for DF
        fps_r = round(fps)
        is_df = fps_r in (30, 60) and (fps < fps_r)

        def _to_tc(frame):
            tc = frames_to_tc(frame, fps)
            if is_df:
                tc = tc[:8] + ";" + tc[9:]
            return tc

        try:
            with open(path, "w", newline="", encoding="utf-8") as fh:
                writer = csv.writer(fh)
                writer.writerow(["Marker Name", "Description", "In", "Out",
                                  "Duration", "Marker Type"])
                for rec in targets:
                    abs_frame = rec["timeline_frame"] + start_frame
                    dur       = max(int(rec.get("duration", 1)), 1)
                    in_tc     = _to_tc(abs_frame)
                    out_tc    = _to_tc(abs_frame + dur - 1)
                    # Premiere Duration column = out_frame - in_frame
                    # (0 for a 1-frame marker; we write the difference)
                    dur_tc    = _to_tc(dur - 1)
                    writer.writerow([
                        rec.get("name",  ""),
                        rec.get("note",  ""),
                        in_tc, out_tc, dur_tc,
                        "Comment",
                    ])
        except Exception as exc:
            messagebox.showerror("Export Failed",
                                 f"Could not write file:\n{exc}", parent=self)
            return

        messagebox.showinfo(
            "Export Complete",
            f"Exported {len(targets)} marker(s) to:\n{os.path.basename(path)}\n\n"
            "In Premiere Pro: Markers panel → ☰ menu → Import Markers.",
            parent=self,
        )

    # ── Import from Premiere Pro ────────────────────────────────────────────

    def _import_premiere(self):
        app = self._app
        timeline, err = app._fresh_timeline()
        if not timeline:
            messagebox.showwarning("Not Connected", err, parent=self)
            return

        path = self._open_file_dialog(
            filedialog.askopenfilename,
            title="Import Premiere Pro Markers",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return

        # Parse optional TC offset
        offset_frames = 0
        offset_raw = self._offset_var.get().strip()
        if offset_raw and offset_raw not in ("00:00:00:00", "0", ""):
            offset_frames = tc_to_frames(offset_raw, app._fps)

        # Read file (utf-8-sig handles Premiere's occasional BOM)
        raw_rows = []
        try:
            with open(path, newline="", encoding="utf-8-sig") as fh:
                raw_rows = list(csv.DictReader(fh))
        except Exception as exc:
            messagebox.showerror("Import Failed",
                                 f"Could not read file:\n{exc}", parent=self)
            return

        if not raw_rows:
            messagebox.showinfo("Import", "The file is empty.", parent=self)
            return

        # Auto-detect column names — tolerate slight variations between
        # Premiere versions and user-exported CSVs
        headers  = list(raw_rows[0].keys())
        def _find(candidates):
            return next((h for h in headers
                         if h.strip().lower() in candidates), None)

        name_col = _find({"marker name", "name"})
        desc_col = _find({"description", "note", "comment", "notes"})
        in_col   = _find({"in", "start", "timecode", "marker in"})
        dur_col  = _find({"duration", "dur"})

        if in_col is None:
            messagebox.showerror(
                "Unrecognised Format",
                "Could not find a start-timecode column ('In' or 'Start').\n\n"
                f"Columns found: {', '.join(headers)}",
                parent=self,
            )
            return

        # Convert to Marker Madness row format
        converted   = []
        skipped_bad = 0
        for row in raw_rows:
            tc_str = row.get(in_col, "").strip().replace(";", ":")
            if not tc_str:
                skipped_bad += 1
                continue
            abs_frame = tc_to_frames(tc_str, app._fps) - offset_frames
            if abs_frame < 0:
                skipped_bad += 1
                continue

            # Premiere stores Duration as out_frame - in_frame (0 for a 1-frame marker)
            dur_frames = 1
            if dur_col:
                dur_raw = row.get(dur_col, "").strip().replace(";", ":")
                if dur_raw:
                    dur_frames = max(tc_to_frames(dur_raw, app._fps) + 1, 1)

            converted.append({
                "Frame":      str(abs_frame),
                "Color":      "Red",
                "Name":       row.get(name_col, "").strip() if name_col else "",
                "Note":       row.get(desc_col, "").strip() if desc_col else "",
                "Marker Dur": str(dur_frames),
            })

        if not converted:
            detail = (f"\n\n{skipped_bad} row(s) had missing or unreadable timecodes."
                      if skipped_bad else "")
            messagebox.showinfo("Import",
                                f"No valid markers found after parsing.{detail}",
                                parent=self)
            return

        # Hand off to the main app import path
        self.withdraw()
        app._import_rows_from_exchange(
            converted,
            source_label=f"Premiere Pro — {os.path.basename(path)}"
        )
        self.deiconify()
        self.lift()

    # ── Export to Avid Media Composer ───────────────────────────────────────

    # Avid locator colors → nearest Resolve color
    _AVID_TO_RESOLVE = {
        "red":     "Red",
        "yellow":  "Yellow",
        "green":   "Green",
        "cyan":    "Cyan",
        "blue":    "Blue",
        "white":   "Cream",
        "black":   "Blue",
        "magenta": "Fuchsia",
        "violet":  "Lavender",
        "pink":    "Pink",
    }

    # Resolve color → nearest Avid locator color
    _RESOLVE_TO_AVID = {
        "Blue":     "Blue",
        "Cyan":     "Cyan",
        "Green":    "Green",
        "Yellow":   "Yellow",
        "Red":      "Red",
        "Pink":     "Red",
        "Purple":   "Blue",
        "Fuchsia":  "Cyan",
        "Rose":     "Red",
        "Lavender": "Blue",
        "Sky":      "Cyan",
        "Mint":     "Green",
        "Lemon":    "Yellow",
        "Sand":     "Yellow",
        "Cocoa":    "Red",
        "Cream":    "White",
    }

    def _avid_track_label(self, rec):
        """Return Avid track string for a marker record (TC1, V1, A1, etc.)."""
        if rec.get("type") == "Timeline":
            return "TC1"
        ttype = rec.get("track_type", "")
        tidx  = rec.get("track_index", 1)
        if ttype == "video":
            return f"V{tidx}"
        if ttype == "audio":
            return f"A{tidx}"
        return "TC1"

    def _export_avid(self):
        app = self._app
        if not app._all_markers:
            messagebox.showinfo("Export", "No markers to export.", parent=self)
            return

        visible, selected = app._get_filtered_markers()
        targets = selected if self._scope_var.get() == "selected" else visible
        if not targets:
            messagebox.showinfo("Export",
                                "No markers in the current scope.", parent=self)
            return

        fps         = app._fps
        start_frame = app._start_frame
        seq_name    = app._timeline.GetName() if app._timeline else "Sequence"

        safe = "".join(c if c.isalnum() or c in " -_" else "_"
                       for c in seq_name) + "_avid_locators"

        path = self._open_file_dialog(
            filedialog.asksaveasfilename,
            title="Export Locators for Avid Media Composer",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"{safe}.txt",
        )
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8") as fh:
                for rec in targets:
                    abs_frame   = rec["timeline_frame"] + start_frame
                    tc          = frames_to_tc(abs_frame, fps)
                    track_label = self._avid_track_label(rec)
                    avid_color  = self._RESOLVE_TO_AVID.get(rec.get("color", "Blue"), "Blue")
                    comment     = rec.get("name", "")
                    # Avid format: seq \t TC \t track \t color \t comment \t 1 \t \t color
                    fh.write(f"{seq_name}\t{tc}\t{track_label}\t{avid_color}"
                             f"\t{comment}\t1\t\t{avid_color}\n")
        except Exception as exc:
            messagebox.showerror("Export Failed",
                                 f"Could not write file:\n{exc}", parent=self)
            return

        messagebox.showinfo(
            "Export Complete",
            f"Exported {len(targets)} locator(s) to:\n{os.path.basename(path)}\n\n"
            "In Avid: Clip menu → Import Locators, or File → Import and select the .txt file.",
            parent=self,
        )

    # ── Import from Avid Media Composer ─────────────────────────────────────

    def _import_avid(self):
        app = self._app
        timeline, err = app._fresh_timeline()
        if not timeline:
            messagebox.showwarning("Not Connected", err, parent=self)
            return

        path = self._open_file_dialog(
            filedialog.askopenfilename,
            title="Import Avid Media Composer Locators",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return

        # Parse optional TC offset
        offset_frames = 0
        offset_raw = self._avid_offset_var.get().strip()
        if offset_raw and offset_raw not in ("00:00:00:00", "0", ""):
            offset_frames = tc_to_frames(offset_raw, app._fps)

        raw_lines = []
        try:
            with open(path, newline="", encoding="utf-8-sig") as fh:
                raw_lines = [ln.rstrip("\n\r") for ln in fh if ln.strip()]
        except Exception as exc:
            messagebox.showerror("Import Failed",
                                 f"Could not read file:\n{exc}", parent=self)
            return

        if not raw_lines:
            messagebox.showinfo("Import", "The file is empty.", parent=self)
            return

        # Avid locator format (tab-delimited, no header):
        #   col0: sequence name
        #   col1: timecode  HH:MM:SS:FF
        #   col2: track     TC1 / V1 / V2 / A1 / A2 …
        #   col3: color
        #   col4: comment / locator text
        #   col5: duration (always "1")
        #   col6: (empty)
        #   col7: color (repeat of col3)
        converted   = []
        skipped_bad = 0
        for line in raw_lines:
            parts = line.split("\t")
            if len(parts) < 5:
                skipped_bad += 1
                continue

            tc_str = parts[1].strip() if len(parts) > 1 else ""
            if not tc_str:
                skipped_bad += 1
                continue

            abs_frame = tc_to_frames(tc_str, app._fps) - offset_frames
            if abs_frame < 0:
                skipped_bad += 1
                continue

            avid_color   = parts[3].strip().lower() if len(parts) > 3 else ""
            resolve_color = self._AVID_TO_RESOLVE.get(avid_color, "Red")
            comment      = parts[4].strip() if len(parts) > 4 else ""

            converted.append({
                "Frame":      str(abs_frame),
                "Color":      resolve_color,
                "Name":       comment,
                "Note":       "",
                "Marker Dur": "1",
            })

        if not converted:
            detail = (f"\n\n{skipped_bad} line(s) had missing or unreadable timecodes."
                      if skipped_bad else "")
            messagebox.showinfo("Import",
                                f"No valid locators found after parsing.{detail}",
                                parent=self)
            return

        self.withdraw()
        app._import_rows_from_exchange(
            converted,
            source_label=f"Avid — {os.path.basename(path)}"
        )
        self.deiconify()
        self.lift()


# ---------------------------------------------------------------------------
# Shot Change Report dialog
# ---------------------------------------------------------------------------

class ShotChangeReportDialog(tk.Toplevel):
    """Compare two Marker Madness CSV exports and produce a shot change report.

    Reads marker Name as the matching key.  Compares clip duration and color.
    Produces an interactive table plus optional CSV / HTML export.
    """

    COLS = [
        ("name",         "Marker Name",        200),
        ("clip_name",    "Clip Name",          160),
        ("before_dur",   "Before Duration",    110),
        ("after_dur",    "After Duration",     110),
        ("change",       "Frame Change +/-",   110),
        ("before_color", "Before Color",        90),
        ("after_color",  "After Color",         90),
        ("status",       "Status",              80),
    ]

    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()
        # self.transient(parent) omitted — causes macOS to re-activate the
        # parent when the dialog appears, stealing focus and breaking Comboboxes.
        self.title("Shot Change Report")
        self.resizable(True, True)
        self.configure(bg=BG)

        self._before_path  = tk.StringVar()
        self._after_path   = tk.StringVar()
        self._thumb_path   = tk.StringVar()
        self._changes_only = tk.BooleanVar(value=True)
        self._sort_var     = tk.StringVar(value="Timeline Order")
        self._results      = []

        self._build_ui()
        self.minsize(880, 520)
        center_on_parent(self, parent)
        self.deiconify()
        self.lift()
        self.focus_force()
        self.attributes("-topmost", True)

    # ── UI construction ───────────────────────────────────────────────────

    def _build_ui(self):
        # File pickers
        pf = tk.LabelFrame(self, text=" CSV Files ", fg=TEXT, bg=BG,
                           font=F_SMALL, padx=12, pady=8)
        pf.pack(fill="x", padx=16, pady=(12, 4))

        for label, var, cmd in [
            ("Before (original):", self._before_path, self._pick_before),
            ("After (revised):",   self._after_path,  self._pick_after),
        ]:
            row = tk.Frame(pf, bg=BG)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=label, fg=TEXT, bg=BG, font=F_SMALL,
                     width=18, anchor="w").pack(side="left")
            tk.Entry(row, textvariable=var, bg=ENTRY_BG, fg=TEXT,
                     insertbackground=TEXT, relief="flat",
                     font=F_SMALL).pack(side="left", fill="x", expand=True, padx=(0, 6))
            TBtn(row, text="Browse…", command=cmd,
                 bg=BTN, fg=DIM, padx=6, pady=2).pack(side="left")

        th_row = tk.Frame(pf, bg=BG)
        th_row.pack(fill="x", pady=3)
        tk.Label(th_row, text="Thumbnails (optional):", fg=TEXT, bg=BG,
                 font=F_SMALL, width=18, anchor="w").pack(side="left")
        tk.Entry(th_row, textvariable=self._thumb_path, bg=ENTRY_BG, fg=TEXT,
                 insertbackground=TEXT, relief="flat",
                 font=F_SMALL).pack(side="left", fill="x", expand=True, padx=(0, 6))
        TBtn(th_row, text="Browse…", command=self._pick_thumbs,
             bg=BTN, fg=DIM, padx=6, pady=2).pack(side="left")
        tk.Label(th_row, text="← folder from After timeline's batch frame export",
                 fg=DIM, bg=BG, font=("Avenir Next", 9)).pack(side="left", padx=(8, 0))

        # Options row
        of = tk.Frame(self, bg=BG)
        of.pack(fill="x", padx=16, pady=4)

        tk.Checkbutton(of, text="Changes only (hide unchanged shots)",
                       variable=self._changes_only,
                       fg=TEXT, bg=BG, activeforeground=TEXT, activebackground=BG,
                       selectcolor=ENTRY_BG, font=F_SMALL).pack(side="left")
        tk.Label(of, text="  Sort:", fg=TEXT, bg=BG, font=F_SMALL).pack(side="left", padx=(16, 4))
        ttk.Combobox(of, textvariable=self._sort_var,
                     values=["Timeline Order", "Marker Name"],
                     state="readonly", width=16).pack(side="left")
        TBtn(of, text="⟳  Generate", command=self._generate,
             bg=ACCENT, fg=BG).pack(side="right")

        # Results table
        tf = tk.Frame(self, bg=BG)
        tf.pack(fill="both", expand=True, padx=16, pady=(8, 4))

        vsb = ttk.Scrollbar(tf, orient="vertical")
        vsb.pack(side="right", fill="y")

        self._tree = ttk.Treeview(
            tf,
            columns=[c[0] for c in self.COLS],
            show="headings",
            yscrollcommand=vsb.set,
            selectmode="browse",
        )
        vsb.config(command=self._tree.yview)

        for col_id, heading, width in self.COLS:
            self._tree.heading(col_id, text=heading)
            anchor = "center" if col_id in ("change", "status") else "w"
            self._tree.column(col_id, width=width, anchor=anchor,
                              stretch=(col_id in ("name", "clip_name")))

        self._tree.tag_configure("changed",   foreground="#ffffff")
        self._tree.tag_configure("slipped",   foreground="#7ec8e3")
        self._tree.tag_configure("dropped",   foreground="#e05555")
        self._tree.tag_configure("added",     foreground="#4caf7d")
        self._tree.tag_configure("unchanged", foreground="#ffa500")
        self._tree.pack(side="left", fill="both", expand=True)

        # Bottom bar
        bf = tk.Frame(self, bg=BG)
        bf.pack(fill="x", padx=16, pady=(0, 12))

        self._status_var = tk.StringVar(value="Load two CSV files and click Generate.")
        tk.Label(bf, textvariable=self._status_var,
                 fg=TEXT, bg=BG, font=F_SMALL).pack(side="left")

        TBtn(bf, text="✕  Close", command=self.destroy,
             bg=BTN, fg=DIM, padx=8).pack(side="right", padx=(4, 0))
        self._export_html_btn = TBtn(bf, text="⬇ Export HTML",
                                     command=self._export_html,
                                     bg=GREEN, fg=BG, padx=8)
        self._export_html_btn.pack(side="right", padx=4)
        self._export_csv_btn = TBtn(bf, text="⬇ Export CSV",
                                    command=self._export_csv,
                                    bg=GREEN, fg=BG, padx=8)
        self._export_csv_btn.pack(side="right", padx=4)
        self._export_html_btn.config(state="disabled")
        self._export_csv_btn.config(state="disabled")

    # ── File pickers ──────────────────────────────────────────────────────

    def _open_file_dialog(self, fn, *args, **kwargs):
        """Temporarily drop topmost before opening a file dialog so it isn't hidden."""
        main_topmost = bool(self.master.attributes("-topmost"))
        if main_topmost:
            self.master.attributes("-topmost", False)
        self.attributes("-topmost", False)
        try:
            result = fn(*args, parent=self, **kwargs)
        finally:
            self.attributes("-topmost", True)
            if main_topmost:
                self.master.attributes("-topmost", True)
            self.lift()
            self.focus_force()
        return result

    def _pick_before(self):
        p = self._open_file_dialog(
            filedialog.askopenfilename,
            title="Select Before CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if p:
            self._before_path.set(p)

    def _pick_after(self):
        p = self._open_file_dialog(
            filedialog.askopenfilename,
            title="Select After CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if p:
            self._after_path.set(p)

    def _pick_thumbs(self):
        # Default to the directory of the After CSV; fall back to Before if
        # After isn't set yet; fall back to the system default if neither is.
        initial = ""
        for candidate in (self._after_path.get(), self._before_path.get()):
            if candidate:
                d = os.path.dirname(candidate)
                if os.path.isdir(d):
                    initial = d
                    break
        kw = {"title": "Select Thumbnails Folder"}
        if initial:
            kw["initialdir"] = initial
        p = self._open_file_dialog(filedialog.askdirectory, **kw)
        if p:
            self._thumb_path.set(p)

    # ── CSV reading & comparison ──────────────────────────────────────────

    def _read_csv(self, path):
        rows = []
        try:
            with open(path, newline="", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    rows.append(row)
        except Exception as exc:
            messagebox.showerror("CSV Error",
                                 f"Could not read:\n{path}\n\n{exc}", parent=self)
        return rows

    def _dur_display(self, row):
        tc = (row.get("Clip Duration") or "").strip()
        if tc:
            return tc[3:] if tc.startswith("00:") else tc
        f = (row.get("Clip Dur frames") or "").strip()
        return f"{f}f" if f else "—"

    def _dur_frames(self, row):
        try:
            return int((row.get("Clip Dur frames") or "").strip())
        except (ValueError, AttributeError):
            return None

    def _infer_fps(self, rows):
        """Infer project fps from rows that have both Clip Duration (TC) and Clip Dur frames."""
        from collections import Counter
        known = [23.976, 24.0, 25.0, 29.97, 30.0, 48.0, 50.0, 59.94, 60.0]
        candidates = Counter()
        for row in rows:
            dur_f = self._dur_frames(row)
            if dur_f is None or dur_f <= 0:
                continue
            tc = (row.get("Clip Duration") or "").strip().replace(";", ":")
            parts = tc.split(":")
            if len(parts) != 4:
                continue
            try:
                hh, mm, ss, ff = [int(p) for p in parts]
            except ValueError:
                continue
            total_secs = hh * 3600 + mm * 60 + ss
            if total_secs < 1:
                continue
            est = (dur_f - ff) / total_secs
            closest = min(known, key=lambda f: abs(f - est))
            if abs(closest - est) / closest < 0.1:
                candidates[closest] += 1
        if not candidates:
            return None
        return candidates.most_common(1)[0][0]

    def _compute_slip(self, b_row, a_row, fps):
        """Return signed slip delta in frames, or None if not slipped / data missing.

        Compares the marker's offset from Clip In before and after, so it
        correctly detects slips even when the clip moved in the timeline due
        to ripple trims on other shots.  Returns 0 (sentinel) when a slip is
        detected but fps is unknown (no frame count available).
        """
        def norm(s):
            return (s or "").strip().replace(";", ":")

        b_tc      = norm(b_row.get("Timecode", ""))
        a_tc      = norm(a_row.get("Timecode", ""))
        b_clip_in = norm(b_row.get("Clip In",  ""))
        a_clip_in = norm(a_row.get("Clip In",  ""))

        if not (b_tc and a_tc and b_clip_in and a_clip_in):
            return None

        if fps is not None:
            b_offset = tc_to_frames(b_tc, fps) - tc_to_frames(b_clip_in, fps)
            a_offset = tc_to_frames(a_tc, fps) - tc_to_frames(a_clip_in, fps)
            delta = a_offset - b_offset
            return delta if delta != 0 else None
        else:
            # Fallback without fps: require Clip In unchanged (original behaviour)
            if b_clip_in != a_clip_in or b_tc == a_tc:
                return None
            return 0  # slip confirmed but delta unknown

    def _tc_sort_key(self, row):
        tc = (row.get("Timecode") or "").replace(";", ":")
        parts = tc.split(":")
        if len(parts) == 4:
            try:
                hh, mm, ss, ff = [int(p) for p in parts]
                return hh * 3600000 + mm * 60000 + ss * 1000 + ff
            except ValueError:
                pass
        return 0

    def _row_key(self, row):
        """Composite match key: (marker Name, Clip Name).
        Same marker name on a different clip is treated as a distinct shot.
        Unnamed markers fall back to timecode as the name component."""
        name = row.get("Name", "").strip()
        if not name:
            tc = row.get("Timecode", "").strip()
            if not tc:
                return None
            name = f"[TC:{tc}]"
        clip = row.get("Clip", "").strip()
        return (name, clip)

    def _build_comparison(self, before_rows, after_rows, fps=None):
        before_map = {}
        for r in before_rows:
            key = self._row_key(r)
            if key:
                before_map[key] = r

        after_map = {}
        for r in after_rows:
            key = self._row_key(r)
            if key:
                after_map[key] = r

        results = []

        for (disp_name, b_clip), b in before_map.items():
            a = after_map.get((disp_name, b_clip))
            if a is None:
                results.append({
                    "name": disp_name, "clip_name": b_clip,
                    "before_dur": self._dur_display(b),
                    "after_dur": "—", "change": "—",
                    "before_color": b.get("Color", ""), "after_color": "—",
                    "status": "Dropped", "tag": "dropped",
                    "tc_key": self._tc_sort_key(b),
                    "tc_str": b.get("Timecode", "").replace(";", ":"),
                })
            else:
                b_f = self._dur_frames(b)
                a_f = self._dur_frames(a)
                b_col = b.get("Color", "").strip()
                a_col = a.get("Color", "").strip()

                slip_delta  = self._compute_slip(b, a, fps)
                slipped     = slip_delta is not None
                dur_changed = (b_f is not None and a_f is not None and b_f != a_f)
                col_changed = (b_col != a_col)
                changed     = dur_changed or col_changed or slipped

                if dur_changed and b_f is not None and a_f is not None:
                    d = a_f - b_f
                    change_str = f"+{d}" if d > 0 else str(d)
                elif slipped:
                    if slip_delta:  # non-zero: we have the frame count
                        change_str = f"+{slip_delta}" if slip_delta > 0 else str(slip_delta)
                    else:           # 0 sentinel: slip confirmed, fps unavailable
                        change_str = "Slipped"
                else:
                    change_str = "—"

                pure_slip = slipped and not dur_changed and not col_changed
                results.append({
                    "name": disp_name, "clip_name": b_clip,
                    "before_dur": self._dur_display(b),
                    "after_dur": self._dur_display(a), "change": change_str,
                    "before_color": b_col, "after_color": a_col,
                    "status": "Slipped" if pure_slip else ("Changed" if changed else "Unchanged"),
                    "tag":    "slipped" if pure_slip else ("changed" if changed else "unchanged"),
                    "tc_key": self._tc_sort_key(a),
                    "tc_str": a.get("Timecode", "").replace(";", ":"),
                })

        for (disp_name, a_clip), a in after_map.items():
            if (disp_name, a_clip) not in before_map:
                results.append({
                    "name": disp_name, "clip_name": a_clip,
                    "before_dur": "—",
                    "after_dur": self._dur_display(a), "change": "—",
                    "before_color": "—", "after_color": a.get("Color", ""),
                    "status": "Added", "tag": "added",
                    "tc_key": self._tc_sort_key(a),
                    "tc_str": a.get("Timecode", "").replace(";", ":"),
                })

        return results

    # ── Generate ──────────────────────────────────────────────────────────

    def _generate(self):
        before_path = self._before_path.get().strip()
        after_path  = self._after_path.get().strip()
        if not before_path or not after_path:
            messagebox.showwarning("Missing Files",
                                   "Please select both a Before and After CSV file.",
                                   parent=self)
            return

        before_rows = self._read_csv(before_path)
        after_rows  = self._read_csv(after_path)
        if not before_rows and not after_rows:
            return

        fps = self._infer_fps(before_rows + after_rows)
        results = self._build_comparison(before_rows, after_rows, fps)

        if self._sort_var.get() == "Marker Name":
            results.sort(key=lambda r: r["name"].lower())
        else:
            results.sort(key=lambda r: r["tc_key"])

        self._results = results
        self._populate_table()

        changed   = sum(1 for r in results if r["status"] == "Changed")
        slipped   = sum(1 for r in results if r["status"] == "Slipped")
        dropped   = sum(1 for r in results if r["status"] == "Dropped")
        added     = sum(1 for r in results if r["status"] == "Added")
        unchanged = sum(1 for r in results if r["status"] == "Unchanged")
        parts = [f"{len(results)} shots total"]
        if changed:   parts.append(f"{changed} changed")
        if slipped:   parts.append(f"{slipped} slipped")
        if dropped:   parts.append(f"{dropped} dropped")
        if added:     parts.append(f"{added} added")
        if unchanged: parts.append(f"{unchanged} unchanged")
        self._status_var.set("  ·  ".join(parts))

        if results:
            self._export_csv_btn.config(state="normal")
            self._export_html_btn.config(state="normal")

    def _populate_table(self):
        self._tree.delete(*self._tree.get_children())
        changes_only = self._changes_only.get()
        for r in self._results:
            if changes_only and r["status"] == "Unchanged":
                continue
            self._tree.insert("", "end",
                              values=(r["name"], r["clip_name"],
                                      r["before_dur"], r["after_dur"],
                                      r["change"], r["before_color"],
                                      r["after_color"], r["status"]),
                              tags=(r["tag"],))

    # ── Thumbnail lookup ──────────────────────────────────────────────────

    def _find_thumbnail(self, shot_name, thumb_folder, timecode=""):
        if not thumb_folder or not os.path.isdir(thumb_folder):
            return ""
        # Timecode-first: thumbnail filenames contain TC as HH-MM-SS-FF
        if timecode:
            tc_slug = timecode.replace(":", "-").replace(";", "-")
            for fname in os.listdir(thumb_folder):
                if tc_slug in fname:
                    return os.path.join(thumb_folder, fname)
        # Fall back to name slug match
        slug = "".join(c if c.isalnum() or c in " -_" else "_"
                       for c in shot_name).lower()
        for fname in os.listdir(thumb_folder):
            if slug in fname.lower():
                return os.path.join(thumb_folder, fname)
        return ""

    # ── Export ────────────────────────────────────────────────────────────

    def _export_csv(self):
        if not self._results:
            return
        before_stem = os.path.splitext(os.path.basename(self._before_path.get()))[0]
        default_name = f"{before_stem}_change_report.csv" if before_stem else "shot_change_report.csv"
        path = self._open_file_dialog(
            filedialog.asksaveasfilename,
            title="Save Shot Change Report",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=default_name,
        )
        if not path:
            return
        try:
            changes_only = self._changes_only.get()
            with open(path, "w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                w.writerow(["Marker Name", "Clip Name", "Before Duration",
                             "After Duration", "Change (frames)",
                             "Before Color", "After Color", "Status"])
                for r in self._results:
                    if changes_only and r["status"] == "Unchanged":
                        continue
                    w.writerow([r["name"], r["clip_name"],
                                r["before_dur"], r["after_dur"],
                                r["change"], r["before_color"], r["after_color"],
                                r["status"]])
            messagebox.showinfo("Exported", f"Report saved to:\n{path}", parent=self)
        except Exception as exc:
            messagebox.showerror("Export Error", str(exc), parent=self)

    def _export_html(self):
        if not self._results:
            return
        before_stem = os.path.splitext(os.path.basename(self._before_path.get()))[0]
        default_name = f"{before_stem}_change_report.html" if before_stem else "shot_change_report.html"
        path = self._open_file_dialog(
            filedialog.asksaveasfilename,
            title="Save Shot Change Report (HTML)",
            defaultextension=".html",
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")],
            initialfile=default_name,
        )
        if not path:
            return

        thumb_folder = self._thumb_path.get().strip()
        changes_only = self._changes_only.get()

        def esc(s):
            return str(s).replace("&", "&amp;").replace("<", "&lt;")

        STATUS_STYLE = {
            "Changed":   "color:#b87800;font-weight:600",
            "Slipped":   "color:#5b9bd5;font-weight:600",
            "Dropped":   "color:#cc3333;font-weight:600",
            "Added":     "color:#2a7a4f;font-weight:600",
            "Unchanged": "color:#999",
        }

        rows_html = []
        for r in self._results:
            if changes_only and r["status"] == "Unchanged":
                continue

            img_cell = ""
            if thumb_folder:
                tp = self._find_thumbnail(r["name"], thumb_folder, r.get("tc_str", ""))
                if tp:
                    rel = os.path.relpath(tp, os.path.dirname(path))
                    img_cell = (f'<td><img src="{rel}" '
                                f'style="max-height:60px;border-radius:3px;"></td>')
                else:
                    img_cell = "<td></td>"

            def color_dot(cname):
                if cname in ("—", ""):
                    return esc(cname)
                h = COLOR_HEX.get(cname, "#888")
                dot = (f"<span style='display:inline-block;width:10px;height:10px;"
                       f"border-radius:50%;background:{h};margin-right:5px;"
                       f"vertical-align:middle'></span>")
                return dot + esc(cname)

            chg = r["change"]
            if chg.startswith("+"):
                chg_style = "color:#cc3333;font-weight:600;font-family:monospace"
            elif chg.startswith("-"):
                chg_style = "color:#2a7a4f;font-weight:600;font-family:monospace"
            else:
                chg_style = "font-family:monospace;color:#999"

            st_style = STATUS_STYLE.get(r["status"], "")
            rows_html.append(
                f"<tr>"
                f"{img_cell}"
                f"<td>{esc(r['name'])}</td>"
                f"<td style='color:#555'>{esc(r['clip_name'])}</td>"
                f"<td style='font-family:monospace'>{esc(r['before_dur'])}</td>"
                f"<td style='font-family:monospace'>{esc(r['after_dur'])}</td>"
                f"<td style='text-align:center;{chg_style}'>{esc(chg)}</td>"
                f"<td>{color_dot(r['before_color'])}</td>"
                f"<td>{color_dot(r['after_color'])}</td>"
                f"<td style='text-align:center;{st_style}'>{esc(r['status'])}</td>"
                f"</tr>"
            )

        thumb_th    = "<th>Frame</th>" if thumb_folder else ""
        date_str    = datetime.datetime.now().strftime("%B %d, %Y")
        before_name = esc(os.path.basename(self._before_path.get()))
        after_name  = esc(os.path.basename(self._after_path.get()))
        title_stem  = esc(os.path.splitext(os.path.basename(path))[0])

        html = (
            "<!DOCTYPE html>\n<html lang='en'>\n<head>\n<meta charset='utf-8'>\n"
            f"<title>{title_stem}</title>\n<style>\n"
            "body{background:#fff;color:#111;font-family:Helvetica,Arial,sans-serif;"
            "padding:32px 40px;margin:0}\n"
            "header{margin-bottom:24px}\n"
            "header h1{margin:0 0 4px;font-size:22px;font-weight:700}\n"
            "header p{margin:0;font-size:13px;color:#666}\n"
            "table{border-collapse:collapse;width:100%;font-size:13px}\n"
            "th{background:#f4f4f4;padding:8px 12px;text-align:left;"
            "font-weight:600;color:#333;border:1px solid #ddd}\n"
            "td{padding:7px 12px;border:1px solid #ddd;vertical-align:middle}\n"
            "tr:nth-child(even) td{background:#fafafa}\n"
            "tr:hover td{background:#f0f4ff}\n"
            "footer{margin-top:24px;font-size:11px;color:#aaa;text-align:right}\n"
            "@media print{body{padding:16px}tr:hover td{background:inherit}}\n"
            "</style>\n</head>\n<body>\n"
            f"<header>\n<h1>{title_stem}</h1>\n"
            f"<p>Before: <strong>{before_name}</strong>"
            f"&nbsp;&nbsp;→&nbsp;&nbsp;After: <strong>{after_name}</strong>"
            f"&nbsp;&nbsp;·&nbsp;&nbsp;{date_str}</p>\n</header>\n"
            "<table>\n"
            f"<tr>{thumb_th}<th>Marker Name</th><th>Clip Name</th>"
            "<th>Before Duration</th><th>After Duration</th><th>Change</th>"
            "<th>Before Color</th><th>After Color</th><th>Status</th></tr>\n"
            + "\n".join(rows_html)
            + "\n</table>\n"
            "<footer>Generated by Marker Madness</footer>\n"
            "</body>\n</html>"
        )

        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(html)
            messagebox.showinfo("Exported", f"HTML report saved to:\n{path}", parent=self)
        except Exception as exc:
            messagebox.showerror("Export Error", str(exc), parent=self)


# ---------------------------------------------------------------------------
# Batch frame-export progress dialog
# ---------------------------------------------------------------------------

class BatchExportDialog(tk.Toplevel):
    """Non-blocking progress window shown during batch frame export."""

    def __init__(self, parent, total: int):
        super().__init__(parent)
        self.withdraw()
        # self.transient(parent) omitted — causes macOS to re-activate the
        # parent when the dialog appears, stealing focus and breaking Comboboxes.
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

        _pb_style = ttk.Style()
        _pb_style.configure("MM.Horizontal.TProgressbar",
                            troughcolor=ENTRY_BG,
                            background=ACCENT,
                            lightcolor=ACCENT,
                            darkcolor=ACCENT)
        self._bar = ttk.Progressbar(self, style="MM.Horizontal.TProgressbar",
                                    orient="horizontal", length=360,
                                    mode="determinate", maximum=total)
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
        # self.transient(parent) omitted — causes macOS to re-activate the
        # parent when the dialog appears, stealing focus and breaking Comboboxes.
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
        # self.transient(parent) omitted — causes macOS to re-activate the
        # parent when the dialog appears, stealing focus and breaking Comboboxes.
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

        # Column presets
        preset_row = tk.Frame(col_frame, bg=BG)
        preset_row.pack(anchor="w", padx=12, pady=(2, 4))
        tk.Label(preset_row, text="Preset:", fg=DIM, bg=BG, font=F_SMALL).pack(side="left", padx=(0, 6))
        TBtn(preset_row, text="🖨  Print-friendly", command=self._apply_print_preset,
             bg=ACCENT, fg=BG, font=F_SMALL).pack(side="left", padx=(0, 4))
        TBtn(preset_row, text="All columns", command=self._apply_all_preset,
             bg=ACCENT, fg=BG, font=F_SMALL).pack(side="left")

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
        self._name_label_entry.bind("<Up>",
            lambda e: (self._name_label_entry.icursor(0), "break"))
        self._name_label_entry.bind("<Down>",
            lambda e: (self._name_label_entry.icursor(tk.END), "break"))
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

    def _apply_print_preset(self):
        # Enable thumbnails so the HTML report is generated, then select print-friendly columns
        self._thumb_var.set(True)
        self._on_thumb_toggle()
        print_cols = {"thumbnail", "name", "note", "timecode", "clip", "dur_t", "dur_f"}
        for key, var in self._col_vars.items():
            var.set(key in print_cols)

    def _apply_all_preset(self):
        for var in self._col_vars.values():
            var.set(True)

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
        # self.transient(parent) omitted — causes macOS to re-activate the
        # parent when the dialog appears, stealing focus and breaking Comboboxes.
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
        # self.transient(parent) omitted — causes macOS to re-activate the
        # parent when the dialog appears, stealing focus and breaking Comboboxes.
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
APP_VERSION = "1.4.1"

class MarkerMadness:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.configure(bg=BG)
        self.root.createcommand('::tk::mac::ShowHelp',
            lambda: webbrowser.open("https://resolve-tools.com/marker-madness-guide"))
        self.root.after_idle(lambda: self.root.minsize(
            1300, max(self._side_panel.winfo_reqheight(), 750)))

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

        # Quick Edit Bar
        self._qe_iid        = None
        self._qe_bar        = None
        self._qe_name_var   = tk.StringVar()
        self._qe_note_var   = tk.StringVar()
        self._qe_name_entry = None
        self._qe_note_entry = None

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
        self._no_prompt_delete_var    = tk.BooleanVar(value=self._prefs.get("no_prompt_delete",    False))
        self._import_preview_var      = tk.BooleanVar(value=self._prefs.get("import_preview", True))
        self._grab_delay_var          = tk.IntVar(value=150)
        self._search_var       = tk.StringVar()
        self._search_job       = None
        self._main_undo_stack  = []
        self._main_redo_stack  = []

        self._build_ui()
        self.root.bind("<Command-z>",         lambda e: self._main_undo())
        self.root.bind("<Control-z>",         lambda e: self._main_undo())
        self.root.bind("<Command-Shift-z>",   lambda e: self._main_redo())
        self.root.bind("<Command-Shift-Z>",   lambda e: self._main_redo())
        self.root.bind("<Control-Shift-z>",   lambda e: self._main_redo())
        self.root.bind("<Control-Shift-Z>",   lambda e: self._main_redo())

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
        val = self._stay_on_top_var.get()
        # Persist the choice so it survives restarts
        self._prefs["stay_on_top"] = val
        _save_prefs(self._prefs)
        if val:
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
        """Call a messagebox function ensuring the root window is visible first.

        Lifts the root window before showing the dialog so that the messagebox
        never appears buried behind DaVinci Resolve after an automated refresh
        steals window focus.
        """
        if self._stay_on_top_var.get():
            self.root.attributes("-topmost", False)
        try:
            self.root.lift()
            self.root.focus_force()
        except Exception:
            pass
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
        self._main_redo_btn = TBtn(top, text="↪ Redo",
                                   command=self._main_redo,
                                   bg=BTN_HOV, fg=DIM)
        self._main_redo_btn.pack(side="right", padx=(0, 4))
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

        TBtn(tb1, text="+ Add",            command=self._add_marker_at_playhead,
             bg=ACCENT, fg=BG).pack(side="left", padx=3)
        TBtn(tb1, text="⊹ Batch Stamp",   command=self._stamp_track_dialog,
             bg=PURPLE, fg=BG).pack(side="left", padx=3)
        TBtn(tb1, text="✎ Edit",           command=self._edit_marker,
             bg=ACCENT, fg=BG).pack(side="left", padx=3)
        TBtn(tb1, text="⚡ Batch Rename",   command=self._open_renamer,
             bg=PURPLE, fg=BG).pack(side="left", padx=3)

        TBtn(tb1, text="✕ Delete",         command=self._delete_marker,
             bg=RED, fg=BG).pack(side="left", padx=3)
        TBtn(tb1, text="✕✕ Delete All",   command=self._delete_all,
             bg=RED, fg=BG).pack(side="left", padx=3)

        # Transfer section — stacked pairs: top row ⬆Timeline, bottom row ⬇Clip
        tk.Frame(tb1, bg=BTN_HOV, width=1).pack(side="left", fill="y", padx=8)
        tk.Label(tb1, text="Transfer:", fg=TEXT, bg=BG, font=F_SMALL).pack(side="left", padx=(0, 4))

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

        # Nudge section
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

        tk.Label(tb2, text="Color:", fg=TEXT, bg=BG, font=F_SMALL).pack(side="left", padx=(0, 3))
        self._filter_color = tk.StringVar(value="All")
        fcb = ttk.Combobox(tb2, textvariable=self._filter_color,
                           values=["All"] + MARKER_COLORS, state="readonly", width=11)
        fcb.pack(side="left")
        fcb.bind("<<ComboboxSelected>>", lambda _: self._populate_table())
        TBtn(tb2, text="✕", command=self._reset_color_filter,
             bg=BTN, fg=DIM, padx=5, pady=2).pack(side="left", padx=(2, 0))

        tk.Label(tb2, text="Type:", fg=TEXT, bg=BG, font=F_SMALL).pack(side="left", padx=(16, 3))
        self._filter_type = tk.StringVar(value="All Types")
        ttk.Combobox(tb2, textvariable=self._filter_type,
                     values=["All Types", "Timeline", "Clip"],
                     state="readonly", width=11).pack(side="left")
        self._filter_type.trace_add("write", lambda *_: self._populate_table())

        # Search field
        tk.Label(tb2, text="🔍 Search:", fg=TEXT, bg=BG, font=F_SMALL).pack(side="left", padx=(16, 3))
        self._search_entry = tk.Entry(tb2, textvariable=self._search_var, width=20,
                                bg=ENTRY_BG, fg=TEXT, insertbackground=TEXT,
                                relief="flat", font=F_MAIN)
        self._search_entry.pack(side="left")
        self._search_entry.bind("<Up>",   lambda e: (self._search_entry.icursor(0), "break"))
        self._search_entry.bind("<Down>", lambda e: (self._search_entry.icursor(tk.END), "break"))
        self._search_var.trace_add("write", self._on_search_changed)
        _attach_entry_menu(self._search_entry)
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
        tk.Checkbutton(tb2, text="Preview Import", variable=self._import_preview_var,
                       fg=TEXT, bg=BG, activeforeground=TEXT, activebackground=BG,
                       selectcolor=ENTRY_BG, font=F_SMALL).pack(side="right", padx=(0, 2))
        tk.Frame(tb2, bg=BTN_HOV, width=1).pack(side="right", fill="y", padx=8)
        TBtn(tb2, text="↺ Reset Column Layout", command=self._reset_layout,
             bg=BTN, fg=DIM).pack(side="right", padx=3)

        # Toolbar row 3 — reports / exchange
        tb3 = tk.Frame(self.root, bg=BG, pady=2)
        tb3.pack(fill="x", padx=12)
        TBtn(tb3, text="📊 Shot Change Report", command=self._open_shot_change_report,
             bg=BTN, fg=DIM, padx=8, pady=2).pack(side="right")
        TBtn(tb3, text="🔄 Marker Exchange", command=self._open_marker_exchange,
             bg=BTN, fg=DIM, padx=8, pady=2).pack(side="right", padx=(0, 8))

        # Main area: table + preview
        # Preview must be packed first (side="right") so expand=True on the
        # table frame doesn't crowd it out when column widths are wide.
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True, padx=12, pady=(4, 4))
        self._build_preview(main)
        self._build_table(main)

        # Quick Edit Bar — built here, hidden until activated
        self._build_quick_edit_bar()

        # Status bar
        sb = tk.Frame(self.root, bg=PANEL, pady=4)
        self._status_bar = sb
        sb.pack(fill="x")
        self._count_var = tk.StringVar(value="")
        tk.Label(sb, textvariable=self._count_var, fg=TEXT, bg=PANEL,
                 font=F_SMALL).pack(side="left", padx=12)
        tk.Label(sb, text="Right-click Name/Note to edit  ·  Enter for Quick Edit mode  ·  Double-click for full editor  ·  Esc to deselect all",
                 fg=TEXT, bg=PANEL, font=F_SMALL).pack(side="right", padx=12)

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
        self._tree.bind("<Escape>",           self._deselect_all)
        self._tree.bind("<Return>",           self._qe_activate)
        self._tree.bind("<KP_Enter>",         self._qe_activate)

        # Column drag-to-reorder — detect heading drags, suppress sort when drag occurs
        self._tree.bind("<ButtonPress-1>",   self._col_drag_start,  add="+")
        self._tree.bind("<B1-Motion>",       self._col_drag_motion, add="+")
        self._tree.bind("<ButtonRelease-1>", self._col_drag_end,    add="+")

        # Row tags — no foreground override; dot image carries the color
        self._tree.tag_configure("tl_row")
        self._tree.tag_configure("clip_row")

    def _build_preview(self, parent):
        panel = tk.Frame(parent, bg=PANEL, width=360)
        panel.pack(side="right", fill="y", padx=(8, 0))
        panel.pack_propagate(False)
        self._side_panel = panel

        tk.Label(panel, text="Frame Preview", fg=ACCENT, bg=PANEL,
                 font=F_BOLD).pack(pady=(12, 4))

        self._img_canvas = tk.Canvas(panel, bg=ENTRY_BG, width=336, height=161,
                                      relief="flat", highlightthickness=0)
        self._img_canvas.pack(padx=10, pady=4)
        self._img_canvas.create_text(168, 80,
                                      text="Select a marker\nthen click\nGrab Frame",
                                      fill=DIM, font=F_SMALL, justify="center",
                                      tags="placeholder")

        self._prev_info = tk.StringVar(value="")
        tk.Label(panel, textvariable=self._prev_info, fg=TEXT, bg=PANEL,
                 font=F_SMALL, wraplength=336, justify="left",
                 height=3, anchor="nw").pack(padx=10, pady=(2, 0))

        # Checkboxes — 2 columns × 2 rows
        cb_grid = tk.Frame(panel, bg=PANEL)
        cb_grid.pack(fill="x", padx=10, pady=(0, 20))
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

        delay_row = tk.Frame(panel, bg=PANEL)
        delay_row.pack(fill="x", padx=10, pady=(0, 2))
        tk.Label(delay_row, text="Grab delay (ms):", fg=TEXT, bg=PANEL,
                 font=F_SMALL).pack(side="left")
        def _dec_delay():
            self._grab_delay_var.set(max(50, self._grab_delay_var.get() - 50))
        def _inc_delay():
            self._grab_delay_var.set(min(2000, self._grab_delay_var.get() + 50))
        def _make_step_btn(parent, text, cmd):
            lbl = tk.Label(parent, text=text, bg=BTN, fg=TEXT,
                           font=F_SMALL, padx=8, pady=2, cursor="hand2")
            lbl.bind("<Enter>",           lambda _e: lbl.config(bg=BTN_HOV))
            lbl.bind("<Leave>",           lambda _e: lbl.config(bg=BTN))
            lbl.bind("<ButtonRelease-1>", lambda _e: cmd())
            return lbl
        _make_step_btn(delay_row, "−", _dec_delay).pack(side="left", padx=(8, 1))
        tk.Entry(delay_row, textvariable=self._grab_delay_var, width=4,
                 bg=ENTRY_BG, fg=TEXT, insertbackground=TEXT,
                 relief="flat", font=F_SMALL,
                 justify="center").pack(side="left", padx=1)
        _make_step_btn(delay_row, "+", _inc_delay).pack(side="left", padx=(1, 0))
        tk.Label(panel, text="Increase if thumbnails duplicate on export",
                 fg=TEXT, bg=PANEL, font=F_SMALL,
                 anchor="w").pack(fill="x", padx=10, pady=(0, 10))

        TBtn(panel, text="⏎  Jump to Marker", command=self._jump_to_marker,
             bg=ACCENT, fg=BG).pack(fill="x", padx=10, pady=(0, 4))
        TBtn(panel, text="📷  Grab Frame",    command=self._grab_frame,
             bg=ACCENT, fg=BG).pack(fill="x", padx=10, pady=(0, 4))
        TBtn(panel, text="⬇  Export Frame",   command=self._export_frame,
             bg=GREEN, fg=BG).pack(fill="x", padx=10, pady=(0, 4))
        TBtn(panel, text="📷  Batch Export High Res Frames", command=self._batch_export_full_res_frames,
             bg=ACCENT, fg=BG).pack(fill="x", padx=10, pady=(0, 6))

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

        # Nudge state — amount always resets to 0 on launch (safe default)
        try:
            self._nudge_auto_var.set(p.get("nudge_skip_confirm", False))
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
            "no_prompt_delete":  self._no_prompt_delete_var.get(),
            "import_preview": self._import_preview_var.get(),
            "nudge_skip_confirm":  self._nudge_auto_var.get(),
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

        # Compute candidate paste frames so we can offer only populated tracks.
        candidate_frames = {
            playhead_frame + e["frame_offset"]
            for e in self._marker_clipboard
            if playhead_frame + e["frame_offset"] >= 0
        }
        available_tracks = self._get_tracks_at_frames(timeline, candidate_frames)

        dlg = PasteMarkersDialog(self.root, count, tc_label, available_tracks)
        self.root.wait_window(dlg)
        if dlg.result is None:
            return

        target_track_type, target_track_index = dlg.result
        paste_to_ruler = (target_track_type == "ruler")

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

            if paste_to_ruler:
                ok, _err = self._add_marker_on_timeline(
                    timeline, tl_frame,
                    entry["color"], entry["name"], entry["note"], entry["duration"]
                )
                obj      = timeline
                frame_id = tl_frame
            else:
                clip_item = self._find_clip_at_frame(
                    timeline, tl_frame, target_track_type, target_track_index
                )
                if clip_item is None:
                    # Fallback: no clip at this frame on the chosen track → ruler
                    ok, _err = self._add_marker_on_timeline(
                        timeline, tl_frame,
                        entry["color"], entry["name"], entry["note"], entry["duration"]
                    )
                    obj      = timeline
                    frame_id = tl_frame
                else:
                    try:
                        left_offset = clip_item.GetLeftOffset() or 0
                    except Exception:
                        left_offset = 0
                    frame_id = (tl_frame + self._start_frame) - clip_item.GetStart() + left_offset
                    ok, _err = self._resolve_add_marker(
                        clip_item, frame_id,
                        entry["color"], entry["name"], entry["note"], entry["duration"], ""
                    )
                    obj      = clip_item
            if ok:
                added += 1
                self._tl_frames.add(tl_frame)
                undo_batch.append((obj, frame_id, entry))
            else:
                failed += 1

        if undo_batch:
            self._push_main_undo("add_timeline", undo_batch)

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
                                left_offset = item.GetLeftOffset() or 0
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

    def _reset_color_filter(self):
        self._filter_color.set("All")
        self._populate_table()

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
        prev_selection = self._tree.selection()
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

        # Restore selection for markers that still exist after repopulate
        if prev_selection:
            still_valid = [iid for iid in prev_selection if self._tree.exists(iid)]
            if still_valid:
                self._tree.selection_set(still_valid)

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
        if self._qe_bar and self._qe_bar.winfo_ismapped():
            self._qe_deactivate()
            return "break"
        self._tree.selection_remove(self._tree.selection())
        return "break"

    def _open_renamer(self):
        if not hasattr(self, "_renamer_dlg") or not self._renamer_dlg.winfo_exists():
            self._renamer_dlg = MarkerRenamerDialog(self)
        else:
            # Always re-center over the main window so it's never off-screen
            center_on_parent(self._renamer_dlg, self.root)
            self._renamer_dlg.deiconify()
            self._renamer_dlg.lift()
            self._renamer_dlg._schedule_preview()

    def _open_shot_change_report(self):
        if not hasattr(self, "_scr_dlg") or not self._scr_dlg.winfo_exists():
            self._scr_dlg = ShotChangeReportDialog(self.root)
        else:
            self._scr_dlg.deiconify()
            self._scr_dlg.lift()

    def _open_marker_exchange(self):
        if not hasattr(self, "_exchange_dlg") or not self._exchange_dlg.winfo_exists():
            self._exchange_dlg = MarkerExchangeDialog(self.root, self)
        else:
            self._exchange_dlg.deiconify()
            self._exchange_dlg.lift()

    def _import_rows_from_exchange(self, rows: list, source_label: str = "Exchange"):
        """Import pre-converted rows from a Marker Exchange source.

        Each row must be a dict with:
            Frame      — absolute frame number (str)
            Color      — Resolve color name (str, default Red)
            Name       — marker name (str)
            Note       — marker note (str)
            Marker Dur — duration in frames (str)

        Respects the Preview Import preference.  All markers land on the
        timeline ruler unless the user redirects them in the preview dialog.
        """
        timeline, err = self._fresh_timeline()
        if not timeline:
            self._mb(messagebox.showwarning, "Not connected", err)
            return
        if not rows:
            return

        candidate_frames = {int(r.get("Frame", 0)) - self._start_frame for r in rows}
        available_tracks = self._get_tracks_at_frames(timeline, candidate_frames)

        if not self._import_preview_var.get():
            targets      = rows
            target_track = ("ruler", 0)
            conflicts    = [r for r in targets
                            if (int(r.get("Frame", 0)) - self._start_frame) in self._tl_frames]
            overwrite    = False
            if conflicts:
                ans = self._mb(messagebox.askyesnocancel,
                    "Conflicts Found",
                    f"{len(conflicts)} frame(s) already have timeline markers.\n\n"
                    "Yes = overwrite  ·  No = skip  ·  Cancel = abort"
                )
                if ans is None:
                    return
                overwrite = ans
        else:
            dlg = ImportPreviewDialog(self.root, rows, self._start_frame,
                                      self._tl_frames, source_label, available_tracks)
            self.root.wait_window(dlg)
            if dlg.result is None:
                return
            targets      = dlg.result
            target_track = dlg.track_result
            overwrite    = True
            _save_prefs(self._collect_prefs())

        paste_to_ruler = (target_track[0] == "ruler")

        added = skipped = failed = 0
        for row in targets:
            try:
                tl_frame = int(row.get("Frame", 0)) - self._start_frame
                color    = row.get("Color", "Red")
                if color not in MARKER_COLORS:
                    color = "Red"
                name     = row.get("Name",     "")
                note     = row.get("Note",     "")
                duration = int(row.get("Marker Dur") or row.get("Duration") or 1)

                if paste_to_ruler:
                    if tl_frame in self._tl_frames:
                        if not overwrite:
                            skipped += 1
                            continue
                        self._resolve_delete_marker(timeline, tl_frame)
                    ok, _e = self._add_marker_on_timeline(
                        timeline, tl_frame, color, name, note, duration
                    )
                    if ok:
                        added += 1
                        self._tl_frames.add(tl_frame)
                    else:
                        failed += 1
                else:
                    track_type, track_index = target_track
                    clip_item = self._find_clip_at_frame(timeline, tl_frame,
                                                         track_type, track_index)
                    if clip_item is None:
                        # No clip — fall back to ruler
                        ok, _e = self._add_marker_on_timeline(
                            timeline, tl_frame, color, name, note, duration
                        )
                        if ok:
                            added += 1
                            self._tl_frames.add(tl_frame)
                        else:
                            failed += 1
                    else:
                        try:
                            left_offset = clip_item.GetLeftOffset() or 0
                        except Exception:
                            left_offset = 0
                        frame_id = ((tl_frame + self._start_frame)
                                    - clip_item.GetStart() + left_offset)
                        ok, _e = self._resolve_add_marker(
                            clip_item, frame_id, color, name, note, duration, ""
                        )
                        if ok:
                            added += 1
                        else:
                            failed += 1
            except Exception:
                failed += 1

        self._refresh()
        msg = f"Import from {source_label} complete.\n\nAdded: {added}"
        if skipped:
            msg += f"\nSkipped: {skipped}"
        if failed:
            msg += f"\nFailed: {failed}"
        self._mb(messagebox.showinfo, "Import Complete", msg)

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
            _attach_entry_menu(widget)

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
        # Return focus to the treeview only when no dialog window is open.
        # Unconditionally calling focus_set() here steals focus from any
        # open Toplevel on every _refresh(), causing dialogs to fall behind
        # the main window every time the table is rebuilt.
        try:
            open_toplevels = [w for w in self.root.winfo_children()
                              if isinstance(w, tk.Toplevel) and w.winfo_viewable()]
            if not open_toplevels and self.root.focus_displayof() is not self._search_entry:
                self._tree.focus_set()
        except Exception:
            pass  # Never unconditionally steal focus during automated refreshes

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
            # If Quick Edit Bar is open, follow the selection
            if self._qe_bar and self._qe_bar.winfo_ismapped() and sel[0] != self._qe_iid:
                self._qe_load_row(sel[0])
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
        Returns (success, error_string).

        Resolve 21 Beta changed AddMarker to return None instead of True on
        success in some builds.  When the return value is falsy we verify by
        reading GetMarkers() back — if the marker is now there, we treat it
        as success regardless of the return value.
        """
        fn = getattr(obj, "AddMarker", None)
        if fn is None:
            return False, "AddMarker method not found on object — check Resolve scripting API."
        try:
            # Resolve 21 Beta 33+ silently rejects AddMarker when name is an
            # empty string, returning False with no marker created. Substitute
            # a single space so the call succeeds; Resolve displays it as blank.
            _name = name if name else " "
            result = fn(frame_id, color, _name, note, int(duration), custom)
            if result:
                return True, ""
            # Falsy result (False, None, 0): verify by reading back.
            # Some Resolve 21 Beta builds return None/False even on success.
            try:
                markers_after = obj.GetMarkers() or {}
                if frame_id in markers_after:
                    return True, ""   # Marker is there — treat as success
            except Exception:
                pass
            return False, f"AddMarker returned {result!r} (marker not found in GetMarkers after call)"
        except Exception as exc:
            return False, str(exc)

    def _add_marker_on_timeline(self, timeline, tl_frame, color, name, note, duration,
                                 custom=""):
        """AddMarker on the timeline ruler.

        Resolve's API coordinate system for AddMarker changed across versions:
        some builds expect a 0-based frame offset (same as GetMarkers returns),
        others expect the absolute frame number (including TC start offset).
        We try 0-based first; if _start_frame > 0 and that fails, we retry
        with the absolute frame.  Returns (success, error_string).
        """
        ok, err = self._resolve_add_marker(
            timeline, tl_frame, color, name, note, duration, custom
        )
        if not ok and self._start_frame != 0:
            abs_frame = tl_frame + self._start_frame
            ok, err = self._resolve_add_marker(
                timeline, abs_frame, color, name, note, duration, custom
            )
            if not ok:
                err = (f"AddMarker({tl_frame}) [0-based] → False; "
                       f"AddMarker({abs_frame}) [absolute] → False")
        return ok, err

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
            ok, err = self._add_marker_on_timeline(
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
        """Gateway dialog: choose Add at Playhead or Stamp All Clips on Track."""
        dlg = AddActionDialog(self.root)
        self.root.wait_window(dlg)
        if dlg.result is None:
            return
        if dlg.result == "playhead":
            self._add_marker_at_playhead()
        else:
            self._stamp_track_dialog()

    def _add_marker_at_playhead(self):
        """Single-marker add flow — opens MarkerDialog at playhead."""
        timeline, err = self._fresh_timeline()
        if not timeline:
            self._mb(messagebox.showwarning, "Not connected", err)
            return

        # Build track list for the target dropdown — video tracks only if they
        # have at least one clip; audio tracks included unconditionally.
        track_list = []
        for ttype in ("video", "audio"):
            try:
                count = timeline.GetTrackCount(ttype)
            except Exception:
                count = 0
            for ti in range(1, count + 1):
                if ttype == "video":
                    try:
                        items = timeline.GetItemListInTrack("video", ti) or []
                    except Exception:
                        items = []
                    if not items:
                        continue
                track_list.append((ttype, ti))

        # Pass a live callable so the dialog's Refresh Position button works.
        try:
            tc_str = timeline.GetCurrentTimecode() or ""
            abs_frame = tc_to_frames(tc_str, self._fps) if tc_str else self._start_frame
        except Exception:
            abs_frame = self._start_frame

        dlg = MarkerDialog(self.root, "Add Marker", self._fps,
                           frame=abs_frame, get_tc_fn=self._current_tc,
                           track_list=track_list)
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
        else:
            # "video:1" or "audio:2" format — add to clip on that specific track
            ttype, tidx_str = r["target"].split(":")
            self._add_marker_to_clip_on_track(timeline, tl_frame, r,
                                               ttype, int(tidx_str))

    def _add_marker_to_clip_on_track(self, timeline, tl_frame, r, ttype, tidx):
        """Add a single marker to the clip on a specific track at the playhead."""
        item = self._find_clip_at_frame(timeline, tl_frame,
                                        track_type=ttype, track_index=tidx)
        if item is None:
            prefix = "V" if ttype == "video" else "A"
            self._mb(messagebox.showwarning, "No Clip Found",
                f"No clip on {prefix}{tidx} at the current playhead position.\n"
                "Move the playhead to a clip and try again.")
            return
        self._add_marker_to_clip_item(item, tl_frame, r)

    def _add_marker_to_timeline(self, timeline, tl_frame, r):
        ok, err = self._add_marker_on_timeline(
            timeline, tl_frame, r["color"], r["name"], r["note"], r["duration"]
        )
        if ok:
            self._push_main_undo("add_timeline", [(timeline, tl_frame, r)])
            self._refresh()
        else:
            abs_frame = tl_frame + self._start_frame
            if tl_frame in self._tl_frames or abs_frame in self._tl_frames:
                self._mb(messagebox.showerror, "Conflict",
                    "A timeline marker already exists at that position.\n"
                    "Delete it first or move the playhead.")
            else:
                diag = (f"Frame (0-based): {tl_frame}   Frame (absolute): {abs_frame}\n"
                        f"Timeline start frame: {self._start_frame}\n"
                        f"Existing TL frames (first 5): {sorted(self._tl_frames)[:5]}")
                self._mb(messagebox.showerror, "Error",
                    f"Resolve could not add the marker.\n\n{err}\n\n{diag}")

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

    # Names of Resolve built-in transitions — shared between _add_marker_to_clip_item
    # and _stamp_track so both paths skip the same objects.
    _TRANSITION_NAMES = frozenset({
        "cross dissolve", "film dissolve", "dip to color dissolve",
        "additive dissolve", "smooth cut", "dip to black", "dip to white",
    })

    # Maximum number of undo levels kept in the main undo stack.
    _MAX_UNDO = 20

    def _add_marker_to_clip_item(self, item, tl_frame, r, frame_offset=0):
        """Common tail: compute clip_offset, optionally apply frame_offset, add marker."""
        # Guard: transitions don't support markers and calling API methods on them
        # can crash Resolve.  Bail out immediately before touching the object further.
        try:
            if item.GetName().strip().lower() in self._TRANSITION_NAMES:
                self._mb(messagebox.showwarning, "Transition Selected",
                    "The playhead is over a transition effect.\n\n"
                    "Markers cannot be added to transitions — "
                    "move the playhead to a clip or title and try again.")
                return
        except Exception:
            pass  # If we can't even read the name, fall through and let it fail gracefully

        try:
            left_offset = item.GetLeftOffset() or 0
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
        # Try the calculated offset first; fall back to left_offset then 0
        # for generator/title clips whose GetLeftOffset() may be unreliable.
        ok = False; err = ""; used_frame = clip_offset
        for _fid in [clip_offset, left_offset, 0]:
            ok, err = self._resolve_add_marker(
                item, _fid, r["color"], r["name"], r["note"], r["duration"], ""
            )
            if ok:
                used_frame = _fid
                break
        if ok:
            self._push_main_undo("add_clip", [(item, used_frame, r)])
            self._refresh()
        else:
            self._mb(messagebox.showerror, "Error",
                f"Could not add clip marker — this clip type may not support markers.\n\n{err}")

    # ── Stamp-Track helpers ───────────────────────────────────────────────

    def _stamp_track_dialog(self):
        """Open StampTrackDialog, then stamp every clip in the chosen track."""
        timeline, err = self._fresh_timeline()
        if not timeline:
            self._mb(messagebox.showwarning, "Not connected", err)
            return

        # Build track list from the current timeline
        track_list = []
        for ttype in ("video", "audio"):
            try:
                count = timeline.GetTrackCount(ttype)
            except Exception:
                count = 0
            for ti in range(1, count + 1):
                track_list.append((ttype, ti))

        if not track_list:
            self._mb(messagebox.showwarning, "No Tracks",
                "No tracks found in the current timeline.")
            return

        # Get current fps for TC conversion inside the dialog
        fps = self._fps
        try:
            fps = float(timeline.GetSetting("timelineFrameRate") or fps)
        except Exception:
            pass

        dlg = StampTrackDialog(self.root, track_list, timeline=timeline, fps=fps)
        self.root.wait_window(dlg)
        if dlg.result is None:
            return

        # Re-fetch a fresh timeline proxy after dialog interaction
        timeline, err = self._fresh_timeline()
        if not timeline:
            self._mb(messagebox.showwarning, "Not connected", err)
            return

        try:
            self._stamp_track(timeline, dlg.result)
        except Exception as _exc:
            self._mb(messagebox.showerror, "Stamp Failed",
                     f"An unexpected error occurred while stamping:\n\n{_exc}")

    def _stamp_track(self, timeline, params):
        """Stamp a marker on every clip in the chosen track.

        params : (ttype, tidx, color, name, note, duration, offset,
                  skip_existing, range_frames)
        range_frames is None (entire track) or (in_frames, out_frames).
        """
        ttype, tidx, color, name, note, duration, offset, skip_existing, range_frames = params
        try:
            items = timeline.GetItemListInTrack(ttype, tidx) or []
        except Exception:
            items = []

        prefix = "V" if ttype == "video" else "A"
        if not items:
            self._mb(messagebox.showinfo, "No Clips",
                f"No clips found on track {prefix}{tidx}.")
            return

        # ── Detect transitions ────────────────────────────────────────────
        # GetItemListInTrack() returns transition objects (Cross Dissolve,
        # Film Dissolve, etc.) mixed in with real clips and generators.
        # Calling AddMarker on a transition crashes Resolve.
        #
        # Two-method detection — both require no MediaPoolItem so real
        # camera clips are never skipped:
        #
        #   1. Exact name: GetName() matches a known Resolve built-in
        #      transition name exactly (e.g. "Cross Dissolve"). This is
        #      the primary check — reliable, no false positives.
        #
        #   2. Geometric fallback: item has no MPI and its start falls
        #      strictly *inside* the previous item's time range. This is
        #      condition-1 only — we deliberately omit checking whether the
        #      *next* item's start falls inside this item's range (condition-2)
        #      because that would falsely flag every title clip whose tail
        #      is overlapped by the following dissolve.

        # (start, end, has_mpi) for every item
        item_info = []
        for itm in items:
            try:
                s, e = itm.GetStart(), itm.GetEnd()
            except Exception:
                s = e = None
            try:
                has_mpi = itm.GetMediaPoolItem() is not None
            except Exception:
                has_mpi = False
            item_info.append((s, e, has_mpi))

        transition_indices = set()
        for i, itm in enumerate(items):
            s, e, has_mpi = item_info[i]
            if has_mpi:
                continue  # Real clip — can never be a transition

            # Exact name match against the class-level transition name set
            try:
                if itm.GetName().strip().lower() in self._TRANSITION_NAMES:
                    transition_indices.add(i)
                    continue
            except Exception:
                pass

            # Method 2 (geometric) intentionally removed.
            # Condition-1 overlap detection falsely flags title clips that follow
            # a dissolve, because Resolve sets the title's GetStart() to a frame
            # that falls inside the dissolve's time range.  Exact name matching
            # (Method 1 above) reliably catches all built-in Resolve transitions
            # without any false positives.

        added = 0; skipped = 0; out_of_range = 0; failed = 0
        transitions_skipped = len(transition_indices)
        first_err = None

        for i, item in enumerate(items):
            # Skip transitions — they crash Resolve when AddMarker is called
            if i in transition_indices:
                continue

            # ── In/Out range filter ──────────────────────────────────────
            if range_frames is not None:
                try:
                    clip_start = item.GetStart()
                    clip_end   = item.GetEnd()
                    range_in, range_out = range_frames
                    if clip_end <= range_in or clip_start >= range_out:
                        out_of_range += 1
                        continue
                except Exception:
                    pass  # can't read position — stamp it anyway

            try:
                left_offset = item.GetLeftOffset() or 0
            except Exception:
                left_offset = 0
            clip_offset = left_offset + offset

            if skip_existing:
                try:
                    existing = item.GetMarkers() or {}
                    if clip_offset in existing:
                        skipped += 1
                        continue
                except Exception:
                    pass  # can't read markers — fall through and try to add

            # ── Gather diagnostics for first failing clip ─────────────────
            if first_err is None:
                try:
                    _name = item.GetName()
                    _dur  = item.GetDuration()
                except Exception:
                    _name = "?"; _dur = "?"
                try:
                    _mpi      = item.GetMediaPoolItem()
                    _mpi_info = "native clip" if _mpi else "generator/title (no source media)"
                except Exception:
                    _mpi_info = "can't read clip type"
                try:
                    _existing_mf = list((item.GetMarkers() or {}).keys())[:5]
                except Exception:
                    _existing_mf = "error"
                _diag = (
                    f"clip='{_name}'  dur={_dur}  left_offset={left_offset}  "
                    f"offset={offset}  clip_offset={clip_offset}\n"
                    f"  type: {_mpi_info}\n"
                    f"  existing marker frames: {_existing_mf}"
                )
            else:
                _diag = None

            # ── Try clip_offset, then bare offset, then frame 0 ──────────
            ok = False; err = "all attempts failed"
            for _fid in [clip_offset, offset, 0]:
                ok, err = self._resolve_add_marker(
                    item, _fid, color, name, note, duration, ""
                )
                if ok:
                    break
                err = f"AddMarker({_fid}) → False"

            if ok:
                added += 1
            else:
                failed += 1
                if first_err is None:
                    first_err = (f"{err}\n{_diag}" if _diag else err)

        self._refresh()
        total = added + skipped + out_of_range + failed
        range_line = ""
        if range_frames is not None:
            range_line = f"Outside In/Out range:  {out_of_range}\n"
        trans_line = ""
        if transitions_skipped:
            trans_line = f"Transitions skipped:   {transitions_skipped}\n"
        diag_line = ""
        if failed and first_err:
            diag_line = f"\n\nFirst failure reason:\n{first_err}"
        msg = (
            f"Stamp complete  →  Track {prefix}{tidx}\n\n"
            f"Clips processed:       {total}\n"
            f"Markers added:         {added}\n"
            f"{range_line}"
            f"{trans_line}"
            f"Skipped (conflict):    {skipped}\n"
            f"Failed:                {failed}"
            f"{diag_line}"
        )
        self._mb(messagebox.showinfo, "Stamp Complete", msg)

    # ── Quick Edit Bar ────────────────────────────────────────────────────

    def _build_quick_edit_bar(self):
        bar = tk.Frame(self.root, bg=PANEL, pady=6)
        self._qe_bar = bar
        # Not packed yet — shown only when activated

        tk.Frame(bar, bg=ACCENT, width=3).pack(side="left", fill="y")
        tk.Label(bar, text="⚡ Quick Edit", fg=ACCENT, bg=PANEL,
                 font=F_BOLD).pack(side="left", padx=(10, 20))

        tk.Label(bar, text="Name:", fg=TEXT, bg=PANEL, font=F_SMALL).pack(side="left", padx=(0, 4))
        self._qe_name_entry = tk.Entry(bar, textvariable=self._qe_name_var,
                                       bg=ENTRY_BG, fg=TEXT, insertbackground=TEXT,
                                       relief="flat", font=F_MAIN, width=28)
        self._qe_name_entry.pack(side="left", padx=(0, 16))

        tk.Label(bar, text="Notes:", fg=TEXT, bg=PANEL, font=F_SMALL).pack(side="left", padx=(0, 4))
        self._qe_note_entry = tk.Entry(bar, textvariable=self._qe_note_var,
                                       bg=ENTRY_BG, fg=TEXT, insertbackground=TEXT,
                                       relief="flat", font=F_MAIN, width=44)
        self._qe_note_entry.pack(side="left", fill="x", expand=True, padx=(0, 12))

        tk.Label(bar, text="↑↓ navigate  ·  Tab switch field  ·  Esc exit",
                 fg=DIM, bg=PANEL, font=F_SMALL).pack(side="right", padx=12)

        _attach_entry_menu(self._qe_name_entry)
        _attach_entry_menu(self._qe_note_entry)

        for entry, other in [(self._qe_name_entry, self._qe_note_entry),
                              (self._qe_note_entry, self._qe_name_entry)]:
            entry.bind("<Tab>",       lambda e, o=other: (o.focus_set(), o.select_range(0, "end"), "break"))
            entry.bind("<Shift-Tab>", lambda e, o=other: (o.focus_set(), o.select_range(0, "end"), "break"))
            entry.bind("<Return>",    lambda e: self._qe_advance(+1))
            entry.bind("<KP_Enter>",  lambda e: self._qe_advance(+1))
            entry.bind("<Down>",      lambda e: self._qe_advance(+1))
            entry.bind("<Up>",        lambda e: self._qe_advance(-1))
            entry.bind("<Escape>",    lambda e: self._qe_deactivate())

    def _qe_activate(self, _=None):
        sel = self._tree.selection()
        if not sel:
            return "break"
        self._close_inline()
        self._qe_load_row(sel[0])
        if not self._qe_bar.winfo_ismapped():
            self._qe_bar.pack(fill="x", before=self._status_bar)
        self._qe_name_entry.focus_set()
        self._qe_name_entry.select_range(0, "end")
        return "break"

    def _qe_deactivate(self):
        self._qe_save_current()
        if self._qe_bar.winfo_ismapped():
            self._qe_bar.pack_forget()
        self._qe_iid = None
        self._tree.focus_set()

    def _qe_load_row(self, iid: str):
        self._qe_iid = iid
        rec = self._by_id.get(iid, {})
        self._qe_name_var.set(rec.get("name", ""))
        self._qe_note_var.set(rec.get("note", ""))
        self._tree.see(iid)

    def _qe_save_current(self):
        iid = self._qe_iid
        if not iid or not self._tree.exists(iid):
            return
        rec = self._by_id.get(iid)
        if not rec:
            return
        new_name = self._qe_name_var.get()
        new_note = self._qe_note_var.get()
        if new_name == rec["name"] and new_note == rec["note"]:
            return
        ok, err = self._write_marker(rec, color=rec["color"], name=new_name,
                                     note=new_note, duration=rec["duration"], custom="")
        if ok:
            rec["name"] = new_name
            rec["note"] = new_note
            vals = list(self._tree.item(iid, "values"))
            vals[COL_IDS.index("name")] = new_name
            vals[COL_IDS.index("note")] = new_note
            self._tree.item(iid, values=vals)
        else:
            self._mb(messagebox.showerror, "Error", f"Could not update marker.\n\n{err}")

    def _qe_advance(self, direction: int):
        self._qe_save_current()
        iid = self._qe_iid
        if not iid:
            return "break"
        children = self._tree.get_children()
        if not children or iid not in children:
            return "break"
        idx = list(children).index(iid)
        next_idx = idx + direction
        if 0 <= next_idx < len(children):
            next_iid = children[next_idx]
            self._tree.selection_set(next_iid)
            self._qe_load_row(next_iid)
        self._qe_name_entry.focus_set()
        self._qe_name_entry.select_range(0, "end")
        return "break"

    # ── Full editor dialog ────────────────────────────────────────────────

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
            ok, _err = self._add_marker_on_timeline(
                timeline, tl_frame, use_color, rec["name"],
                rec["note"], rec["duration"]
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
            self._push_main_undo("promote", undo_batch)

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
                left_offset = item.GetLeftOffset() or 0
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
            # Fallback chain: computed offset → left_offset → 0
            # (generator clips may have unreliable GetLeftOffset())
            ok = False; _err = ""; used_frame = clip_offset
            for _fid in [clip_offset, left_offset, 0]:
                ok, _err = self._resolve_add_marker(
                    item, _fid, use_color, rec["name"],
                    rec["note"], rec["duration"], ""
                )
                if ok:
                    used_frame = _fid
                    break
            if ok:
                added += 1
                # Store track identity so undo can re-fetch a fresh item proxy.
                undo_batch.append(("clip_marker", item, used_frame, move,
                                   timeline, tl_frame, rec,
                                   chosen_type, chosen_idx))
                if move:
                    self._resolve_delete_marker(timeline, tl_frame)
            else:
                failed += 1

        if undo_batch:
            self._push_main_undo("demote", undo_batch)

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
                ok, _ = self._add_marker_on_timeline(
                    timeline, new_frame, rec["color"], rec["name"],
                    rec["note"], rec["duration"]
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
            self._push_main_undo("nudge", undo_batch)

        # Compute new IIDs so we can restore selection after refresh.
        # Timeline marker IID: "t_{new_frame}"; clip marker IID: same prefix
        # but with the old marker-frame replaced by the new one at the end.
        new_iids = []
        for entry in undo_batch:
            if entry[0] == "tl":
                _, _old_f, new_f, _rec = entry
                new_iids.append(f"t_{new_f}")
            else:
                _, old_mf, new_mf, rec, _item = entry
                old_id = rec["id"]
                suffix = f"_{old_mf}"
                if old_id.endswith(suffix):
                    new_iids.append(old_id[:-len(suffix)] + f"_{new_mf}")
                else:
                    new_iids.append(old_id)

        self._refresh()

        # Restore selection on the nudged markers at their new positions.
        if new_iids:
            valid = [iid for iid in new_iids if self._tree.exists(iid)]
            if valid:
                self._tree.selection_set(valid)

        if not self._nudge_auto_var.get():
            msg = f"Nudged {moved} marker{'s' if moved != 1 else ''} by {offset:+d} frames."
            if skipped:
                msg += f"\nSkipped {skipped} (conflict or out of range)."
            self._mb(messagebox.showinfo, "Nudge Complete", msg)

    # ── Main window undo helpers ──────────────────────────────────────────

    def _push_main_undo(self, op_type: str, batch: list):
        """Append one undo entry, cap the stack at _MAX_UNDO, clear redo, update buttons."""
        self._main_undo_stack.append((op_type, batch))
        if len(self._main_undo_stack) > self._MAX_UNDO:
            self._main_undo_stack.pop(0)
        self._main_redo_stack.clear()
        self._update_main_undo_btns()

    def _update_main_undo_btns(self):
        """Keep Undo/Redo button labels and colours in sync with the stacks."""
        n = len(self._main_undo_stack)
        m = len(self._main_redo_stack)
        if n == 0:
            self._main_undo_btn.config(bg=BTN_HOV, fg=DIM, text="↩ Undo")
        elif n == 1:
            self._main_undo_btn.config(bg=ACCENT,  fg=BG,  text="↩ Undo")
        else:
            self._main_undo_btn.config(bg=ACCENT,  fg=BG,  text=f"↩ Undo ({n})")
        if m == 0:
            self._main_redo_btn.config(bg=BTN_HOV, fg=DIM, text="↪ Redo")
        elif m == 1:
            self._main_redo_btn.config(bg=ACCENT,  fg=BG,  text="↪ Redo")
        else:
            self._main_redo_btn.config(bg=ACCENT,  fg=BG,  text=f"↪ Redo ({m})")

    # ── Main window undo ──────────────────────────────────────────────────

    def _main_undo(self):
        if not self._main_undo_stack:
            return
        timeline, err = self._fresh_timeline()
        if not timeline:
            self._mb(messagebox.showwarning, "Not connected", err)
            return

        op_type, batch = self._main_undo_stack.pop()
        redo_batch = []

        if op_type == "demote":
            for entry in batch:
                _, item, clip_offset, was_move, tl, tl_frame, rec = entry[:7]
                track_type = entry[7] if len(entry) > 7 else None
                track_idx  = entry[8] if len(entry) > 8 else None
                # Re-fetch a live item proxy — the stored one is stale after _refresh()
                if track_type and track_idx:
                    fresh = self._find_clip_at_frame(
                        timeline, tl_frame, track_type, track_idx)
                    if fresh:
                        item = fresh
                self._resolve_delete_marker(item, clip_offset)
                if was_move:
                    # Use the freshly-fetched timeline, not the stale one from the batch
                    self._add_marker_on_timeline(
                        timeline, tl_frame, rec["color"], rec["name"],
                        rec["note"], rec["duration"]
                    )
                redo_batch.append(entry)

        elif op_type == "promote":
            for entry in batch:
                _, tl, tl_frame, was_move, clip_item, clip_mf, rec = entry
                self._resolve_delete_marker(tl, tl_frame)
                if was_move and clip_item:
                    self._resolve_add_marker(
                        clip_item, clip_mf, rec["color"], rec["name"],
                        rec["note"], rec["duration"], ""
                    )
                redo_batch.append(entry)

        elif op_type == "add_timeline":
            for entry in batch:
                obj, frame_id = entry[0], entry[1]
                self._resolve_delete_marker(obj, frame_id)
                redo_batch.append(entry)

        elif op_type == "add_clip":
            for entry in batch:
                item, clip_offset = entry[0], entry[1]
                self._resolve_delete_marker(item, clip_offset)
                redo_batch.append(entry)

        elif op_type == "nudge":
            for entry in batch:
                if entry[0] == "tl":
                    _, old_frame, new_frame, rec = entry
                    self._add_marker_on_timeline(
                        timeline, old_frame, rec["color"], rec["name"],
                        rec["note"], rec["duration"]
                    )
                    self._resolve_delete_marker(timeline, new_frame)
                    # Redo: move back from old_frame to new_frame (swap positions)
                    redo_batch.append(("tl", new_frame, old_frame, rec))
                else:
                    _, old_mf, new_mf, rec, item = entry
                    self._resolve_add_marker(
                        item, old_mf, rec["color"], rec["name"],
                        rec["note"], rec["duration"], ""
                    )
                    self._resolve_delete_marker(item, new_mf)
                    redo_batch.append(("clip", new_mf, old_mf, rec, item))

        if redo_batch:
            self._main_redo_stack.append((op_type, redo_batch))
        self._update_main_undo_btns()
        self._refresh()

    def _main_redo(self):
        if not self._main_redo_stack:
            return
        timeline, err = self._fresh_timeline()
        if not timeline:
            self._mb(messagebox.showwarning, "Not connected", err)
            return

        op_type, batch = self._main_redo_stack.pop()
        undo_batch = []

        if op_type == "demote":
            # Re-do demote: add clip markers, if was_move: delete timeline markers
            for entry in batch:
                _, item, clip_offset, was_move, tl, tl_frame, rec = entry[:7]
                track_type = entry[7] if len(entry) > 7 else None
                track_idx  = entry[8] if len(entry) > 8 else None
                # Re-fetch a live item proxy
                if track_type and track_idx:
                    fresh = self._find_clip_at_frame(
                        timeline, tl_frame, track_type, track_idx)
                    if fresh:
                        item = fresh
                ok, _ = self._resolve_add_marker(
                    item, clip_offset, rec["color"], rec["name"],
                    rec["note"], rec["duration"], ""
                )
                if ok:
                    if was_move:
                        # Use fresh timeline, not stale batch reference
                        self._resolve_delete_marker(timeline, tl_frame)
                    undo_batch.append(entry)

        elif op_type == "promote":
            # Re-do promote: add timeline markers, if was_move: delete clip markers
            for entry in batch:
                _, tl, tl_frame, was_move, clip_item, clip_mf, rec = entry
                ok, _ = self._add_marker_on_timeline(
                    tl, tl_frame, rec["color"], rec["name"],
                    rec["note"], rec["duration"]
                )
                if ok:
                    if was_move and clip_item:
                        self._resolve_delete_marker(clip_item, clip_mf)
                    undo_batch.append(entry)

        elif op_type == "add_timeline":
            # Re-add the markers that were deleted by undo
            for entry in batch:
                obj, frame_id = entry[0], entry[1]
                rec_data = entry[2] if len(entry) > 2 else {}
                # Use _add_marker_on_timeline so the 0-based/absolute
                # fallback applies when obj is a timeline object.
                ok, _ = self._add_marker_on_timeline(
                    obj, frame_id,
                    rec_data.get("color", "Blue"), rec_data.get("name", ""),
                    rec_data.get("note", ""), rec_data.get("duration", 1)
                )
                if ok:
                    undo_batch.append(entry)

        elif op_type == "add_clip":
            # Re-add the clip markers deleted by undo
            for entry in batch:
                item, clip_offset = entry[0], entry[1]
                rec_data = entry[2] if len(entry) > 2 else {}
                ok, _ = self._resolve_add_marker(
                    item, clip_offset,
                    rec_data.get("color", "Blue"), rec_data.get("name", ""),
                    rec_data.get("note", ""), rec_data.get("duration", 1), ""
                )
                if ok:
                    undo_batch.append(entry)

        elif op_type == "nudge":
            # Redo batch has swapped positions: ("tl", new_frame, old_frame, rec)
            # Apply: add at new_frame (index 1), delete at old_frame (index 2)
            for entry in batch:
                if entry[0] == "tl":
                    _, redo_to, redo_from, rec = entry
                    ok, _ = self._add_marker_on_timeline(
                        timeline, redo_to, rec["color"], rec["name"],
                        rec["note"], rec["duration"]
                    )
                    if ok:
                        self._resolve_delete_marker(timeline, redo_from)
                        undo_batch.append(("tl", redo_from, redo_to, rec))
                else:
                    _, redo_to, redo_from, rec, item = entry
                    ok, _ = self._resolve_add_marker(
                        item, redo_to, rec["color"], rec["name"],
                        rec["note"], rec["duration"], ""
                    )
                    if ok:
                        self._resolve_delete_marker(item, redo_from)
                        undo_batch.append(("clip", redo_from, redo_to, rec, item))

        if undo_batch:
            self._main_undo_stack.append((op_type, undo_batch))
        self._update_main_undo_btns()
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
            # Pause so Resolve finishes the seek before we grab — SetCurrentTimecode
            # is async; too short a delay causes GrabStill() to capture the previous
            # frame, producing duplicate/mismatched stills. User-tunable via prefs.
            time.sleep(self._grab_delay_var.get() / 1000.0)
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
                        # Sort newest-first so a stale file from a retry never wins
                        matches.sort(key=os.path.getmtime, reverse=True)
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

        dlg = BatchExportOptionsDialog(self.root, len(visible), len(selected))
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
                row += f"<td class='col-{key}'{s}>{content}</td>"
            rows_html.append(f"<tr>{row}</tr>")

        tl_safe  = esc(timeline_name)
        rows_str = "\n".join(rows_html)
        date_str = datetime.datetime.now().strftime("%B %d, %Y")
        headers  = "".join(
            f"<th class='col-{key}'>{name_label if key == 'name' else html_col_labels.get(key, key)}</th>"
            for key in columns
        )
        _col_widths = {
            "thumbnail": "12%",
            "timecode":  "12%",
            "name":      "13%",
            "note":      "25%",
            "clip":      "9%",
            "clip_in":   "10%",
            "clip_out":  "10%",
            "dur_f":     "9%",
            "dur_t":     "11%",
            "type":      "6%",
            "color":     "7%",
        }
        colgroup = "<colgroup>" + "".join(
            f'<col class="col-{k}"' + (f' style="width:{_col_widths[k]}"' if k in _col_widths else "") + ">"
            for k in columns
        ) + "</colgroup>"
        html = (
            "<!DOCTYPE html>\n<html lang='en'>\n<head>\n"
            "<meta charset='utf-8'>\n"
            f"<title>{tl_safe} — Report</title>\n"
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
            "table{table-layout:fixed;width:100%;border-collapse:separate;border-spacing:0;"
            "border-top:1px solid #999;border-left:1px solid #999}"
            "td,th{border-right:1px solid #999;border-bottom:1px solid #999}"
            ".col-note{overflow-wrap:break-word;word-break:break-word}"
            ".col-clip{overflow-wrap:break-word;word-break:break-all}"
            "img{max-width:100%;height:auto;display:block}"
            "}\n"
            "</style>\n</head>\n<body>\n"
            "<header>\n"
            f"<h1>{tl_safe}</h1>\n"
            f"<p>Report &nbsp;·&nbsp; {date_str}</p>\n"
            "</header>\n"
            + f"<table>\n{colgroup}\n<tr>{headers}</tr>\n"
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

        candidate_frames   = {int(r.get("Frame", 0)) - self._start_frame for r in rows}
        available_tracks   = self._get_tracks_at_frames(timeline, candidate_frames)

        if not self._import_preview_var.get():
            # Skip preview — import all rows, ask about conflicts; land on ruler
            targets      = rows
            target_track = ("ruler", 0)
            conflicts = [r for r in targets
                         if (int(r.get("Frame", 0)) - self._start_frame) in self._tl_frames]
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
        else:
            dlg = ImportPreviewDialog(self.root, rows, self._start_frame,
                                      self._tl_frames, path, available_tracks)
            self.root.wait_window(dlg)
            if dlg.result is None:
                return
            targets      = dlg.result
            target_track = dlg.track_result
            overwrite = True  # user reviewed conflicts in the dialog and kept those rows
            _save_prefs(self._collect_prefs())

        paste_to_ruler = (target_track[0] == "ruler")

        added = skipped = failed = 0
        for row in targets:
            try:
                tl_frame = int(row.get("Frame", 0)) - self._start_frame
                color    = row.get("Color", "Blue")
                if color not in MARKER_COLORS:
                    color = "Blue"
                name     = row.get("Name",     "")
                note     = row.get("Note",     "")
                duration = int(row.get("Marker Dur") or row.get("Duration") or 1)

                if paste_to_ruler:
                    if tl_frame in self._tl_frames:
                        if not overwrite:
                            skipped += 1
                            continue
                        self._resolve_delete_marker(timeline, tl_frame)
                    ok, _e = self._add_marker_on_timeline(
                        timeline, tl_frame, color, name, note, duration
                    )
                    if ok:
                        added += 1
                        self._tl_frames.add(tl_frame)
                    else:
                        failed += 1
                else:
                    track_type, track_index = target_track
                    clip_item = self._find_clip_at_frame(timeline, tl_frame,
                                                         track_type, track_index)
                    if clip_item is None:
                        # No clip at this frame — fall back to ruler
                        ok, _e = self._add_marker_on_timeline(
                            timeline, tl_frame, color, name, note, duration
                        )
                        if ok:
                            added += 1
                            self._tl_frames.add(tl_frame)
                        else:
                            failed += 1
                    else:
                        try:
                            left_offset = clip_item.GetLeftOffset() or 0
                        except Exception:
                            left_offset = 0
                        frame_id = ((tl_frame + self._start_frame)
                                    - clip_item.GetStart() + left_offset)
                        ok, _e = self._resolve_add_marker(
                            clip_item, frame_id, color, name, note, duration, ""
                        )
                        if ok:
                            added += 1
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

        # Re-fetch a fresh project proxy — the cached self._project can go stale
        # between refreshes, causing silent failures in the gallery API.
        try:
            pm      = self._resolve.GetProjectManager()
            project = pm.GetCurrentProject() if pm else None
        except Exception:
            project = None
        if not project:
            project = self._project  # fall back to cached copy

        # Export the still to a dedicated preview folder.
        # ExportStills can be asynchronous in some Resolve builds, so we poll
        # for the file rather than assuming it exists the moment the call returns.
        # We also check the return value — False means a silent failure.
        #
        # NOTE: do NOT add a sleep here or call OpenPage() before ExportStills.
        # GrabStill() briefly activates the Color page's album context; calling
        # GetCurrentStillAlbum() immediately captures that same context.  Any
        # delay or page-switch causes Resolve to return a different album, and
        # ExportStills will silently fail because the still isn't in that album.
        preview_dir = os.path.join(PREFS_DIR, "preview")
        os.makedirs(preview_dir, exist_ok=True)
        tmp_prefix  = "mm_preview"
        export_time = time.time() - 1  # 1-second margin before the call
        try:
            album = project.GetGallery().GetCurrentStillAlbum()
            ok = album.ExportStills([still], preview_dir, tmp_prefix, "png")
            if ok is False:
                raise RuntimeError("ExportStills returned False — Resolve could not write the file.")
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

        # Poll up to 3 s for the file to appear (ExportStills is async in some
        # Resolve builds and the file may not be on disk when the call returns).
        # Search both our preview_dir and system temp in case Resolve overrode the path.
        matches  = []
        deadline = time.time() + 3.0
        while time.time() < deadline:
            candidates = []
            for search_dir in (preview_dir, tempfile.gettempdir()):
                candidates.extend(glob.glob(os.path.join(search_dir, f"{tmp_prefix}*.png")))
            matches = sorted(
                [f for f in candidates if os.path.getmtime(f) >= export_time],
                key=os.path.getmtime, reverse=True
            )
            if matches:
                break
            time.sleep(0.2)

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
            self._img_canvas.create_text(168, 80,
                                          text=f"Preview error:\n{exc}",
                                          fill=RED, font=F_SMALL, justify="center")
            return
        cw, ch = 336, 161
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
    if sys.platform == "darwin":
        import tempfile as _tempfile, base64 as _b64
        _icon_path = None
        try:
            _tf = _tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            _tf.write(_b64.b64decode(APP_ICON_B64))
            _tf.close()
            _icon_path = _tf.name
        except Exception:
            pass
        if _icon_path:
            # Tkinter window icon (Mission Control, Exposé) — own try so
            # ctypes dock-icon code still runs even if PhotoImage fails
            try:
                root._icon_photo = tk.PhotoImage(data=APP_ICON_B64)
                root.iconphoto(True, root._icon_photo)
            except Exception:
                pass
            # NSApplication dock icon + Cmd+Tab identity
            try:
                import ctypes, ctypes.util
                _objc = ctypes.cdll.LoadLibrary(ctypes.util.find_library('objc'))
                _objc.objc_getClass.restype = _objc.sel_registerName.restype = ctypes.c_void_p
                _msg = _objc.objc_msgSend; _msg.restype = ctypes.c_void_p
                _msg.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_char_p]
                _ns_path = _msg(_objc.objc_getClass(b'NSString'), _objc.sel_registerName(b'stringWithUTF8String:'), _icon_path.encode())
                _msg.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
                _img = _msg(_objc.objc_getClass(b'NSImage'), _objc.sel_registerName(b'alloc'))
                _msg.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
                _img = _msg(_img, _objc.sel_registerName(b'initWithContentsOfFile:'), _ns_path)
                if _img:  # nil means file not found — skip rather than clear the icon
                    _msg.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
                    _app = _msg(_objc.objc_getClass(b'NSApplication'), _objc.sel_registerName(b'sharedApplication'))
                    _msg.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
                    _msg(_app, _objc.sel_registerName(b'setApplicationIconImage:'), _img)
                    _msg.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_long]
                    _msg(_app, _objc.sel_registerName(b'setActivationPolicy:'), 0)
                    _msg.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_char_p]
                    _app_name = _msg(_objc.objc_getClass(b'NSString'), _objc.sel_registerName(b'stringWithUTF8String:'), b'Marker Madness')
                    _msg.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
                    _pi = _msg(_objc.objc_getClass(b'NSProcessInfo'), _objc.sel_registerName(b'processInfo'))
                    _msg.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
                    _msg(_pi, _objc.sel_registerName(b'setProcessName:'), _app_name)
            except Exception:
                pass
            try:
                import os as _os; _os.unlink(_icon_path)
            except Exception:
                pass

    root.withdraw()                  # hide before anything renders
    root.title(APP_TITLE)
    app = MarkerMadness(root)

    # Restore saved window geometry, or on first launch position near the
    # cursor so the window opens on whichever display the user is working on.
    saved_geom = app._prefs.get("window_geometry", "")
    if saved_geom:
        try:
            root.geometry(saved_geom)
        except Exception:
            saved_geom = ""
    if not saved_geom:
        root.update_idletasks()
        w, h  = 1560, 920
        px    = root.winfo_pointerx()
        py    = root.winfo_pointery()
        x     = px - w // 2
        y     = max(py - int(h * 0.38), 40)
        root.geometry(f"{w}x{h}+{x}+{y}")

    root.deiconify()                 # reveal at the correct position
    root.mainloop()


if __name__ == "__main__":
    main()
