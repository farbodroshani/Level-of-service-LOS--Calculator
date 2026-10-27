"""Tkinter user interface for the HCM 7 Highway Level of Service Calculator."""
import datetime
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Dict, List, Optional, Tuple

from . import __author__, __version__
from .two_lane import calculate_two_lane
from .uninterrupted import (MEDIAN_REDUCTION, PCE_SPECIFIC_GRADE, calculate_freeway, calculate_multilane,
                            design_for_target_los)

APP_NAME = "Highway Level of Service Calculator"

FACILITIES = ["Freeway", "Multilane Highway", "Two-Lane Highway"]
SHORT_LABELS = {"Multilane Highway": "Multilane", "Two-Lane Highway": "Two-Lane"}
ANALYSIS_MODES = ["Analyze LOS", "Design lanes"]
VOLUME_MODES = ["Directional", "Two-way"]
TERRAIN_TYPES = ["Level", "Rolling", "Specific grade"]
SEGMENT_TYPES = ["Passing Constrained", "Passing Zone", "Passing Lane"]
TRUCK_MIXES = list(PCE_SPECIFIC_GRADE.keys())

UI_FONT = "Segoe UI" if sys.platform == "win32" else "Helvetica"
MONO_FONT = "Consolas" if sys.platform == "win32" else "Courier"

COLORS = {
    "bg": "#eef1f5",
    "card": "#ffffff",
    "header": "#14324f",
    "header_sub": "#a9bdd1",
    "accent": "#1f6feb",
    "accent_dark": "#1858c4",
    "text": "#1f2933",
    "muted": "#6b7785",
    "border": "#d8dee6",
    "segment": "#e4e9f0",
    "error": "#c62828",
    "error_bg": "#fdecea",
    "status": "#e2e7ee",
}

LOS_COLORS = {"A": "#2e7d32", "B": "#558b2f", "C": "#9e9d24", "D": "#f59f00", "E": "#e8590c", "F": "#c62828"}

LOS_DESCRIPTIONS = {
    "density": {
        "A": "Free flow - vehicles are almost completely unimpeded",
        "B": "Reasonably free flow - slight restriction to maneuver",
        "C": "Stable flow - lane changes need more care",
        "D": "Speeds begin to decline - limited freedom to maneuver",
        "E": "Operation at or near capacity - highly volatile",
        "F": "Breakdown - demand exceeds capacity",
    },
    "followers": {
        "A": "Speeds near the limit, little platooning",
        "B": "Light platooning",
        "C": "Moderate platooning",
        "D": "Heavy platooning, passing increasingly difficult",
        "E": "Significant platooning, passing essentially impossible",
        "F": "Demand exceeds capacity",
    },
}

# Input range checks: key -> (minimum, maximum)
RANGES = {
    "volume": (1, 20000), "opposing_volume": (0, 5000), "phf": (0.25, 1.0), "trucks": (0, 100), "hv": (0, 100),
    "directional_split": (0, 100), "lanes": (1, 12), "saf": (0.1, 1.5), "caf": (0.1, 1.5),
    "length": (0.01, 50), "grade_length": (0.01, 10), "posted_speed": (15, 85), "pl_pf_in": (0, 100),
    "pl_length": (0.01, 10), "pl_distance": (0.01, 100), "pl_flow_in": (1, 5000),
}


class Field:
    """One input row: label, entry or drop-down, unit and optional help."""

    def __init__(self, key: str, label: str, unit: str = "", default: str = "", options: Optional[List[str]] = None,
                 help: str = "", optional: bool = False, text: bool = False,
                 show: Optional[Callable[[Dict[str, str], bool], bool]] = None):
        self.key = key
        self.label = label
        self.unit = unit
        self.default = default
        self.options = options
        self.help = help
        self.optional = optional
        self.is_text = text or options is not None
        self.show = show or (lambda values, design: True)


def demand_fields(volume: str, phf: str, lanes: str, trucks: str) -> List[Tuple[str, List[Field]]]:
    return [
        ("Traffic demand", [
            Field("volume_mode", "Volume input", options=VOLUME_MODES, default=VOLUME_MODES[0],
                  help="Directional: demand in the analysis direction.\nTwo-way: total demand, split by direction."),
            Field("volume", "Demand volume", "veh/h", volume),
            Field("directional_split", "Directional split", "%", "50",
                  help="Share of the two-way volume in the analysis direction.",
                  show=lambda v, d: v["volume_mode"] == "Two-way"),
            Field("phf", "Peak hour factor", "", phf, help="Typical values: 0.85-0.98 on freeways, "
                                                           "0.75-0.95 on multilane highways."),
            Field("trucks", "Heavy vehicles", "%", trucks,
                  help="Single-unit trucks plus tractor-trailers.\nBuses and RVs are counted as single-unit trucks."),
        ]),
        ("Lanes", [
            Field("lanes", "Lanes in one direction", "ln", lanes, show=lambda v, d: not d),
            Field("target_los", "Target LOS", options=["A", "B", "C", "D", "E"], default="C",
                  help="The smallest number of lanes (2-8) that meets this LOS is reported.",
                  show=lambda v, d: d),
        ]),
    ]


def terrain_fields() -> Tuple[str, List[Field]]:
    specific = lambda v, d: v["terrain"] == "Specific grade"
    return ("Terrain and grade", [
        Field("terrain", "Terrain", options=TERRAIN_TYPES, default="Level",
              help="Level: ET = 2.0, Rolling: ET = 3.0 (Exhibit 12-25).\n"
                   "HCM 7 has no PCE for mountainous terrain - use a specific grade."),
        Field("grade", "Grade", "%", "3", help="Negative for downgrades (Exhibits 12-26 to 12-28).", show=specific),
        Field("grade_length", "Grade length", "mi", "1.0", show=specific),
        Field("truck_mix", "Truck mix", options=TRUCK_MIXES, default=TRUCK_MIXES[0],
              help="30/70 is typical of rural facilities, 50/50 of urban facilities.", show=specific),
    ])


FORMS: Dict[str, List[Tuple[str, List[Field]]]] = {
    "Freeway": demand_fields("4000", "0.92", "3", "5") + [
        ("Geometry", [
            Field("measured_ffs", "Measured FFS", "mi/h", optional=True,
                  help="Optional. Leave blank to estimate FFS from geometry (Equation 12-2)."),
            Field("lane_width", "Lane width", "ft", "12"),
            Field("lateral_clearance", "Right lateral clearance", "ft", "6"),
            Field("ramp_density", "Total ramp density", "ramps/mi", "1.0",
                  help="On- and off-ramps within 3 mi upstream and downstream of the segment midpoint, "
                       "divided by 6 mi."),
        ]),
        terrain_fields(),
        ("Adjustment factors", [
            Field("saf", "Speed adjustment factor", "SAF", "1.0",
                  help="1.0 for base conditions. Use Chapter 11 values for weather, work zones,\n"
                       "incidents or unfamiliar drivers."),
            Field("caf", "Capacity adjustment factor", "CAF", "1.0",
                  help="1.0 for base conditions. Use Chapter 11 values for weather, work zones,\n"
                       "incidents or unfamiliar drivers."),
        ]),
    ],
    "Multilane Highway": demand_fields("1900", "0.90", "2", "13") + [
        ("Geometry", [
            Field("measured_ffs", "Measured FFS", "mi/h", optional=True,
                  help="Optional. Leave blank to estimate FFS from geometry (Equation 12-3)."),
            Field("bffs", "Base free-flow speed", "mi/h", "55",
                  help="If unknown: posted speed + 5 mi/h (limits of 50 mi/h or more)\n"
                       "or posted speed + 7 mi/h (limits below 50 mi/h)."),
            Field("lane_width", "Lane width", "ft", "11"),
            Field("median", "Median type", options=list(MEDIAN_REDUCTION.keys()), default="Undivided"),
            Field("right_clearance", "Right lateral clearance", "ft", "4"),
            Field("left_clearance", "Left lateral clearance", "ft", "2",
                  help="Undivided highways and TWLTLs use 6 ft automatically.",
                  show=lambda v, d: v["median"] == "Divided"),
            Field("access_points", "Access point density", "pts/mi", "12",
                  help="Driveways and unsignalized intersections on the right side, per mile."),
        ]),
        terrain_fields(),
    ],
    "Two-Lane Highway": [
        ("Traffic demand", [
            Field("volume", "Analysis-direction volume", "veh/h", "752"),
            Field("opposing_volume", "Opposing-direction volume", "veh/h", "500",
                  show=lambda v, d: v["segment_type"] == "Passing Zone"),
            Field("phf", "Peak hour factor", "", "0.94"),
            Field("hv", "Heavy vehicles", "%", "5"),
        ]),
        ("Segment", [
            Field("segment_type", "Segment type", options=SEGMENT_TYPES, default=SEGMENT_TYPES[0],
                  help="Passing Constrained: passing prohibited or negligible.\n"
                       "Passing Zone: passing in the oncoming lane allowed.\n"
                       "Passing Lane: added lane in the analysis direction."),
            Field("length", "Segment length", "mi", "0.75"),
            Field("grade", "Grade", "%", "0", help="Negative for downgrades (Exhibit 15-11)."),
            Field("posted_speed", "Posted speed limit", "mi/h", "50",
                  help="Also selects the LOS thresholds: 50 mi/h or more uses the higher-speed criteria."),
            Field("measured_ffs", "Measured FFS", "mi/h", optional=True,
                  help="Optional. Leave blank to estimate FFS (Equations 15-2 to 15-6)."),
            Field("lane_width", "Lane width", "ft", "12"),
            Field("shoulder_width", "Shoulder width", "ft", "6"),
            Field("access_points", "Access point density", "pts/mi", "0"),
        ]),
        ("Horizontal curves", [
            Field("curves", "Curves (optional)", "", "", text=True,
                  help="One entry per curve: radius ft, superelevation %, length ft.\n"
                       "Separate curves with ';'  e.g.  450, 3, 432; 300, 2, 366.5"),
        ]),
        ("Upstream passing lane", [
            Field("has_upstream_pl", "Passing lane upstream?", options=["No", "Yes"], default="No",
                  help="Adjusts follower density for segments within the effective length\n"
                       "of an upstream passing lane (Step 9).",
                  show=lambda v, d: v["segment_type"] != "Passing Lane"),
            Field("pl_length", "Passing lane length", "mi", "1.5",
                  show=lambda v, d: v["has_upstream_pl"] == "Yes" and v["segment_type"] != "Passing Lane"),
            Field("pl_distance", "Distance from its start", "mi", "2.5",
                  help="From the start of the passing lane to the end of this segment.",
                  show=lambda v, d: v["has_upstream_pl"] == "Yes" and v["segment_type"] != "Passing Lane"),
            Field("pl_pf_in", "Percent followers entering it", "%", "70",
                  show=lambda v, d: v["has_upstream_pl"] == "Yes" and v["segment_type"] != "Passing Lane"),
            Field("pl_flow_in", "Flow rate entering it", "veh/h", "", optional=True,
                  help="Optional. Defaults to this segment's flow rate.",
                  show=lambda v, d: v["has_upstream_pl"] == "Yes" and v["segment_type"] != "Passing Lane"),
        ]),
    ],
}


class Tooltip:
    def __init__(self, widget: tk.Widget, text: str):
        self.widget = widget
        self.text = text
        self.tip: Optional[tk.Toplevel] = None
        self.after_id = None
        widget.bind("<Enter>", self.schedule, add="+")
        widget.bind("<Leave>", self.hide, add="+")

    def schedule(self, _event=None):
        self.after_id = self.widget.after(350, self.show)

    def show(self):
        if self.tip:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tip, text=self.text, justify="left", bg="#1f2933", fg="white", padx=10, pady=6,
                 font=(UI_FONT, 9)).pack()

    def hide(self, _event=None):
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None
        if self.tip:
            self.tip.destroy()
            self.tip = None


class ScrollableFrame(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.canvas = tk.Canvas(self, bg=COLORS["card"], highlightthickness=0, bd=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.window = None
        self.canvas.bind("<Configure>", self._fit_width)
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._on_wheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

    def set_content(self, frame: ttk.Frame):
        if self.window is None:
            self.window = self.canvas.create_window((0, 0), window=frame, anchor="nw")
        else:
            self.canvas.itemconfigure(self.window, window=frame)
        frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.update_idletasks()
        self._fit_width()
        self.canvas.yview_moveto(0)

    def _fit_width(self, _event=None):
        if self.window is not None:
            self.canvas.itemconfigure(self.window, width=self.canvas.winfo_width())
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_wheel(self, event):
        if self.canvas.yview() != (0.0, 1.0):
            self.canvas.yview_scroll(int(-event.delta / 120), "units")


class FacilityForm:
    """Builds and manages the input rows for one facility type."""

    def __init__(self, parent: tk.Widget, sections: List[Tuple[str, List[Field]]], on_change: Callable[[], None]):
        self.frame = ttk.Frame(parent, style="Card.TFrame", padding=(4, 0, 12, 8))
        self.frame.columnconfigure(1, weight=1)
        self.sections = sections
        self.vars: Dict[str, tk.StringVar] = {}
        self.widgets: Dict[str, Dict[str, tk.Widget]] = {}
        self.section_rows: List[Tuple[List[Field], List[tk.Widget]]] = []

        row = 0
        for title, fields in sections:
            header = ttk.Label(self.frame, text=title.upper(), style="Section.TLabel")
            header.grid(row=row, column=0, columnspan=4, sticky="w", pady=(14, 2))
            sep = ttk.Separator(self.frame)
            sep.grid(row=row + 1, column=0, columnspan=4, sticky="ew", pady=(0, 6))
            self.section_rows.append((fields, [header, sep]))
            row += 2
            for field in fields:
                self._build_row(field, row, on_change)
                row += 1

    def _build_row(self, field: Field, row: int, on_change: Callable[[], None]):
        var = tk.StringVar(value=field.default)
        var.trace_add("write", lambda *_: on_change())
        self.vars[field.key] = var

        label = ttk.Label(self.frame, text=field.label, style="Card.TLabel")
        label.grid(row=row, column=0, sticky="w", padx=(0, 10), pady=4)
        if field.options:
            control = ttk.Combobox(self.frame, textvariable=var, values=field.options, state="readonly", width=22)
        else:
            control = ttk.Entry(self.frame, textvariable=var, width=22)
        control.grid(row=row, column=1, sticky="ew", pady=4)
        unit = ttk.Label(self.frame, text=field.unit, style="Unit.TLabel", width=9)
        unit.grid(row=row, column=2, sticky="w", padx=(8, 0))
        info = ttk.Label(self.frame, text="ⓘ" if field.help else "", style="Info.TLabel", cursor="question_arrow")
        info.grid(row=row, column=3, sticky="w", padx=(2, 0))
        if field.help:
            Tooltip(info, field.help)
            Tooltip(label, field.help)
        self.widgets[field.key] = {"label": label, "control": control, "unit": unit, "info": info}

    def values(self) -> Dict[str, str]:
        return {key: var.get().strip() for key, var in self.vars.items()}

    def refresh(self, design: bool):
        values = self.values()
        for fields, header_widgets in self.section_rows:
            any_visible = False
            for field in fields:
                visible = field.show(values, design)
                any_visible = any_visible or visible
                for widget in self.widgets[field.key].values():
                    widget.grid() if visible else widget.grid_remove()
            for widget in header_widgets:
                widget.grid() if any_visible else widget.grid_remove()

    def visible_fields(self, design: bool) -> List[Field]:
        values = self.values()
        return [f for _, fields in self.sections for f in fields if f.show(values, design)]

    def reset(self):
        for _, fields in self.sections:
            for field in fields:
                self.vars[field.key].set(field.default)

    def mark(self, key: str, invalid: bool):
        control = self.widgets[key]["control"]
        if isinstance(control, ttk.Entry) and not isinstance(control, ttk.Combobox):
            control.configure(style="Invalid.TEntry" if invalid else "TEntry")


class LOSCalculatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} - HCM 7th Edition")
        self.configure(bg=COLORS["bg"])
        self.minsize(1080, 680)
        self._center(1320, 820)

        self.facility_var = tk.StringVar(value=FACILITIES[0])
        self.mode_var = tk.StringVar(value=ANALYSIS_MODES[0])
        self.status_var = tk.StringVar(value="Enter the inputs and press Calculate (or Enter).")
        self.report = ""

        self._setup_styles()
        self._build_menu()
        self._build_header()
        self._build_status_bar()
        self._build_body()

        self.facility_var.trace_add("write", lambda *_: self.switch_facility())
        self.mode_var.trace_add("write", lambda *_: self.refresh_form())
        self.bind("<Return>", lambda e: self.calculate())
        self.bind("<Control-s>", lambda e: self.save_report())
        self.switch_facility()

    # ---------- Layout ----------

    def _center(self, width: int, height: int):
        width = min(width, self.winfo_screenwidth() - 40)
        height = min(height, self.winfo_screenheight() - 80)
        x = (self.winfo_screenwidth() - width) // 2
        y = max((self.winfo_screenheight() - height) // 2 - 20, 0)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        c = COLORS
        style.configure(".", background=c["bg"], foreground=c["text"], font=(UI_FONT, 10))
        style.configure("Card.TFrame", background=c["card"])
        style.configure("Card.TLabel", background=c["card"])
        style.configure("Title.TLabel", background=c["card"], font=(UI_FONT, 13, "bold"))
        style.configure("Muted.TLabel", background=c["card"], foreground=c["muted"])
        style.configure("Unit.TLabel", background=c["card"], foreground=c["muted"], font=(UI_FONT, 9))
        style.configure("Info.TLabel", background=c["card"], foreground=c["accent"], font=(UI_FONT, 10))
        style.configure("Section.TLabel", background=c["card"], foreground=c["header"], font=(UI_FONT, 9, "bold"))
        style.configure("Caption.TLabel", background=c["card"], foreground=c["muted"], font=(UI_FONT, 9, "bold"))
        style.configure("TSeparator", background=c["border"])

        style.configure("TEntry", fieldbackground="white", bordercolor=c["border"], lightcolor=c["border"],
                        darkcolor=c["border"], padding=5)
        style.map("TEntry", bordercolor=[("focus", c["accent"])], lightcolor=[("focus", c["accent"])])
        style.configure("Invalid.TEntry", fieldbackground=c["error_bg"], bordercolor=c["error"],
                        lightcolor=c["error"], darkcolor=c["error"], padding=5)
        style.configure("TCombobox", fieldbackground="white", background="white", bordercolor=c["border"],
                        lightcolor=c["border"], darkcolor=c["border"], arrowcolor=c["text"], padding=4)
        style.map("TCombobox", fieldbackground=[("readonly", "white")], selectbackground=[("readonly", "white")],
                  selectforeground=[("readonly", c["text"])], bordercolor=[("focus", c["accent"])])

        style.configure("Accent.TButton", background=c["accent"], foreground="white", bordercolor=c["accent"],
                        lightcolor=c["accent"], darkcolor=c["accent"], font=(UI_FONT, 10, "bold"),
                        padding=(20, 8))
        style.map("Accent.TButton", background=[("pressed", c["accent_dark"]), ("active", c["accent_dark"])],
                  lightcolor=[("active", c["accent_dark"])], darkcolor=[("active", c["accent_dark"])])
        style.configure("Secondary.TButton", background=c["card"], foreground=c["text"], bordercolor=c["border"],
                        lightcolor=c["card"], darkcolor=c["card"], padding=(14, 8))
        style.map("Secondary.TButton", background=[("active", c["segment"])])

        style.configure("Segment.Toolbutton", background=c["segment"], foreground=c["text"], padding=(10, 7),
                        anchor="center", font=(UI_FONT, 10), bordercolor=c["segment"], lightcolor=c["segment"],
                        darkcolor=c["segment"])
        style.map("Segment.Toolbutton",
                  background=[("disabled", c["segment"]), ("selected", c["accent"]), ("active", "#d5dde8")],
                  foreground=[("disabled", "#a0a9b4"), ("selected", "white")],
                  lightcolor=[("selected", c["accent"])], darkcolor=[("selected", c["accent"])],
                  bordercolor=[("selected", c["accent"])])

        style.configure("Treeview", background=c["card"], fieldbackground=c["card"], rowheight=28,
                        bordercolor=c["border"], font=(UI_FONT, 10))
        style.configure("Treeview.Heading", background="#f1f4f8", foreground=c["muted"], relief="flat",
                        font=(UI_FONT, 9, "bold"), padding=(8, 6))
        style.map("Treeview", background=[("selected", "#dbe7fb")], foreground=[("selected", c["text"])])
        style.configure("TNotebook", background=c["card"], bordercolor=c["border"], tabmargins=(0, 4, 0, 0))
        style.configure("TNotebook.Tab", padding=(16, 7), background=c["segment"], foreground=c["muted"],
                        bordercolor=c["border"])
        style.map("TNotebook.Tab", background=[("selected", c["card"])], foreground=[("selected", c["text"])])

    def _build_menu(self):
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Calculate", accelerator="Enter", command=self.calculate)
        file_menu.add_command(label="Save report...", accelerator="Ctrl+S", command=self.save_report)
        file_menu.add_command(label="Copy report", command=self.copy_report)
        file_menu.add_separator()
        file_menu.add_command(label="Reset inputs", command=self.reset_inputs)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)
        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="Methodology", command=self.show_methodology)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        self.config(menu=menubar)

    def _build_header(self):
        header = tk.Frame(self, bg=COLORS["header"])
        header.pack(fill="x", side="top")
        inner = tk.Frame(header, bg=COLORS["header"])
        inner.pack(fill="x", padx=24, pady=14)
        tk.Label(inner, text=APP_NAME, bg=COLORS["header"], fg="white",
                 font=(UI_FONT, 17, "bold")).pack(side="left")
        tk.Label(inner, text="   Highway Capacity Manual, 7th Edition  ·  Chapters 12 and 15",
                 bg=COLORS["header"], fg=COLORS["header_sub"], font=(UI_FONT, 10)).pack(side="left", pady=(5, 0))
        tk.Label(inner, text=f"v{__version__}", bg=COLORS["header"], fg=COLORS["header_sub"],
                 font=(UI_FONT, 9)).pack(side="right")

    def _build_status_bar(self):
        bar = tk.Frame(self, bg=COLORS["status"])
        bar.pack(fill="x", side="bottom")
        self.status_label = tk.Label(bar, textvariable=self.status_var, bg=COLORS["status"], fg=COLORS["text"],
                                     font=(UI_FONT, 9), anchor="w")
        self.status_label.pack(side="left", padx=16, pady=5)
        tk.Label(bar, text=f"© 2025 {__author__}  ·  Independent tool, not affiliated with TRB",
                 bg=COLORS["status"], fg=COLORS["muted"], font=(UI_FONT, 9)).pack(side="right", padx=16)

    def _card(self, parent) -> Tuple[tk.Frame, ttk.Frame]:
        border = tk.Frame(parent, bg=COLORS["border"])
        card = ttk.Frame(border, style="Card.TFrame", padding=18)
        card.pack(fill="both", expand=True, padx=1, pady=1)
        return border, card

    def _build_body(self):
        body = tk.Frame(self, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=18, pady=16)
        body.columnconfigure(0, weight=1, minsize=500, uniform="col")
        body.columnconfigure(1, weight=1, minsize=500, uniform="col")
        body.rowconfigure(0, weight=1)

        left_border, left = self._card(body)
        left_border.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        right_border, right = self._card(body)
        right_border.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self._build_inputs(left)
        self._build_results(right)

    def _segmented(self, parent, variable: tk.StringVar, options: List[str]) -> List[ttk.Radiobutton]:
        frame = ttk.Frame(parent, style="Card.TFrame")
        frame.pack(fill="x", pady=(4, 12))
        buttons = []
        for i, option in enumerate(options):
            frame.columnconfigure(i, weight=1, uniform="seg")
            button = ttk.Radiobutton(frame, text=SHORT_LABELS.get(option, option), value=option, variable=variable, style="Segment.Toolbutton")
            button.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 2, 0))
            buttons.append(button)
        return buttons

    def _build_inputs(self, card: ttk.Frame):
        ttk.Label(card, text="Facility type", style="Caption.TLabel").pack(anchor="w")
        self._segmented(card, self.facility_var, FACILITIES)
        ttk.Label(card, text="Analysis", style="Caption.TLabel").pack(anchor="w")
        self.mode_buttons = self._segmented(card, self.mode_var, ANALYSIS_MODES)

        actions = ttk.Frame(card, style="Card.TFrame")
        actions.pack(side="bottom", fill="x", pady=(12, 0))
        ttk.Button(actions, text="Calculate", style="Accent.TButton", command=self.calculate).pack(side="right")
        ttk.Button(actions, text="Reset", style="Secondary.TButton", command=self.reset_inputs).pack(
            side="right", padx=(0, 8))

        self.scroller = ScrollableFrame(card, style="Card.TFrame")
        self.scroller.pack(fill="both", expand=True)
        self.forms = {name: FacilityForm(self.scroller.canvas, sections, self.refresh_form)
                      for name, sections in FORMS.items()}

    def _build_results(self, card: ttk.Frame):
        summary = ttk.Frame(card, style="Card.TFrame")
        summary.pack(fill="x")
        self.badge = tk.Label(summary, text="–", width=3, bg=COLORS["segment"], fg="white",
                              font=(UI_FONT, 34, "bold"), padx=8, pady=2)
        self.badge.pack(side="left")
        text = ttk.Frame(summary, style="Card.TFrame")
        text.pack(side="left", fill="x", expand=True, padx=(16, 0))
        self.result_title = ttk.Label(text, text="No results yet", style="Title.TLabel")
        self.result_title.pack(anchor="w")
        self.result_subtitle = ttk.Label(text, text="Choose a facility, enter the inputs and press Calculate.",
                                         style="Muted.TLabel", wraplength=460)
        self.result_subtitle.pack(anchor="w", pady=(2, 0))
        self.result_headline = ttk.Label(text, text="", style="Card.TLabel", font=(UI_FONT, 11, "bold"))
        self.result_headline.pack(anchor="w", pady=(4, 0))

        self.notebook = ttk.Notebook(card)
        self.notebook.pack(fill="both", expand=True, pady=(16, 0))

        table_tab = ttk.Frame(self.notebook, style="Card.TFrame", padding=(0, 8, 0, 0))
        self.table = ttk.Treeview(table_tab, columns=("measure", "value"), show="headings", selectmode="browse")
        self.table.heading("measure", text="PERFORMANCE MEASURE", anchor="w")
        self.table.heading("value", text="VALUE", anchor="e")
        self.table.column("measure", anchor="w", width=280)
        self.table.column("value", anchor="e", width=140)
        self.table.tag_configure("odd", background="#f7f9fb")
        self.table.pack(fill="both", expand=True)
        self.notebook.add(table_tab, text="Results")

        steps_tab = ttk.Frame(self.notebook, style="Card.TFrame", padding=(0, 8, 0, 0))
        scrollbar = ttk.Scrollbar(steps_tab)
        scrollbar.pack(side="right", fill="y")
        self.steps_text = tk.Text(steps_tab, wrap="word", font=(MONO_FONT, 10), bg="#f9fafb", fg=COLORS["text"],
                                  relief="flat", padx=14, pady=12, yscrollcommand=scrollbar.set,
                                  highlightthickness=1, highlightbackground=COLORS["border"])
        self.steps_text.pack(side="left", fill="both", expand=True)
        self.steps_text.tag_configure("heading", font=(MONO_FONT, 10, "bold"), foreground=COLORS["header"],
                                      spacing1=6)
        scrollbar.config(command=self.steps_text.yview)
        self.steps_text.configure(state="disabled")
        self.notebook.add(steps_tab, text="Step-by-step")

        actions = ttk.Frame(card, style="Card.TFrame")
        actions.pack(fill="x", pady=(12, 0))
        ttk.Button(actions, text="Save report...", style="Secondary.TButton", command=self.save_report).pack(
            side="right")
        ttk.Button(actions, text="Copy report", style="Secondary.TButton", command=self.copy_report).pack(
            side="right", padx=(0, 8))

    # ---------- Form state ----------

    @property
    def form(self) -> FacilityForm:
        return self.forms[self.facility_var.get()]

    @property
    def design_mode(self) -> bool:
        return self.mode_var.get() == ANALYSIS_MODES[1]

    def switch_facility(self):
        two_lane = self.facility_var.get() == "Two-Lane Highway"
        if two_lane and self.design_mode:
            self.mode_var.set(ANALYSIS_MODES[0])
        self.mode_buttons[1].state(["disabled"] if two_lane else ["!disabled"])
        self.scroller.set_content(self.form.frame)
        self.refresh_form()
        self.clear_results()

    def refresh_form(self):
        if hasattr(self, "forms"):
            self.form.refresh(self.design_mode)
            for key in self.form.widgets:
                self.form.mark(key, False)

    def reset_inputs(self):
        self.form.reset()
        self.clear_results()
        self.set_status("Inputs reset to the default example values.")

    def set_status(self, text: str, error: bool = False):
        self.status_var.set(text)
        self.status_label.configure(fg=COLORS["error"] if error else COLORS["text"])

    # ---------- Calculation ----------

    def gather_inputs(self) -> Dict:
        inputs: Dict = {}
        errors = []
        for field in self.form.visible_fields(self.design_mode):
            value = self.form.vars[field.key].get().strip()
            if field.is_text:
                inputs[field.key] = value
                continue
            if value == "" and field.optional:
                continue
            try:
                number = float(value.replace(",", ""))
            except ValueError:
                errors.append(f"{field.label}: enter a number")
                self.form.mark(field.key, True)
                continue
            low, high = RANGES.get(field.key, (None, None))
            if low is not None and not low <= number <= high:
                errors.append(f"{field.label}: must be between {low:g} and {high:g}")
                self.form.mark(field.key, True)
                continue
            if field.key == "lanes" and number != int(number):
                errors.append(f"{field.label}: must be a whole number")
                self.form.mark(field.key, True)
                continue
            inputs[field.key] = number
        if errors:
            raise ValueError("\n".join(errors))
        inputs["is_two_way"] = inputs.get("volume_mode") == "Two-way"
        return inputs

    def calculate(self):
        facility = self.facility_var.get()
        try:
            inputs = self.gather_inputs()
            if facility == "Two-Lane Highway":
                result = calculate_two_lane(inputs)
                self.show_result(result, "followers")
            elif self.design_mode:
                kind = "Freeway" if facility == "Freeway" else "Multilane"
                design = design_for_target_los(inputs, kind, inputs["target_los"])
                if "error" in design:
                    raise ValueError(design["error"])
                self.show_result(design["result"], "density", lanes=design["lanes_required"],
                                 target=inputs["target_los"])
            else:
                result = calculate_freeway(inputs) if facility == "Freeway" else calculate_multilane(inputs)
                self.show_result(result, "density")
        except ValueError as e:
            self.set_status(str(e).splitlines()[0], error=True)
            messagebox.showerror("Check the inputs", str(e), parent=self)

    def clear_results(self):
        self.report = ""
        self.badge.configure(text="–", bg=COLORS["segment"])
        self.result_title.configure(text="No results yet")
        self.result_subtitle.configure(text="Choose a facility, enter the inputs and press Calculate.")
        self.result_headline.configure(text="")
        self.table.delete(*self.table.get_children())
        self._set_steps("")

    def show_result(self, result: Dict, kind: str, lanes: Optional[int] = None, target: Optional[str] = None):
        los = result["LOS"]
        self.badge.configure(text=los, bg=LOS_COLORS[los])
        if lanes is not None:
            self.result_title.configure(text=f"{lanes} lanes per direction required")
            self.result_subtitle.configure(text=f"Smallest number of lanes that meets target LOS {target}. "
                                                f"Resulting LOS {los}: {LOS_DESCRIPTIONS[kind][los].lower()}.")
        else:
            self.result_title.configure(text=f"Level of Service {los}")
            self.result_subtitle.configure(text=LOS_DESCRIPTIONS[kind][los])

        headline_key = "Density (pc/mi/ln)" if kind == "density" else "Follower density (followers/mi/ln)"
        headline = result.get(headline_key)
        if isinstance(headline, (int, float)):
            name, unit = headline_key.split(" (")
            self.result_headline.configure(text=f"{name}: {headline:.1f} {unit.rstrip(')')}")
        else:
            self.result_headline.configure(text="Demand exceeds capacity")

        rows = [("Lanes required", lanes)] if lanes is not None else []
        rows += [(k, v) for k, v in result.items() if k not in ("steps", "LOS")]
        self.table.delete(*self.table.get_children())
        for i, (name, value) in enumerate(rows):
            self.table.insert("", "end", values=(name, self._fmt(value)), tags=("odd",) if i % 2 else ())

        self._set_steps(result["steps"])
        self.report = self._build_report(rows + [("Level of Service", los)], result["steps"])
        self.set_status(f"Calculated {self.facility_var.get().lower()} - LOS {los}.")

    @staticmethod
    def _fmt(value) -> str:
        # Results are already rounded by the calculators, so keep their precision
        if isinstance(value, (int, float)):
            return f"{value:,}"
        return str(value)

    def _set_steps(self, steps: str):
        self.steps_text.configure(state="normal")
        self.steps_text.delete("1.0", "end")
        for line in steps.splitlines():
            tag = "heading" if line.startswith(("---", "===")) else ()
            self.steps_text.insert("end", line.strip("-= ") if tag else line, tag)
            self.steps_text.insert("end", "\n")
        self.steps_text.configure(state="disabled")

    # ---------- Report ----------

    def _build_report(self, rows, steps: str) -> str:
        lines = [
            f"{APP_NAME} v{__version__}",
            "Method: Highway Capacity Manual, 7th Edition",
            f"Generated: {datetime.datetime.now():%Y-%m-%d %H:%M}",
            f"Facility: {self.facility_var.get()}    Analysis: {self.mode_var.get()}",
            "",
            "INPUTS",
        ]
        for field in self.form.visible_fields(self.design_mode):
            value = self.form.vars[field.key].get().strip()
            if value:
                lines.append(f"  {field.label:<34} {value} {field.unit}".rstrip())
        lines += ["", "RESULTS"]
        lines += [f"  {name:<40} {self._fmt(value)}" for name, value in rows]
        lines += ["", "STEP-BY-STEP CALCULATIONS", steps, "",
                  "Independent tool - not affiliated with or endorsed by the Transportation Research Board."]
        return "\n".join(lines)

    def copy_report(self):
        if not self.report:
            self.set_status("Run a calculation first.", error=True)
            return
        self.clipboard_clear()
        self.clipboard_append(self.report)
        self.set_status("Report copied to the clipboard.")

    def save_report(self):
        if not self.report:
            self.set_status("Run a calculation first.", error=True)
            return
        name = self.facility_var.get().lower().replace(" ", "_")
        path = filedialog.asksaveasfilename(parent=self, title="Save report", defaultextension=".txt",
                                            initialfile=f"los_report_{name}.txt",
                                            filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.report)
            self.set_status(f"Report saved to {path}")

    # ---------- Help ----------

    def show_methodology(self):
        messagebox.showinfo("Methodology", (
            "Basic freeway and multilane highway segments - HCM 7 Chapter 12\n"
            "  FFS estimation, capacity, heavy vehicle PCEs (general terrain or specific grade),\n"
            "  speed-flow model (Equation 12-1), density-based LOS (Exhibit 12-15).\n\n"
            "Two-lane highways - HCM 7 Chapter 15\n"
            "  Vertical and horizontal alignment, average speed, percent followers,\n"
            "  follower-density-based LOS (Exhibit 15-6), passing lanes and their\n"
            "  downstream effect.\n\n"
            "Results are verified against the HCM 7 Chapter 26 example problems."), parent=self)

    def show_about(self):
        messagebox.showinfo("About", (
            f"{APP_NAME}\nVersion {__version__}\n\n"
            f"© 2025 {__author__}\n\n"
            "Based on the Highway Capacity Manual, 7th Edition.\n"
            "This is an independent educational tool and is not affiliated with\n"
            "or endorsed by the Transportation Research Board."), parent=self)


def enable_high_dpi():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass


def main():
    enable_high_dpi()
    app = LOSCalculatorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
