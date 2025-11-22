import time
import tkinter as tk
from tkinter import ttk, messagebox

from .server import MeterState


class MeterApp(tk.Tk):
    """GUI dashboard for the Virtual Energy Meter."""

    def __init__(self, update_interval_ms: int = 1000):
        super().__init__()

        self.title("Virtual Energy Meter - Dashboard")
        self.geometry("560x360")
        self.resizable(False, False)

        # Simulation state
        self.meter_state = MeterState()
        self.update_interval_ms = update_interval_ms
        self.running = True

        # UI state
        self.noise_enabled = tk.BooleanVar(value=True)
        self.profile_var = tk.StringVar(value="Industrial / Heavy")
        self.status_var = tk.StringVar(value="Ready")

        self._build_style()
        self._build_menubar()
        self._build_layout()

        # Start periodic updates
        self._schedule_update()

    # ------------------------
    # UI construction
    # ------------------------
    def _build_style(self):
        style = ttk.Style(self)
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"))
        style.configure("SubHeader.TLabel", font=("Segoe UI", 11, "bold"))
        style.configure("Value.TLabel", font=("Consolas", 11))
        style.configure("Unit.TLabel", font=("Segoe UI", 9))
        style.configure("Status.TLabel", font=("Segoe UI", 9))

    def _build_menubar(self):
        menubar = tk.Menu(self)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=self._on_exit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

    def _build_layout(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)

        # Header
        title = ttk.Label(
            main_frame,
            text="Virtual 3-Phase Energy Meter",
            style="Header.TLabel",
        )
        title.grid(row=0, column=0, columnspan=2, sticky="w")

        subtitle = ttk.Label(
            main_frame,
            text="Simulated electrical measurements – suitable for SCADA / PLC testing",
            style="Unit.TLabel",
        )
        subtitle.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 8))

        # Controls (left-top)
        controls_frame = ttk.LabelFrame(main_frame, text="Controls", padding=8)
        controls_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        controls_frame.columnconfigure(0, weight=1)
        controls_frame.columnconfigure(1, weight=1)
        controls_frame.columnconfigure(2, weight=1)

        # Start/Stop button
        self.start_stop_button = ttk.Button(
            controls_frame,
            text="Pause simulation",
            command=self._toggle_running,
            width=18,
        )
        self.start_stop_button.grid(row=0, column=0, padx=4, pady=2, sticky="w")

        # Profile selector
        ttk.Label(controls_frame, text="Profile:", style="SubHeader.TLabel").grid(
            row=0, column=1, padx=(8, 2), pady=2, sticky="e"
        )
        profile_box = ttk.Combobox(
            controls_frame,
            textvariable=self.profile_var,
            state="readonly",
            width=20,
            values=[
                "Light / Office",
                "Industrial / Heavy",
                "Random test",
            ],
        )
        profile_box.grid(row=0, column=2, padx=4, pady=2, sticky="w")

        # Noise checkbox
        noise_check = ttk.Checkbutton(
            controls_frame,
            text="Enable noise",
            variable=self.noise_enabled,
        )
        noise_check.grid(row=1, column=0, padx=4, pady=2, sticky="w")

        # Main measurement panels
        phases_frame = ttk.LabelFrame(main_frame, text="Per-phase measurements", padding=10)
        phases_frame.grid(row=3, column=0, sticky="nsew", padx=(0, 8))

        totals_frame = ttk.LabelFrame(main_frame, text="Totals", padding=10)
        totals_frame.grid(row=3, column=1, sticky="nsew")

        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Per-phase headers
        headers = ["Phase", "Voltage [V]", "Current [A]", "Power [kW]"]
        for col, text in enumerate(headers):
            ttk.Label(phases_frame, text=text, style="SubHeader.TLabel").grid(
                row=0, column=col, padx=4, pady=(0, 4), sticky="w"
            )

        # StringVars
        self.phase_vars = {
            "L1": {"V": tk.StringVar(), "I": tk.StringVar(), "P": tk.StringVar()},
            "L2": {"V": tk.StringVar(), "I": tk.StringVar(), "P": tk.StringVar()},
            "L3": {"V": tk.StringVar(), "I": tk.StringVar(), "P": tk.StringVar()},
        }
        self.total_kw_var = tk.StringVar()
        self.pf_var = tk.StringVar()
        self.freq_var = tk.StringVar()

        # Per-phase rows
        for row, phase in enumerate(["L1", "L2", "L3"], start=1):
            ttk.Label(phases_frame, text=phase, style="SubHeader.TLabel").grid(
                row=row, column=0, padx=4, pady=2, sticky="w"
            )
            ttk.Label(phases_frame, textvariable=self.phase_vars[phase]["V"], style="Value.TLabel").grid(
                row=row, column=1, padx=4, pady=2, sticky="e"
            )
            ttk.Label(phases_frame, textvariable=self.phase_vars[phase]["I"], style="Value.TLabel").grid(
                row=row, column=2, padx=4, pady=2, sticky="e"
            )
            ttk.Label(phases_frame, textvariable=self.phase_vars[phase]["P"], style="Value.TLabel").grid(
                row=row, column=3, padx=4, pady=2, sticky="e"
            )

        # Totals panel
        ttk.Label(totals_frame, text="Total Active Power:", style="SubHeader.TLabel").grid(
            row=0, column=0, padx=4, pady=4, sticky="w"
        )
        ttk.Label(totals_frame, textvariable=self.total_kw_var, style="Value.TLabel").grid(
            row=0, column=1, padx=4, pady=4, sticky="e"
        )

        ttk.Label(totals_frame, text="Power Factor:", style="SubHeader.TLabel").grid(
            row=1, column=0, padx=4, pady=4, sticky="w"
        )
        ttk.Label(totals_frame, textvariable=self.pf_var, style="Value.TLabel").grid(
            row=1, column=1, padx=4, pady=4, sticky="e"
        )

        ttk.Label(totals_frame, text="Frequency:", style="SubHeader.TLabel").grid(
            row=2, column=0, padx=4, pady=4, sticky="w"
        )
        ttk.Label(totals_frame, textvariable=self.freq_var, style="Value.TLabel").grid(
            row=2, column=1, padx=4, pady=4, sticky="e"
        )

        # Footer / status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        status_frame.columnconfigure(0, weight=1)

        status_label = ttk.Label(
            status_frame,
            textvariable=self.status_var,
            style="Status.TLabel",
            anchor="w",
        )
        status_label.grid(row=0, column=0, sticky="ew")

    # ------------------------
    # Menu / actions
    # ------------------------
    def _on_exit(self):
        self.destroy()

    def _show_about(self):
        messagebox.showinfo(
            "About",
            "Virtual Energy Meter\n\n"
            "Simulated 3-phase meter with GUI dashboard and Modbus TCP backend.\n"
            "Built with Python and Tkinter.",
        )

    def _toggle_running(self):
        self.running = not self.running
        if self.running:
            self.start_stop_button.config(text="Pause simulation")
            self._set_status("Simulation running")
        else:
            self.start_stop_button.config(text="Resume simulation")
            self._set_status("Simulation paused")

    # ------------------------
    # Simulation / updates
    # ------------------------
    def _schedule_update(self):
        if self.running:
            self._update_values()
        self.after(self.update_interval_ms, self._schedule_update)

    def _apply_profile(self):
        """Adjust currents / PF based on selected profile."""
        profile = self.profile_var.get()

        if profile == "Light / Office":
            # lower currents, good PF
            self.meter_state.current_l1 = max(1.0, self.meter_state.current_l1 * 0.5)
            self.meter_state.current_l2 = max(1.0, self.meter_state.current_l2 * 0.5)
            self.meter_state.current_l3 = max(1.0, self.meter_state.current_l3 * 0.5)
            self.meter_state.pf = min(0.99, max(0.95, self.meter_state.pf))
        elif profile == "Industrial / Heavy":
            # higher currents, slightly lower PF
            self.meter_state.current_l1 = min(80.0, self.meter_state.current_l1 * 1.5 + 5)
            self.meter_state.current_l2 = min(80.0, self.meter_state.current_l2 * 1.5 + 5)
            self.meter_state.current_l3 = min(80.0, self.meter_state.current_l3 * 1.5 + 5)
            self.meter_state.pf = max(0.85, min(0.96, self.meter_state.pf))
        elif profile == "Random test":
            # wild card behaviour – random currents
            import random

            self.meter_state.current_l1 = random.uniform(0.0, 100.0)
            self.meter_state.current_l2 = random.uniform(0.0, 100.0)
            self.meter_state.current_l3 = random.uniform(0.0, 100.0)
            self.meter_state.pf = random.uniform(0.75, 0.99)

    def _update_values(self):
        # Advance simulation only if noise is enabled
        if self.noise_enabled.get():
            self.meter_state.update()

        # Apply profile shaping
        self._apply_profile()

        # Compute powers
        p1, p2, p3, ptot = self.meter_state.powers_kw()

        # Voltages
        self.phase_vars["L1"]["V"].set(f"{self.meter_state.voltage_l1:6.1f}")
        self.phase_vars["L2"]["V"].set(f"{self.meter_state.voltage_l2:6.1f}")
        self.phase_vars["L3"]["V"].set(f"{self.meter_state.voltage_l3:6.1f}")

        # Currents
        self.phase_vars["L1"]["I"].set(f"{self.meter_state.current_l1:6.2f}")
        self.phase_vars["L2"]["I"].set(f"{self.meter_state.current_l2:6.2f}")
        self.phase_vars["L3"]["I"].set(f"{self.meter_state.current_l3:6.2f}")

        # Powers
        self.phase_vars["L1"]["P"].set(f"{p1:6.2f}")
        self.phase_vars["L2"]["P"].set(f"{p2:6.2f}")
        self.phase_vars["L3"]["P"].set(f"{p3:6.2f}")

        # Totals
        self.total_kw_var.set(f"{ptot:6.2f} kW")
        self.pf_var.set(f"{self.meter_state.pf:4.3f}")
        self.freq_var.set(f"{self.meter_state.freq:5.2f} Hz")

        # Status bar text
        now = time.strftime("%H:%M:%S")
        noise_text = "On" if self.noise_enabled.get() else "Off"
        self._set_status(
            f"Running • Last update: {now} • Profile: {self.profile_var.get()} • Noise: {noise_text}"
        )

    def _set_status(self, text: str):
        self.status_var.set(text)


def main():
    app = MeterApp()
    app.mainloop()


if __name__ == "__main__":
    main()
