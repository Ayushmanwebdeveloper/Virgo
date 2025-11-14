#!/usr/bin/env python3
"""
Virgo Radio Telescope GUI - Enhanced Version
A comprehensive graphical interface for the Virgo spectrometer and radiometer
with all features from the command-line tool
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import os
import sys
import time
from datetime import datetime

# Import Virgo modules
try:
    from virgo import (observe, plot, predict, simulate, monitor_rfi, plot_rfi,
                       map_hi, gain, beamwidth, A_e, SEFD, snr, NF, T_noise,
                       G_T, frequency, wavelength, equatorial, galactic)
except ImportError as e:
    print(f"Error: Could not import virgo module: {e}")
    print("Make sure Virgo is installed: pip install -e .")
    sys.exit(1)


class VirgoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Virgo Radio Telescope Control GUI - Enhanced")
        self.root.geometry("1500x950")

        # Observation state
        self.is_observing = False
        self.is_monitoring_rfi = False
        self.observation_thread = None
        self.current_obs_file = None
        self.current_cal_file = None

        # RFI blanking ranges
        self.rfi_ranges = []

        # Create main layout
        self.create_menu()
        self.create_main_layout()

    def create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Observation", command=self.load_observation)
        file_menu.add_command(label="Load Calibration", command=self.load_calibration)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Predict Source Position", command=self.show_predict)
        tools_menu.add_command(label="Simulate HI Profile", command=self.show_simulate)
        tools_menu.add_command(label="View HI Map", command=self.show_hi_map)
        tools_menu.add_command(label="Monitor RFI", command=self.show_rfi_monitor)
        tools_menu.add_separator()
        tools_menu.add_command(label="Antenna Calculator", command=self.show_antenna_calc)
        tools_menu.add_command(label="Coordinate Converter", command=self.show_coord_converter)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="User Guide", command=self.show_user_guide)
        help_menu.add_command(label="About", command=self.show_about)

        # Set close protocol
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_main_layout(self):
        """Create the main GUI layout"""
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create tabs
        self.observation_tab = ttk.Frame(self.notebook)
        self.calibration_tab = ttk.Frame(self.notebook)
        self.analysis_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.observation_tab, text="Observation")
        self.notebook.add(self.calibration_tab, text="Calibration")
        self.notebook.add(self.analysis_tab, text="Analysis & Plotting")

        # Setup each tab
        self.setup_observation_tab()
        self.setup_calibration_tab()
        self.setup_analysis_tab()

    def setup_observation_tab(self):
        """Setup the observation tab with parameter inputs and live display"""
        # Left panel - Parameters
        left_frame = ttk.Frame(self.observation_tab)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)

        # Parameters frame with scrollbar
        params_frame = ttk.LabelFrame(left_frame, text="Observation Parameters")
        params_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        canvas = tk.Canvas(params_frame, width=400)
        scrollbar = ttk.Scrollbar(params_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        row = 0

        # Spectrometer Type
        ttk.Label(scrollable_frame, text="Spectrometer Type", font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1

        ttk.Label(scrollable_frame, text="Type:").grid(row=row, column=0, sticky=tk.W, padx=5)
        self.spectrometer_type = ttk.Combobox(scrollable_frame, width=27, state='readonly')
        self.spectrometer_type.grid(row=row, column=1, padx=5, pady=2)
        self.spectrometer_type['values'] = ('WOLA (Default - Lower sidelobes)', 'FTF (Lightweight)')
        self.spectrometer_type.current(0)
        row += 1

        # SDR Settings
        ttk.Label(scrollable_frame, text="SDR Configuration", font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        row += 1

        ttk.Label(scrollable_frame, text="Device Args:").grid(row=row, column=0, sticky=tk.W, padx=5)
        self.dev_args = ttk.Entry(scrollable_frame, width=30)
        self.dev_args.grid(row=row, column=1, padx=5, pady=2)
        self.dev_args.insert(0, "rtl=0")
        row += 1

        ttk.Label(scrollable_frame, text="RF Gain (dB):").grid(row=row, column=0, sticky=tk.W, padx=5)
        self.rf_gain = ttk.Entry(scrollable_frame, width=30)
        self.rf_gain.grid(row=row, column=1, padx=5, pady=2)
        self.rf_gain.insert(0, "30")
        row += 1

        ttk.Label(scrollable_frame, text="IF Gain (dB):").grid(row=row, column=0, sticky=tk.W, padx=5)
        self.if_gain = ttk.Entry(scrollable_frame, width=30)
        self.if_gain.grid(row=row, column=1, padx=5, pady=2)
        self.if_gain.insert(0, "25")
        row += 1

        ttk.Label(scrollable_frame, text="BB Gain (dB):").grid(row=row, column=0, sticky=tk.W, padx=5)
        self.bb_gain = ttk.Entry(scrollable_frame, width=30)
        self.bb_gain.grid(row=row, column=1, padx=5, pady=2)
        self.bb_gain.insert(0, "18")
        row += 1

        # Frequency Settings
        ttk.Label(scrollable_frame, text="Frequency Configuration", font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        row += 1

        ttk.Label(scrollable_frame, text="Frequency (Hz):*").grid(row=row, column=0, sticky=tk.W, padx=5)
        self.frequency = ttk.Entry(scrollable_frame, width=30)
        self.frequency.grid(row=row, column=1, padx=5, pady=2)
        self.frequency.insert(0, "1420405752")
        row += 1

        ttk.Label(scrollable_frame, text="Bandwidth (Hz):*").grid(row=row, column=0, sticky=tk.W, padx=5)
        self.bandwidth = ttk.Entry(scrollable_frame, width=30)
        self.bandwidth.grid(row=row, column=1, padx=5, pady=2)
        self.bandwidth.insert(0, "2400000")
        row += 1

        ttk.Label(scrollable_frame, text="Channels:*").grid(row=row, column=0, sticky=tk.W, padx=5)
        self.channels = ttk.Entry(scrollable_frame, width=30)
        self.channels.grid(row=row, column=1, padx=5, pady=2)
        self.channels.insert(0, "2048")
        row += 1

        # Timing Settings
        ttk.Label(scrollable_frame, text="Timing Configuration", font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        row += 1

        ttk.Label(scrollable_frame, text="Sample Time (s):*").grid(row=row, column=0, sticky=tk.W, padx=5)
        self.t_sample = ttk.Entry(scrollable_frame, width=30)
        self.t_sample.grid(row=row, column=1, padx=5, pady=2)
        self.t_sample.insert(0, "1.0")
        row += 1

        ttk.Label(scrollable_frame, text="Duration (s):").grid(row=row, column=0, sticky=tk.W, padx=5)
        self.duration = ttk.Entry(scrollable_frame, width=30)
        self.duration.grid(row=row, column=1, padx=5, pady=2)
        self.duration.insert(0, "60")
        row += 1

        ttk.Label(scrollable_frame, text="Start In (s):").grid(row=row, column=0, sticky=tk.W, padx=5)
        self.start_in = ttk.Entry(scrollable_frame, width=30)
        self.start_in.grid(row=row, column=1, padx=5, pady=2)
        self.start_in.insert(0, "0")
        row += 1

        # Observer Location
        ttk.Label(scrollable_frame, text="Observer Location", font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        row += 1

        ttk.Label(scrollable_frame, text="Latitude (deg):").grid(row=row, column=0, sticky=tk.W, padx=5)
        self.obs_lat = ttk.Entry(scrollable_frame, width=30)
        self.obs_lat.grid(row=row, column=1, padx=5, pady=2)
        row += 1

        ttk.Label(scrollable_frame, text="Longitude (deg):").grid(row=row, column=0, sticky=tk.W, padx=5)
        self.obs_lon = ttk.Entry(scrollable_frame, width=30)
        self.obs_lon.grid(row=row, column=1, padx=5, pady=2)
        row += 1

        ttk.Label(scrollable_frame, text="Height (m):").grid(row=row, column=0, sticky=tk.W, padx=5)
        self.obs_height = ttk.Entry(scrollable_frame, width=30)
        self.obs_height.grid(row=row, column=1, padx=5, pady=2)
        self.obs_height.insert(0, "0")
        row += 1

        # Target Coordinates
        ttk.Label(scrollable_frame, text="Target Coordinates", font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        row += 1

        ttk.Label(scrollable_frame, text="Coordinate Type:").grid(row=row, column=0, sticky=tk.W, padx=5)
        self.coord_type = ttk.Combobox(scrollable_frame, width=27, state='readonly')
        self.coord_type.grid(row=row, column=1, padx=5, pady=2)
        self.coord_type['values'] = ('None', 'Equatorial (RA/Dec)', 'Horizontal (Az/Alt)')
        self.coord_type.current(0)
        self.coord_type.bind('<<ComboboxSelected>>', self.on_coord_type_change)
        row += 1

        # RA/Dec inputs (initially hidden)
        self.ra_label = ttk.Label(scrollable_frame, text="RA (hours):")
        self.ra_entry = ttk.Entry(scrollable_frame, width=30)

        self.dec_label = ttk.Label(scrollable_frame, text="Dec (deg):")
        self.dec_entry = ttk.Entry(scrollable_frame, width=30)

        # Az/Alt inputs (initially hidden)
        self.az_label = ttk.Label(scrollable_frame, text="Azimuth (deg):")
        self.az_entry = ttk.Entry(scrollable_frame, width=30)

        self.alt_label = ttk.Label(scrollable_frame, text="Altitude (deg):")
        self.alt_entry = ttk.Entry(scrollable_frame, width=30)

        self.coord_row_start = row

        # Output Settings
        ttk.Label(scrollable_frame, text="Output Configuration", font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        row += 1

        ttk.Label(scrollable_frame, text="Observation File:").grid(row=row, column=0, sticky=tk.W, padx=5)
        self.obs_file = ttk.Entry(scrollable_frame, width=30)
        self.obs_file.grid(row=row, column=1, padx=5, pady=2)
        self.obs_file.insert(0, "observation.dat")
        row += 1

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Control buttons
        control_frame = ttk.Frame(left_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        self.start_btn = ttk.Button(control_frame, text="Start Observation", command=self.start_observation)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(control_frame, text="Stop", command=self.stop_observation, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="HI Preset", command=self.load_hi_preset).pack(side=tk.LEFT, padx=5)

        # Right panel - Live Display
        right_frame = ttk.Frame(self.observation_tab)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Status display
        status_frame = ttk.LabelFrame(right_frame, text="Status Log")
        status_frame.pack(fill=tk.X, padx=5, pady=5)

        self.status_text = scrolledtext.ScrolledText(status_frame, height=8, wrap=tk.WORD)
        self.status_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_status("Virgo GUI Enhanced - Ready")

        # Live spectrum display
        plot_frame = ttk.LabelFrame(right_frame, text="Live Spectrum Display")
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax1 = self.fig.add_subplot(211)
        self.ax2 = self.fig.add_subplot(212)

        self.ax1.set_title("Average Spectrum")
        self.ax1.set_xlabel("Frequency (MHz)")
        self.ax1.set_ylabel("Power")
        self.ax1.grid(True, alpha=0.3)

        self.ax2.set_title("Power vs Time")
        self.ax2.set_xlabel("Time (s)")
        self.ax2.set_ylabel("Power")
        self.ax2.grid(True, alpha=0.3)

        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(self.canvas, plot_frame)
        toolbar.update()

    def on_coord_type_change(self, event=None):
        """Handle coordinate type change"""
        coord_type = self.coord_type.get()

        # Hide all coordinate inputs first
        self.ra_label.grid_forget()
        self.ra_entry.grid_forget()
        self.dec_label.grid_forget()
        self.dec_entry.grid_forget()
        self.az_label.grid_forget()
        self.az_entry.grid_forget()
        self.alt_label.grid_forget()
        self.alt_entry.grid_forget()

        row = self.coord_row_start

        if coord_type == 'Equatorial (RA/Dec)':
            self.ra_label.grid(row=row, column=0, sticky=tk.W, padx=5)
            self.ra_entry.grid(row=row, column=1, padx=5, pady=2)
            row += 1
            self.dec_label.grid(row=row, column=0, sticky=tk.W, padx=5)
            self.dec_entry.grid(row=row, column=1, padx=5, pady=2)
        elif coord_type == 'Horizontal (Az/Alt)':
            self.az_label.grid(row=row, column=0, sticky=tk.W, padx=5)
            self.az_entry.grid(row=row, column=1, padx=5, pady=2)
            row += 1
            self.alt_label.grid(row=row, column=0, sticky=tk.W, padx=5)
            self.alt_entry.grid(row=row, column=1, padx=5, pady=2)

    def setup_calibration_tab(self):
        """Setup the calibration tab"""
        # Instructions
        info_frame = ttk.LabelFrame(self.calibration_tab, text="Calibration Instructions")
        info_frame.pack(fill=tk.X, padx=10, pady=10)

        info_text = """
Calibration Procedure:
1. Point antenna at cold sky region (high galactic latitude, away from Milky Way)
2. Click "Start Calibration Observation" below
3. Wait for observation to complete
4. Point antenna at your target
5. Perform target observation with SAME parameters
6. Use Analysis tab to generate calibrated spectrum

Benefits: Removes instrumental effects, converts to SNR/temperature scale
        """
        ttk.Label(info_frame, text=info_text, justify=tk.LEFT).pack(padx=10, pady=10)

        # Calibration controls
        cal_frame = ttk.LabelFrame(self.calibration_tab, text="Calibration Controls")
        cal_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(cal_frame, text="Calibration File:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.cal_file_entry = ttk.Entry(cal_frame, width=50)
        self.cal_file_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(cal_frame, text="Browse", command=self.browse_cal_file).grid(row=0, column=2, padx=5, pady=5)

        ttk.Button(cal_frame, text="Start Calibration Observation",
                  command=self.start_calibration_obs).grid(row=1, column=0, columnspan=3, pady=10)

        # Quick calibration presets
        preset_frame = ttk.LabelFrame(self.calibration_tab, text="Quick Presets")
        preset_frame.pack(fill=tk.X, padx=10, pady=10)

        btn_frame = ttk.Frame(preset_frame)
        btn_frame.pack(padx=10, pady=10)

        ttk.Button(btn_frame, text="HI Line (1420 MHz)",
                  command=lambda: self.load_preset("HI")).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Continuum (1400 MHz)",
                  command=lambda: self.load_preset("continuum")).pack(side=tk.LEFT, padx=5)

    def setup_analysis_tab(self):
        """Setup the analysis and plotting tab"""
        # Top section - File selection and options
        top_frame = ttk.Frame(self.analysis_tab)
        top_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=10)

        # File selection
        file_frame = ttk.LabelFrame(top_frame, text="File Selection")
        file_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(file_frame, text="Observation File:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.analysis_obs_file = ttk.Entry(file_frame, width=50)
        self.analysis_obs_file.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(file_frame, text="Browse", command=self.browse_obs_file).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(file_frame, text="Calibration File:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.analysis_cal_file = ttk.Entry(file_frame, width=50)
        self.analysis_cal_file.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(file_frame, text="Browse", command=self.browse_analysis_cal_file).grid(row=1, column=2, padx=5, pady=5)

        # Processing options frame with scrollbar
        proc_outer_frame = ttk.LabelFrame(top_frame, text="Processing Options")
        proc_outer_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        proc_canvas = tk.Canvas(proc_outer_frame, height=200)
        proc_scrollbar = ttk.Scrollbar(proc_outer_frame, orient="vertical", command=proc_canvas.yview)
        proc_frame = ttk.Frame(proc_canvas)

        proc_frame.bind(
            "<Configure>",
            lambda e: proc_canvas.configure(scrollregion=proc_canvas.bbox("all"))
        )

        proc_canvas.create_window((0, 0), window=proc_frame, anchor="nw")
        proc_canvas.configure(yscrollcommand=proc_scrollbar.set)

        row = 0

        # RFI Mitigation - Median Filters
        ttk.Label(proc_frame, text="RFI Mitigation", font=('Arial', 9, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        row += 1

        ttk.Label(proc_frame, text="Median Filter (Frequency):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.analysis_median_freq = ttk.Entry(proc_frame, width=20)
        self.analysis_median_freq.grid(row=row, column=1, padx=5, pady=2)
        row += 1

        ttk.Label(proc_frame, text="Median Filter (Time):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.analysis_median_time = ttk.Entry(proc_frame, width=20)
        self.analysis_median_time.grid(row=row, column=1, padx=5, pady=2)
        row += 1

        # RFI Frequency Blanking
        ttk.Label(proc_frame, text="RFI Freq Blanking:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Button(proc_frame, text="Manage RFI Ranges", command=self.manage_rfi_ranges).grid(row=row, column=1, padx=5, pady=2, sticky=tk.W)
        row += 1

        # Display options
        ttk.Label(proc_frame, text="Display Options", font=('Arial', 9, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=(10, 5))
        row += 1

        self.analysis_db = tk.BooleanVar(value=True)
        ttk.Checkbutton(proc_frame, text="Use dB Scale", variable=self.analysis_db).grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)
        row += 1

        self.analysis_vlsr = tk.BooleanVar(value=False)
        ttk.Checkbutton(proc_frame, text="VLSR Frame", variable=self.analysis_vlsr).grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)
        row += 1

        self.analysis_meta = tk.BooleanVar(value=False)
        ttk.Checkbutton(proc_frame, text="Show Metadata", variable=self.analysis_meta).grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)
        row += 1

        self.analysis_slope_corr = tk.BooleanVar(value=False)
        ttk.Checkbutton(proc_frame, text="Slope Correction", variable=self.analysis_slope_corr).grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)
        row += 1

        # Spectral line
        ttk.Label(proc_frame, text="Spectral Line", font=('Arial', 9, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=(10, 5))
        row += 1

        ttk.Label(proc_frame, text="Rest Frequency (Hz):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.analysis_rest_freq = ttk.Entry(proc_frame, width=20)
        self.analysis_rest_freq.grid(row=row, column=1, padx=5, pady=2)
        self.analysis_rest_freq.insert(0, "1420405752")
        row += 1

        # Pulsar de-dispersion
        ttk.Label(proc_frame, text="Dispersion Measure (pc/cm³):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.analysis_dm = ttk.Entry(proc_frame, width=20)
        self.analysis_dm.grid(row=row, column=1, padx=5, pady=2)
        row += 1

        # Axis limits
        ttk.Label(proc_frame, text="Axis Limits", font=('Arial', 9, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=(10, 5))
        row += 1

        ttk.Label(proc_frame, text="X-axis (freq) limits:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        xlim_frame = ttk.Frame(proc_frame)
        xlim_frame.grid(row=row, column=1, padx=5, pady=2, sticky=tk.W)
        self.analysis_xlim_low = ttk.Entry(xlim_frame, width=9)
        self.analysis_xlim_low.pack(side=tk.LEFT)
        ttk.Label(xlim_frame, text=" to ").pack(side=tk.LEFT)
        self.analysis_xlim_high = ttk.Entry(xlim_frame, width=9)
        self.analysis_xlim_high.pack(side=tk.LEFT)
        row += 1

        ttk.Label(proc_frame, text="Y-axis (time) limits:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        ylim_frame = ttk.Frame(proc_frame)
        ylim_frame.grid(row=row, column=1, padx=5, pady=2, sticky=tk.W)
        self.analysis_ylim_low = ttk.Entry(ylim_frame, width=9)
        self.analysis_ylim_low.pack(side=tk.LEFT)
        ttk.Label(ylim_frame, text=" to ").pack(side=tk.LEFT)
        self.analysis_ylim_high = ttk.Entry(ylim_frame, width=9)
        self.analysis_ylim_high.pack(side=tk.LEFT)
        row += 1

        ttk.Label(proc_frame, text="Avg spectrum Y limits:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        avg_ylim_frame = ttk.Frame(proc_frame)
        avg_ylim_frame.grid(row=row, column=1, padx=5, pady=2, sticky=tk.W)
        self.analysis_avg_ylim_low = ttk.Entry(avg_ylim_frame, width=9)
        self.analysis_avg_ylim_low.pack(side=tk.LEFT)
        ttk.Label(avg_ylim_frame, text=" to ").pack(side=tk.LEFT)
        self.analysis_avg_ylim_high = ttk.Entry(avg_ylim_frame, width=9)
        self.analysis_avg_ylim_high.pack(side=tk.LEFT)
        row += 1

        ttk.Label(proc_frame, text="Cal spectrum Y limits:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        cal_ylim_frame = ttk.Frame(proc_frame)
        cal_ylim_frame.grid(row=row, column=1, padx=5, pady=2, sticky=tk.W)
        self.analysis_cal_ylim_low = ttk.Entry(cal_ylim_frame, width=9)
        self.analysis_cal_ylim_low.pack(side=tk.LEFT)
        ttk.Label(cal_ylim_frame, text=" to ").pack(side=tk.LEFT)
        self.analysis_cal_ylim_high = ttk.Entry(cal_ylim_frame, width=9)
        self.analysis_cal_ylim_high.pack(side=tk.LEFT)
        row += 1

        # Output file
        ttk.Label(proc_frame, text="Output plot file:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.analysis_plot_file = ttk.Entry(proc_frame, width=20)
        self.analysis_plot_file.grid(row=row, column=1, padx=5, pady=2)
        self.analysis_plot_file.insert(0, "analysis_plot.png")

        proc_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        proc_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Buttons
        btn_frame = ttk.Frame(top_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(btn_frame, text="Generate Plot", command=self.generate_plot).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Export FITS", command=self.export_fits).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Export CSV", command=self.export_csv).pack(side=tk.LEFT, padx=5)

        # Plot display
        plot_frame = ttk.LabelFrame(self.analysis_tab, text="Generated Plot")
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.analysis_fig = Figure(figsize=(10, 8), dpi=100)
        self.analysis_canvas = FigureCanvasTkAgg(self.analysis_fig, master=plot_frame)
        self.analysis_canvas.draw()
        self.analysis_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(self.analysis_canvas, plot_frame)
        toolbar.update()

    def manage_rfi_ranges(self):
        """Manage RFI blanking frequency ranges"""
        rfi_window = tk.Toplevel(self.root)
        rfi_window.title("RFI Frequency Blanking")
        rfi_window.geometry("500x400")

        ttk.Label(rfi_window, text="RFI Frequency Ranges to Blank", font=('Arial', 11, 'bold')).pack(pady=10)

        # List of ranges
        list_frame = ttk.Frame(rfi_window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        rfi_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        rfi_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=rfi_listbox.yview)

        # Populate listbox
        for rfi_range in self.rfi_ranges:
            rfi_listbox.insert(tk.END, f"{rfi_range[0]} - {rfi_range[1]} Hz")

        # Add range controls
        add_frame = ttk.LabelFrame(rfi_window, text="Add Range")
        add_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(add_frame, text="Low Freq (Hz):").grid(row=0, column=0, padx=5, pady=5)
        low_entry = ttk.Entry(add_frame, width=20)
        low_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(add_frame, text="High Freq (Hz):").grid(row=1, column=0, padx=5, pady=5)
        high_entry = ttk.Entry(add_frame, width=20)
        high_entry.grid(row=1, column=1, padx=5, pady=5)

        def add_range():
            try:
                low = float(low_entry.get())
                high = float(high_entry.get())
                if low >= high:
                    messagebox.showerror("Error", "Low frequency must be less than high frequency")
                    return
                self.rfi_ranges.append((low, high))
                rfi_listbox.insert(tk.END, f"{low} - {high} Hz")
                low_entry.delete(0, tk.END)
                high_entry.delete(0, tk.END)
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers")

        def remove_range():
            selection = rfi_listbox.curselection()
            if selection:
                idx = selection[0]
                rfi_listbox.delete(idx)
                self.rfi_ranges.pop(idx)

        def clear_all():
            rfi_listbox.delete(0, tk.END)
            self.rfi_ranges.clear()

        btn_frame = ttk.Frame(add_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)

        ttk.Button(btn_frame, text="Add", command=add_range).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Remove Selected", command=remove_range).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear All", command=clear_all).pack(side=tk.LEFT, padx=5)

        ttk.Button(rfi_window, text="Close", command=rfi_window.destroy).pack(pady=10)

    def log_status(self, message):
        """Log a status message with timestamp"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.status_text.see(tk.END)
            self.status_text.update_idletasks()
        except:
            pass  # Ignore errors if widget is destroyed

    def start_observation(self):
        """Start an observation"""
        try:
            # Validate required parameters
            if not all([self.frequency.get(), self.bandwidth.get(),
                       self.channels.get(), self.t_sample.get()]):
                messagebox.showerror("Error", "Please fill in all required parameters (marked with *)")
                return

            # Build observation parameters
            obs_params = {
                'dev_args': self.dev_args.get() or '',
                'rf_gain': float(self.rf_gain.get()) if self.rf_gain.get() else 30,
                'if_gain': float(self.if_gain.get()) if self.if_gain.get() else 25,
                'bb_gain': float(self.bb_gain.get()) if self.bb_gain.get() else 18,
                'frequency': float(self.frequency.get()),
                'bandwidth': float(self.bandwidth.get()),
                'channels': int(self.channels.get()),
                't_sample': float(self.t_sample.get()),
                'duration': float(self.duration.get()) if self.duration.get() else 60,
            }

            # Add observer location if provided
            if self.obs_lat.get() and self.obs_lon.get():
                obs_params['loc'] = f"{self.obs_lat.get()}, {self.obs_lon.get()}, {self.obs_height.get() or '0'}"

            # Add target coordinates if provided
            coord_type = self.coord_type.get()
            if coord_type == 'Equatorial (RA/Dec)':
                if self.ra_entry.get() and self.dec_entry.get():
                    obs_params['ra_dec'] = f"{self.ra_entry.get()}, {self.dec_entry.get()}"
            elif coord_type == 'Horizontal (Az/Alt)':
                if self.az_entry.get() and self.alt_entry.get():
                    obs_params['az_alt'] = f"{self.az_entry.get()}, {self.alt_entry.get()}"

            obs_file = self.obs_file.get() or "observation.dat"
            start_in = float(self.start_in.get()) if self.start_in.get() else 0

            # Get spectrometer type
            spec_type = 'wola' if 'WOLA' in self.spectrometer_type.get() else 'ftf'

            self.log_status(f"Starting observation: {obs_file}")
            self.log_status(f"Spectrometer: {spec_type.upper()}")
            self.log_status(f"Frequency: {obs_params['frequency']/1e6:.2f} MHz, BW: {obs_params['bandwidth']/1e6:.2f} MHz")

            # Disable start button, enable stop
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.is_observing = True

            # Run observation in separate thread
            self.observation_thread = threading.Thread(
                target=self._run_observation,
                args=(obs_params, spec_type, obs_file, start_in)
            )
            self.observation_thread.daemon = True
            self.observation_thread.start()

            # Start monitoring thread for live updates
            self.monitor_thread = threading.Thread(target=self._monitor_observation, args=(obs_file,))
            self.monitor_thread.daemon = True
            self.monitor_thread.start()

        except ValueError as e:
            messagebox.showerror("Error", f"Invalid parameter value: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start observation: {e}")
            self.log_status(f"Error: {e}")

    def _run_observation(self, obs_params, spectrometer, obs_file, start_in):
        """Run the observation (in separate thread)"""
        try:
            observe(obs_params, spectrometer=spectrometer, obs_file=obs_file, start_in=start_in)
            self.root.after(0, self.log_status, f"Observation complete: {obs_file}")
            self.current_obs_file = obs_file
        except Exception as e:
            self.root.after(0, self.log_status, f"Observation failed: {e}")
            self.root.after(0, messagebox.showerror, "Observation Error", str(e))
        finally:
            self.is_observing = False
            self.root.after(0, self._observation_complete)

    def _monitor_observation(self, obs_file):
        """Monitor observation progress and update live plot"""
        last_size = 0
        while self.is_observing:
            try:
                if os.path.exists(obs_file):
                    current_size = os.path.getsize(obs_file)
                    if current_size > last_size:
                        self.root.after(0, self._update_live_plot, obs_file)
                        last_size = current_size
                time.sleep(2)
            except Exception as e:
                print(f"Monitor error: {e}")
                break

    def _update_live_plot(self, obs_file):
        """Update the live spectrum plot"""
        try:
            if not os.path.exists(obs_file):
                return

            # Get header info
            header_file = obs_file + '.header'
            if not os.path.exists(header_file):
                return

            # Parse header
            header = {}
            with open(header_file, 'r') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        header[key.strip()] = value.strip()

            channels = int(header.get('channels', 1024))
            bandwidth = float(header.get('bandwidth', 2.4e6))
            frequency = float(header.get('frequency', 1420e6))

            # Read data
            with open(obs_file, 'rb') as f:
                data = np.fromfile(f, dtype=np.float32)

            if len(data) == 0:
                return

            # Reshape to 2D array
            num_samples = len(data) // channels
            if num_samples == 0:
                return

            data = data[:num_samples * channels].reshape(num_samples, channels)

            # Compute average spectrum
            avg_spectrum = np.mean(data, axis=0)

            # Frequency axis
            freqs = np.linspace(frequency - bandwidth/2, frequency + bandwidth/2, channels) / 1e6

            # Update spectrum plot
            self.ax1.clear()
            self.ax1.plot(freqs, avg_spectrum, linewidth=0.8)
            self.ax1.set_title(f"Average Spectrum (Live) - {num_samples} samples")
            self.ax1.set_xlabel("Frequency (MHz)")
            self.ax1.set_ylabel("Power")
            self.ax1.grid(True, alpha=0.3)

            # Update time series
            time_series = np.mean(data, axis=1)
            times = np.arange(len(time_series))

            self.ax2.clear()
            self.ax2.plot(times, time_series, linewidth=0.8)
            self.ax2.set_title("Power vs Time (Live)")
            self.ax2.set_xlabel("Sample")
            self.ax2.set_ylabel("Average Power")
            self.ax2.grid(True, alpha=0.3)

            self.fig.tight_layout()
            self.canvas.draw()

        except Exception as e:
            print(f"Plot update error: {e}")

    def _observation_complete(self):
        """Called when observation completes"""
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def stop_observation(self):
        """Stop the current observation"""
        self.is_observing = False
        self.log_status("Stopping observation...")

    def load_hi_preset(self):
        """Load HI line preset parameters"""
        self.frequency.delete(0, tk.END)
        self.frequency.insert(0, "1420405752")
        self.bandwidth.delete(0, tk.END)
        self.bandwidth.insert(0, "2400000")
        self.channels.delete(0, tk.END)
        self.channels.insert(0, "2048")
        self.analysis_rest_freq.delete(0, tk.END)
        self.analysis_rest_freq.insert(0, "1420405752")
        self.log_status("Loaded HI line preset (21 cm)")

    def load_preset(self, preset_type):
        """Load calibration presets"""
        if preset_type == "HI":
            self.load_hi_preset()
        elif preset_type == "continuum":
            self.frequency.delete(0, tk.END)
            self.frequency.insert(0, "1400000000")
            self.bandwidth.delete(0, tk.END)
            self.bandwidth.insert(0, "2400000")
            self.log_status("Loaded continuum preset (1400 MHz)")

    def browse_cal_file(self):
        """Browse for calibration file"""
        filename = filedialog.askopenfilename(
            title="Select Calibration File",
            filetypes=[("DAT files", "*.dat"), ("All files", "*.*")]
        )
        if filename:
            self.cal_file_entry.delete(0, tk.END)
            self.cal_file_entry.insert(0, filename)
            self.current_cal_file = filename

    def browse_obs_file(self):
        """Browse for observation file"""
        filename = filedialog.askopenfilename(
            title="Select Observation File",
            filetypes=[("DAT files", "*.dat"), ("All files", "*.*")]
        )
        if filename:
            self.analysis_obs_file.delete(0, tk.END)
            self.analysis_obs_file.insert(0, filename)

    def browse_analysis_cal_file(self):
        """Browse for calibration file in analysis tab"""
        filename = filedialog.askopenfilename(
            title="Select Calibration File",
            filetypes=[("DAT files", "*.dat"), ("All files", "*.*")]
        )
        if filename:
            self.analysis_cal_file.delete(0, tk.END)
            self.analysis_cal_file.insert(0, filename)

    def start_calibration_obs(self):
        """Start a calibration observation"""
        cal_filename = f"calibration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.dat"
        self.obs_file.delete(0, tk.END)
        self.obs_file.insert(0, cal_filename)

        self.log_status("Starting calibration observation...")
        self.log_status("Point your antenna at a cold sky region!")

        self.notebook.select(0)
        self.start_observation()

    def generate_plot(self):
        """Generate analysis plot"""
        try:
            obs_file = self.analysis_obs_file.get()
            if not obs_file or not os.path.exists(obs_file):
                messagebox.showerror("Error", "Please select a valid observation file")
                return

            plot_args = {
                'obs_file': obs_file,
                'plot_file': self.analysis_plot_file.get() or "analysis_plot.png",
            }

            # Add calibration if specified
            cal_file = self.analysis_cal_file.get()
            if cal_file and os.path.exists(cal_file):
                plot_args['cal_file'] = cal_file

            # Add processing options
            if self.analysis_median_freq.get():
                plot_args['n'] = int(self.analysis_median_freq.get())
            if self.analysis_median_time.get():
                plot_args['m'] = int(self.analysis_median_time.get())
            if self.analysis_db.get():
                plot_args['dB'] = True
            if self.analysis_rest_freq.get():
                plot_args['f_rest'] = float(self.analysis_rest_freq.get())
            if self.analysis_dm.get():
                plot_args['dm'] = float(self.analysis_dm.get())
            if self.analysis_vlsr.get():
                plot_args['vlsr'] = True
            if self.analysis_meta.get():
                plot_args['meta'] = True
            if self.analysis_slope_corr.get():
                plot_args['slope_correction'] = True

            # Add RFI blanking ranges
            if self.rfi_ranges:
                plot_args['rfi'] = self.rfi_ranges

            # Add axis limits if provided
            if self.analysis_xlim_low.get() and self.analysis_xlim_high.get():
                plot_args['xlim'] = [float(self.analysis_xlim_low.get()), float(self.analysis_xlim_high.get())]
            if self.analysis_ylim_low.get() and self.analysis_ylim_high.get():
                plot_args['ylim'] = [float(self.analysis_ylim_low.get()), float(self.analysis_ylim_high.get())]
            if self.analysis_avg_ylim_low.get() and self.analysis_avg_ylim_high.get():
                plot_args['avg_ylim'] = [float(self.analysis_avg_ylim_low.get()), float(self.analysis_avg_ylim_high.get())]
            if self.analysis_cal_ylim_low.get() and self.analysis_cal_ylim_high.get():
                plot_args['cal_ylim'] = [float(self.analysis_cal_ylim_low.get()), float(self.analysis_cal_ylim_high.get())]

            self.log_status("Generating plot...")
            plot(**plot_args)

            # Load and display the plot
            try:
                from PIL import Image
                img = Image.open(plot_args['plot_file'])

                self.analysis_fig.clear()
                ax = self.analysis_fig.add_subplot(111)
                ax.imshow(img)
                ax.axis('off')
                self.analysis_canvas.draw()
            except ImportError:
                # Pillow not available, just show success message
                pass

            self.log_status(f"Plot generated: {plot_args['plot_file']}")
            messagebox.showinfo("Success", f"Plot saved to {plot_args['plot_file']}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate plot: {e}")
            self.log_status(f"Plot generation failed: {e}")

    def export_fits(self):
        """Export data to FITS format"""
        try:
            obs_file = self.analysis_obs_file.get()
            if not obs_file or not os.path.exists(obs_file):
                messagebox.showerror("Error", "Please select an observation file")
                return

            fits_file = filedialog.asksaveasfilename(
                title="Save FITS File",
                defaultextension=".fits",
                filetypes=[("FITS files", "*.fits"), ("All files", "*.*")]
            )

            if fits_file:
                plot_args = {
                    'obs_file': obs_file,
                    'waterfall_fits': fits_file,
                    'plot_file': 'temp_plot.png'
                }

                # Add calibration if available
                cal_file = self.analysis_cal_file.get()
                if cal_file and os.path.exists(cal_file):
                    plot_args['cal_file'] = cal_file

                plot(**plot_args)

                if os.path.exists('temp_plot.png'):
                    os.remove('temp_plot.png')

                self.log_status(f"FITS file saved: {fits_file}")
                messagebox.showinfo("Success", f"FITS file saved to {fits_file}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to export FITS: {e}")
            self.log_status(f"FITS export failed: {e}")

    def export_csv(self):
        """Export data to CSV format"""
        try:
            obs_file = self.analysis_obs_file.get()
            if not obs_file or not os.path.exists(obs_file):
                messagebox.showerror("Error", "Please select an observation file")
                return

            csv_file = filedialog.asksaveasfilename(
                title="Save CSV File",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )

            if csv_file:
                plot_args = {
                    'obs_file': obs_file,
                    'spectra_csv': csv_file,
                    'plot_file': 'temp_plot.png'
                }

                # Add calibration if available
                cal_file = self.analysis_cal_file.get()
                if cal_file and os.path.exists(cal_file):
                    plot_args['cal_file'] = cal_file

                plot(**plot_args)

                if os.path.exists('temp_plot.png'):
                    os.remove('temp_plot.png')

                self.log_status(f"CSV file saved: {csv_file}")
                messagebox.showinfo("Success", f"CSV file saved to {csv_file}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to export CSV: {e}")
            self.log_status(f"CSV export failed: {e}")

    def load_observation(self):
        """Load an existing observation"""
        filename = filedialog.askopenfilename(
            title="Load Observation File",
            filetypes=[("DAT files", "*.dat"), ("All files", "*.*")]
        )
        if filename:
            self.current_obs_file = filename
            self.analysis_obs_file.delete(0, tk.END)
            self.analysis_obs_file.insert(0, filename)
            self.log_status(f"Loaded observation: {filename}")
            self.notebook.select(2)

    def load_calibration(self):
        """Load a calibration file"""
        filename = filedialog.askopenfilename(
            title="Load Calibration File",
            filetypes=[("DAT files", "*.dat"), ("All files", "*.*")]
        )
        if filename:
            self.current_cal_file = filename
            self.analysis_cal_file.delete(0, tk.END)
            self.analysis_cal_file.insert(0, filename)
            self.log_status(f"Loaded calibration: {filename}")

    def show_predict(self):
        """Show source prediction tool"""
        pred_window = tk.Toplevel(self.root)
        pred_window.title("Source Position Prediction")
        pred_window.geometry("600x500")

        ttk.Label(pred_window, text="Predict Source Position", font=('Arial', 12, 'bold')).pack(pady=10)

        # Input frame
        input_frame = ttk.LabelFrame(pred_window, text="Observer Location")
        input_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(input_frame, text="Latitude (deg):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        lat_entry = ttk.Entry(input_frame, width=20)
        lat_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="Longitude (deg):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        lon_entry = ttk.Entry(input_frame, width=20)
        lon_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="Height (m):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        height_entry = ttk.Entry(input_frame, width=20)
        height_entry.grid(row=2, column=1, padx=5, pady=5)
        height_entry.insert(0, "0")

        ttk.Label(input_frame, text="Source Name:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        source_entry = ttk.Entry(input_frame, width=20)
        source_entry.grid(row=3, column=1, padx=5, pady=5)
        source_entry.insert(0, "Cas A")

        ttk.Label(input_frame, text="Date (YYYY-MM-DD):").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        date_entry = ttk.Entry(input_frame, width=20)
        date_entry.grid(row=4, column=1, padx=5, pady=5)
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        plot_sun_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(input_frame, text="Plot Sun position", variable=plot_sun_var).grid(row=5, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)

        def run_predict():
            try:
                lat = float(lat_entry.get())
                lon = float(lon_entry.get())
                height = float(height_entry.get())
                source = source_entry.get()
                date = date_entry.get() if date_entry.get() else ''
                plot_file = 'predict_plot.png'

                predict(lat=lat, lon=lon, height=height, source=source,
                       date=date, plot_sun=plot_sun_var.get(), plot_file=plot_file)

                messagebox.showinfo("Success", f"Prediction plot saved to {plot_file}")
                self.log_status(f"Generated prediction plot: {plot_file}")

            except Exception as e:
                messagebox.showerror("Error", f"Prediction failed: {e}")

        ttk.Button(input_frame, text="Generate Prediction", command=run_predict).grid(row=6, column=0, columnspan=2, pady=10)

        # Info
        info_text = """
This tool predicts the altitude and azimuth of a source
throughout the day for your observer location.

Common sources: Cas A, Cyg A, Tau A, Vir A, Sun, Moon
        """
        ttk.Label(pred_window, text=info_text, justify=tk.LEFT).pack(padx=10, pady=10)

    def show_simulate(self):
        """Show HI profile simulation"""
        sim_window = tk.Toplevel(self.root)
        sim_window.title("HI Profile Simulation")
        sim_window.geometry("500x400")

        ttk.Label(sim_window, text="Simulate HI Line Profile", font=('Arial', 12, 'bold')).pack(pady=10)

        # Input frame
        input_frame = ttk.LabelFrame(sim_window, text="Galactic Coordinates")
        input_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(input_frame, text="Galactic Longitude (deg):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        l_entry = ttk.Entry(input_frame, width=20)
        l_entry.grid(row=0, column=1, padx=5, pady=5)
        l_entry.insert(0, "0")

        ttk.Label(input_frame, text="Galactic Latitude (deg):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        b_entry = ttk.Entry(input_frame, width=20)
        b_entry.grid(row=1, column=1, padx=5, pady=5)
        b_entry.insert(0, "0")

        ttk.Label(input_frame, text="Beamwidth (deg):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        bw_entry = ttk.Entry(input_frame, width=20)
        bw_entry.grid(row=2, column=1, padx=5, pady=5)
        bw_entry.insert(0, "0.6")

        ttk.Label(input_frame, text="Velocity Min (km/s):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        vmin_entry = ttk.Entry(input_frame, width=20)
        vmin_entry.grid(row=3, column=1, padx=5, pady=5)
        vmin_entry.insert(0, "-400")

        ttk.Label(input_frame, text="Velocity Max (km/s):").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        vmax_entry = ttk.Entry(input_frame, width=20)
        vmax_entry.grid(row=4, column=1, padx=5, pady=5)
        vmax_entry.insert(0, "400")

        def run_simulate():
            try:
                l = float(l_entry.get())
                b = float(b_entry.get())
                beamwidth = float(bw_entry.get())
                v_min = float(vmin_entry.get())
                v_max = float(vmax_entry.get())
                plot_file = 'simulate_plot.png'

                simulate(l=l, b=b, beamwidth=beamwidth, v_min=v_min, v_max=v_max, plot_file=plot_file)

                messagebox.showinfo("Success", f"Simulation plot saved to {plot_file}")
                self.log_status(f"Generated simulation plot: {plot_file}")

            except Exception as e:
                messagebox.showerror("Error", f"Simulation failed: {e}")

        ttk.Button(input_frame, text="Run Simulation", command=run_simulate).grid(row=5, column=0, columnspan=2, pady=10)

        # Info
        info_text = """
This simulates the HI line profile based on the
LAB HI Survey for a given galactic coordinate.

Useful for planning observations and comparing results.
        """
        ttk.Label(sim_window, text=info_text, justify=tk.LEFT).pack(padx=10, pady=10)

    def show_hi_map(self):
        """Show all-sky HI map"""
        try:
            # Get RA/Dec if available
            ra = None
            dec = None
            if self.coord_type.get() == 'Equatorial (RA/Dec)':
                if self.ra_entry.get() and self.dec_entry.get():
                    ra = float(self.ra_entry.get())
                    dec = float(self.dec_entry.get())

            plot_file = 'hi_map.png'
            map_hi(ra=ra, dec=dec, plot_file=plot_file)

            messagebox.showinfo("Success", f"HI map saved to {plot_file}")
            self.log_status(f"Generated HI map: {plot_file}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate HI map: {e}")

    def show_rfi_monitor(self):
        """Show RFI monitoring tool"""
        rfi_window = tk.Toplevel(self.root)
        rfi_window.title("RFI Monitor")
        rfi_window.geometry("600x500")

        ttk.Label(rfi_window, text="RFI Monitor - Wideband Frequency Survey", font=('Arial', 12, 'bold')).pack(pady=10)

        # Frequency range
        freq_frame = ttk.LabelFrame(rfi_window, text="Frequency Range")
        freq_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(freq_frame, text="Start Frequency (Hz):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        f_lo_entry = ttk.Entry(freq_frame, width=20)
        f_lo_entry.grid(row=0, column=1, padx=5, pady=5)
        f_lo_entry.insert(0, "1400000000")

        ttk.Label(freq_frame, text="End Frequency (Hz):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        f_hi_entry = ttk.Entry(freq_frame, width=20)
        f_hi_entry.grid(row=1, column=1, padx=5, pady=5)
        f_hi_entry.insert(0, "1440000000")

        # Survey parameters
        params_frame = ttk.LabelFrame(rfi_window, text="Survey Parameters")
        params_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(params_frame, text="Bandwidth per step (Hz):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        bw_entry = ttk.Entry(params_frame, width=20)
        bw_entry.grid(row=0, column=1, padx=5, pady=5)
        bw_entry.insert(0, "2400000")

        ttk.Label(params_frame, text="Integration time (s):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        int_entry = ttk.Entry(params_frame, width=20)
        int_entry.grid(row=1, column=1, padx=5, pady=5)
        int_entry.insert(0, "5")

        ttk.Label(params_frame, text="Output directory:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        dir_entry = ttk.Entry(params_frame, width=20)
        dir_entry.grid(row=2, column=1, padx=5, pady=5)
        dir_entry.insert(0, "rfi_data")

        status_label = ttk.Label(rfi_window, text="", foreground="blue")
        status_label.pack(pady=5)

        def start_rfi_monitor():
            try:
                f_lo = float(f_lo_entry.get())
                f_hi = float(f_hi_entry.get())
                bw = float(bw_entry.get())
                duration = float(int_entry.get())
                data_dir = dir_entry.get()

                # Build observation parameters from main window
                obs_params = {
                    'dev_args': self.dev_args.get() or '',
                    'rf_gain': float(self.rf_gain.get()) if self.rf_gain.get() else 30,
                    'if_gain': float(self.if_gain.get()) if self.if_gain.get() else 25,
                    'bb_gain': float(self.bb_gain.get()) if self.bb_gain.get() else 18,
                    'bandwidth': bw,
                    'channels': int(self.channels.get()) if self.channels.get() else 2048,
                    't_sample': float(self.t_sample.get()) if self.t_sample.get() else 1.0,
                    'duration': duration,
                }

                status_label.config(text="Starting RFI survey... This may take several minutes.")
                rfi_window.update()

                # Run in thread to avoid blocking GUI
                def run_rfi():
                    try:
                        monitor_rfi(f_lo=f_lo, f_hi=f_hi, obs_parameters=obs_params, data=data_dir)
                        self.root.after(0, lambda: status_label.config(text="Survey complete! Generating plot..."))

                        # Generate plot
                        rfi_params = obs_params.copy()
                        rfi_params['f_lo'] = f_lo
                        plot_rfi(rfi_parameters=rfi_params, data=data_dir, dB=True, plot_file='rfi_plot.png')

                        self.root.after(0, lambda: messagebox.showinfo("Success", "RFI survey complete! Plot saved to rfi_plot.png"))
                        self.root.after(0, lambda: self.log_status(f"RFI survey completed: rfi_plot.png"))
                    except Exception as e:
                        self.root.after(0, lambda: messagebox.showerror("Error", f"RFI survey failed: {e}"))

                thread = threading.Thread(target=run_rfi)
                thread.daemon = True
                thread.start()

            except Exception as e:
                messagebox.showerror("Error", f"Invalid parameters: {e}")

        ttk.Button(rfi_window, text="Start RFI Survey", command=start_rfi_monitor).pack(pady=10)

        # Info
        info_text = """
This performs a wideband frequency sweep to identify
radio frequency interference in your environment.

WARNING: This can take a long time depending on the frequency range!
        """
        ttk.Label(rfi_window, text=info_text, justify=tk.LEFT, foreground="red").pack(padx=10, pady=10)

    def show_antenna_calc(self):
        """Show antenna calculator tools"""
        calc_window = tk.Toplevel(self.root)
        calc_window.title("Antenna Calculator")
        calc_window.geometry("700x600")

        ttk.Label(calc_window, text="Antenna & System Calculator", font=('Arial', 12, 'bold')).pack(pady=10)

        # Create notebook for different calculators
        calc_notebook = ttk.Notebook(calc_window)
        calc_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Gain calculator
        gain_tab = ttk.Frame(calc_notebook)
        calc_notebook.add(gain_tab, text="Gain")

        ttk.Label(gain_tab, text="Parabolic Antenna Gain", font=('Arial', 10, 'bold')).pack(pady=10)

        gain_frame = ttk.Frame(gain_tab)
        gain_frame.pack(padx=10, pady=10)

        ttk.Label(gain_frame, text="Diameter (m):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        d_entry = ttk.Entry(gain_frame, width=20)
        d_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(gain_frame, text="Frequency (Hz):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        f_entry = ttk.Entry(gain_frame, width=20)
        f_entry.grid(row=1, column=1, padx=5, pady=5)
        f_entry.insert(0, "1420405752")

        ttk.Label(gain_frame, text="Efficiency (0-1):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        e_entry = ttk.Entry(gain_frame, width=20)
        e_entry.grid(row=2, column=1, padx=5, pady=5)
        e_entry.insert(0, "0.7")

        result_gain = ttk.Label(gain_frame, text="", font=('Arial', 10, 'bold'), foreground="blue")
        result_gain.grid(row=3, column=0, columnspan=2, pady=10)

        def calc_gain():
            try:
                D = float(d_entry.get())
                f = float(f_entry.get())
                e = float(e_entry.get())
                g = gain(D=D, f=f, e=e, u='dBi')
                result_gain.config(text=f"Gain: {g:.2f} dBi")
            except Exception as ex:
                result_gain.config(text=f"Error: {ex}")

        ttk.Button(gain_frame, text="Calculate", command=calc_gain).grid(row=4, column=0, columnspan=2, pady=5)

        # Beamwidth calculator
        bw_tab = ttk.Frame(calc_notebook)
        calc_notebook.add(bw_tab, text="Beamwidth")

        ttk.Label(bw_tab, text="Half-Power Beamwidth (FWHM)", font=('Arial', 10, 'bold')).pack(pady=10)

        bw_frame = ttk.Frame(bw_tab)
        bw_frame.pack(padx=10, pady=10)

        ttk.Label(bw_frame, text="Diameter (m):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        bw_d_entry = ttk.Entry(bw_frame, width=20)
        bw_d_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(bw_frame, text="Frequency (Hz):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        bw_f_entry = ttk.Entry(bw_frame, width=20)
        bw_f_entry.grid(row=1, column=1, padx=5, pady=5)
        bw_f_entry.insert(0, "1420405752")

        result_bw = ttk.Label(bw_frame, text="", font=('Arial', 10, 'bold'), foreground="blue")
        result_bw.grid(row=2, column=0, columnspan=2, pady=10)

        def calc_bw():
            try:
                D = float(bw_d_entry.get())
                f = float(bw_f_entry.get())
                bw = beamwidth(D=D, f=f)
                result_bw.config(text=f"Beamwidth: {bw:.2f}°")
            except Exception as ex:
                result_bw.config(text=f"Error: {ex}")

        ttk.Button(bw_frame, text="Calculate", command=calc_bw).grid(row=3, column=0, columnspan=2, pady=5)

        # SEFD calculator
        sefd_tab = ttk.Frame(calc_notebook)
        calc_notebook.add(sefd_tab, text="SEFD")

        ttk.Label(sefd_tab, text="System Equivalent Flux Density", font=('Arial', 10, 'bold')).pack(pady=10)

        sefd_frame = ttk.Frame(sefd_tab)
        sefd_frame.pack(padx=10, pady=10)

        ttk.Label(sefd_frame, text="Effective Aperture (m²):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ae_entry = ttk.Entry(sefd_frame, width=20)
        ae_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(sefd_frame, text="System Temp (K):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        tsys_entry = ttk.Entry(sefd_frame, width=20)
        tsys_entry.grid(row=1, column=1, padx=5, pady=5)
        tsys_entry.insert(0, "100")

        result_sefd = ttk.Label(sefd_frame, text="", font=('Arial', 10, 'bold'), foreground="blue")
        result_sefd.grid(row=2, column=0, columnspan=2, pady=10)

        def calc_sefd():
            try:
                ae = float(ae_entry.get())
                tsys = float(tsys_entry.get())
                s = SEFD(A_e=ae, T_sys=tsys)
                result_sefd.config(text=f"SEFD: {s:.2f} Jy")
            except Exception as ex:
                result_sefd.config(text=f"Error: {ex}")

        ttk.Button(sefd_frame, text="Calculate", command=calc_sefd).grid(row=3, column=0, columnspan=2, pady=5)

        # SNR calculator
        snr_tab = ttk.Frame(calc_notebook)
        calc_notebook.add(snr_tab, text="SNR")

        ttk.Label(snr_tab, text="Signal-to-Noise Ratio (Radiometer Equation)", font=('Arial', 10, 'bold')).pack(pady=10)

        snr_frame = ttk.Frame(snr_tab)
        snr_frame.pack(padx=10, pady=10)

        ttk.Label(snr_frame, text="Source Flux (Jy):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        s_entry = ttk.Entry(snr_frame, width=20)
        s_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(snr_frame, text="SEFD (Jy):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        sefd_snr_entry = ttk.Entry(snr_frame, width=20)
        sefd_snr_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(snr_frame, text="Integration Time (s):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        t_entry = ttk.Entry(snr_frame, width=20)
        t_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(snr_frame, text="Bandwidth (Hz):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        bw_snr_entry = ttk.Entry(snr_frame, width=20)
        bw_snr_entry.grid(row=3, column=1, padx=5, pady=5)
        bw_snr_entry.insert(0, "2400000")

        result_snr = ttk.Label(snr_frame, text="", font=('Arial', 10, 'bold'), foreground="blue")
        result_snr.grid(row=4, column=0, columnspan=2, pady=10)

        def calc_snr():
            try:
                S = float(s_entry.get())
                sefd_val = float(sefd_snr_entry.get())
                t = float(t_entry.get())
                bw = float(bw_snr_entry.get())
                s = snr(S=S, sefd=sefd_val, t=t, bw=bw)
                result_snr.config(text=f"SNR: {s:.2f}")
            except Exception as ex:
                result_snr.config(text=f"Error: {ex}")

        ttk.Button(snr_frame, text="Calculate", command=calc_snr).grid(row=5, column=0, columnspan=2, pady=5)

    def show_coord_converter(self):
        """Show coordinate conversion tool"""
        coord_window = tk.Toplevel(self.root)
        coord_window.title("Coordinate Converter")
        coord_window.geometry("600x500")

        ttk.Label(coord_window, text="Coordinate Converter", font=('Arial', 12, 'bold')).pack(pady=10)

        # Alt/Az to RA/Dec
        eq_frame = ttk.LabelFrame(coord_window, text="Horizontal → Equatorial")
        eq_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(eq_frame, text="Altitude (deg):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        alt_eq = ttk.Entry(eq_frame, width=20)
        alt_eq.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(eq_frame, text="Azimuth (deg):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        az_eq = ttk.Entry(eq_frame, width=20)
        az_eq.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(eq_frame, text="Observer Lat (deg):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        lat_eq = ttk.Entry(eq_frame, width=20)
        lat_eq.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(eq_frame, text="Observer Lon (deg):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        lon_eq = ttk.Entry(eq_frame, width=20)
        lon_eq.grid(row=3, column=1, padx=5, pady=5)

        ttk.Label(eq_frame, text="Observer Height (m):").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        height_eq = ttk.Entry(eq_frame, width=20)
        height_eq.grid(row=4, column=1, padx=5, pady=5)
        height_eq.insert(0, "0")

        result_eq = ttk.Label(eq_frame, text="", font=('Arial', 10, 'bold'), foreground="blue")
        result_eq.grid(row=5, column=0, columnspan=2, pady=10)

        def convert_to_eq():
            try:
                alt = float(alt_eq.get())
                az = float(az_eq.get())
                lat = float(lat_eq.get())
                lon = float(lon_eq.get())
                height = float(height_eq.get())
                ra, dec = equatorial(alt=alt, az=az, lat=lat, lon=lon, height=height)
                result_eq.config(text=f"RA: {ra:.4f} hr, Dec: {dec:.4f}°")
            except Exception as ex:
                result_eq.config(text=f"Error: {ex}")

        ttk.Button(eq_frame, text="Convert", command=convert_to_eq).grid(row=6, column=0, columnspan=2, pady=5)

        # RA/Dec to Galactic
        gal_frame = ttk.LabelFrame(coord_window, text="Equatorial → Galactic")
        gal_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(gal_frame, text="RA (hours):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ra_gal = ttk.Entry(gal_frame, width=20)
        ra_gal.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(gal_frame, text="Dec (deg):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        dec_gal = ttk.Entry(gal_frame, width=20)
        dec_gal.grid(row=1, column=1, padx=5, pady=5)

        result_gal = ttk.Label(gal_frame, text="", font=('Arial', 10, 'bold'), foreground="blue")
        result_gal.grid(row=2, column=0, columnspan=2, pady=10)

        def convert_to_gal():
            try:
                ra = float(ra_gal.get())
                dec = float(dec_gal.get())
                l, b = galactic(ra=ra, dec=dec)
                result_gal.config(text=f"l: {l:.4f}°, b: {b:.4f}°")
            except Exception as ex:
                result_gal.config(text=f"Error: {ex}")

        ttk.Button(gal_frame, text="Convert", command=convert_to_gal).grid(row=3, column=0, columnspan=2, pady=5)

    def show_user_guide(self):
        """Show user guide"""
        guide_window = tk.Toplevel(self.root)
        guide_window.title("User Guide")
        guide_window.geometry("700x600")

        text = scrolledtext.ScrolledText(guide_window, wrap=tk.WORD, width=80, height=35)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        guide_text = """
VIRGO RADIO TELESCOPE GUI - USER GUIDE

=== GETTING STARTED ===

1. OBSERVATION TAB
   - Set spectrometer type (WOLA recommended for better performance)
   - Configure SDR parameters (gains, device args)
   - Set frequency, bandwidth, and channels
   - Optionally add observer location and target coordinates
   - Click "Start Observation" to begin
   - Watch live spectrum display update in real-time

2. CALIBRATION TAB
   - Point antenna at cold sky region
   - Click "Start Calibration Observation"
   - Save calibration file for later use
   - Use same settings for target observations

3. ANALYSIS TAB
   - Load observation and calibration files
   - Configure RFI mitigation (median filters, frequency blanking)
   - Set display options (dB scale, VLSR, metadata)
   - Customize axis limits if needed
   - Click "Generate Plot" for final analysis
   - Export to FITS or CSV as needed

=== TOOLS ===

- Predict Source Position: Calculate Alt/Az for any source
- Simulate HI Profile: Preview expected HI line shape
- View HI Map: See all-sky neutral hydrogen distribution
- Monitor RFI: Survey frequency range for interference
- Antenna Calculator: Compute gain, beamwidth, SEFD, SNR
- Coordinate Converter: Transform between coordinate systems

=== TIPS ===

• Start with HI Line preset for first observation
• Calibrate regularly (daily recommended)
• Use median filtering to remove RFI
• Longer integration = better sensitivity
• Monitor live display for issues
• Save important calibration files

=== KEYBOARD SHORTCUTS ===

Ctrl+O: Load observation
Ctrl+C: Load calibration
Ctrl+Q: Quit

For more information, visit: https://virgo.readthedocs.io
        """

        text.insert(tk.END, guide_text)
        text.config(state=tk.DISABLED)

    def show_about(self):
        """Show about dialog"""
        about_text = """
Virgo Radio Telescope GUI - Enhanced
Version 2.0

A comprehensive graphical interface for the Virgo
spectrometer and radiometer with all features from
the command-line tool.

Features:
• Complete parameter configuration
• Live spectrum visualization
• Advanced RFI mitigation
• Multiple spectrometer types (WOLA/FTF)
• Observer location and target coordinates
• Prediction and simulation tools
• Antenna calculators
• Coordinate conversion
• FITS/CSV export

Created for radio astronomy education and research.

Virgo: Apostolos Spanakis-Misirlis (@0xCoto)
GUI: Enhanced version with 100% feature coverage

Documentation: https://virgo.readthedocs.io
GitHub: https://github.com/0xCoto/Virgo
        """
        messagebox.showinfo("About Virgo GUI", about_text)

    def on_closing(self):
        """Handle window closing"""
        if self.is_observing or self.is_monitoring_rfi:
            if messagebox.askokcancel("Quit", "Observation in progress. Really quit?"):
                self.is_observing = False
                self.is_monitoring_rfi = False
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    """Main entry point"""
    root = tk.Tk()
    try:
        app = VirgoGUI(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Fatal Error", f"Failed to start GUI: {e}\n\nMake sure Virgo is properly installed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
