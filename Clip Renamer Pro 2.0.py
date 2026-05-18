#!/usr/bin/env python3
"""
Clip Renamer Pro 2.0 — DaVinci Resolve Clip & Timeline Renamer

Renames clips and/or timelines selected in the Resolve Media Pool bin.
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
from tkinter import ttk

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
# Theme  (matches Marker Madness exactly)
# ---------------------------------------------------------------------------

BG       = "#2d2d2d"
PANEL    = "#333333"
TEXT     = "#E2E2E2"
ACCENT   = "#ffa500"
BTN      = "#505050"
BTN_HOV  = "#626262"
ENTRY_BG = "#1e1e1e"
TITLE_BG = "#1a1a1a"
DIM      = "#909090"
GREEN    = "#388E3C"
BLUE     = "#1976D2"
PURPLE   = "#7B1FA2"
RED      = "#E53935"

F_MAIN   = ("Avenir Next", 12)
F_BOLD   = ("Avenir Next", 13, "bold")
F_SMALL  = ("Avenir Next", 10)
F_MONO   = ("Courier", 12)
F_TITLE  = ("Avenir Next", 18, "bold")
F_STATUS = ("Avenir Next", 10, "italic")
F_HDR    = ("Avenir Next", 10, "bold")

# ---------------------------------------------------------------------------
# TBtn  (matches Marker Madness)
# ---------------------------------------------------------------------------

def _hover_color(hex_color, factor=0.18):
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    r = min(255, int(r + (255 - r) * factor))
    g = min(255, int(g + (255 - g) * factor))
    b = min(255, int(b + (255 - b) * factor))
    return f"#{r:02x}{g:02x}{b:02x}"

BTN_TEXT = "#111111"

class TBtn(tk.Button):
    def __init__(self, parent, bg=BTN, fg=BTN_TEXT, padx=12, pady=6, font=F_MAIN, **kw):
        _hov = _hover_color(bg)
        super().__init__(parent, bg=bg, fg=fg, relief="flat",
                         activebackground=_hov, activeforeground=fg,
                         padx=padx, pady=pady, cursor="hand2", font=font, **kw)
        self.bind("<Enter>", lambda _: self.config(bg=_hov))
        self.bind("<Leave>", lambda _: self.config(bg=bg))

# ---------------------------------------------------------------------------
# Transformation engine  (stepped counter from Marker Madness)
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
# Main app
# ---------------------------------------------------------------------------

class ClipRenamerPro:
    def __init__(self, root):
        self.root = root
        self.root.withdraw()
        self.root.title("Clip Renamer Pro")
        self.root.configure(bg=BG)
        self.root.resizable(False, True)
        self.root.minsize(720, 567)
        _w, _h = 720, 697
        _sw = self.root.winfo_screenwidth()
        _sh = self.root.winfo_screenheight()
        self.root.geometry(f"{_w}x{_h}+{(_sw - _w) // 2}+{(_sh - _h) // 2}")

        self._resolve     = get_resolve()
        self._project     = None
        self._media_pool  = None
        self._last_changes = []   # list of (obj, old_name)
        self._preview_job  = None

        if self._resolve:
            pm = self._resolve.GetProjectManager()
            self._project    = pm.GetCurrentProject() if pm else None
            self._media_pool = self._project.GetMediaPool() if self._project else None

        self._stay_on_top_var   = tk.BooleanVar(value=True)
        self._topmost_check_job = None
        self._hdr_proj_var      = tk.StringVar(value="—")

        self._style_comboboxes()
        self._build()
        self.root.bind("<Command-z>", lambda e: self._undo())
        self.root.bind("<Control-z>", lambda e: self._undo())
        if self._project:
            try:
                self._hdr_proj_var.set(self._project.GetName())
            except Exception:
                pass
        self._update_preview()
        self._on_stay_on_top_changed()
        self.root.after(150, self._initial_lift)

    # ── Combobox dark style ────────────────────────────────────────────────

    def _style_comboboxes(self):
        try:
            s = ttk.Style()
            s.theme_use("default")
            s.configure("Dark.TCombobox",
                        fieldbackground=ENTRY_BG,
                        background=BTN,
                        foreground=TEXT,
                        arrowcolor=TEXT,
                        selectbackground=BTN_HOV,
                        selectforeground=TEXT)
            s.map("Dark.TCombobox",
                  fieldbackground=[("readonly", ENTRY_BG)],
                  foreground=[("readonly", TEXT)],
                  background=[("readonly", BTN)])
        except Exception:
            pass

    # ── Build UI ───────────────────────────────────────────────────────────

    def _build(self):
        _tb = tk.Frame(self.root, bg=TITLE_BG, pady=8)
        _tb.pack(fill="x")
        tk.Label(_tb, text="  Clip Renamer Pro", fg=ACCENT, bg=TITLE_BG,
                 font=("Avenir Next", 18)).pack(side="left")
        tk.Label(_tb, text="v2.0", fg=DIM, bg=TITLE_BG,
                 font=("Avenir Next", 10)).pack(side="left", pady=(6, 0))
        _info = tk.Frame(_tb, bg=TITLE_BG)
        _info.pack(side="right", padx=12)
        tk.Label(_info, text="Project", fg=DIM, bg=TITLE_BG, font=F_STATUS).pack(side="left")
        tk.Label(_info, textvariable=self._hdr_proj_var,
                 fg=TEXT, bg=TITLE_BG, font=F_MAIN).pack(side="left", padx=(5, 0))

        # Top button bar
        top = tk.Frame(self.root, bg=BG)
        top.pack(fill="x", padx=8, pady=6)

        TBtn(top, text="Clear",            command=self._clear,
             bg=BTN,    padx=10, pady=4).pack(side="left", padx=(0, 4))
        TBtn(top, text="Refresh",          command=self._refresh,
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

        # Main panel
        main = tk.Frame(self.root, bg=PANEL)
        main.pack(fill="both", expand=True, padx=8, pady=(0, 4))

        # ── Rename Operations header ──────────────────────────────────────
        tk.Label(main, text="RENAME OPERATIONS", fg=ACCENT, bg=PANEL,
                 font=F_HDR).pack(fill="x", padx=12, pady=(10, 2))

        ops = tk.Frame(main, bg=PANEL)
        ops.pack(fill="x", padx=12, pady=4)

        def entry_var(trace=True):
            v = tk.StringVar()
            if trace:
                v.trace_add("write", lambda *_: self._schedule_preview())
            return v

        def spin_var(val, trace=True):
            v = tk.IntVar(value=val)
            if trace:
                v.trace_add("write", lambda *_: self._schedule_preview())
            return v

        def check(parent, text, var, cmd=None):
            return tk.Checkbutton(parent, text=text, variable=var,
                                  fg=TEXT, bg=PANEL, selectcolor=ENTRY_BG,
                                  activebackground=PANEL, activeforeground=TEXT,
                                  font=F_MAIN, command=cmd or self._schedule_preview)

        def entry(parent, var, width=None):
            kw = {"width": width} if width else {}
            e = tk.Entry(parent, textvariable=var, bg=ENTRY_BG, fg=TEXT,
                         insertbackground=TEXT, relief="flat", font=F_MAIN,
                         highlightthickness=1, highlightbackground="#444444",
                         highlightcolor="#666666", **kw)
            e.bind("<Up>",       lambda ev: e.icursor(0)              or "break")
            e.bind("<Down>",     lambda ev: e.icursor("end")          or "break")
            e.bind("<KP_Enter>", lambda ev: self._schedule_preview()  or "break")
            return e

        def spin(parent, var, lo, hi, width=4):
            sb = tk.Spinbox(parent, from_=lo, to=hi, textvariable=var, width=width,
                            bg=ENTRY_BG, fg=TEXT, insertbackground=TEXT,
                            buttonbackground=BTN, relief="flat", font=F_MAIN,
                            highlightthickness=1, highlightbackground="#444444",
                            highlightcolor="#666666",
                            command=self._schedule_preview)
            sb.bind("<KP_Enter>", lambda ev: self._schedule_preview() or "break")
            return sb

        def combo(parent, var, values, width=13):
            cb = ttk.Combobox(parent, textvariable=var, values=values,
                              state="readonly", width=width, style="Dark.TCombobox",
                              font=F_MAIN)
            cb.bind("<<ComboboxSelected>>", lambda *_: self._schedule_preview())
            return cb

        def lbl(parent, text, w=None):
            kw = {"width": w} if w else {}
            return tk.Label(parent, text=text, fg=DIM, bg=PANEL, font=F_MAIN, **kw)

        def row(parent):
            f = tk.Frame(parent, bg=PANEL)
            f.pack(fill="x", pady=3)
            return f

        # Find / Replace
        r = row(ops)
        self._find_var    = entry_var()
        self._replace_var = entry_var()
        lbl(r, "Find:", 7).pack(side="left")
        entry(r, self._find_var).pack(side="left", fill="x", expand=True, padx=(0, 8))
        lbl(r, "Replace with:").pack(side="left", padx=(0, 4))
        entry(r, self._replace_var).pack(side="left", fill="x", expand=True)

        # Add / Replace entire / Position
        r = row(ops)
        self._add_var         = entry_var()
        self._replace_all_var   = tk.BooleanVar()
        self._after_counter_var = tk.BooleanVar()
        self._add_pos_var       = tk.StringVar(value="After name")
        lbl(r, "Add:", 7).pack(side="left")
        entry(r, self._add_var).pack(side="left", fill="x", expand=True, padx=(0, 8))
        check(r, "Replace entire name", self._replace_all_var).pack(side="left", padx=(0, 8))
        check(r, "After counter", self._after_counter_var).pack(side="left", padx=(0, 8))
        combo(r, self._add_pos_var, ["After name", "Before name"]).pack(side="left")

        # Trim + Counter in a shared grid so spinboxes align in columns
        tc_grid = tk.Frame(ops, bg=PANEL)
        tc_grid.pack(fill="x", pady=3)
        tc_grid.columnconfigure(7, weight=1)

        PAD_LBL  = (12, 4)
        PAD_SPIN = (0, 0)

        self._trim_var       = tk.BooleanVar()
        self._trim_begin_var = spin_var(0)
        self._trim_end_var   = spin_var(0)
        check(tc_grid, "Trim",    self._trim_var   ).grid(row=0, column=0, sticky="w", padx=(0, 4), pady=3)
        lbl(tc_grid, "Begin:").grid(row=0, column=1, sticky="e", padx=PAD_LBL)
        spin(tc_grid, self._trim_begin_var, 0, 100, width=4).grid(row=0, column=2, sticky="w", padx=PAD_SPIN)
        lbl(tc_grid, "End:").grid(row=0, column=3, sticky="e", padx=PAD_LBL)
        spin(tc_grid, self._trim_end_var,   0, 100, width=4).grid(row=0, column=4, sticky="w", padx=PAD_SPIN)

        self._counter_var    = tk.BooleanVar()
        self._ctr_digits_var = spin_var(2)
        self._ctr_start_var  = spin_var(1)
        self._ctr_step_var   = spin_var(1)
        self._ctr_pos_var    = tk.StringVar(value="After name")
        check(tc_grid, "Counter", self._counter_var).grid(row=1, column=0, sticky="w", padx=(0, 4), pady=3)
        lbl(tc_grid, "Digits:").grid(row=1, column=1, sticky="e", padx=PAD_LBL)
        spin(tc_grid, self._ctr_digits_var, 1, 5,    width=4).grid(row=1, column=2, sticky="w", padx=PAD_SPIN)
        lbl(tc_grid, "Start:").grid(row=1, column=3, sticky="e", padx=PAD_LBL)
        spin(tc_grid, self._ctr_start_var,  0, 9999, width=4).grid(row=1, column=4, sticky="w", padx=PAD_SPIN)
        combo(tc_grid, self._ctr_pos_var, ["After name", "Before name"], width=12).grid(row=1, column=7, sticky="w", padx=(12, 0))
        lbl(tc_grid, "Step:").grid(row=2, column=1, sticky="e", padx=PAD_LBL, pady=(0, 3))
        spin(tc_grid, self._ctr_step_var, 1, 9999, width=4).grid(row=2, column=2, sticky="w", padx=PAD_SPIN)

        # Case / Remove digits
        r = row(ops)
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

        check(r, "UPPERCASE",     self._upper_var, upper_cmd).pack(side="left", padx=(0, 8))
        check(r, "lowercase",     self._lower_var, lower_cmd).pack(side="left", padx=(0, 8))
        check(r, "Title Case",    self._title_var, title_cmd).pack(side="left", padx=(0, 8))
        check(r, "Remove digits", self._nodig_var).pack(side="left")

        # Divider
        tk.Frame(main, bg=BTN_HOV, height=1).pack(fill="x", padx=12, pady=8)

        # Preview panels
        pf = tk.Frame(main, bg=PANEL)
        pf.pack(fill="both", expand=True, padx=12, pady=(0, 4))
        pf.columnconfigure(0, weight=1)
        pf.columnconfigure(1, weight=1)
        pf.rowconfigure(0, weight=1)

        left_col = tk.Frame(pf, bg=PANEL)
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        tk.Label(left_col, text="SELECTED IN BIN", fg=DIM, bg=PANEL,
                 font=F_HDR).pack(anchor="w", pady=(0, 2))
        self._selected_text = tk.Text(left_col, bg=ENTRY_BG, fg=TEXT, relief="flat",
                                      font=F_MONO, state="disabled", wrap="none", height=16,
                                      highlightthickness=1, highlightbackground="#444444",
                                      highlightcolor="#666666")
        self._selected_text.pack(fill="both", expand=True)

        right_col = tk.Frame(pf, bg=PANEL)
        right_col.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        tk.Label(right_col, text="RENAME PREVIEW", fg=ACCENT, bg=PANEL,
                 font=F_HDR).pack(anchor="w", pady=(0, 2))
        self._preview_text = tk.Text(right_col, bg=ENTRY_BG, fg=ACCENT, relief="flat",
                                     font=F_MONO, state="disabled", wrap="none", height=16,
                                     highlightthickness=1, highlightbackground="#444444",
                                     highlightcolor="#666666")
        self._preview_text.pack(fill="both", expand=True)

        # Status bar
        self._status_var = tk.StringVar(
            value="Select items in the bin, then choose an action below.")
        tk.Label(main, textvariable=self._status_var, fg=DIM, bg=PANEL,
                 font=F_STATUS, anchor="w").pack(fill="x", padx=12, pady=(6, 10))

        # Action buttons
        btn_row = tk.Frame(self.root, bg=BG)
        btn_row.pack(fill="x", padx=8, pady=(0, 8))
        TBtn(btn_row, text="Rename Clips",
             command=lambda: self._do_rename("clips"),
             bg=BLUE, padx=14, pady=8,
             font=F_MAIN).pack(side="left", fill="x", expand=True, padx=(0, 4))
        TBtn(btn_row, text="Rename Timelines",
             command=lambda: self._do_rename("timelines"),
             bg=PURPLE, padx=14, pady=8,
             font=F_MAIN).pack(side="left", fill="x", expand=True, padx=4)
        TBtn(btn_row, text="Rename All",
             command=lambda: self._do_rename("all"),
             bg=GREEN, padx=14, pady=8,
             font=F_MAIN).pack(side="left", fill="x", expand=True, padx=(4, 0))

    # ── Helpers ───────────────────────────────────────────────────────────

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

    def _get_selected(self):
        result = {"clips": [], "timelines": []}
        if not self._media_pool or not self._project:
            return result
        selected = self._media_pool.GetSelectedClips()
        if not selected:
            return result

        tl_by_name = {}
        tl_count = self._project.GetTimelineCount()
        for i in range(1, tl_count + 1):
            tl = self._project.GetTimelineByIndex(i)
            if tl:
                tl_by_name[tl.GetName()] = tl

        for item in selected:
            props = item.GetClipProperty() or {}
            nm    = props.get("Clip Name", "") or item.GetName() or ""
            itype = props.get("Type", "")
            if itype == "Timeline" or nm in tl_by_name:
                result["timelines"].append({
                    "name": nm, "obj": tl_by_name.get(nm), "clip_obj": item})
            else:
                result["clips"].append({"name": nm, "obj": item})
        return result


    def _set_text(self, widget, text):
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.config(state="disabled")

    def _schedule_preview(self, *_):
        if self._preview_job:
            self.root.after_cancel(self._preview_job)
        self._preview_job = self.root.after(80, self._update_preview)

    def _update_preview(self):
        self._preview_job = None
        sel   = self._get_selected()
        total = len(sel["clips"]) + len(sel["timelines"])

        if total == 0:
            self._set_text(self._selected_text, "(nothing selected in bin)")
            self._set_text(self._preview_text,  "")
            self._status_var.set(
                "Select items in the bin, then choose an action below.")
            return

        step      = self._ctr_step_var.get()
        counter   = self._ctr_start_var.get() * step
        sel_lines = []
        prv_lines = []

        for it in sel["clips"]:
            new = apply_transform(it["name"], **self._get_params(counter))
            if self._counter_var.get():
                counter += step
            sel_lines.append(f"[clip]      {it['name']}")
            prv_lines.append(f"[clip]      {new}")

        for it in sel["timelines"]:
            new = apply_transform(it["name"], **self._get_params(counter))
            if self._counter_var.get():
                counter += step
            sel_lines.append(f"[timeline]  {it['name']}")
            prv_lines.append(f"[timeline]  {new}")

        self._set_text(self._selected_text, "\n".join(sel_lines))
        self._set_text(self._preview_text,  "\n".join(prv_lines))
        self._status_var.set(
            f"{len(sel['clips'])} clip(s), {len(sel['timelines'])} timeline(s) selected")

    def _initial_lift(self):
        self.root.deiconify()
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
        if event.widget != self.root:
            return
        if self._stay_on_top_var.get():
            self.root.attributes("-topmost", True)
        self._schedule_preview()

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

    # ── Actions ───────────────────────────────────────────────────────────

    def _do_rename(self, filter_type):
        sel     = self._get_selected()
        step    = self._ctr_step_var.get()
        counter = self._ctr_start_var.get() * step
        changed = 0
        self._last_changes = []

        if filter_type in ("clips", "all"):
            for it in sel["clips"]:
                new = apply_transform(it["name"], **self._get_params(counter))
                if self._counter_var.get():
                    counter += step
                if new != it["name"]:
                    it["obj"].SetName(new)
                    self._last_changes.append((it["obj"], it["name"]))
                    changed += 1

        if filter_type in ("timelines", "all"):
            for it in sel["timelines"]:
                if it["obj"]:
                    new = apply_transform(it["name"], **self._get_params(counter))
                    if self._counter_var.get():
                        counter += step
                    if new != it["name"]:
                        it["obj"].SetName(new)
                        self._last_changes.append((it["obj"], it["name"]))
                        changed += 1

        self._undo_btn.config(
            state="normal" if self._last_changes else "disabled")
        self._status_var.set(f"[OK] Renamed {changed} item(s).")
        self._update_preview()

    def _undo(self):
        if not self._last_changes:
            return
        for obj, old_name in reversed(self._last_changes):
            obj.SetName(old_name)
        count = len(self._last_changes)
        self._last_changes = []
        self._undo_btn.config(state="disabled")
        self._status_var.set(f"[OK] Undone {count} rename(s).")
        self._update_preview()

    def _restore(self):
        if not self._last_changes:
            self._status_var.set("[!] Nothing to restore.")
            return
        for obj, old_name in reversed(self._last_changes):
            obj.SetName(old_name)
        count = len(self._last_changes)
        self._last_changes = []
        self._undo_btn.config(state="disabled")
        self._status_var.set(f"[OK] Restored {count} item(s).")
        self._update_preview()

    def _refresh(self):
        self._last_changes = []
        self._undo_btn.config(state="disabled")
        self._update_preview()

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


if __name__ == "__main__":
    try:
        root = tk.Tk()
        ClipRenamerPro(root)
        root.mainloop()
    except Exception as e:
        import traceback
        print("[Clip Renamer Pro] Fatal error:")
        traceback.print_exc()
