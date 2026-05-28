#!/usr/bin/env python3
"""
Clipper 1.2 — DaVinci Resolve Subclip Generator

Creates a Media Pool subclip for every clip on a chosen video track
in the current Resolve timeline. Part of the Marker Madness suite.

Installation:
  Copy this file into the Marker Madness suite folder, then launch from
  Workspace > Scripts > Utility inside DaVinci Resolve.

  macOS:   ~/Library/Application Support/Blackmagic Design/DaVinci Resolve/
            Fusion/Scripts/Utility/Marker Madness/
  Windows: C:\\ProgramData\\Blackmagic Design\\DaVinci Resolve\\
            Fusion\\Scripts\\Utility\\Marker Madness\\
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# ---------------------------------------------------------------------------
# App icon (embedded Base64 PNG — no external file required)
# ---------------------------------------------------------------------------

APP_ICON_B64 = (
    "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"
    "RK5CYII="
)

# ---------------------------------------------------------------------------
# DaVinci Resolve API connection
# ---------------------------------------------------------------------------

RESOLVE_SCRIPT_PATHS = {
    "darwin": "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules",
    "win32":  os.path.join(
        os.environ.get("PROGRAMDATA", "C:\\ProgramData"),
        "Blackmagic Design", "DaVinci Resolve", "Support", "Developer",
        "Scripting", "Modules",
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
# Theme  (identical across the Marker Madness suite)
# ---------------------------------------------------------------------------

BG       = "#2d2d2d"
PANEL    = "#333333"
TEXT     = "#E2E2E2"
ACCENT   = "#ffa500"
BTN      = "#505050"
BTN_HOV  = "#626262"
ENTRY_BG = "#1e1e1e"
TITLE_BG = "#1a1a1a"
SEL_BG   = "#505050"    # treeview selection — matches the rest of the suite
DIM      = "#909090"
GREEN    = "#388E3C"
BLUE     = "#1976D2"
PURPLE   = "#7B1FA2"
RED      = "#C62828"
BTN_TEXT = "#111111"

F_MAIN   = ("Avenir Next", 12)
F_BOLD   = ("Avenir Next", 13, "bold")
F_SMALL  = ("Avenir Next", 10)
F_MONO   = ("Courier", 12)
F_STATUS = ("Avenir Next", 10, "italic")
F_HDR    = ("Avenir Next", 10, "bold")

# ---------------------------------------------------------------------------
# Hover helper + TBtn  (identical across the suite)
# ---------------------------------------------------------------------------


def _hover_color(hex_color, factor=0.18):
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    r = min(255, int(r + (255 - r) * factor))
    g = min(255, int(g + (255 - g) * factor))
    b = min(255, int(b + (255 - b) * factor))
    return f"#{r:02x}{g:02x}{b:02x}"


class TBtn(tk.Button):
    def __init__(self, parent, bg=BTN, fg=BTN_TEXT, padx=12, pady=6,
                 font=F_MAIN, **kw):
        _hov = _hover_color(bg)
        super().__init__(parent, bg=bg, fg=fg, relief="flat", bd=0,
                         activebackground=_hov, activeforeground=fg,
                         highlightthickness=0,
                         padx=padx, pady=pady, cursor="hand2",
                         font=font, **kw)
        self.bind("<Enter>", lambda _: self.config(bg=_hov))
        self.bind("<Leave>", lambda _: self.config(bg=bg))


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def frames_to_tc(frame, fps):
    """Convert an absolute frame count to HH:MM:SS:FF string."""
    fps = int(round(fps)) or 24
    ff  = frame % fps
    s   = (frame // fps) % 60
    m   = (frame // fps // 60) % 60
    h   = frame // fps // 3600
    return f"{h:02d}:{m:02d}:{s:02d}:{ff:02d}"


def tc_to_frames(tc: str, fps: float) -> int:
    """Parse HH:MM:SS:FF (or HH:MM:SS.FF) timecode to a frame count.
    Returns -1 if the string cannot be parsed."""
    try:
        tc = tc.strip().replace(";", ":").replace(".", ":")
        parts = tc.split(":")
        if len(parts) == 4:
            h, m, s, ff = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
        elif len(parts) == 3:
            h, m, s, ff = 0, int(parts[0]), int(parts[1]), int(parts[2])
        else:
            return -1
        ifps = int(round(fps)) or 24
        return (h * 3600 + m * 60 + s) * ifps + ff
    except (ValueError, IndexError):
        return -1


def _walk_folders(folder, prefix=""):
    """Yield (display_path, folder_obj) pairs for the whole folder tree."""
    name = folder.GetName()
    path = f"{prefix}/{name}".lstrip("/") if prefix else name
    yield path, folder
    try:
        for sub in (folder.GetSubFolderList() or []):
            yield from _walk_folders(sub, path)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Main application class
# ---------------------------------------------------------------------------


class Clipper:

    def __init__(self, root):
        self.root = root
        self.root.withdraw()
        self.root.title("Clipper 1.2")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)
        self.root.minsize(640, 560)

        _w, _h = 720, 900
        self.root.update_idletasks()
        _sh = self.root.winfo_screenheight()
        # Leave headroom for macOS menu bar (~28 px) + Dock (~72 px)
        _h  = min(_h, _sh - 120)
        _cx = self.root.winfo_pointerx()
        _cy = self.root.winfo_pointery()
        # Don't clamp _x — that would force the window onto the primary display
        # even when the cursor is on a secondary monitor.
        _x  = _cx - _w // 2
        # Centre on cursor vertically, but clamp so the bottom stays on-screen.
        _y  = _cy - _h // 2
        _y  = max(40, _y)               # don't go above the menu bar
        _y  = min(_y, _sh - _h - 10)   # don't let the bottom fall off-screen
        self.root.geometry(f"{_w}x{_h}+{_x}+{_y}")

        # ── Resolve connection ────────────────────────────────────────────
        self._resolve    = None
        self._project    = None
        self._timeline   = None
        self._media_pool = None
        self._fps        = 24.0

        self._connect()

        # ── UI state ─────────────────────────────────────────────────────
        self._track_var      = tk.StringVar()
        self._bin_var        = tk.StringVar()
        self._bin_search_var = tk.StringVar()
        self._prefix_var     = tk.StringVar()
        self._suffix_var     = tk.StringVar()
        self._stay_on_top    = tk.BooleanVar(value=True)
        self._range_var      = tk.StringVar(value="all")   # "all" | "inout" | "selection"
        self._range_in_var   = tk.StringVar(value="")
        self._range_out_var  = tk.StringVar(value="")
        self._handles_var      = tk.IntVar(value=0)    # shared head+tail
        self._handles_custom   = tk.BooleanVar(value=False)
        self._head_handles_var = tk.IntVar(value=0)    # custom head
        self._tail_handles_var = tk.IntVar(value=0)    # custom tail
        self._markers_var      = tk.BooleanVar(value=False)  # preserve clip markers
        self._order_var        = tk.BooleanVar(value=False)  # preserve timeline order prefix
        self._order_mode_var   = tk.StringVar(value="seq")   # "seq" (T01_) | "tc" (timecode)
        self._video_only_var   = tk.BooleanVar(value=False)  # strip audio tracks from created timelines

        # internal data
        self._track_list        = []   # [(label, ttype, tidx, clip_count)]
        self._bin_list          = []   # [(display_path, folder_obj)] — full list
        self._preview_rows      = []   # list of dicts per clip
        self._preview_job       = None
        self._refreshing        = False   # guard against selection events during refresh
        self._focus_refresh_job = None    # debounce handle for focus-in auto-refresh
        self._last_tl_name      = self._tl_name()  # track name for poll comparison
        self._abort_flag        = False   # set True to stop the current batch

        self._build_ui()
        self._on_stay_on_top()

        # Bind focus-in auto-refresh
        self.root.bind("<FocusIn>", self._on_focus_in)

        # initial populate
        self._refresh_tracks()
        self._refresh_bins()
        self._schedule_preview()

        self.root.after(100, self._initial_lift)
        self.root.after(4000, self._poll_timeline)

    # ── Resolve connection ────────────────────────────────────────────────

    def _connect(self):
        self._resolve = get_resolve()
        if not self._resolve:
            return
        try:
            pm = self._resolve.GetProjectManager()
            self._project    = pm.GetCurrentProject() if pm else None
            self._timeline   = self._project.GetCurrentTimeline() if self._project else None
            self._media_pool = self._project.GetMediaPool() if self._project else None
            if self._timeline:
                try:
                    self._fps = float(self._timeline.GetSetting("timelineFrameRate") or 24)
                except Exception:
                    self._fps = 24.0
        except Exception:
            self._project = self._timeline = self._media_pool = None

    def _reconnect(self):
        self._connect()
        self._refresh_tracks()
        self._refresh_bins()
        self._schedule_preview()
        self._update_header()
        self._log("Reconnected to Resolve." if self._timeline else
                  "Could not connect — is DaVinci Resolve running?")

    # ── Auto-refresh: focus + poll ────────────────────────────────────────

    def _on_focus_in(self, event):
        """Trigger a debounced refresh whenever the window regains focus."""
        if event.widget != self.root:
            return
        if self._focus_refresh_job:
            self.root.after_cancel(self._focus_refresh_job)
        self._focus_refresh_job = self.root.after(500, self._auto_refresh_on_focus)

    def _auto_refresh_on_focus(self):
        self._focus_refresh_job = None
        self._on_refresh_clicked()

    def _poll_timeline(self):
        """Poll every 4 s; auto-refresh if Resolve has switched to a different timeline."""
        try:
            if self._resolve:
                pm = self._resolve.GetProjectManager()
                if pm:
                    proj = pm.GetCurrentProject()
                    if proj:
                        tl = proj.GetCurrentTimeline()
                        if tl:
                            name = tl.GetName()
                            if name != self._last_tl_name:
                                self._on_refresh_clicked()
        except Exception:
            pass
        self.root.after(4000, self._poll_timeline)

    def _tl_name(self):
        try:
            return self._timeline.GetName() if self._timeline else "No timeline"
        except Exception:
            return "No timeline"

    def _proj_name(self):
        try:
            return self._project.GetName() if self._project else "—"
        except Exception:
            return "—"

    # ── UI build ──────────────────────────────────────────────────────────

    def _build_ui(self):
        self._style_ttk()
        self._build_header()
        self._build_config()
        self._build_footer()   # footer first → anchored to bottom before preview expands
        self._build_preview()  # preview fills whatever space remains in the middle

    def _style_ttk(self):
        st = ttk.Style()
        st.theme_use("clam")
        st.configure("Treeview",
                     background=ENTRY_BG, foreground=TEXT,
                     fieldbackground=ENTRY_BG, rowheight=22,
                     font=F_MAIN, borderwidth=0)
        st.configure("Treeview.Heading",
                     background=PANEL, foreground=ACCENT,
                     font=F_HDR, relief="flat")
        st.map("Treeview",
               background=[("selected", SEL_BG)],
               foreground=[("selected", TEXT)])
        st.configure("TCombobox",
                     fieldbackground=ENTRY_BG, background=BTN,
                     foreground=TEXT, selectbackground=ENTRY_BG,
                     selectforeground=TEXT)
        st.map("TCombobox",
               fieldbackground=[("readonly", ENTRY_BG)],
               foreground=[("readonly", TEXT)])
        st.configure("TScrollbar",
                     background=BTN, troughcolor=ENTRY_BG,
                     arrowcolor=TEXT, borderwidth=0)

    def _build_header(self):
        hf = tk.Frame(self.root, bg=PANEL)
        hf.pack(fill="x")

        # App name
        name_row = tk.Frame(hf, bg=PANEL)
        name_row.pack(fill="x", padx=16, pady=(12, 0))
        tk.Label(name_row, text="✂  Clipper", fg=ACCENT, bg=PANEL,
                 font=("Avenir Next", 18, "bold")).pack(side="left")
        tk.Label(name_row, text="v1.2", fg=DIM, bg=PANEL,
                 font=F_SMALL).pack(side="left", padx=(4, 0), pady=(4, 0))

        # Float on top checkbox
        tk.Checkbutton(name_row, text="Float on Top",
                       variable=self._stay_on_top,
                       fg=DIM, bg=PANEL,
                       activeforeground=TEXT, activebackground=PANEL,
                       selectcolor=ENTRY_BG, font=F_SMALL,
                       command=self._on_stay_on_top).pack(side="right")

        # Project / timeline / fps row
        info_row = tk.Frame(hf, bg=PANEL)
        info_row.pack(fill="x", padx=16, pady=(4, 12))

        self._hdr_proj_var = tk.StringVar(value=self._proj_name())
        self._hdr_tl_var   = tk.StringVar(value=self._tl_name())
        self._hdr_fps_var  = tk.StringVar(value=f"{self._fps:.3g} fps")

        for label, var in [
            ("Project:", self._hdr_proj_var),
            ("Timeline:", self._hdr_tl_var),
            ("FPS:",      self._hdr_fps_var),
        ]:
            tk.Label(info_row, text=label, fg=DIM, bg=PANEL,
                     font=F_SMALL).pack(side="left", padx=(0, 4))
            tk.Label(info_row, textvariable=var, fg=TEXT, bg=PANEL,
                     font=F_SMALL).pack(side="left", padx=(0, 20))

    def _build_config(self):
        cf = tk.Frame(self.root, bg=BG)
        cf.pack(fill="x", padx=16, pady=(14, 0))
        cf.columnconfigure(1, weight=1)

        # Section label
        tk.Label(cf, text="SETTINGS", fg=ACCENT, bg=BG,
                 font=F_HDR).grid(row=0, column=0, columnspan=3,
                                   sticky="w", pady=(0, 8))

        lbl_kw = {"padx": (0, 12), "pady": 5, "sticky": "w"}

        # ── Track row ────────────────────────────────────────────────────
        tk.Label(cf, text="Track:", fg=TEXT, bg=BG,
                 font=F_MAIN).grid(row=1, column=0, **lbl_kw)

        track_frame = tk.Frame(cf, bg=BG)
        track_frame.grid(row=1, column=1, sticky="w", pady=5)

        self._track_combo = ttk.Combobox(track_frame, textvariable=self._track_var,
                                          state="readonly", width=20, font=F_MAIN)
        self._track_combo.pack(side="left")
        self._track_combo.bind("<<ComboboxSelected>>", self._on_track_changed)

        TBtn(track_frame, text="↻  Refresh",
             command=self._on_refresh_clicked,
             bg=BTN_HOV, fg=BG, padx=8, pady=4).pack(side="left", padx=(8, 0))

        self._clip_count_lbl = tk.Label(track_frame, text="", fg=DIM, bg=BG,
                                         font=F_SMALL)
        self._clip_count_lbl.pack(side="left", padx=(10, 0))

        # ── Destination bin ───────────────────────────────────────────────
        tk.Label(cf, text="Destination:", fg=TEXT, bg=BG,
                 font=F_MAIN).grid(row=2, column=0, **lbl_kw)

        bin_col = tk.Frame(cf, bg=BG)
        bin_col.grid(row=2, column=1, sticky="ew", pady=5)

        # Search row
        bin_search_row = tk.Frame(bin_col, bg=BG)
        bin_search_row.pack(fill="x", pady=(0, 4))
        tk.Label(bin_search_row, text="🔍", fg=DIM, bg=BG,
                 font=F_SMALL).pack(side="left", padx=(0, 4))
        self._bin_search_entry = tk.Entry(
            bin_search_row, textvariable=self._bin_search_var,
            bg=ENTRY_BG, fg=TEXT, insertbackground=TEXT,
            relief="flat", font=F_SMALL, width=26)
        self._bin_search_entry.pack(side="left")
        tk.Label(bin_search_row, text="filter bins", fg=DIM, bg=BG,
                 font=F_SMALL).pack(side="left", padx=(6, 0))
        TBtn(bin_search_row, text="✕", command=self._clear_bin_search,
             bg=BTN_HOV, fg=BG, padx=5, pady=2,
             font=F_SMALL).pack(side="left", padx=(6, 0))
        self._bin_search_var.trace_add("write", self._on_bin_search)

        # Combo + action buttons row
        bin_picker_row = tk.Frame(bin_col, bg=BG)
        bin_picker_row.pack(fill="x")
        self._bin_combo = ttk.Combobox(bin_picker_row, textvariable=self._bin_var,
                                        state="readonly", width=30, font=F_SMALL)
        self._bin_combo.pack(side="left")
        TBtn(bin_picker_row, text="◎ Current Bin", command=self._set_current_bin,
             bg=GREEN, fg=BG, padx=8, pady=4).pack(side="left", padx=(8, 0))
        TBtn(bin_picker_row, text="+ New Bin", command=self._new_bin,
             bg=BLUE, fg=BG, padx=8, pady=4).pack(side="left", padx=(6, 0))

        # ── Range row ────────────────────────────────────────────────────
        tk.Label(cf, text="Range:", fg=TEXT, bg=BG,
                 font=F_MAIN).grid(row=3, column=0, **lbl_kw)

        range_col = tk.Frame(cf, bg=BG)
        range_col.grid(row=3, column=1, sticky="w", pady=5)

        rb_kw = dict(fg=TEXT, bg=BG, activeforeground=TEXT,
                     activebackground=BG, selectcolor=ENTRY_BG,
                     font=F_MAIN, command=self._on_range_changed)
        tk.Radiobutton(range_col, text="Entire timeline",
                       variable=self._range_var, value="all",
                       **rb_kw).pack(side="left")
        tk.Radiobutton(range_col, text="In/Out range",
                       variable=self._range_var, value="inout",
                       **rb_kw).pack(side="left", padx=(12, 0))
        tk.Radiobutton(range_col, text="User Selection",
                       variable=self._range_var, value="selection",
                       **rb_kw).pack(side="left", padx=(12, 0))

        # In/Out TC fields — hidden until "In/Out range" is selected
        self._range_tc_frame = tk.Frame(cf, bg=BG)
        self._range_tc_frame.grid(row=4, column=1, sticky="w", pady=(0, 4))
        # (not gridded / shown until needed — see _on_range_changed)
        self._range_tc_frame.grid_remove()

        tc_kw = {"bg": ENTRY_BG, "fg": TEXT, "insertbackground": TEXT,
                 "relief": "flat", "font": F_MONO, "width": 12}
        tk.Label(self._range_tc_frame, text="In:", fg=DIM, bg=BG,
                 font=F_SMALL).pack(side="left", padx=(0, 4))
        self._range_in_entry = tk.Entry(self._range_tc_frame,
                                         textvariable=self._range_in_var, **tc_kw)
        self._range_in_entry.pack(side="left")
        self._range_in_entry.bind(
            "<FocusOut>", lambda _: self._normalize_tc_field(self._range_in_var))
        self._range_in_entry.bind(
            "<Return>",   lambda _: self._normalize_tc_field(self._range_in_var))
        tk.Label(self._range_tc_frame, text="Out:", fg=DIM, bg=BG,
                 font=F_SMALL).pack(side="left", padx=(10, 4))
        self._range_out_entry = tk.Entry(self._range_tc_frame,
                                          textvariable=self._range_out_var, **tc_kw)
        self._range_out_entry.pack(side="left")
        self._range_out_entry.bind(
            "<FocusOut>", lambda _: self._normalize_tc_field(self._range_out_var))
        self._range_out_entry.bind(
            "<Return>",   lambda _: self._normalize_tc_field(self._range_out_var))
        TBtn(self._range_tc_frame, text="↺ From Timeline",
             command=self._grab_range_from_timeline,
             bg=BTN_HOV, fg=BG, padx=8, pady=3,
             font=F_SMALL).pack(side="left", padx=(10, 0))
        tk.Label(self._range_tc_frame, text="  ·  filters clips on the track selected above",
                 fg=DIM, bg=BG, font=F_SMALL).pack(side="left")

        # Bind TC entry changes to refresh preview + update button label
        self._range_in_var.trace_add("write",  lambda *_: (self._schedule_preview(),
                                                            self._update_run_btn_label()))
        self._range_out_var.trace_add("write", lambda *_: (self._schedule_preview(),
                                                            self._update_run_btn_label()))

        # ── Prefix / Suffix rows ──────────────────────────────────────────
        tk.Label(cf, text="Prefix:", fg=TEXT, bg=BG,
                 font=F_MAIN).grid(row=5, column=0, **lbl_kw)
        tk.Entry(cf, textvariable=self._prefix_var, bg=ENTRY_BG, fg=TEXT,
                 insertbackground=TEXT, relief="flat", font=F_MAIN,
                 width=24).grid(row=5, column=1, sticky="w", pady=5)

        tk.Label(cf, text="Suffix:", fg=TEXT, bg=BG,
                 font=F_MAIN).grid(row=6, column=0, **lbl_kw)
        sfx_frame = tk.Frame(cf, bg=BG)
        sfx_frame.grid(row=6, column=1, sticky="w", pady=5)
        tk.Entry(sfx_frame, textvariable=self._suffix_var, bg=ENTRY_BG, fg=TEXT,
                 insertbackground=TEXT, relief="flat", font=F_MAIN,
                 width=24).pack(side="left")
        tk.Label(sfx_frame, text="(added to every clip name)",
                 fg=DIM, bg=BG, font=F_SMALL).pack(side="left", padx=(10, 0))

        # ── Handles row ───────────────────────────────────────────────────
        tk.Label(cf, text="Handles:", fg=TEXT, bg=BG,
                 font=F_MAIN).grid(row=7, column=0, **lbl_kw)
        hdl_frame = tk.Frame(cf, bg=BG)
        hdl_frame.grid(row=7, column=1, sticky="w", pady=5)

        # Shared head+tail counter  [−] [n] [+]
        self._make_counter(hdl_frame, self._handles_var).pack(side="left")
        tk.Label(hdl_frame, text="frames each side",
                 fg=DIM, bg=BG, font=F_SMALL).pack(side="left", padx=(6, 14))

        # Custom checkbox
        tk.Checkbutton(hdl_frame, text="Custom head / tail",
                       variable=self._handles_custom,
                       fg=DIM, bg=BG, activeforeground=TEXT,
                       activebackground=BG, selectcolor=ENTRY_BG,
                       font=F_SMALL,
                       command=self._on_handles_mode).pack(side="left")

        # Custom head/tail row — hidden until checkbox ticked
        self._hdl_custom_frame = tk.Frame(cf, bg=BG)
        self._hdl_custom_frame.grid(row=8, column=1, sticky="w", pady=(0, 4))
        self._hdl_custom_frame.grid_remove()

        tk.Label(self._hdl_custom_frame, text="Head:", fg=DIM, bg=BG,
                 font=F_SMALL).pack(side="left", padx=(0, 4))
        self._make_counter(self._hdl_custom_frame,
                           self._head_handles_var).pack(side="left")
        tk.Label(self._hdl_custom_frame, text="fr",
                 fg=DIM, bg=BG, font=F_SMALL).pack(side="left", padx=(4, 16))
        tk.Label(self._hdl_custom_frame, text="Tail:", fg=DIM, bg=BG,
                 font=F_SMALL).pack(side="left", padx=(0, 4))
        self._make_counter(self._hdl_custom_frame,
                           self._tail_handles_var).pack(side="left")
        tk.Label(self._hdl_custom_frame, text="fr",
                 fg=DIM, bg=BG, font=F_SMALL).pack(side="left", padx=(4, 0))

        for v in (self._handles_var, self._head_handles_var, self._tail_handles_var):
            v.trace_add("write", lambda *_: self._schedule_preview())

        # Hint
        tk.Label(cf, text="Clip name = Prefix + Source Clip Name + Suffix",
                 fg=DIM, bg=BG, font=F_SMALL).grid(
                     row=9, column=0, columnspan=3, sticky="w", pady=(2, 4))

        # Options row 1 — markers + timeline order
        opts_frame = tk.Frame(cf, bg=BG)
        opts_frame.grid(row=10, column=0, columnspan=3, sticky="w", pady=(0, 4))

        tk.Checkbutton(opts_frame,
                       text="Preserve clip markers",
                       variable=self._markers_var,
                       fg=TEXT, bg=BG, activeforeground=TEXT,
                       activebackground=BG, selectcolor=ENTRY_BG,
                       font=F_MAIN).pack(side="left")

        tk.Checkbutton(opts_frame,
                       text="Preserve Timeline Order",
                       variable=self._order_var,
                       command=self._toggle_order_mode_frame,
                       fg=TEXT, bg=BG, activeforeground=TEXT,
                       activebackground=BG, selectcolor=ENTRY_BG,
                       font=F_MAIN).pack(side="left", padx=(20, 0))

        # Row 11 — sort-prefix sub-options (shown only when Preserve Timeline Order is on)
        self._order_mode_frame = tk.Frame(cf, bg=BG)
        self._order_mode_frame.grid(row=11, column=0, columnspan=3, sticky="w", pady=(0, 2))
        self._order_mode_frame.grid_remove()   # hidden until checkbox is ticked

        tk.Label(self._order_mode_frame, text="Sort prefix:",
                 fg=DIM, bg=BG, font=F_MAIN).pack(side="left", padx=(44, 10))

        tk.Radiobutton(self._order_mode_frame,
                       text="Sequential  (T01_, T02_…)",
                       variable=self._order_mode_var, value="seq",
                       command=self._schedule_preview,
                       fg=TEXT, bg=BG, activeforeground=TEXT, activebackground=BG,
                       selectcolor=ENTRY_BG, font=F_MAIN).pack(side="left")

        tk.Radiobutton(self._order_mode_frame,
                       text="Timecode  (01-00-44-05_…)",
                       variable=self._order_mode_var, value="tc",
                       command=self._schedule_preview,
                       fg=TEXT, bg=BG, activeforeground=TEXT, activebackground=BG,
                       selectcolor=ENTRY_BG, font=F_MAIN).pack(side="left", padx=(16, 0))

        # Row 12 — video only
        opts_frame2 = tk.Frame(cf, bg=BG)
        opts_frame2.grid(row=12, column=0, columnspan=3, sticky="w", pady=(4, 8))

        tk.Checkbutton(opts_frame2,
                       text="Video only  (strip audio tracks from created sequences and clips)",
                       variable=self._video_only_var,
                       fg=TEXT, bg=BG, activeforeground=TEXT,
                       activebackground=BG, selectcolor=ENTRY_BG,
                       font=F_MAIN).pack(side="left")

        # Separator
        tk.Frame(cf, bg=BTN_HOV, height=1).grid(
            row=13, column=0, columnspan=3, sticky="ew", pady=(4, 0))

    def _build_preview(self):
        pf = tk.Frame(self.root, bg=BG)
        pf.pack(fill="both", expand=True, padx=16, pady=(12, 0))

        # Header row
        hdr = tk.Frame(pf, bg=BG)
        hdr.pack(fill="x", pady=(0, 6))
        tk.Label(hdr, text="PREVIEW", fg=ACCENT, bg=BG,
                 font=F_HDR).pack(side="left")
        TBtn(hdr, text="↻  Refresh Preview",
             command=self._schedule_preview,
             bg=PURPLE, fg=BG, padx=8, pady=3,
             font=F_SMALL).pack(side="right")
        self._preview_status = tk.Label(hdr, text="", fg=DIM, bg=BG,
                                         font=F_SMALL)
        self._preview_status.pack(side="right", padx=(0, 12))

        # Treeview + scrollbars
        tree_frame = tk.Frame(pf, bg=BG)
        tree_frame.pack(fill="both", expand=True)

        cols = ("#", "Subclip Name", "Source Clip", "In TC", "Out TC", "Duration")
        self._tree = ttk.Treeview(tree_frame, columns=cols,
                                   show="headings", selectmode="extended")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                             command=self._tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal",
                             command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set,
                              xscrollcommand=hsb.set)

        widths = [36, 240, 200, 90, 90, 80]
        anchors = ["center", "w", "w", "center", "center", "center"]
        for col, w, a in zip(cols, widths, anchors):
            self._tree.heading(col, text=col)
            self._tree.column(col, width=w, minwidth=w, anchor=a, stretch=(col == "Subclip Name"))

        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self._tree.pack(side="left", fill="both", expand=True)

        # Row striping
        self._tree.tag_configure("odd",  background=ENTRY_BG)
        self._tree.tag_configure("even", background="#232323")
        self._tree.tag_configure("warn", foreground="#ffcc44")

        # Auto-switch to User Selection mode on row click
        self._tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        # Cmd+A / Ctrl+A — select every row in the preview
        self._tree.bind("<Command-a>", self._select_all_rows)
        self._tree.bind("<Control-a>", self._select_all_rows)

    def _build_footer(self):
        ff = tk.Frame(self.root, bg=BG)
        ff.pack(side="bottom", fill="x", padx=16, pady=(8, 12))

        # Separator
        tk.Frame(ff, bg=BTN_HOV, height=1).pack(fill="x", pady=(0, 8))

        # Log
        log_frame = tk.Frame(ff, bg=ENTRY_BG, bd=0)
        log_frame.pack(fill="x", pady=(0, 8))
        self._log_text = tk.Text(log_frame, bg=ENTRY_BG, fg=DIM,
                                  relief="flat", font=F_SMALL,
                                  height=8, state="disabled",
                                  wrap="word", padx=6, pady=4)
        self._log_text.pack(fill="x")

        # Buttons
        btn_row = tk.Frame(ff, bg=BG)
        btn_row.pack(fill="x")

        TBtn(btn_row, text="↻  Reconnect",
             command=self._reconnect,
             bg=BTN_HOV, fg=BG, padx=10, pady=6).pack(side="left")

        self._run_btn = TBtn(btn_row, text="▶  Create All Clips",
                              command=self._run_for_mode,
                              bg=ACCENT, fg=BG, padx=14, pady=6,
                              font=F_MAIN)
        self._run_btn.pack(side="right")

        TBtn(btn_row, text="✕  Close",
             command=self.root.destroy,
             bg=BTN_HOV, fg=BG, padx=10, pady=6).pack(side="right", padx=(0, 8))

        self._abort_btn = TBtn(btn_row, text="⛔  Abort",
                                command=self._request_abort,
                                bg=RED, fg=BG, padx=10, pady=6)
        self._abort_btn.pack(side="right", padx=(0, 8))
        self._abort_btn.pack_forget()   # hidden until a batch is running

        self._range_seq_btn = TBtn(btn_row, text="⊡  Clip from Range",
                                    command=self._create_sequence_from_range,
                                    bg=BTN_HOV, fg=BG, padx=10, pady=6)
        self._range_seq_btn.pack(side="right", padx=(0, 8))

    # ── Header ────────────────────────────────────────────────────────────

    def _update_header(self):
        try:
            self._hdr_proj_var.set(self._proj_name())
            self._hdr_tl_var.set(self._tl_name())
            self._hdr_fps_var.set(f"{self._fps:.3g} fps")
        except Exception:
            pass

    # ── Track helpers ─────────────────────────────────────────────────────

    def _refresh_tracks(self):
        """Populate the track dropdown from the current timeline."""
        self._track_list = []
        labels = []

        if not self._timeline:
            self._track_combo["values"] = ["— not connected —"]
            self._track_var.set("— not connected —")
            self._clip_count_lbl.config(text="")
            return

        try:
            for ttype in ("video", "audio"):
                count = 0
                try:
                    count = self._timeline.GetTrackCount(ttype)
                except Exception:
                    pass
                for ti in range(1, count + 1):
                    prefix = "V" if ttype == "video" else "A"
                    try:
                        items = self._timeline.GetItemListInTrack(ttype, ti) or []
                        n_clips = len(items)
                    except Exception:
                        n_clips = 0
                    noun  = "clip" if n_clips == 1 else "clips"
                    label = f"{prefix}{ti}  —  {n_clips} {noun}"
                    self._track_list.append((label, ttype, ti, n_clips))
                    labels.append(label)
        except Exception:
            pass

        if not labels:
            labels = ["— no tracks found —"]
        else:
            # Prepend a catch-all entry that covers every track at once.
            total_clips = sum(nc for (_, _, _, nc) in self._track_list)
            noun        = "clip" if total_clips == 1 else "clips"
            all_label   = f"All tracks  —  {total_clips} {noun}"
            self._track_list.insert(0, (all_label, "all", 0, total_clips))
            labels.insert(0, all_label)

        self._track_combo["values"] = labels

        # ── Smart track restore ───────────────────────────────────────────
        # 1. Try to keep the current selection by matching track type + index
        #    (ignores clip-count changes in the label string).
        # 2. If the track no longer exists, pick the first track that has clips.
        # 3. Final fallback: first label in the list.
        cur = self._track_var.get()

        # Resolve current selection → (ttype, tidx)
        cur_ttype, cur_tidx = None, None
        for (lbl, tt, ti, _) in self._track_list:
            if lbl == cur:
                cur_ttype, cur_tidx = tt, ti
                break

        # Find the refreshed label for the same track
        matched = None
        if cur_ttype is not None:
            for (lbl, tt, ti, _) in self._track_list:
                if tt == cur_ttype and ti == cur_tidx:
                    matched = lbl
                    break

        if matched:
            self._track_var.set(matched)
        else:
            # Track gone — pick first track that actually has clips
            first_with_clips = next(
                (lbl for (lbl, _, _, nc) in self._track_list if nc > 0), None)
            self._track_var.set(first_with_clips if first_with_clips else labels[0])

        self._update_clip_count_label()

    def _update_clip_count_label(self):
        # In In/Out range mode the label is owned by _refresh_preview (which
        # shows "X of Y clips in range"). Don't overwrite it here.
        if self._range_var.get() == "inout":
            return
        sel = self._track_var.get()
        for (label, ttype, tidx, n_clips) in self._track_list:
            if label == sel:
                noun = "clip" if n_clips == 1 else "clips"
                clr  = ACCENT if n_clips else DIM
                self._clip_count_lbl.config(
                    text=f"{n_clips} {noun} will become subclips", fg=clr)
                return
        self._clip_count_lbl.config(text="", fg=DIM)

    def _selected_track(self):
        """Return (ttype, tidx) for the currently selected track, or (None, None)."""
        sel = self._track_var.get()
        for (label, ttype, tidx, _) in self._track_list:
            if label == sel:
                return ttype, tidx
        return None, None

    # ── Bin helpers ───────────────────────────────────────────────────────

    def _refresh_bins(self):
        """Walk the media pool folder tree and populate the bin dropdown."""
        self._bin_list = []
        labels = []

        if not self._media_pool:
            self._bin_combo["values"] = ["— not connected —"]
            self._bin_var.set("— not connected —")
            return

        try:
            root_folder = self._media_pool.GetRootFolder()
            for path, folder in _walk_folders(root_folder):
                self._bin_list.append((path, folder))
                labels.append(path)
        except Exception:
            pass

        if not labels:
            labels = ["— no bins found —"]

        self._bin_combo["values"] = labels
        cur = self._bin_var.get()
        if cur not in labels:
            # Default to whichever bin is currently active in Resolve
            try:
                active = self._media_pool.GetCurrentFolder()
                if active:
                    active_name = active.GetName()
                    for path, folder in self._bin_list:
                        try:
                            if folder.GetName() == active_name:
                                self._bin_var.set(path)
                                return
                        except Exception:
                            continue
            except Exception:
                pass
            self._bin_var.set(labels[0])

    def _selected_folder(self):
        """Return the folder object for the currently selected bin, or None.
        Uses the cached list — prefer _get_dest_folder() for live operations."""
        sel = self._bin_var.get()
        for (path, folder) in self._bin_list:
            if path == sel:
                return folder
        return None

    def _get_dest_folder(self):
        """Re-walk the bin tree fresh to return a live folder reference.
        Avoids stale proxy objects that cause SetCurrentFolder to silently fail."""
        sel_path = self._bin_var.get()
        if not self._media_pool or not sel_path:
            return None
        try:
            root = self._media_pool.GetRootFolder()
            for path, folder in _walk_folders(root):
                if path == sel_path:
                    return folder
        except Exception:
            pass
        return None

    def _new_bin(self):
        """Prompt for a name, create a new top-level bin in the media pool."""
        if not self._media_pool:
            messagebox.showwarning("Not Connected",
                "Not connected to DaVinci Resolve.", parent=self.root)
            return
        name = simpledialog.askstring(
            "New Bin", "Bin name:", parent=self.root)
        if not name or not name.strip():
            return
        name = name.strip()
        try:
            root_folder = self._media_pool.GetRootFolder()
            new_folder  = self._media_pool.AddSubFolder(root_folder, name)
            if not new_folder:
                messagebox.showerror("Error",
                    f"Could not create bin \"{name}\".\n"
                    "It may already exist at the root level.",
                    parent=self.root)
                return
        except Exception as exc:
            messagebox.showerror("Error",
                f"Could not create bin.\n\n{exc}", parent=self.root)
            return
        self._refresh_bins()
        # Select the new bin
        for path, _ in self._bin_list:
            if path.endswith(name):
                self._bin_var.set(path)
                break
        self._log(f"Created bin: {name}")

    def _set_current_bin(self):
        """Set the destination to whichever bin is active in the Resolve Media Pool."""
        if not self._media_pool:
            messagebox.showwarning("Not Connected",
                "Not connected to DaVinci Resolve.", parent=self.root)
            return
        try:
            active = self._media_pool.GetCurrentFolder()
            if not active:
                self._log("⚠  No active bin found in the Media Pool.")
                return
            active_name = active.GetName()

            def _find_by_name(bl):
                for path, f in bl:
                    try:
                        if f.GetName() == active_name:
                            return path
                    except Exception:
                        continue
                return None

            # Try the cached list first
            path = _find_by_name(self._bin_list)
            if path:
                self._bin_var.set(path)
                self._log(f"Destination → {path}")
                return
            # Refresh and retry
            self._refresh_bins()
            path = _find_by_name(self._bin_list)
            if path:
                self._bin_var.set(path)
                self._log(f"Destination → {path}")
                return
            self._log(f"⚠  '{active_name}' not found in bin list — bin list refreshed.")
        except Exception as exc:
            self._log(f"⚠  Could not read current bin: {exc}")

    def _on_bin_search(self, *_):
        """Filter the bin dropdown to entries matching the search text."""
        q = self._bin_search_var.get().strip().lower()
        if q:
            filtered = [path for (path, _) in self._bin_list
                        if q in path.lower()]
        else:
            filtered = [path for (path, _) in self._bin_list]
        self._bin_combo["values"] = filtered if filtered else ["— no matches —"]
        # Keep current selection if still visible, else pick first match
        if self._bin_var.get() not in (filtered or []):
            self._bin_var.set(filtered[0] if filtered else "")

    def _clear_bin_search(self):
        self._bin_search_var.set("")
        self._bin_search_entry.focus_set()

    def _run_for_mode(self):
        """Dispatch the main action button based on the active range mode."""
        mode = self._range_var.get()
        if mode == "selection":
            self._create_selected_subclips()
        else:
            self._create_subclips()

    def _update_run_btn_label(self):
        """Keep the main action button label in sync with the active range mode."""
        mode = self._range_var.get()
        if mode == "inout":
            self._run_btn.config(text="▶  Create In/Out Clips")
        elif mode == "selection":
            n = len(self._tree.selection())
            suffix = f"  ({n})" if n else ""
            self._run_btn.config(text=f"▶  Create Selected{suffix}")
        else:
            self._run_btn.config(text="▶  Create All Clips")

    def _select_all_rows(self, _event=None):
        """Select every row in the preview table (Cmd+A / Ctrl+A)."""
        all_ids = self._tree.get_children()
        if all_ids:
            self._tree.selection_set(all_ids)
        return "break"   # prevent default Tk text-selection behaviour

    def _toggle_order_mode_frame(self):
        """Show or hide the Sequential / Timecode radio sub-row under Preserve Timeline Order."""
        if self._order_var.get():
            self._order_mode_frame.grid()
        else:
            self._order_mode_frame.grid_remove()
        self._schedule_preview()

    def _on_range_changed(self):
        """Show/hide TC fields; auto-grab marks for In/Out; keep preview for Selection."""
        mode = self._range_var.get()
        if mode == "inout":
            self._range_tc_frame.grid()
        else:
            self._range_tc_frame.grid_remove()
        self._update_run_btn_label()

        if mode == "selection":
            # Don't rebuild — current preview becomes the pool to select from.
            # The button label already shows "Create Selected".
            return

        # Entire Timeline or In/Out range: clear any row highlights and rebuild.
        self._refreshing = True
        self._tree.selection_set([])
        self._refreshing = False

        if mode == "inout":
            # Auto-grab In/Out marks silently; if none found the TC fields stay
            # empty and the user can enter them manually or click ↺ From Timeline.
            self._grab_range_from_timeline(silent=True)
            # The TC-var traces will schedule the preview if marks were populated.
            # Call explicitly as well so we always rebuild (handles the "no marks" case).

        self._schedule_preview()

    def _on_tree_select(self, *_):
        """Silently flip the radio to User Selection when any row is clicked.
        Never auto-reverts — user must click a radio to leave this mode."""
        if self._refreshing:
            return
        sel = self._tree.selection()
        n   = len(sel)
        if n > 0 and self._range_var.get() != "selection":
            # Set the radio without calling _on_range_changed — no rebuild,
            # so the current preview (possibly range-filtered) stays intact.
            self._range_var.set("selection")
            self._range_tc_frame.grid_remove()
        # Sync the main action button label (shows count when in selection mode)
        self._update_run_btn_label()

    def _grab_range_from_timeline(self, silent=False):
        """Read timeline In/Out marks and populate the range TC fields.

        Resolve 21+  → GetMarkInOut() returns
                        {'video': {'in': <frame>, 'out': <frame>}, 'audio': ...}
                        where frame is relative to the timeline's start frame.
        Older Resolve → GetCurrentInPoint() / GetCurrentOutPoint() returning
                        either a raw frame count or a packed-decimal TC integer
                        (e.g. 3004219 = 03:00:42:19).

        silent=True   → suppress all dialogs (used for the auto-grab on radio click).
        """
        if not self._timeline:
            if not silent:
                messagebox.showwarning("Not Connected",
                    "Not connected to Resolve.", parent=self.root)
            return

        # Timeline start frame — needed to convert relative frames to TC
        tl_start = 0
        try:
            tl_start = int(self._timeline.GetStartFrame() or 0)
        except Exception:
            pass

        def _frame_to_tc(frame):
            """Convert a timeline-relative frame count to a TC string."""
            return frames_to_tc(int(frame) + tl_start, self._fps)

        def _resolve_val_legacy(val):
            """Handle older API returns: packed-decimal TC or raw frame count."""
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

        # ── Resolve 21+: GetMarkInOut() ───────────────────────────────────
        # Returns {'video': {'in': <frame>, 'out': <frame>}, 'audio': {...}}
        fn_mio = getattr(self._timeline, 'GetMarkInOut', None)
        if callable(fn_mio):
            try:
                result = fn_mio()
                self._log(f"  GetMarkInOut() → {result!r}")
                in_val = out_val = None

                if isinstance(result, dict):
                    # Prefer 'video'; fall back to top-level in/out keys
                    for key in ('video', 'audio', None):
                        section = result.get(key, result) if key else result
                        if isinstance(section, dict) and 'in' in section:
                            in_val  = section['in']
                            out_val = section.get('out')
                            break
                elif isinstance(result, (list, tuple)) and len(result) >= 2:
                    in_val, out_val = result[0], result[1]

                if in_val is not None and int(in_val) >= 0:
                    tc = _frame_to_tc(in_val)
                    self._range_in_var.set(tc)
                    got_in = True
                    self._log(f"    in  frame {in_val} + {tl_start} → {tc}")

                if out_val is not None and int(out_val) >= 0:
                    tc = _frame_to_tc(out_val)
                    self._range_out_var.set(tc)
                    got_out = True
                    self._log(f"    out frame {out_val} + {tl_start} → {tc}")

            except Exception as exc:
                self._log(f"  GetMarkInOut exception: {exc}")

        # ── Older Resolve: individual in/out methods ──────────────────────
        if not got_in:
            for attr in ("GetCurrentInPoint", "GetInPoint"):
                fn = getattr(self._timeline, attr, None)
                if not callable(fn):
                    continue
                try:
                    raw = fn()
                    self._log(f"  TL.{attr}() → {raw!r}")
                    tc = _resolve_val_legacy(raw)
                    if tc:
                        self._range_in_var.set(tc)
                        got_in = True
                        break
                except Exception as exc:
                    self._log(f"  TL.{attr} exception: {exc}")

        if not got_out:
            for attr in ("GetCurrentOutPoint", "GetOutPoint"):
                fn = getattr(self._timeline, attr, None)
                if not callable(fn):
                    continue
                try:
                    raw = fn()
                    self._log(f"  TL.{attr}() → {raw!r}")
                    tc = _resolve_val_legacy(raw)
                    if tc:
                        self._range_out_var.set(tc)
                        got_out = True
                        break
                except Exception as exc:
                    self._log(f"  TL.{attr} exception: {exc}")

        if got_in and got_out:
            self._log("In/Out range imported from timeline.")
        elif got_in:
            self._log("⚠  Got In point — enter Out manually (HH:MM:SS:FF).")
        elif got_out:
            self._log("⚠  Got Out point — enter In manually (HH:MM:SS:FF).")
        else:
            if not silent:
                messagebox.showinfo(
                    "Can't Read In/Out Points",
                    "Clipper couldn't read the timeline's In/Out points automatically.\n\n"
                    "This can happen if:\n"
                    "  • No In/Out points are set in Resolve yet (press I and O)\n"
                    "  • Your version of DaVinci Resolve doesn't expose them\n"
                    "    via the scripting API\n\n"
                    "Just type the timecodes directly into the In and Out fields\n"
                    "(format: HH:MM:SS:FF).",
                    parent=self.root)

    def _get_range_frames(self):
        """Return (in_frame, out_frame) from the TC fields, or (None, None)."""
        if self._range_var.get() != "inout":
            return None, None
        in_f  = tc_to_frames(self._range_in_var.get(),  self._fps)
        out_f = tc_to_frames(self._range_out_var.get(), self._fps)
        if in_f < 0 or out_f < 0 or out_f <= in_f:
            return None, None
        return in_f, out_f

    # ── Preview ───────────────────────────────────────────────────────────

    def _on_track_changed(self, *_):
        self._update_clip_count_label()
        self._schedule_preview()

    def _on_refresh_clicked(self):
        self._connect()   # re-fetch current timeline, project, fps from Resolve
        self._last_tl_name = self._tl_name()   # keep poll in sync
        self._refresh_tracks()
        self._refresh_bins()
        self._schedule_preview()
        self._update_header()

    def _schedule_preview(self, *_):
        if self._preview_job:
            self.root.after_cancel(self._preview_job)
        self._preview_job = self.root.after(120, self._refresh_preview)

    def _refresh_preview(self):
        self._preview_job = None
        self._refreshing  = True
        self._tree.delete(*self._tree.get_children())
        self._refreshing  = False
        self._preview_rows = []

        if not self._timeline:
            self._preview_status.config(text="Not connected", fg=DIM)
            return

        ttype, tidx = self._selected_track()
        if ttype is None:
            self._preview_status.config(text="Select a track", fg=DIM)
            return

        prefix = self._prefix_var.get()
        suffix = self._suffix_var.get()

        # ── Collect items from the selected track(s) ──────────────────────
        # Each entry is (TimelineItem, ttype, tidx) so per-row track info
        # is available for marker copying and log labels downstream.
        items_with_track = []   # [(item, ttype, tidx)]
        try:
            if ttype == "all":
                for (lbl, tt, ti, _) in self._track_list:
                    if tt not in ("video", "audio"):
                        continue
                    for item in (self._timeline.GetItemListInTrack(tt, ti) or []):
                        items_with_track.append((item, tt, ti))
                # Sort left-to-right by timeline position; video before audio on
                # ties; lower track index first on further ties.
                def _all_sort(x):
                    try:
                        s = x[0].GetStart()
                    except Exception:
                        s = 0
                    return (s, 0 if x[1] == "video" else 1, x[2])
                items_with_track.sort(key=_all_sort)
            else:
                for item in (self._timeline.GetItemListInTrack(ttype, tidx) or []):
                    items_with_track.append((item, ttype, tidx))
        except Exception as exc:
            self._preview_status.config(
                text=f"Error reading track: {exc}", fg=RED)
            return

        # Apply In/Out range filter if active
        range_in, range_out = self._get_range_frames()
        tl_start = 0
        try:
            tl_start = self._timeline.GetStartFrame() or 0
        except Exception:
            pass

        name_counts = {}  # track how many times each base name appears
        rows = []
        for (item, row_ttype, row_tidx) in items_with_track:
            try:
                clip_name = item.GetName() or "Untitled"
                mpi       = item.GetMediaPoolItem()
                src_in    = item.GetLeftOffset()
                tl_dur    = item.GetDuration()

                # Correct source duration for retimed clips
                try:
                    spd     = item.GetPlayBackSpeed() or 1.0
                    src_dur = int(round(tl_dur * abs(spd)))
                except Exception:
                    src_dur = tl_dur
                src_out   = src_in + src_dur - 1

                # Apply handles to source in/out
                if self._handles_custom.get():
                    head_h = max(0, self._head_handles_var.get())
                    tail_h = max(0, self._tail_handles_var.get())
                else:
                    head_h = tail_h = max(0, self._handles_var.get())
                src_in  = max(0, src_in - head_h)
                src_out = src_out + tail_h
                src_dur = src_out - src_in + 1

                # In/Out range filter: skip clips that don't overlap the range.
                # range_in/out come from tc_to_frames() — already absolute frames
                # (same coordinate system as item.GetStart/End). Do NOT add
                # tl_start here; that would double-count the TC offset.
                if range_in is not None:
                    clip_abs_start = item.GetStart()
                    clip_abs_end   = item.GetEnd()
                    if clip_abs_end <= range_in or clip_abs_start >= range_out:
                        continue

                subclip_base = f"{prefix}{clip_name}{suffix}"
                name_counts[subclip_base] = name_counts.get(subclip_base, 0) + 1

                try:
                    tl_start_frame = item.GetStart()
                except Exception:
                    tl_start_frame = 0

                rows.append({
                    "clip_name":      clip_name,
                    "subclip_base":   subclip_base,
                    "item":           item,   # kept for fresh mpi fetch at create time
                    "mpi":            mpi,
                    "src_in":         src_in,
                    "src_out":        src_out,
                    "src_dur":        src_dur,
                    "has_mpi":        mpi is not None,
                    "ttype":          row_ttype,  # per-row track info for downstream use
                    "tidx":           row_tidx,
                    "tl_start_frame": tl_start_frame,  # for Timecode sort prefix
                })
            except Exception:
                continue

        # Assign final names (disambiguate duplicates)
        name_seen = {}
        for row in rows:
            base = row["subclip_base"]
            if name_counts[base] > 1:
                name_seen[base] = name_seen.get(base, 0) + 1
                row["subclip_name"] = f"{base}_{name_seen[base]:02d}"
            else:
                row["subclip_name"] = base

        # Populate treeview
        for i, row in enumerate(rows):
            tag  = "odd" if i % 2 == 0 else "even"
            warn = not row["has_mpi"]
            if warn:
                tag = "warn"

            in_tc  = frames_to_tc(row["src_in"],  self._fps)
            out_tc = frames_to_tc(row["src_out"], self._fps)
            dur_tc = frames_to_tc(row["src_dur"], self._fps)

            src_lbl = row["clip_name"] if row["has_mpi"] else f"{row['clip_name']}  ⚠ no media"

            self._tree.insert("", "end",
                              values=(i + 1,
                                      row["subclip_name"],
                                      src_lbl,
                                      in_tc, out_tc, dur_tc),
                              tags=(tag,))

        self._preview_rows = rows
        n = len(rows)
        warn_ct = sum(1 for r in rows if not r["has_mpi"])

        range_in, range_out = self._get_range_frames()
        range_suffix = ""
        if range_in is not None:
            range_suffix = (f"  ·  In/Out range  "
                            f"{self._range_in_var.get()} → {self._range_out_var.get()}")
        if ttype == "all":
            track_label = "all tracks"
        else:
            tpfx = "V" if ttype == "video" else "A"
            track_label = f"{tpfx}{tidx}"
        status = f"{n} clip{'s' if n != 1 else ''} on {track_label}{range_suffix}"
        if warn_ct:
            status += f"  ·  ⚠ {warn_ct} without source media (will be skipped)"
        self._preview_status.config(
            text=status, fg=ACCENT if n else DIM)

        # Keep the track-dropdown clip count label in sync with the preview.
        # In In/Out mode show "X of Y clips in range"; otherwise show the full count.
        if range_in is not None:
            raw_count = 0
            sel = self._track_var.get()
            for (lbl, _tt, _ti, nc) in self._track_list:
                if lbl == sel:
                    raw_count = nc
                    break
            noun = "clip" if n == 1 else "clips"
            self._clip_count_lbl.config(
                text=f"{n} of {raw_count} {noun} in range",
                fg=ACCENT if n else DIM)
        else:
            self._update_clip_count_label()

    # ── Create subclips ───────────────────────────────────────────────────

    def _create_sequence_from_range(self):
        """Create one new timeline sequence from clips on the selected track.

        In 'Entire Timeline' mode: captures every clip on the track — no marks needed.
        In 'In/Out range' mode: captures only clips that overlap the marked range.

        Unlike Create All Clips (which makes one subclip per clip), this collects
        the clips and assembles them into a single new timeline sequence — producing
        one sequence in the destination bin.
        """
        if not self._timeline or not self._media_pool:
            messagebox.showwarning("Not Connected",
                "Not connected to DaVinci Resolve.\nUse ↻ Reconnect and try again.",
                parent=self.root)
            return

        dest_folder = self._get_dest_folder()
        if dest_folder is None:
            messagebox.showwarning("No Destination",
                "Select a destination bin before creating clips.",
                parent=self.root)
            return

        ttype, tidx = self._selected_track()
        if ttype is None:
            messagebox.showwarning("No Track", "Select a track first.", parent=self.root)
            return

        # Determine range mode
        range_mode      = self._range_var.get()
        use_full_track  = (range_mode == "all")
        use_selection   = (range_mode == "selection")
        in_f = out_f = -1
        in_tc = out_tc = ""

        if not use_full_track and not use_selection:
            # In/Out mode — grab marks, bail if none set
            self._grab_range_from_timeline(silent=True)
            in_tc  = self._range_in_var.get().strip()
            out_tc = self._range_out_var.get().strip()
            in_f   = tc_to_frames(in_tc,  self._fps)
            out_f  = tc_to_frames(out_tc, self._fps)

            if in_f < 0 or out_f < 0 or out_f <= in_f:
                messagebox.showwarning("No Range",
                    "No In/Out marks found on the timeline.\n\n"
                    "To capture a specific range: switch to In/Out Range mode, "
                    "press I and O in Resolve to set marks, then click Clip from Range.\n\n"
                    "To capture the full track: switch to Entire Timeline mode, "
                    "then click Clip from Range.",
                    parent=self.root)
                return

        clip_infos  = []
        clip_metas  = []   # parallel: {"item": TimelineItem, "head_h": int}
        skipped_mpi = 0

        if use_selection:
            # ── User Selection mode: build from the highlighted preview rows ──
            # No marks needed — use exactly what the user selected in the table.
            sel_ids = self._tree.selection()
            if not sel_ids:
                messagebox.showwarning("No Selection",
                    "Select clips in the preview table first, then click Clip from Range.",
                    parent=self.root)
                return
            sel_set = {self._tree.index(iid) for iid in sel_ids}
            chosen  = [r for i, r in enumerate(self._preview_rows) if i in sel_set]
            if not chosen:
                messagebox.showwarning("No Selection",
                    "No valid clips in the current selection.",
                    parent=self.root)
                return

            if self._handles_custom.get():
                head_h = max(0, self._head_handles_var.get())
            else:
                head_h = max(0, self._handles_var.get())

            for row in chosen:
                if not row["has_mpi"]:
                    skipped_mpi += 1
                    continue
                try:
                    mpi = row["item"].GetMediaPoolItem() or row.get("mpi")
                except Exception:
                    mpi = row.get("mpi")
                if not mpi:
                    skipped_mpi += 1
                    continue
                # src_in/src_out already have handles baked in from the preview
                ci = {"mediaPoolItem": mpi,
                      "startFrame":    row["src_in"],
                      "endFrame":      row["src_out"]}
                stream_idx = None
                try:
                    s = row["item"].GetCurrentVideoStreamIdx()
                    if s is not None:
                        stream_idx = int(s)
                except Exception:
                    pass
                if stream_idx is not None:
                    ci["videoStreamIdx"] = stream_idx
                clip_infos.append(ci)
                clip_metas.append({"item": row["item"], "head_h": head_h})

        else:
            # ── Entire Timeline or In/Out mode: collect from track(s) ──────
            try:
                if ttype == "all":
                    raw_items = []
                    for (lbl, tt, ti, _) in self._track_list:
                        if tt not in ("video", "audio"):
                            continue
                        for item in (self._timeline.GetItemListInTrack(tt, ti) or []):
                            raw_items.append(item)
                    raw_items.sort(key=lambda x: x.GetStart())
                    items = raw_items
                else:
                    items = self._timeline.GetItemListInTrack(ttype, tidx) or []
            except Exception as exc:
                messagebox.showerror("Track Error",
                    f"Could not read track: {exc}", parent=self.root)
                return

            for item in items:
                try:
                    if not use_full_track:
                        if item.GetEnd() <= in_f or item.GetStart() >= out_f:
                            continue      # outside the marked range
                    mpi = item.GetMediaPoolItem()
                    if not mpi:
                        skipped_mpi += 1
                        continue          # no source media — can't create subclip

                    src_in = item.GetLeftOffset()
                    tl_dur = item.GetDuration()

                    # Correct source duration for retimed clips.
                    spd = 1.0
                    try:
                        spd     = item.GetPlayBackSpeed() or 1.0
                        src_dur = int(round(tl_dur * abs(spd)))
                    except Exception:
                        src_dur = tl_dur
                    src_out = src_in + src_dur - 1

                    # Capture the active camera angle for multicam clips.
                    # NOTE: use None sentinel — angle 0 is valid, must not be
                    # dropped by a truthiness check.
                    stream_idx = None
                    try:
                        s = item.GetCurrentVideoStreamIdx()
                        if s is not None:
                            stream_idx = int(s)
                    except Exception:
                        pass

                    # Apply handles
                    if self._handles_custom.get():
                        head_h = max(0, self._head_handles_var.get())
                        tail_h = max(0, self._tail_handles_var.get())
                    else:
                        head_h = tail_h = max(0, self._handles_var.get())
                    src_in  = max(0, src_in - head_h)
                    src_out = src_out + tail_h

                    ci = {
                        "mediaPoolItem": mpi,
                        "startFrame":    src_in,
                        "endFrame":      src_out,
                        # trackIndex intentionally omitted — avoids source-track
                        # misinterpretation in some Resolve builds.
                    }
                    if stream_idx is not None:
                        ci["videoStreamIdx"] = stream_idx

                    clip_infos.append(ci)
                    clip_metas.append({"item": item, "head_h": head_h})
                    self._log(f"  clip: src_in={src_in} src_out={src_out} "
                              f"tl_dur={tl_dur} spd={spd} stream={stream_idx}")
                except Exception as exc:
                    self._log(f"  ⚠  skipped item: {exc}")
                    continue
        # ── end of track-based collection ─────────────────────────────────

        if not clip_infos:
            note = ""
            if skipped_mpi:
                note = f"\n\n({skipped_mpi} clip(s) skipped — no source media)"
            if use_selection:
                messagebox.showinfo("No Clips",
                    f"None of the selected clips have source media.{note}",
                    parent=self.root)
            elif use_full_track:
                messagebox.showinfo("No Clips",
                    f"No clips with source media found on the selected track.{note}",
                    parent=self.root)
            else:
                messagebox.showinfo("No Clips",
                    f"No clips with source media found in the marked range.{note}\n\n"
                    "Check the In/Out marks and selected track.",
                    parent=self.root)
            return

        # Build a descriptive name for the new sequence
        tl_name = self._timeline.GetName() if self._timeline else "Clip"
        if use_full_track:
            tpfx     = "V" if ttype == "video" else "A"
            seq_name = f"{tl_name} — {tpfx}{tidx} (full track)"
        else:
            in_safe  = in_tc.replace(":", "-")
            out_safe = out_tc.replace(":", "-")
            seq_name = f"{tl_name} ({in_safe}–{out_safe})"

        bin_name = self._bin_var.get()
        self._log(f"Clip from Range: '{seq_name}'  clips={len(clip_infos)}")

        # Save the current timeline so we can restore it after CreateTimelineFromClips
        _orig_tl = None
        try:
            _orig_tl = self._project.GetCurrentTimeline()
        except Exception:
            pass

        # Set destination bin as current so the new timeline lands there
        try:
            self._media_pool.SetCurrentFolder(dest_folder)
        except Exception:
            pass

        self._start_batch()

        # Log every clip that will be placed so we can diagnose positioning issues
        for i, ci in enumerate(clip_infos):
            self._log(f"  clip[{i}]: startFrame={ci['startFrame']} "
                      f"endFrame={ci['endFrame']} "
                      f"dur={ci['endFrame'] - ci['startFrame'] + 1} "
                      f"track={ci.get('trackIndex','?')} "
                      f"stream={ci.get('videoStreamIdx','n/a')}")

        # Strategy: create the timeline from the FIRST clip only (no recordFrame
        # needed — Resolve places a single clip at position 0 by default), then
        # AppendToTimeline each remaining clip.  This avoids the recordFrame
        # scatter bug where Resolve uses startFrame as the record position when
        # multiple clips are passed to CreateTimelineFromClips at once.
        first_ci = {k: v for k, v in clip_infos[0].items()
                    if k != "recordFrame"}

        new_tl = None
        for tag, end_adj in [("incl", 0), ("excl+1", 1)]:
            adj = {**first_ci, "endFrame": first_ci["endFrame"] + end_adj}
            try:
                new_tl = self._media_pool.CreateTimelineFromClips(seq_name, [adj])
                self._log(f"  CreateTimelineFromClips({tag}) clip[0] → {new_tl!r}")
                if new_tl:
                    break
            except Exception as exc:
                self._log(f"  CreateTimelineFromClips({tag}) exception: {exc}")

        if not new_tl:
            if _orig_tl:
                try:
                    self._project.SetCurrentTimeline(_orig_tl)
                except Exception:
                    pass
            self._end_batch()
            self._log(f"✗  Failed — could not create '{seq_name}'")
            messagebox.showerror("Failed",
                "Could not create the range clip.\n\n"
                "Make sure the timeline has In/Out marks set, a track is selected, "
                "and clips in the range have source media.",
                parent=self.root)
            self._schedule_preview()
            return

        # Copy markers from the first original clip onto the first clip in the new timeline
        copy_markers = self._markers_var.get()
        if copy_markers:
            try:
                new_items_0 = new_tl.GetItemListInTrack(ttype, 1) or []
                if new_items_0:
                    n = self._copy_markers(clip_metas[0]["item"],
                                           new_items_0[0],
                                           clip_metas[0]["head_h"])
                    self._log(f"  clip[0] markers copied: {n}")
            except Exception as exc:
                self._log(f"  ⚠ marker copy clip[0]: {exc}")

        # Switch to the new timeline so AppendToTimeline targets it
        try:
            self._project.SetCurrentTimeline(new_tl)
        except Exception as exc:
            self._log(f"  ⚠ SetCurrentTimeline: {exc}")

        # Append remaining clips one at a time — AppendToTimeline always
        # places each clip immediately after the last clip in the current timeline,
        # guaranteeing correct sequential order without any recordFrame arithmetic.
        appended = 1
        has_append = callable(getattr(self._media_pool, "AppendToTimeline", None))
        self._log(f"  AppendToTimeline available: {has_append}")

        if has_append and len(clip_infos) > 1:
            for i, ci in enumerate(clip_infos[1:], 1):
                ci_clean = {k: v for k, v in ci.items() if k != "recordFrame"}
                ok = False
                # AppendToTimeline uses exclusive endFrame (unlike CreateTimelineFromClips
                # which uses inclusive). Always add 1 to avoid accumulating 1-frame shortfall.
                for tag, end_adj in [("excl+1", 1), ("incl", 0)]:
                    adj = {**ci_clean, "endFrame": ci_clean["endFrame"] + end_adj}
                    try:
                        r = self._media_pool.AppendToTimeline([adj])
                        self._log(f"  AppendToTimeline[{i}]({tag}) → {r!r}")
                        if r:
                            appended += 1
                            ok = True
                            # Copy markers from the original clip to the new timeline item
                            if copy_markers:
                                try:
                                    n = self._copy_markers(clip_metas[i]["item"],
                                                           r[0],
                                                           clip_metas[i]["head_h"])
                                    self._log(f"  clip[{i}] markers copied: {n}")
                                except Exception as exc:
                                    self._log(f"  ⚠ marker copy clip[{i}]: {exc}")
                            break
                    except Exception as exc:
                        self._log(f"  AppendToTimeline[{i}]({tag}) exception: {exc}")
                if not ok:
                    self._log(f"  ⚠ clip[{i}] could not be appended")

                # Allow UI events (Abort button) to register after each append
                self.root.update()
                if self._abort_flag:
                    self._log(f"⛔  Clip from Range aborted — placed {appended} of {len(clip_infos)} clips.")
                    break
        elif not has_append and len(clip_infos) > 1:
            self._log("  ⚠ AppendToTimeline not available — only first clip placed.")

        self._log(f"  placed {appended} of {len(clip_infos)} clips in '{seq_name}'")

        # Strip audio tracks if Video only is enabled
        if self._video_only_var.get():
            n_audio = self._strip_audio_tracks(new_tl)
            self._log(f"  Video only — removed {n_audio} audio track(s)")

        # Restore original timeline
        if _orig_tl:
            try:
                self._project.SetCurrentTimeline(_orig_tl)
            except Exception:
                pass

        self._end_batch()

        self._log(f"✓  '{seq_name}' → '{bin_name}'")
        messagebox.showinfo("Done",
            f"Created:\n{seq_name}\n\nBin: {bin_name}\n\n"
            f"Clips placed: {appended} of {len(clip_infos)}"
            + (f"\nSkipped (no media): {skipped_mpi}" if skipped_mpi else ""),
            parent=self.root)

        self._schedule_preview()

    def _strip_audio_tracks(self, tl):
        """Delete all audio tracks from a timeline.

        Deletes from the highest index downward to avoid index-shifting issues.
        Returns the number of tracks removed, or 0 if the API is unavailable.

        Note: for single-clip compound timelines Resolve may report 0 audio
        tracks even when the source has audio — the audio is embedded at the
        source MPI level and is not exposed as a deletable track.  In that
        case this function returns 0 and logs a warning.  Use Clip from Range
        (which builds a full sequence) for reliable audio stripping.
        """
        try:
            if not callable(getattr(tl, "DeleteTrack", None)):
                self._log("  ⚠ DeleteTrack not available — audio tracks not removed")
                return 0
            count = int(tl.GetTrackCount("audio") or 0)
            if count == 0:
                self._log("  ⚠ Video only: 0 audio tracks found in this timeline — "
                          "source audio may be embedded at MPI level (not deletable). "
                          "Use Clip from Range for reliable audio stripping.")
                return 0
            for ai in range(count, 0, -1):
                ok = tl.DeleteTrack("audio", ai)
                self._log(f"    DeleteTrack(audio, {ai}) → {ok}")

            # Resolve refuses to delete the very last audio track — a timeline
            # must always have at least one.  If A1 still exists, disable it so
            # it produces no output.
            remaining = int(tl.GetTrackCount("audio") or 0)
            if remaining > 0:
                try:
                    tl.SetTrackEnable("audio", 1, False)
                    self._log("    A1 disabled (Resolve cannot delete the last audio track)")
                except Exception as exc:
                    self._log(f"    ⚠ Could not disable A1: {exc} — "
                              "track remains but should carry no clips")

            return count - remaining
        except Exception as exc:
            self._log(f"  ⚠ _strip_audio_tracks: {exc}")
            return 0

    def _copy_markers(self, src_item, dst_item, head_h=0):
        """Copy all markers from src_item (original timeline item) to dst_item
        (new timeline item), shifting each offset forward by head_h frames to
        account for any handle added at the head of the clip.

        Returns the number of markers copied.
        """
        try:
            markers = src_item.GetMarkers() or {}
            count = 0
            for offset, m in markers.items():
                new_offset = int(offset) + head_h
                try:
                    dst_item.AddMarker(
                        new_offset,
                        m.get("color",      "Blue"),
                        m.get("name",       ""),
                        m.get("note",       ""),
                        m.get("duration",   1),
                        m.get("customData", ""),
                    )
                    count += 1
                except Exception as exc:
                    self._log(f"    ⚠ AddMarker(offset={new_offset}): {exc}")
            return count
        except Exception as exc:
            self._log(f"  ⚠ _copy_markers: {exc}")
            return 0

    def _create_subclips(self):
        """Create subclips for all clips in the preview (respects Range filter)."""
        if not self._preview_rows:
            messagebox.showinfo("Nothing to Do",
                "No clips in the preview.\n"
                "Choose a track (and check the Range setting) then click Refresh Preview.",
                parent=self.root)
            return
        self._run_subclip_batch(self._preview_rows, label="All")

    def _create_selected_subclips(self):
        """Create subclips for the rows currently selected in the preview table."""
        sel_ids = self._tree.selection()
        if not sel_ids:
            messagebox.showinfo("No Selection",
                "Click rows in the preview to select them first.\n\n"
                "Shift-click for a range · Cmd-click (or Ctrl-click) to multi-select.",
                parent=self.root)
            return

        # Map tree item IDs → row indices (Treeview items are 0-based insertion order)
        all_ids = self._tree.get_children()
        idx_map = {iid: i for i, iid in enumerate(all_ids)}

        selected_rows = []
        for iid in sel_ids:
            idx = idx_map.get(iid)
            if idx is not None and idx < len(self._preview_rows):
                selected_rows.append(self._preview_rows[idx])

        if not selected_rows:
            messagebox.showinfo("No Selection",
                "Could not match selection to clip rows. Try Refresh Preview.",
                parent=self.root)
            return

        # Reuse the main create logic but with only selected rows
        self._run_subclip_batch(selected_rows, label="Selected")

    def _run_subclip_batch(self, rows, label="All"):
        """Core subclip creation loop — called by both Create All and Create Selected.

        Strategy (in priority order):
          1. MediaPool.CreateSubClip      — native subclip (preferred)
          2. MediaPool.CreateTimelineFromClips — compound-clip workaround for
             beta builds where CreateSubClip is wired to None
          3. Give up gracefully with a diagnostic dump.
        """
        if not self._timeline or not self._media_pool:
            messagebox.showwarning("Not Connected",
                "Not connected to DaVinci Resolve.\n"
                "Use ↻ Reconnect and try again.", parent=self.root)
            return

        dest_folder = self._get_dest_folder()
        if dest_folder is None:
            messagebox.showwarning("No Destination",
                "Select a destination bin before creating subclips.",
                parent=self.root)
            return

        ttype, tidx = self._selected_track()
        if ttype == "all":
            tpfx      = "All tracks"
            track_lbl = "All tracks"
        else:
            tpfx      = "V" if ttype == "video" else "A"
            track_lbl = f"{tpfx}{tidx}"
        bin_name = self._bin_var.get()

        self._start_batch()

        added = 0; skipped = 0; failed = 0
        errors = []

        # ── API probe ─────────────────────────────────────────────────────
        has_create = callable(getattr(self._media_pool, 'CreateSubClip',           None))
        has_tl     = callable(getattr(self._media_pool, 'CreateTimelineFromClips', None))
        has_move   = callable(getattr(self._media_pool, 'MoveClips',               None))

        try:
            ver = self._resolve.GetVersionString()
        except Exception:
            ver = "unknown"

        self._log(f"Resolve {ver}  |  "
                  f"CreateSubClip: {'✓' if has_create else '✗'}  "
                  f"CreateTimelineFromClips: {'✓' if has_tl else '✗'}  "
                  f"MoveClips: {'✓' if has_move else '✗'}")
        self._log(f"Batch: track={tpfx}{tidx}  clips={len(rows)}  "
                  f"valid (pre-filter)={len(rows)}")

        use_subclip = has_create
        use_tl      = not has_create and has_tl

        if not use_subclip and not use_tl:
            # Nothing we can do — dump available methods for diagnosis
            try:
                pool_methods = sorted(
                    m for m in dir(self._media_pool)
                    if not m.startswith('_')
                    and callable(getattr(self._media_pool, m, None))
                )
                self._log(f"  Callable pool methods: {pool_methods}")
            except Exception:
                pass
            self._end_batch()
            messagebox.showerror(
                "No Suitable API Found",
                f"Neither CreateSubClip nor CreateTimelineFromClips is callable\n"
                f"in Resolve {ver}.\n\n"
                "Please report this with the log output so we can find a workaround.",
                parent=self.root)
            return

        if use_tl:
            self._log("  ⚠  CreateSubClip is None in this beta — using "
                      "CreateTimelineFromClips as workaround (creates compound clips).")

        # ── Gather mpi references ─────────────────────────────────────────
        valid = []
        for row in rows:
            if not row["has_mpi"]:
                skipped += 1
                self._log(f"  ⚠  Skipped (no source media): {row['clip_name']}")
                continue
            mpi = None
            try:
                mpi = row["item"].GetMediaPoolItem()
            except Exception:
                mpi = row.get("mpi")
            if not mpi:
                skipped += 1
                self._log(f"  ⚠  Skipped (lost mpi): {row['clip_name']}")
                continue
            valid.append((row, mpi))

        if not valid:
            self._end_batch()
            messagebox.showinfo("Nothing to Create",
                "No clips with valid source media in this selection.",
                parent=self.root)
            return

        # ── Navigate to destination (needed for both paths) ───────────────
        try:
            self._media_pool.SetCurrentFolder(dest_folder)
            cf_name = ""
            try:
                cf = self._media_pool.GetCurrentFolder()
                cf_name = cf.GetName() if cf else "?"
            except Exception:
                pass
            self._log(f"Folder → '{cf_name}'")
        except Exception as exc:
            self._end_batch()
            messagebox.showerror("Folder Error",
                f"Could not navigate to destination bin.\n\n{exc}", parent=self.root)
            return

        # ── Feature flags for this batch ──────────────────────────────────
        do_markers    = self._markers_var.get()
        do_order      = self._order_var.get()
        order_mode    = self._order_mode_var.get()   # "seq" | "tc"
        do_video_only = self._video_only_var.get()
        n_valid    = len(valid)
        n_width    = len(str(n_valid))   # digits to zero-pad (e.g. 7 clips → 1, 15 → 2)
        # head_h for marker offset adjustment (mirrors _refresh_preview logic)
        if self._handles_custom.get():
            head_h = max(0, self._head_handles_var.get())
        else:
            head_h = max(0, self._handles_var.get())

        def _order_prefix(row, seq_num):
            """Return the Preserve-Timeline-Order prefix for this clip, or ''."""
            if not do_order:
                return ""
            row_tt  = row.get("ttype", ttype)
            row_ti  = row.get("tidx",  tidx)
            # Timecode mode: always include track prefix (V1_, A2_, etc.) so that
            # separate single-track runs can be combined in one bin and sort correctly.
            # Sequential mode: only include track prefix when All Tracks is active.
            include_track = (order_mode == "tc" or ttype == "all")
            v_pfx   = (f"{'V' if row_tt == 'video' else 'A'}{row_ti}_"
                       if include_track else "")
            if order_mode == "tc":
                tc_raw = frames_to_tc(row.get("tl_start_frame", 0), self._fps)
                tc_str = tc_raw.replace(":", "-")
                return f"{v_pfx}{tc_str}_"
            else:
                return f"{v_pfx}T{seq_num:0{n_width}d}_"

        # ── PATH A: CreateSubClip (preferred, with per-clip PATH B fallback) ──
        # CreateSubClip works for most clips but silently fails for some clip
        # types (multicam, compound clips, grouped clips).  When it does fail,
        # we fall back to CreateTimelineFromClips for that specific clip so the
        # batch never hard-fails on clip type.
        #
        # Video Only note (logged, not a blocking dialog): CreateSubClip returns
        # a source reference — audio is linked at timeline placement, not in the
        # bin.  Clips that fall back to PATH B CAN have audio stripped.
        if use_subclip:
            if do_video_only:
                self._log("  Note: Video only — n/a for native subclips. "
                          "Clips that need PATH B fallback will have audio stripped.")

            # Save current timeline so PATH B fallbacks can restore it.
            _orig_tl = None
            try:
                _orig_tl = self._project.GetCurrentTimeline()
            except Exception:
                pass

            created_items = []
            for seq_num, (row, mpi) in enumerate(valid, 1):
                # Build final clip name — timeline-order prefix goes first so
                # bins sort in cut order regardless of source clip name.
                final_name = row["subclip_name"]
                final_name = _order_prefix(row, seq_num) + final_name

                result       = None
                used_fallback = False

                # ── Try PATH A (CreateSubClip) ────────────────────────────
                for tag, clip_info in [
                    ("incl",  {"mediaPoolItem": mpi, "startFrame": row["src_in"],
                               "endFrame": row["src_out"],     "clipName": final_name}),
                    ("excl+1",{"mediaPoolItem": mpi, "startFrame": row["src_in"],
                               "endFrame": row["src_out"] + 1, "clipName": final_name}),
                    ("no-nm", {"mediaPoolItem": mpi, "startFrame": row["src_in"],
                               "endFrame": row["src_out"]}),
                ]:
                    try:
                        result = self._media_pool.CreateSubClip(clip_info)
                        self._log(f"    {tag} endF={clip_info['endFrame']}  → {result!r}")
                        if result:
                            break
                    except Exception as exc:
                        self._log(f"    {tag} exception: {exc}")

                # ── PATH B fallback if PATH A failed ─────────────────────
                # Multicam clips, grouped clips, and some compound clips
                # return None from CreateSubClip even when the API is present.
                if not result and has_tl:
                    self._log(f"  PATH A failed — trying PATH B fallback for '{final_name}'")
                    fb_info = [{"mediaPoolItem": mpi,
                                "startFrame":   row["src_in"],
                                "endFrame":     row["src_out"]}]
                    for tag, end_adj in [("incl", 0), ("excl+1", 1)]:
                        fb_info[0]["endFrame"] = row["src_out"] + end_adj
                        try:
                            result = self._media_pool.CreateTimelineFromClips(
                                final_name, fb_info)
                            self._log(f"    PATH B {tag} → {result!r}")
                            if result:
                                used_fallback = True
                                break
                        except Exception as exc:
                            self._log(f"    PATH B {tag} exception: {exc}")
                    # Always restore the original timeline after a PATH B attempt
                    if _orig_tl:
                        try:
                            self._project.SetCurrentTimeline(_orig_tl)
                        except Exception:
                            pass

                if result:
                    added += 1
                    if used_fallback:
                        self._log(f"  ✓  {final_name}  (compound clip via fallback)")
                        if do_video_only:
                            n_audio = self._strip_audio_tracks(result)
                            self._log(f"    Video only — removed {n_audio} audio track(s)")
                        if do_markers:
                            try:
                                row_tt = row.get("ttype", ttype) or "video"
                                tl_items = result.GetItemListInTrack(row_tt, 1) or []
                                if tl_items:
                                    n = self._copy_markers(row["item"], tl_items[0], head_h)
                                    if n:
                                        self._log(f"    markers copied: {n}")
                            except Exception as exc:
                                self._log(f"    ⚠ marker copy: {exc}")
                    else:
                        created_items.append(result)
                        self._log(f"  ✓  {final_name}")
                        if do_video_only:
                            self._log("    Video only: n/a for native subclip — "
                                      "use Clip from Range for video-only sequences")
                        if do_markers:
                            try:
                                n = self._copy_markers(row["item"], result, head_h)
                                if n:
                                    self._log(f"    markers copied: {n}")
                            except Exception as exc:
                                self._log(f"    ⚠ marker copy: {exc}")
                else:
                    failed += 1
                    errors.append(final_name)
                    self._log(f"  ✗  Failed: {final_name}")

                # Allow UI events to process (enables the Abort button to register)
                self.root.update()
                if self._abort_flag:
                    self._log(f"⛔  Batch aborted after {seq_num} of {n_valid} clips.")
                    break

            # Move native subclips to dest if needed (they land in current folder)
            if created_items and has_move:
                try:
                    cur = self._media_pool.GetCurrentFolder()
                    if cur and cur.GetName() != dest_folder.GetName():
                        ok = self._media_pool.MoveClips(created_items, dest_folder)
                        self._log(f"Moved {len(created_items)} item(s) → '{bin_name}'  ok={ok}")
                except Exception as exc:
                    self._log(f"⚠  Move error: {exc}")

        # ── PATH B: CreateTimelineFromClips (Resolve 21 beta workaround) ──
        else:
            # Remember the current timeline so we can restore it after —
            # CreateTimelineFromClips switches Resolve to each new timeline.
            # We restore after EVERY clip creation (not just at the end) to
            # keep the Edit page showing the original timeline as much as
            # possible. Note: the new timeline tabs remain open in Resolve if
            # the user has stacked timelines enabled — there is no API to
            # close timeline tabs, so the tabs will persist until the user
            # closes them manually.
            _orig_tl = None
            try:
                _orig_tl = self._project.GetCurrentTimeline()
            except Exception:
                pass

            for seq_num, (row, mpi) in enumerate(valid, 1):
                final_name = row["subclip_name"]
                final_name = _order_prefix(row, seq_num) + final_name

                clip_info = [{"mediaPoolItem": mpi,
                              "startFrame":   row["src_in"],
                              "endFrame":     row["src_out"]}]
                result = None
                # Try inclusive then exclusive endFrame
                for tag, end_f in [("incl", row["src_out"]),
                                   ("excl+1", row["src_out"] + 1)]:
                    clip_info[0]["endFrame"] = end_f
                    try:
                        result = self._media_pool.CreateTimelineFromClips(
                            final_name, clip_info)
                        self._log(f"    TL {tag} endF={end_f}  → {result!r}")
                        if result:
                            break
                    except Exception as exc:
                        self._log(f"    TL {tag} exception: {exc}")

                if result:
                    added += 1
                    self._log(f"  ✓  {final_name}  (compound clip)")
                    if do_markers:
                        try:
                            row_tt = row.get("ttype", ttype) or "video"
                            tl_items = result.GetItemListInTrack(row_tt, 1) or []
                            if tl_items:
                                n = self._copy_markers(row["item"], tl_items[0], head_h)
                                if n:
                                    self._log(f"    markers copied: {n}")
                        except Exception as exc:
                            self._log(f"    ⚠ marker copy: {exc}")
                    if do_video_only:
                        try:
                            n_audio_before = int(result.GetTrackCount("audio") or 0)
                        except Exception:
                            n_audio_before = -1
                        n_audio = self._strip_audio_tracks(result)
                        self._log(f"    Video only — audio tracks before={n_audio_before} "
                                  f"removed={n_audio}")
                else:
                    failed += 1
                    errors.append(final_name)
                    self._log(f"  ✗  Failed: {final_name}")

                # Restore immediately after each clip so the user stays in
                # the original timeline throughout the batch.
                if _orig_tl:
                    try:
                        self._project.SetCurrentTimeline(_orig_tl)
                    except Exception:
                        pass

                # Allow UI events to process (enables the Abort button to register)
                self.root.update()
                if self._abort_flag:
                    self._log(f"⛔  Batch aborted after {seq_num} of {n_valid} clips.")
                    break

            self._log(f"Timeline restored → '{_orig_tl.GetName() if _orig_tl else '?'}'")

        self._end_batch()

        aborted = self._abort_flag
        status_word = "Aborted" if aborted else "Done"
        summary = (
            f"{status_word} — {label} — Track {track_lbl}  →  {bin_name}\n\n"
            f"Clips created: {added}\n"
            f"Skipped (no media): {skipped}\n"
            f"Failed:             {failed}"
        )
        if aborted:
            remaining = n_valid - added - failed - skipped
            if remaining > 0:
                summary += f"\nNot processed:      {remaining}"
        if errors:
            summary += "\n\nFailed clips:\n" + "\n".join(f"  • {e}" for e in errors[:10])
            if len(errors) > 10:
                summary += f"\n  … and {len(errors) - 10} more"

        title = "Aborted" if aborted else "Complete"
        messagebox.showinfo(title, summary, parent=self.root)
        self._log(f"{status_word} ({label}) — {added} added, {skipped} skipped, {failed} failed.")
        self._schedule_preview()

    # ── Handles helpers ───────────────────────────────────────────────────

    def _make_counter(self, parent, var, min_val=0, max_val=9999):
        """Return a [−] [entry] [+] counter frame bound to var."""
        f = tk.Frame(parent, bg=BG)
        def _step(delta):
            try:
                v = max(min_val, min(max_val, int(var.get()) + delta))
            except (ValueError, tk.TclError):
                v = min_val
            var.set(v)
        TBtn(f, text="−", command=lambda: _step(-1),
             bg=BTN, fg=BG, padx=8, pady=3, font=F_MONO).pack(side="left")
        tk.Entry(f, textvariable=var, bg=ENTRY_BG, fg=TEXT,
                 insertbackground=TEXT, relief="flat",
                 font=F_MONO, width=4, justify="center").pack(side="left", padx=2)
        TBtn(f, text="+", command=lambda: _step(1),
             bg=BTN, fg=BG, padx=8, pady=3, font=F_MONO).pack(side="left")
        return f

    def _normalize_tc_field(self, var):
        """Auto-format a TC field: if the user typed 8 raw digits (e.g. 03004219)
        reformat them as HH:MM:SS:FF on tab-out or Return."""
        raw    = var.get().strip()
        digits = raw.replace(":", "").replace(";", "").replace(".", "")
        if not digits.isdigit() or len(digits) != 8:
            return
        hh, mm, ss, ff = int(digits[:2]), int(digits[2:4]), int(digits[4:6]), int(digits[6:8])
        ifps = int(round(self._fps)) or 24
        if mm < 60 and ss < 60 and ff < ifps:
            var.set(f"{hh:02d}:{mm:02d}:{ss:02d}:{ff:02d}")

    def _on_handles_mode(self):
        """Show or hide the custom head/tail row."""
        if self._handles_custom.get():
            self._hdl_custom_frame.grid()
        else:
            self._hdl_custom_frame.grid_remove()
        self._schedule_preview()

    # ── Stay on top ───────────────────────────────────────────────────────

    def _on_stay_on_top(self, *_):
        v = self._stay_on_top.get()
        self.root.attributes("-topmost", v)

    # ── Abort ─────────────────────────────────────────────────────────────

    def _start_batch(self):
        """Called at the start of any batch operation. Shows the Abort button."""
        self._abort_flag = False
        self._abort_btn.pack(side="right", padx=(0, 8))
        # Re-pack to ensure it appears in the right slot (between Close and Range)
        self._run_btn.config(state="disabled")
        self._range_seq_btn.config(state="disabled")
        self.root.update_idletasks()

    def _end_batch(self):
        """Called at the end of any batch operation. Hides the Abort button."""
        self._abort_flag = False
        self._abort_btn.pack_forget()
        self._run_btn.config(state="normal")
        self._range_seq_btn.config(state="normal")

    def _request_abort(self):
        """Signal the running batch to stop after the current clip."""
        self._abort_flag = True
        self._abort_btn.config(state="disabled")
        self._log("⛔  Abort requested — will stop after the current clip finishes...")

    # ── Log ───────────────────────────────────────────────────────────────

    def _log(self, msg):
        self._log_text.config(state="normal")
        self._log_text.insert("end", msg + "\n")
        self._log_text.see("end")
        self._log_text.config(state="disabled")

    # ── Lift ──────────────────────────────────────────────────────────────

    def _initial_lift(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
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
                        _app_name = _msg(_objc.objc_getClass(b'NSString'), _objc.sel_registerName(b'stringWithUTF8String:'), b'Clipper')
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
        Clipper(root)
        root.mainloop()
    except Exception as e:
        import traceback
        print("[Clipper] Fatal error:")
        traceback.print_exc()
