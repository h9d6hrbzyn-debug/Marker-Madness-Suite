#!/usr/bin/env python3
"""
Track Command 1.0 — DaVinci Resolve Track Manager

Renames audio and video tracks in the current Resolve timeline.
Part of the Marker Madness suite.

Installation:
  Copy to your DaVinci Resolve scripts folder and run from
  Workspace > Scripts > Utility inside DaVinci Resolve.

  macOS:   /Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Utility/
  Windows: C:\\ProgramData\\Blackmagic Design\\DaVinci Resolve\\Fusion\\Scripts\\Utility\\
  Linux:   /opt/resolve/Developer/Scripting/Modules/
"""

import sys
import os
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

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
# Theme
# ---------------------------------------------------------------------------

BG       = "#2d2d2d"
PANEL    = "#333333"
TEXT     = "#E2E2E2"
ACCENT   = "#ffa500"
BTN      = "#505050"
BTN_HOV  = "#626262"
ENTRY_BG = "#1e1e1e"
TITLE_BG = "#1a1a1a"
DIM      = "#707070"
GREEN    = "#388E3C"
BLUE     = "#1976D2"
PURPLE   = "#7B1FA2"
RED      = "#C62828"
BTN_TEXT = "#111111"

F_MAIN   = ("Avenir Next", 12)
F_BOLD   = ("Avenir Next", 13, "bold")
F_SMALL  = ("Avenir Next", 10)
F_MONO   = ("Courier", 12)
F_TITLE  = ("Avenir Next", 18)
F_STATUS = ("Avenir Next", 10, "italic")
F_HDR    = ("Avenir Next", 10, "bold")

# ---------------------------------------------------------------------------
# Audio subtypes
# ---------------------------------------------------------------------------

AUDIO_SUBTYPES = {
    "3.0":      ["LRC", "LCR"],
    "4.0":      ["LRCS", "LCRS", "Quad"],
    "5.x":      ["5.0", "5.0 Film", "5.1", "5.1 Film"],
    "7.x":      ["7.0", "7.0 Film", "7.1", "7.1 Film"],
    "Adaptive": [str(i) for i in range(1, 37)],
}

def audio_type_string(main_type, sub_type):
    if main_type in ("5.x", "7.x"):
        return sub_type.replace(" ", "").lower()
    elif main_type == "Adaptive":
        return "adaptive" + sub_type
    elif main_type in AUDIO_SUBTYPES:
        return sub_type.lower()
    else:
        return main_type.lower()

# ---------------------------------------------------------------------------
# Hover color helper
# ---------------------------------------------------------------------------

def _hover_color(hex_color, factor=0.18):
    r = int(hex_color[1:3], 16); g = int(hex_color[3:5], 16); b = int(hex_color[5:7], 16)
    r = min(255, int(r + (255 - r) * factor)); g = min(255, int(g + (255 - g) * factor)); b = min(255, int(b + (255 - b) * factor))
    return f"#{r:02x}{g:02x}{b:02x}"

# ---------------------------------------------------------------------------
# TBtn
# ---------------------------------------------------------------------------

class TBtn(tk.Button):
    def __init__(self, parent, bg=BTN, fg=BTN_TEXT, padx=12, pady=6, font=F_MAIN, **kw):
        super().__init__(parent, bg=bg, fg=fg, relief="flat",
                         activebackground=_hover_color(bg), activeforeground=fg,
                         padx=padx, pady=pady, cursor="hand2", font=font, **kw)
        _bg = bg
        _hov = _hover_color(bg)
        self.bind("<Enter>", lambda _: self.config(bg=_hov))
        self.bind("<Leave>", lambda _: self.config(bg=_bg))

# ---------------------------------------------------------------------------
# Transformation engine  (identical to Clip Renamer Pro 2.0)
# ---------------------------------------------------------------------------

def apply_transform(text, *, find="", replace="", add="", add_pos="After",
                    replace_all=False, trim=False, trim_begin=0, trim_end=0,
                    counter=0, counter_enabled=False, counter_digits=2,
                    counter_pos="After", upper=False, lower=False,
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
    return n.strip()

# ---------------------------------------------------------------------------
# Load preview window
# ---------------------------------------------------------------------------

class LoadPreviewWindow(tk.Toplevel):
    def __init__(self, parent, loaded, filename, apply_cb):
        super().__init__(parent)
        self.title(f"Load Preview — {filename}")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()
        self._loaded   = loaded
        self._filename = filename
        self._apply_cb = apply_cb
        self._build()

    def _build(self):
        tk.Label(self, text=f"  Loaded: {self._filename}.txt  ",
                 fg=ACCENT, bg=BG, font=F_BOLD).pack(fill="x", ipady=6)

        pf = tk.Frame(self, bg=BG)
        pf.pack(fill="both", expand=True, padx=12, pady=8)
        pf.columnconfigure(0, weight=1)
        pf.columnconfigure(1, weight=1)

        for col_idx, (label, key) in enumerate(
                [("VIDEO TRACKS", "video"), ("AUDIO TRACKS", "audio")]):
            f = tk.Frame(pf, bg=PANEL)
            f.grid(row=0, column=col_idx, sticky="nsew",
                   padx=(0, 4) if col_idx == 0 else (4, 0))
            tk.Label(f, text=label, fg=ACCENT, bg=PANEL,
                     font=F_HDR).pack(anchor="w", padx=6, pady=4)
            t = tk.Text(f, bg=ENTRY_BG, fg=TEXT, relief="flat",
                        font=F_MONO, wrap="none", height=14, width=28)
            t.pack(fill="both", expand=True, padx=6, pady=(0, 6))
            for track in self._loaded[key]:
                sub = f" ({track.get('subType','')})" if key == "audio" else ""
                t.insert("end", track["name"] + sub + "\n")
            t.config(state="disabled")

        bf = tk.Frame(self, bg=BG)
        bf.pack(fill="x", padx=12, pady=(0, 12))
        for text, mode, color in [
            ("Change Timeline",    "change", GREEN),
            ("Add to Timeline",    "add",    BLUE),
            ("Create New Timeline","new",    "#E65100"),
        ]:
            TBtn(bf, text=text, bg=color, fg=TEXT, padx=10, pady=6,
                 command=lambda m=mode: self._go(m)
                 ).pack(side="left", fill="x", expand=True, padx=2)

    def _go(self, mode):
        self._apply_cb(self._loaded, mode, self._filename)
        self.destroy()

# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------

class TrackCommander:

    def __init__(self, root):
        self.root = root
        self.root.title("Track Command")
        self.root.configure(bg=BG)
        _w, _h = 1420, 840
        self.root.update_idletasks()
        _sw = self.root.winfo_screenwidth()
        _sh = self.root.winfo_screenheight()
        self.root.geometry(f"{_w}x{_h}+{(_sw - _w) // 2}+{(_sh - _h) // 2}")

        self._resolve    = get_resolve()
        self._project    = None
        self._timeline   = None
        self._media_pool = None

        self._tracks       = {"audio": [], "video": []}
        self._orig_names   = {}
        self._start_names  = {}
        self._start_counts = {"audio": 0, "video": 0}
        self._last_changes        = []
        self._preview_job         = None
        self._audio_search_var    = tk.StringVar()
        self._video_search_var    = tk.StringVar()
        self._stay_on_top_var   = tk.BooleanVar(value=True)
        self._topmost_check_job = None
        self._hdr_proj_var      = tk.StringVar(value="—")
        self._hdr_tl_var        = tk.StringVar(value="—")
        self._hdr_tracks_var    = tk.StringVar(value="")

        if self._resolve:
            pm = self._resolve.GetProjectManager()
            self._project = pm.GetCurrentProject() if pm else None
            if self._project:
                self._timeline   = self._project.GetCurrentTimeline()
                self._media_pool = self._project.GetMediaPool()

        self._style_widgets()
        self._read_tracks()
        for tid, nm in self._orig_names.items():
            self._start_names[tid] = nm
        self._start_counts["audio"] = len(self._tracks["audio"])
        self._start_counts["video"] = len(self._tracks["video"])

        self._build()
        self.root.bind("<Command-z>", lambda e: self._undo())
        self.root.bind("<Control-z>", lambda e: self._undo())
        self._populate_audio_tree()
        self._populate_video_tree()
        self._refresh_audio_type_combo()
        self._update_header_info()
        self._set_info(
            f'Timeline: "{self._tl_name()}"\n'
            f'{len(self._tracks["video"])} video, '
            f'{len(self._tracks["audio"])} audio tracks.  Ready.')

        self._on_stay_on_top_changed()
        self.root.after(150, self._initial_lift)

    # ── Resolve helpers ───────────────────────────────────────────────────

    def _reconnect(self):
        """Re-fetch project and current timeline from Resolve."""
        if not self._resolve:
            return
        try:
            pm = self._resolve.GetProjectManager()
            self._project  = pm.GetCurrentProject() if pm else None
            self._timeline = self._project.GetCurrentTimeline() if self._project else None
        except Exception:
            self._project  = None
            self._timeline = None

    def _tl_name(self):
        return self._timeline.GetName() if self._timeline else "No timeline"

    def _update_header_info(self):
        try:
            self._hdr_proj_var.set(self._project.GetName() if self._project else "—")
        except Exception:
            self._hdr_proj_var.set("—")
        try:
            self._hdr_tl_var.set(self._timeline.GetName() if self._timeline else "—")
        except Exception:
            self._hdr_tl_var.set("—")
        v = len(self._tracks.get("video", []))
        a = len(self._tracks.get("audio", []))
        self._hdr_tracks_var.set(f"{v}V  {a}A")

    def _tid(self, track_type, index):
        return ("A" if track_type == "audio" else "V") + str(index)

    def _read_tracks(self):
        self._tracks = {"audio": [], "video": []}
        if not self._timeline:
            return
        for i in range(1, self._timeline.GetTrackCount("audio") + 1):
            nm  = self._timeline.GetTrackName("audio", i)
            sub = self._timeline.GetTrackSubType("audio", i) or "mono"
            tid = self._tid("audio", i)
            self._tracks["audio"].append(
                {"index": i, "name": nm, "subType": sub, "id": tid})
            self._orig_names[tid] = nm
        for i in range(1, self._timeline.GetTrackCount("video") + 1):
            nm  = self._timeline.GetTrackName("video", i)
            tid = self._tid("video", i)
            self._tracks["video"].append({"index": i, "name": nm, "id": tid})
            self._orig_names[tid] = nm

    def _unique_audio_types(self):
        seen, types = set(), []
        for t in self._tracks["audio"]:
            if t["subType"] not in seen:
                seen.add(t["subType"]); types.append(t["subType"])
        return types

    # ── Styling ───────────────────────────────────────────────────────────

    def _style_widgets(self):
        try:
            s = ttk.Style()
            s.theme_use("default")
            s.configure("Dark.TCombobox",
                        fieldbackground=ENTRY_BG, background=BTN,
                        foreground=TEXT, arrowcolor=TEXT,
                        selectbackground=BTN_HOV, selectforeground=TEXT)
            s.map("Dark.TCombobox",
                  fieldbackground=[("readonly", ENTRY_BG)],
                  foreground=[("readonly", TEXT)],
                  background=[("readonly", BTN)])
            s.configure("Track.Treeview",
                        background=BG, foreground=TEXT,
                        fieldbackground=BG, rowheight=26, font=F_MAIN)
            s.configure("Track.Treeview.Heading",
                        background="#1a1a1a", foreground=ACCENT,
                        font=F_HDR, relief="flat")
            s.map("Track.Treeview",
                  background=[("selected", BTN_HOV)],
                  foreground=[("selected", TEXT)])
        except Exception:
            pass

    # ── Build ─────────────────────────────────────────────────────────────

    def _build(self):
        _tb = tk.Frame(self.root, bg=TITLE_BG, pady=8)
        _tb.pack(fill="x")
        tk.Label(_tb, text="  Track Command", fg=ACCENT, bg=TITLE_BG,
                 font=("Avenir Next", 18)).pack(side="left")
        tk.Label(_tb, text="v1.0", fg=DIM, bg=TITLE_BG,
                 font=("Avenir Next", 10)).pack(side="left", pady=(6, 0))
        _info = tk.Frame(_tb, bg=TITLE_BG)
        _info.pack(side="left", padx=24)
        tk.Label(_info, text="Project", fg=DIM, bg=TITLE_BG, font=F_STATUS).pack(side="left")
        tk.Label(_info, textvariable=self._hdr_proj_var,
                 fg=TEXT, bg=TITLE_BG, font=F_MAIN).pack(side="left", padx=(5, 0))
        tk.Label(_info, text="  ·  ", fg=DIM, bg=TITLE_BG, font=F_STATUS).pack(side="left")
        tk.Label(_info, text="Timeline", fg=DIM, bg=TITLE_BG, font=F_STATUS).pack(side="left")
        tk.Label(_info, textvariable=self._hdr_tl_var,
                 fg=TEXT, bg=TITLE_BG, font=F_MAIN).pack(side="left", padx=(5, 0))
        tk.Label(_info, text="  ·  ", fg=DIM, bg=TITLE_BG, font=F_STATUS).pack(side="left")
        tk.Label(_info, textvariable=self._hdr_tracks_var,
                 fg=TEXT, bg=TITLE_BG, font=F_MAIN).pack(side="left")

        top = tk.Frame(self.root, bg=BG)
        top.pack(fill="x", padx=8, pady=6)
        TBtn(top, text="Clear",   command=self._clear,
             bg=BTN,    padx=10, pady=4).pack(side="left", padx=(0, 4))
        TBtn(top, text="Refresh", command=self._refresh,
             bg=PURPLE, padx=10, pady=4).pack(side="left", padx=4)
        self._undo_btn = TBtn(top, text="Undo", command=self._undo,
                              bg=BLUE, padx=10, pady=4)
        self._undo_btn.pack(side="left", padx=4)
        self._undo_btn.config(state="disabled")
        TBtn(top, text="Restore Original", command=self._restore,
             bg=RED, padx=10, pady=4).pack(side="left", padx=4)
        tk.Checkbutton(top, text="Float on Top", variable=self._stay_on_top_var,
                       command=self._on_stay_on_top_changed,
                       fg=TEXT, bg=BG, selectcolor=ENTRY_BG,
                       activebackground=BG, activeforeground=TEXT,
                       font=F_SMALL).pack(side="right", padx=8)

        content = tk.Frame(self.root, bg=BG)
        content.pack(fill="both", expand=True, padx=8, pady=(0, 4))
        content.grid_columnconfigure(0, weight=0, minsize=420)
        content.grid_columnconfigure(1, weight=1)
        content.grid_columnconfigure(2, weight=1)
        content.grid_rowconfigure(0, weight=1)

        left = tk.Frame(content, bg=PANEL)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self._build_rename_ops(left)

        mid = tk.Frame(content, bg=PANEL)
        mid.grid(row=0, column=1, sticky="nsew", padx=(0, 6))
        self._build_audio_col(mid)

        right = tk.Frame(content, bg=PANEL)
        right.grid(row=0, column=2, sticky="nsew")
        self._build_video_col(right)

        TBtn(self.root, text="Apply Changes", command=self._apply,
             bg=GREEN, padx=14, pady=10,
             font=F_MAIN).pack(fill="x", padx=8, pady=(0, 8))

    # ── Rename operations panel ───────────────────────────────────────────

    def _build_rename_ops(self, parent):
        tk.Label(parent, text="RENAME OPERATIONS", fg=ACCENT, bg=PANEL,
                 font=F_HDR).pack(fill="x", padx=10, pady=(10, 4))

        ops = tk.Frame(parent, bg=PANEL)
        ops.pack(fill="x", padx=10)

        def sv():
            v = tk.StringVar()
            v.trace_add("write", lambda *_: self._schedule_preview())
            return v

        def iv(val):
            v = tk.IntVar(value=val)
            v.trace_add("write", lambda *_: self._schedule_preview())
            return v

        def ck(par, text, var, cmd=None):
            return tk.Checkbutton(par, text=text, variable=var,
                                  fg=TEXT, bg=PANEL, selectcolor=ENTRY_BG,
                                  activebackground=PANEL, activeforeground=TEXT,
                                  font=F_MAIN, command=cmd or self._schedule_preview)

        def en(par, var):
            e = tk.Entry(par, textvariable=var, bg=ENTRY_BG, fg=TEXT,
                         insertbackground=TEXT, relief="flat", font=F_MAIN,
                         highlightthickness=1, highlightbackground="#444444",
                         highlightcolor="#666666")
            e.bind("<Up>", lambda ev: e.icursor(0) or "break")
            e.bind("<Down>", lambda ev: e.icursor("end") or "break")
            e.bind("<KP_Enter>", lambda ev: self._schedule_preview() or "break")
            return e

        def sp(par, var, lo, hi, w=4):
            sb = tk.Spinbox(par, from_=lo, to=hi, textvariable=var, width=w,
                            bg=ENTRY_BG, fg=TEXT, insertbackground=TEXT,
                            buttonbackground=BTN, relief="flat", font=F_MAIN,
                            command=self._schedule_preview,
                            highlightthickness=1, highlightbackground="#444444",
                            highlightcolor="#666666")
            sb.bind("<KP_Enter>", lambda ev: self._schedule_preview() or "break")
            return sb

        def cb(par, var, vals, w=11):
            c = ttk.Combobox(par, textvariable=var, values=vals,
                             state="readonly", width=w,
                             style="Dark.TCombobox", font=F_MAIN)
            c.bind("<<ComboboxSelected>>", lambda *_: self._schedule_preview())
            return c

        def lb(par, text, w=None):
            kw = {"width": w} if w else {}
            return tk.Label(par, text=text, fg=DIM, bg=PANEL, font=F_MAIN, **kw)

        def row():
            f = tk.Frame(ops, bg=PANEL)
            f.pack(fill="x", pady=3)
            return f

        # Find / Replace
        r = row()
        self._find_var    = sv()
        self._replace_var = sv()
        lb(r, "Find:", 6).pack(side="left")
        en(r, self._find_var).pack(side="left", fill="x", expand=True, padx=(0, 6))
        lb(r, "Replace:").pack(side="left", padx=(0, 4))
        en(r, self._replace_var).pack(side="left", fill="x", expand=True)

        # Add / Replace entire / Position
        r = row()
        self._add_var         = sv()
        self._replace_all_var   = tk.BooleanVar()
        self._after_counter_var = tk.BooleanVar()
        self._add_pos_var       = tk.StringVar(value="After name")
        lb(r, "Add:", 6).pack(side="left")
        en(r, self._add_var).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ck(r, "Replace entire", self._replace_all_var).pack(side="left", padx=(0, 4))
        ck(r, "After counter", self._after_counter_var).pack(side="left", padx=(0, 4))
        cb(r, self._add_pos_var, ["After name", "Before name"]).pack(side="left")

        # Shared grid for Trim and Counter rows
        self._trim_var       = tk.BooleanVar()
        self._trim_begin_var = iv(0)
        self._trim_end_var   = iv(0)
        self._counter_var    = tk.BooleanVar()
        self._ctr_digits_var = iv(2)
        self._ctr_start_var  = iv(1)
        self._ctr_step_var   = iv(1)
        self._ctr_pos_var    = tk.StringVar(value="After name")

        tc_grid = tk.Frame(ops, bg=PANEL)
        tc_grid.pack(fill="x", pady=3)
        tc_grid.columnconfigure(7, weight=1)

        PAD_LBL  = (10, 4)
        PAD_SPIN = (0, 0)

        # Trim row (row=0)
        ck(tc_grid, "Trim", self._trim_var).grid(
            row=0, column=0, sticky="w", padx=(0, 6), pady=2)
        tk.Label(tc_grid, text="Begin:", fg=DIM, bg=PANEL, font=F_MAIN).grid(
            row=0, column=1, sticky="w", padx=PAD_LBL, pady=2)
        sp(tc_grid, self._trim_begin_var, 0, 100).grid(
            row=0, column=2, sticky="w", padx=PAD_SPIN, pady=2)
        tk.Label(tc_grid, text="End:", fg=DIM, bg=PANEL, font=F_MAIN).grid(
            row=0, column=3, sticky="w", padx=PAD_LBL, pady=2)
        sp(tc_grid, self._trim_end_var, 0, 100).grid(
            row=0, column=4, sticky="w", padx=PAD_SPIN, pady=2)

        # Counter row (row=1)
        ck(tc_grid, "Counter", self._counter_var).grid(
            row=1, column=0, sticky="w", padx=(0, 4), pady=2)
        tk.Label(tc_grid, text="Digits:", fg=DIM, bg=PANEL, font=F_MAIN).grid(
            row=1, column=1, sticky="w", padx=PAD_LBL, pady=2)
        sp(tc_grid, self._ctr_digits_var, 1, 5, w=4).grid(
            row=1, column=2, sticky="w", padx=PAD_SPIN, pady=2)
        tk.Label(tc_grid, text="Start:", fg=DIM, bg=PANEL, font=F_MAIN).grid(
            row=1, column=3, sticky="w", padx=PAD_LBL, pady=2)
        sp(tc_grid, self._ctr_start_var, 0, 9999, w=4).grid(
            row=1, column=4, sticky="w", padx=PAD_SPIN, pady=2)
        cb(tc_grid, self._ctr_pos_var, ["After name", "Before name"]).grid(
            row=1, column=7, sticky="w", padx=(8, 0), pady=2)
        tk.Label(tc_grid, text="Step:", fg=DIM, bg=PANEL, font=F_MAIN).grid(
            row=2, column=1, sticky="w", padx=PAD_LBL, pady=(0, 2))
        sp(tc_grid, self._ctr_step_var, 1, 9999).grid(
            row=2, column=2, sticky="w", padx=PAD_SPIN, pady=(0, 2))

        # Case / Remove digits
        r = row()
        self._upper_var = tk.BooleanVar()
        self._lower_var = tk.BooleanVar()
        self._title_var = tk.BooleanVar()
        self._nodig_var = tk.BooleanVar()

        def upper_cmd():
            if self._upper_var.get():
                self._lower_var.set(False); self._title_var.set(False)
            self._schedule_preview()

        def lower_cmd():
            if self._lower_var.get():
                self._upper_var.set(False); self._title_var.set(False)
            self._schedule_preview()

        def title_cmd():
            if self._title_var.get():
                self._upper_var.set(False); self._lower_var.set(False)
            self._schedule_preview()

        ck(r, "UPPER",     self._upper_var, upper_cmd).pack(side="left", padx=(0, 6))
        ck(r, "lower",     self._lower_var, lower_cmd).pack(side="left", padx=(0, 6))
        ck(r, "Title",     self._title_var, title_cmd).pack(side="left", padx=(0, 6))
        ck(r, "No digits", self._nodig_var).pack(side="left")

        tk.Frame(parent, bg=BTN_HOV, height=1).pack(fill="x", padx=10, pady=8)

        ls = tk.Frame(parent, bg=PANEL)
        ls.pack(fill="x", padx=10, pady=(0, 6))
        TBtn(ls, text="Load Tracks", command=self._load_tracks,
             bg=BTN, padx=8, pady=4, font=F_SMALL
             ).pack(side="left", fill="x", expand=True, padx=(0, 4))
        TBtn(ls, text="Save Tracks", command=self._save_tracks,
             bg=BTN, padx=8, pady=4, font=F_SMALL
             ).pack(side="left", fill="x", expand=True)

        self._info_text = tk.Text(parent, bg=ENTRY_BG, fg=TEXT, relief="flat",
                                  font=F_MONO, state="disabled", wrap="word", height=7,
                                  highlightthickness=1, highlightbackground="#444444",
                                  highlightcolor="#666666")
        self._info_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    # ── Audio column ──────────────────────────────────────────────────────

    def _build_audio_col(self, parent):
        tk.Label(parent, text="AUDIO TRACKS", fg=ACCENT, bg=PANEL,
                 font=F_HDR).pack(fill="x", padx=8, pady=(10, 4))

        sr = tk.Frame(parent, bg=PANEL)
        sr.pack(fill="x", padx=8, pady=(0, 4))
        TBtn(sr, text="Select All", bg=BTN, padx=8, pady=3, font=F_SMALL,
             command=lambda: self._sel_all("audio")
             ).pack(side="left", fill="x", expand=True, padx=(0, 3))
        TBtn(sr, text="Deselect All", bg=BTN, padx=8, pady=3, font=F_SMALL,
             command=lambda: self._desel_all("audio")
             ).pack(side="left", fill="x", expand=True)

        dr = tk.Frame(parent, bg=PANEL)
        dr.pack(fill="x", padx=8, pady=(0, 4))
        TBtn(dr, text="Delete Selected", bg=RED, padx=8, pady=3, font=F_SMALL,
             command=lambda: self._delete_tracks("audio")).pack(side="left")

        sf = tk.Frame(parent, bg=PANEL)
        sf.pack(fill="x", padx=8, pady=(0, 4))
        tk.Label(sf, text="Search:", fg=DIM, bg=PANEL, font=F_SMALL).pack(side="left", padx=(0, 4))
        _se = tk.Entry(sf, textvariable=self._audio_search_var,
                       bg=ENTRY_BG, fg=TEXT, insertbackground=TEXT,
                       relief="flat", font=F_MAIN)
        _se.pack(side="left", fill="x", expand=True)
        self._audio_search_var.trace_add("write", lambda *_: self._filter_audio_tree())

        tr = tk.Frame(parent, bg=PANEL)
        tr.pack(fill="x", padx=8, pady=(0, 6))
        self._audio_type_var = tk.StringVar()
        self._audio_type_cb  = ttk.Combobox(tr, textvariable=self._audio_type_var,
                                             state="readonly", width=10,
                                             style="Dark.TCombobox", font=F_MAIN)
        self._audio_type_cb.pack(side="right")
        TBtn(tr, text="Select Type", bg=BTN, padx=8, pady=3, font=F_SMALL,
             command=self._select_by_type
             ).pack(side="right", padx=(0, 4))

        tf = tk.Frame(parent, bg=PANEL)
        tf.pack(fill="both", expand=True, padx=8)
        self._audio_tree = ttk.Treeview(tf, columns=("name", "preview"),
                                        show="headings", selectmode="extended",
                                        style="Track.Treeview")
        self._audio_tree.heading("name",    text="Track Name")
        self._audio_tree.heading("preview", text="Preview")
        self._audio_tree.column("name",    width=220, stretch=True)
        self._audio_tree.column("preview", width=160, stretch=True)
        asb = ttk.Scrollbar(tf, orient="vertical", command=self._audio_tree.yview)
        self._audio_tree.configure(yscrollcommand=asb.set)
        self._audio_tree.pack(side="left", fill="both", expand=True)
        asb.pack(side="right", fill="y")
        self._audio_tree.bind("<<TreeviewSelect>>", lambda _: self._schedule_preview())

        af = tk.Frame(parent, bg=PANEL)
        af.pack(fill="x", padx=8, pady=6)
        tk.Label(af, text="Add:", fg=DIM, bg=PANEL, font=F_SMALL).pack(side="left")
        self._audio_add_count = tk.IntVar(value=1)
        tk.Spinbox(af, from_=1, to=10, textvariable=self._audio_add_count, width=3,
                   bg=ENTRY_BG, fg=TEXT, insertbackground=TEXT,
                   buttonbackground=BTN, relief="flat", font=F_MAIN,
                   highlightthickness=1, highlightbackground="#444444",
                   highlightcolor="#666666"
                   ).pack(side="left", padx=(4, 4))
        self._audio_main_var = tk.StringVar(value="Mono")
        self._audio_main_cb  = ttk.Combobox(
            af, textvariable=self._audio_main_var,
            values=["Mono", "Stereo", "3.0", "4.0", "5.x", "7.x", "Adaptive"],
            state="readonly", width=8, style="Dark.TCombobox", font=F_MAIN)
        self._audio_main_cb.pack(side="left", padx=(0, 4))
        self._audio_main_var.trace_add("write", lambda *_: self._refresh_sub_combo())
        self._audio_sub_var = tk.StringVar()
        self._audio_sub_cb  = ttk.Combobox(
            af, textvariable=self._audio_sub_var,
            state="readonly", width=8, style="Dark.TCombobox", font=F_MAIN)
        self._audio_sub_cb.pack(side="left", padx=(0, 4))
        TBtn(af, text="Add", bg=GREEN, padx=8, pady=3, font=F_SMALL,
             command=self._add_audio).pack(side="left", padx=(0, 4))
        self._refresh_sub_combo()

    # ── Video column ──────────────────────────────────────────────────────

    def _build_video_col(self, parent):
        tk.Label(parent, text="VIDEO TRACKS", fg=ACCENT, bg=PANEL,
                 font=F_HDR).pack(fill="x", padx=8, pady=(10, 4))

        sr = tk.Frame(parent, bg=PANEL)
        sr.pack(fill="x", padx=8, pady=(0, 4))
        TBtn(sr, text="Select All", bg=BTN, padx=8, pady=3, font=F_SMALL,
             command=lambda: self._sel_all("video")
             ).pack(side="left", fill="x", expand=True, padx=(0, 3))
        TBtn(sr, text="Deselect All", bg=BTN, padx=8, pady=3, font=F_SMALL,
             command=lambda: self._desel_all("video")
             ).pack(side="left", fill="x", expand=True)

        dr = tk.Frame(parent, bg=PANEL)
        dr.pack(fill="x", padx=8, pady=(0, 4))
        TBtn(dr, text="Delete Selected", bg=RED, padx=8, pady=3, font=F_SMALL,
             command=lambda: self._delete_tracks("video")).pack(side="left")

        sf = tk.Frame(parent, bg=PANEL)
        sf.pack(fill="x", padx=8, pady=(0, 4))
        tk.Label(sf, text="Search:", fg=DIM, bg=PANEL, font=F_SMALL).pack(side="left", padx=(0, 4))
        _se = tk.Entry(sf, textvariable=self._video_search_var,
                       bg=ENTRY_BG, fg=TEXT, insertbackground=TEXT,
                       relief="flat", font=F_MAIN)
        _se.pack(side="left", fill="x", expand=True)
        self._video_search_var.trace_add("write", lambda *_: self._filter_video_tree())

        tf = tk.Frame(parent, bg=PANEL)
        tf.pack(fill="both", expand=True, padx=8)
        self._video_tree = ttk.Treeview(tf, columns=("name", "preview"),
                                        show="headings", selectmode="extended",
                                        style="Track.Treeview")
        self._video_tree.heading("name",    text="Track Name")
        self._video_tree.heading("preview", text="Preview")
        self._video_tree.column("name",    width=200, stretch=True)
        self._video_tree.column("preview", width=160, stretch=True)
        vsb = ttk.Scrollbar(tf, orient="vertical", command=self._video_tree.yview)
        self._video_tree.configure(yscrollcommand=vsb.set)
        self._video_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self._video_tree.bind("<<TreeviewSelect>>", lambda _: self._schedule_preview())

        vf = tk.Frame(parent, bg=PANEL)
        vf.pack(fill="x", padx=8, pady=6)
        tk.Label(vf, text="Add:", fg=DIM, bg=PANEL, font=F_SMALL).pack(side="left")
        self._video_add_count = tk.IntVar(value=1)
        tk.Spinbox(vf, from_=1, to=10, textvariable=self._video_add_count, width=3,
                   bg=ENTRY_BG, fg=TEXT, insertbackground=TEXT,
                   buttonbackground=BTN, relief="flat", font=F_MAIN,
                   highlightthickness=1, highlightbackground="#444444",
                   highlightcolor="#666666"
                   ).pack(side="left", padx=(4, 4))
        TBtn(vf, text="Add", bg=GREEN, padx=8, pady=3, font=F_SMALL,
             command=self._add_video).pack(side="left", padx=(0, 4))

    # ── Tree population ───────────────────────────────────────────────────

    def _populate_audio_tree(self):
        sel = set(self._audio_tree.selection())
        for iid in self._audio_tree.get_children():
            self._audio_tree.delete(iid)
        for t in self._tracks["audio"]:
            self._audio_tree.insert("", "end", iid=t["id"],
                                    values=(f"{t['id']} — {t['name']}  ({t['subType']})", ""))
        valid = [t["id"] for t in self._tracks["audio"] if t["id"] in sel]
        if valid:
            self._audio_tree.selection_set(valid)

    def _populate_video_tree(self):
        sel = set(self._video_tree.selection())
        for iid in self._video_tree.get_children():
            self._video_tree.delete(iid)
        for t in self._tracks["video"]:
            self._video_tree.insert("", "end", iid=t["id"],
                                    values=(f"{t['id']} — {t['name']}", ""))
        valid = [t["id"] for t in self._tracks["video"] if t["id"] in sel]
        if valid:
            self._video_tree.selection_set(valid)

    def _refresh_audio_type_combo(self):
        types = self._unique_audio_types()
        self._audio_type_cb["values"] = types
        if types and self._audio_type_var.get() not in types:
            self._audio_type_cb.current(0)

    def _filter_audio_tree(self):
        query = self._audio_search_var.get().lower()
        for iid in self._audio_tree.get_children():
            self._audio_tree.detach(iid)
        for t in self._tracks["audio"]:
            if query in t["name"].lower():
                if not self._audio_tree.exists(t["id"]):
                    self._audio_tree.insert("", "end", iid=t["id"],
                                            values=(f"{t['id']} — {t['name']}  ({t['subType']})", ""))
                else:
                    self._audio_tree.reattach(t["id"], "", "end")

    def _filter_video_tree(self):
        query = self._video_search_var.get().lower()
        for iid in self._video_tree.get_children():
            self._video_tree.detach(iid)
        for t in self._tracks["video"]:
            if query in t["name"].lower():
                if not self._video_tree.exists(t["id"]):
                    self._video_tree.insert("", "end", iid=t["id"],
                                            values=(f"{t['id']} — {t['name']}", ""))
                else:
                    self._video_tree.reattach(t["id"], "", "end")

    def _refresh_sub_combo(self, *_):
        main = self._audio_main_var.get()
        subs = AUDIO_SUBTYPES.get(main, [])
        if subs:
            self._audio_sub_cb["values"] = subs
            self._audio_sub_cb.current(0)
            self._audio_sub_cb.pack(side="left", padx=(0, 4))
        else:
            self._audio_sub_cb.pack_forget()

    # ── Selection helpers ─────────────────────────────────────────────────

    def _sel_all(self, track_type):
        tree = self._audio_tree if track_type == "audio" else self._video_tree
        tree.selection_set(tree.get_children())
        self._schedule_preview()

    def _desel_all(self, track_type):
        tree = self._audio_tree if track_type == "audio" else self._video_tree
        tree.selection_remove(tree.get_children())
        self._schedule_preview()

    def _select_by_type(self):
        sel_type = self._audio_type_var.get()
        ids = [t["id"] for t in self._tracks["audio"] if t["subType"] == sel_type]
        self._audio_tree.selection_set(ids)
        self._schedule_preview()

    # ── Transform params ──────────────────────────────────────────────────

    def _get_params(self, counter=0):
        add_pos = "After counter" if self._after_counter_var.get() else ("Before" if "Before" in self._add_pos_var.get() else "After")
        ctr_pos = "Before" if "Before" in self._ctr_pos_var.get() else "After"
        return dict(
            find            = self._find_var.get(),
            replace         = self._replace_var.get(),
            add             = self._add_var.get(),
            add_pos         = add_pos,
            replace_all     = self._replace_all_var.get(),
            trim            = self._trim_var.get(),
            trim_begin      = self._trim_begin_var.get(),
            trim_end        = self._trim_end_var.get(),
            counter         = counter,
            counter_enabled = self._counter_var.get(),
            counter_digits  = self._ctr_digits_var.get(),
            counter_pos     = ctr_pos,
            upper           = self._upper_var.get(),
            lower           = self._lower_var.get(),
            title_case      = self._title_var.get(),
            remove_digits   = self._nodig_var.get(),
        )

    # ── Preview ───────────────────────────────────────────────────────────

    def _schedule_preview(self, *_):
        if self._preview_job:
            self.root.after_cancel(self._preview_job)
        self._preview_job = self.root.after(80, self._update_preview)

    def _update_preview(self):
        self._preview_job = None
        step       = self._ctr_step_var.get()
        counter    = self._ctr_start_var.get() * step
        a_selected = set(self._audio_tree.selection())
        v_selected = set(self._video_tree.selection())

        for t in self._tracks["audio"]:
            tid = t["id"]
            if tid in a_selected:
                orig    = self._orig_names.get(tid, t["name"])
                new     = apply_transform(orig, **self._get_params(counter))
                if self._counter_var.get():
                    counter += step
                preview = f"→ {new}" if new != orig else ""
            else:
                preview = ""
            cur = self._audio_tree.item(tid, "values")
            if cur:
                self._audio_tree.item(tid, values=(cur[0], preview))

        for t in self._tracks["video"]:
            tid = t["id"]
            if tid in v_selected:
                orig    = self._orig_names.get(tid, t["name"])
                new     = apply_transform(orig, **self._get_params(counter))
                if self._counter_var.get():
                    counter += step
                preview = f"→ {new}" if new != orig else ""
            else:
                preview = ""
            cur = self._video_tree.item(tid, "values")
            if cur:
                self._video_tree.item(tid, values=(cur[0], preview))

    def _initial_lift(self):
        self.root.lift()
        self.root.focus_force()
        if self._stay_on_top_var.get():
            self.root.attributes("-topmost", True)

    def _on_stay_on_top_changed(self, *_):
        if self._stay_on_top_var.get():
            self.root.attributes("-topmost", True)
            self.root.bind("<FocusIn>",  self._on_focus_in)
            self.root.bind("<FocusOut>", self._on_focus_out)
        else:
            self.root.attributes("-topmost", False)
            try:
                self.root.unbind("<FocusIn>")
                self.root.unbind("<FocusOut>")
            except Exception:
                pass

    def _on_focus_in(self, event):
        if event.widget is not self.root:
            return
        if self._stay_on_top_var.get():
            self.root.attributes("-topmost", True)
        self._reconnect()
        self._read_tracks()
        self._populate_audio_tree()
        self._populate_video_tree()
        self._refresh_audio_type_combo()
        self._update_header_info()

    def _on_focus_out(self, event):
        if event.widget != self.root or not self._stay_on_top_var.get():
            return
        if self._topmost_check_job:
            self.root.after_cancel(self._topmost_check_job)
        self._topmost_check_job = self.root.after(120, self._check_frontmost_app)

    def _check_frontmost_app(self):
        self._topmost_check_job = None
        if not self._stay_on_top_var.get():
            return
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
                    capture_output=True, text=True, timeout=1.0)
                keep = "Resolve" in result.stdout.strip()
            except Exception:
                keep = True
            self.root.after(0, lambda: self.root.attributes("-topmost", keep))
        threading.Thread(target=_query, daemon=True).start()

    # ── Apply / Undo / Restore / Refresh / Clear ─────────────────────────

    def _apply(self):
        if not self._timeline:
            return
        step       = self._ctr_step_var.get()
        counter    = self._ctr_start_var.get() * step
        changed    = 0
        self._last_changes = []
        a_selected = set(self._audio_tree.selection())
        v_selected = set(self._video_tree.selection())

        for t in self._tracks["audio"]:
            if t["id"] not in a_selected:
                continue
            orig = self._orig_names.get(t["id"], t["name"])
            new  = apply_transform(orig, **self._get_params(counter))
            if self._counter_var.get():
                counter += step
            if new != orig:
                self._timeline.SetTrackName("audio", t["index"], new)
                self._last_changes.append(
                    {"type": "audio", "index": t["index"], "old": orig})
                self._orig_names[t["id"]] = new
                t["name"] = new
                changed += 1
                self._audio_tree.item(
                    t["id"],
                    values=(f"{t['id']} — {new}  ({t['subType']})", ""))

        for t in self._tracks["video"]:
            if t["id"] not in v_selected:
                continue
            orig = self._orig_names.get(t["id"], t["name"])
            new  = apply_transform(orig, **self._get_params(counter))
            if self._counter_var.get():
                counter += step
            if new != orig:
                self._timeline.SetTrackName("video", t["index"], new)
                self._last_changes.append(
                    {"type": "video", "index": t["index"], "old": orig})
                self._orig_names[t["id"]] = new
                t["name"] = new
                changed += 1
                self._video_tree.item(t["id"], values=(f"{t['id']} — {new}", ""))

        self._undo_btn.config(
            state="normal" if self._last_changes else "disabled")
        self._set_info(f"[OK] Changed {changed} track name(s).")

    def _undo(self):
        if not self._last_changes:
            return
        undone = deleted = restored = 0
        for c in reversed(self._last_changes):
            if c.get("action") == "added":
                self._timeline.DeleteTrack(c["type"], c["index"])
                deleted += 1
            elif c.get("action") == "deleted":
                t_type = c["type"]
                sub    = c.get("subType", "mono").lower()
                ok = (self._timeline.AddTrack("audio", sub)
                      if t_type == "audio"
                      else self._timeline.AddTrack("video"))
                if ok:
                    idx = self._timeline.GetTrackCount(t_type)
                    self._timeline.SetTrackName(t_type, idx, c["name"])
                    restored += 1
            else:
                self._timeline.SetTrackName(c["type"], c["index"], c["old"])
                tid = self._tid(c["type"], c["index"])
                self._orig_names[tid] = c["old"]
                undone += 1
        self._last_changes = []
        self._undo_btn.config(state="disabled")
        self._read_tracks()
        self._populate_audio_tree()
        self._populate_video_tree()
        parts = []
        if undone:   parts.append(f"{undone} rename(s)")
        if deleted:  parts.append(f"{deleted} added track(s) removed")
        if restored: parts.append(f"{restored} deleted track(s) restored")
        self._set_info("[OK] Undone: " + ", ".join(parts) + ".")

    def _restore(self):
        if not self._timeline:
            return
        restored = deleted = 0
        while len(self._tracks["video"]) > self._start_counts["video"]:
            t = self._tracks["video"][-1]
            self._timeline.DeleteTrack("video", t["index"])
            self._read_tracks(); deleted += 1
        while len(self._tracks["audio"]) > self._start_counts["audio"]:
            t = self._tracks["audio"][-1]
            self._timeline.DeleteTrack("audio", t["index"])
            self._read_tracks(); deleted += 1
        for t in self._tracks["audio"]:
            sn = self._start_names.get(t["id"])
            if sn and t["name"] != sn:
                self._timeline.SetTrackName("audio", t["index"], sn)
                self._orig_names[t["id"]] = sn; t["name"] = sn; restored += 1
        for t in self._tracks["video"]:
            sn = self._start_names.get(t["id"])
            if sn and t["name"] != sn:
                self._timeline.SetTrackName("video", t["index"], sn)
                self._orig_names[t["id"]] = sn; t["name"] = sn; restored += 1
        self._last_changes = []
        self._undo_btn.config(state="disabled")
        self._populate_audio_tree()
        self._populate_video_tree()
        self._set_info(
            f"[OK] Restored {restored} name(s), deleted {deleted} extra track(s).")

    def _refresh(self):
        self._reconnect()
        self._read_tracks()
        for tid, nm in self._orig_names.items():
            self._start_names[tid] = nm
        self._start_counts["audio"] = len(self._tracks["audio"])
        self._start_counts["video"] = len(self._tracks["video"])
        self._last_changes = []
        self._undo_btn.config(state="disabled")
        self._audio_search_var.set("")
        self._video_search_var.set("")
        self._populate_audio_tree()
        self._populate_video_tree()
        self._refresh_audio_type_combo()
        self._update_header_info()
        self._set_info(
            f'[OK] Refreshed.\nTimeline: "{self._tl_name()}"\n'
            f'{len(self._tracks["video"])} video, '
            f'{len(self._tracks["audio"])} audio tracks.')

    def _clear(self):
        self._find_var.set("")
        self._replace_var.set("")
        self._add_var.set("")
        self._replace_all_var.set(False)
        self._after_counter_var.set(False)
        self._trim_var.set(False)
        self._trim_begin_var.set(0)
        self._trim_end_var.set(0)
        self._counter_var.set(False)
        self._ctr_digits_var.set(2)
        self._ctr_start_var.set(1)
        self._ctr_step_var.set(1)
        self._upper_var.set(False)
        self._lower_var.set(False)
        self._title_var.set(False)
        self._nodig_var.set(False)
        self._add_pos_var.set("After name")
        self._ctr_pos_var.set("After name")
        self._schedule_preview()

    # ── Add tracks ────────────────────────────────────────────────────────

    def _add_audio(self):
        if not self._timeline:
            return
        count  = self._audio_add_count.get()
        main   = self._audio_main_var.get()
        sub    = self._audio_sub_var.get()
        t_type = audio_type_string(main, sub)
        added  = 0
        self._last_changes = []
        for _ in range(count):
            if self._timeline.AddTrack("audio", t_type):
                idx = self._timeline.GetTrackCount("audio")
                self._timeline.SetTrackName("audio", idx, f"Audio {idx}")
                self._last_changes.append(
                    {"type": "audio", "index": idx, "action": "added"})
                added += 1
        if added:
            self._read_tracks()
            self._populate_audio_tree()
            self._refresh_audio_type_combo()
            self._undo_btn.config(state="normal")
            self._set_info(f"[OK] Added {added} audio track(s).")

    def _add_video(self):
        if not self._timeline:
            return
        count = self._video_add_count.get()
        added = 0
        self._last_changes = []
        for _ in range(count):
            if self._timeline.AddTrack("video"):
                idx = self._timeline.GetTrackCount("video")
                self._timeline.SetTrackName("video", idx, f"Video {idx}")
                self._last_changes.append(
                    {"type": "video", "index": idx, "action": "added"})
                added += 1
        if added:
            self._read_tracks()
            self._populate_video_tree()
            self._undo_btn.config(state="normal")
            self._set_info(f"[OK] Added {added} video track(s).")

    # ── Delete tracks ─────────────────────────────────────────────────────

    def _delete_tracks(self, track_type):
        tree   = self._audio_tree if track_type == "audio" else self._video_tree
        sel    = tree.selection()
        if not sel:
            self._set_info("[!] No tracks selected.")
            return
        tracks = self._tracks[track_type]
        to_del = []
        for iid in sel:
            t = next((x for x in tracks if x["id"] == iid), None)
            if t:
                to_del.append(t)
        if not to_del:
            self._set_info("[!] No tracks selected.")
            return
        n     = len(to_del)
        names = ", ".join(t["name"] for t in to_del)
        msg   = f"Delete {n} {track_type} track(s)?\n\n{names}"
        if not messagebox.askyesno("Delete Tracks", msg, parent=self.root):
            return
        self._last_changes = []
        for t in sorted(to_del, key=lambda x: x["index"], reverse=True):
            try:
                self._timeline.DeleteTrack(track_type, t["index"])
                self._last_changes.append({
                    "action":  "deleted",
                    "type":    track_type,
                    "name":    t["name"],
                    "subType": t.get("subType", "mono").lower(),
                })
            except Exception:
                pass
        self._read_tracks()
        self._populate_audio_tree()
        self._populate_video_tree()
        self._refresh_audio_type_combo()
        self._undo_btn.config(state="normal" if self._last_changes else "disabled")
        self._set_info(f"[OK] Deleted {n} {track_type} track(s).")

    # ── Save / Load ───────────────────────────────────────────────────────

    def _save_tracks(self):
        if not self._timeline:
            return
        fp = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=self._tl_name() + ".txt",
            filetypes=[("Text files", "*.txt")],
            title="Save Track Names")
        if not fp:
            return
        lines = []
        if self._tracks["video"]:
            lines.append("V")
            for t in self._tracks["video"]:
                lines.append(t["name"])
        if self._tracks["audio"]:
            lines.append("A")
            for t in self._tracks["audio"]:
                lines.append(f"{t['name']} {t['subType']}")
        try:
            with open(fp, "w", encoding="utf-8") as fh:
                fh.write("\n".join(lines))
            self._set_info(f"[OK] Saved: {os.path.basename(fp)}")
        except Exception as e:
            self._set_info(f"[X] Save failed: {e}")

    def _load_tracks(self):
        fp = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt")],
            title="Load Track Names")
        if not fp:
            return
        loaded  = {"video": [], "audio": []}
        section = None
        valid   = {"mono", "stereo", "5.1", "7.1", "adaptive12", "adaptive24"}
        try:
            with open(fp, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line == "V":
                        section = "video"
                    elif line == "A":
                        section = "audio"
                    elif line:
                        if section == "video":
                            loaded["video"].append({"name": line})
                        elif section == "audio":
                            parts = line.rsplit(" ", 1)
                            if len(parts) == 2 and parts[1].lower() in valid:
                                loaded["audio"].append(
                                    {"name": parts[0], "subType": parts[1]})
                            else:
                                loaded["audio"].append(
                                    {"name": line, "subType": "mono"})
                        else:
                            loaded["audio"].append({"name": line, "subType": "mono"})
        except Exception as e:
            self._set_info(f"[X] Load failed: {e}"); return

        filename = os.path.splitext(os.path.basename(fp))[0]
        LoadPreviewWindow(self.root, loaded, filename, self._apply_load)

    def _apply_load(self, loaded, mode, filename):
        if mode == "new":
            self._load_create_new(loaded, filename)
        elif mode == "add":
            self._load_add(loaded)
        else:
            self._load_change(loaded)

    def _load_change(self, loaded):
        changed = added = 0
        self._last_changes = []
        for i, lt in enumerate(loaded["video"]):
            if i < len(self._tracks["video"]):
                t = self._tracks["video"][i]
                if t["name"] != lt["name"]:
                    self._timeline.SetTrackName("video", t["index"], lt["name"])
                    self._last_changes.append(
                        {"type": "video", "index": t["index"], "old": t["name"]})
                    self._orig_names[t["id"]] = lt["name"]
                    t["name"] = lt["name"]; changed += 1
            else:
                if self._timeline.AddTrack("video"):
                    self._read_tracks()
                    nt = self._tracks["video"][-1]
                    self._timeline.SetTrackName("video", nt["index"], lt["name"])
                    self._orig_names[nt["id"]] = lt["name"]
                    nt["name"] = lt["name"]; added += 1
        for i, lt in enumerate(loaded["audio"]):
            if i < len(self._tracks["audio"]):
                t = self._tracks["audio"][i]
                if t["name"] != lt["name"]:
                    self._timeline.SetTrackName("audio", t["index"], lt["name"])
                    self._last_changes.append(
                        {"type": "audio", "index": t["index"], "old": t["name"]})
                    self._orig_names[t["id"]] = lt["name"]
                    t["name"] = lt["name"]; changed += 1
            else:
                if self._timeline.AddTrack("audio", lt.get("subType", "mono")):
                    self._read_tracks()
                    nt = self._tracks["audio"][-1]
                    self._timeline.SetTrackName("audio", nt["index"], lt["name"])
                    self._orig_names[nt["id"]] = lt["name"]
                    nt["name"] = lt["name"]; added += 1
        self._populate_audio_tree(); self._populate_video_tree()
        self._undo_btn.config(state="normal" if self._last_changes else "disabled")
        self._set_info(f"[OK] Changed {changed}, added {added} track(s).")

    def _load_add(self, loaded):
        added = 0
        self._last_changes = []
        for lt in loaded["video"]:
            if self._timeline.AddTrack("video"):
                self._read_tracks()
                nt = self._tracks["video"][-1]
                self._timeline.SetTrackName("video", nt["index"], lt["name"])
                self._orig_names[nt["id"]] = lt["name"]
                nt["name"] = lt["name"]; added += 1
        for lt in loaded["audio"]:
            if self._timeline.AddTrack("audio", lt.get("subType", "mono")):
                self._read_tracks()
                nt = self._tracks["audio"][-1]
                self._timeline.SetTrackName("audio", nt["index"], lt["name"])
                self._orig_names[nt["id"]] = lt["name"]
                nt["name"] = lt["name"]; added += 1
        self._populate_audio_tree(); self._populate_video_tree()
        self._undo_btn.config(state="normal" if self._last_changes else "disabled")
        self._set_info(f"[OK] Added {added} track(s).")

    def _load_create_new(self, loaded, filename):
        if not self._media_pool:
            return
        new_tl = self._media_pool.CreateEmptyTimeline(filename)
        if not new_tl:
            self._set_info("[X] Failed to create timeline."); return
        self._project.SetCurrentTimeline(new_tl)
        self._timeline = new_tl
        self._read_tracks()
        for i, lt in enumerate(loaded["video"]):
            if i == 0 and self._tracks["video"]:
                ft = self._tracks["video"][0]
                new_tl.SetTrackName("video", ft["index"], lt["name"])
                self._orig_names[ft["id"]] = lt["name"]; ft["name"] = lt["name"]
            elif i > 0 and new_tl.AddTrack("video"):
                self._read_tracks()
                nt = self._tracks["video"][-1]
                new_tl.SetTrackName("video", nt["index"], lt["name"])
                self._orig_names[nt["id"]] = lt["name"]; nt["name"] = lt["name"]
        if self._tracks["audio"]:
            new_tl.DeleteTrack("audio", 1); self._read_tracks()
        for lt in loaded["audio"]:
            if new_tl.AddTrack("audio", lt.get("subType", "mono")):
                self._read_tracks()
                nt = self._tracks["audio"][-1]
                new_tl.SetTrackName("audio", nt["index"], lt["name"])
                self._orig_names[nt["id"]] = lt["name"]; nt["name"] = lt["name"]
        self._populate_audio_tree(); self._populate_video_tree()
        self._last_changes = []
        self._undo_btn.config(state="disabled")
        self._set_info(f"[OK] Created timeline: {filename}")

    # ── Info panel ────────────────────────────────────────────────────────

    def _set_info(self, msg):
        self._info_text.config(state="normal")
        self._info_text.delete("1.0", "end")
        self._info_text.insert("1.0", msg)
        self._info_text.config(state="disabled")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        root = tk.Tk()
        TrackCommander(root)
        root.mainloop()
    except Exception as e:
        import traceback
        print("[Track Command] Fatal error:")
        traceback.print_exc()
