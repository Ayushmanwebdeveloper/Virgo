#!/usr/bin/env python3
"""
Virgo Radio Telescope GUI
A graphical user interface for the Virgo spectrometer and radiometer
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
    from virgo import observe, plot, predict, simulate
except ImportError:
    print("Error: Could not import virgo module. Make sure it's installed.")
    sys.exit(1)


class VirgoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Virgo Radio Telescope Control GUI")
        self.root.geometry("1400x900")

        # Observation state
        self.is_observing = False
        self.observation_thread = None
        self.current_obs_file = None
        self.current_cal_file = None

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
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Predict Source Position", command=self.show_predict)
        tools_menu.add_command(label="Simulate HI Profile", command=self.show_simulate)
        tools_menu.add_command(label="Monitor RFI", command=self.show_rfi_monitor)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

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

        # Parameters frame
        params_frame = ttk.LabelFrame(left_frame, text="Observation Parameters")
        params_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Add scrollbar for parameters
        canvas = tk.Canvas(params_frame)
        scrollbar = ttk.Scrollbar(params_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # SDR Settings
        ttk.Label(scrollable_frame, text="SDR Configuration", font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)

        ttk.Label(scrollable_frame, text="Device Args:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.dev_args = ttk.Entry(scrollable_frame, width=30)
        self.dev_args.grid(row=1, column=1, padx=5, pady=2)
        self.dev_args.insert(0, "rtl=0")

        ttk.Label(scrollable_frame, text="RF Gain (dB):").grid(row=2, column=0, sticky=tk.W, padx=5)
        self.rf_gain = ttk.Entry(scrollable_frame, width=30)
        self.rf_gain.grid(row=2, column=1, padx=5, pady=2)
        self.rf_gain.insert(0, "30")

        ttk.Label(scrollable_frame, text="IF Gain (dB):").grid(row=3, column=0, sticky=tk.W, padx=5)
        self.if_gain = ttk.Entry(scrollable_frame, width=30)
        self.if_gain.grid(row=3, column=1, padx=5, pady=2)
        self.if_gain.insert(0, "25")

        ttk.Label(scrollable_frame, text="BB Gain (dB):").grid(row=4, column=0, sticky=tk.W, padx=5)
        self.bb_gain = ttk.Entry(scrollable_frame, width=30)
        self.bb_gain.grid(row=4, column=1, padx=5, pady=2)
        self.bb_gain.insert(0, "18")

        # Frequency Settings
        ttk.Label(scrollable_frame, text="Frequency Configuration", font=('Arial', 10, 'bold')).grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))

        ttk.Label(scrollable_frame, text="Frequency (Hz):*").grid(row=6, column=0, sticky=tk.W, padx=5)
        self.frequency = ttk.Entry(scrollable_frame, width=30)
        self.frequency.grid(row=6, column=1, padx=5, pady=2)
        self.frequency.insert(0, "1420405752")  # HI line

        ttk.Label(scrollable_frame, text="Bandwidth (Hz):*").grid(row=7, column=0, sticky=tk.W, padx=5)
        self.bandwidth = ttk.Entry(scrollable_frame, width=30)
        self.bandwidth.grid(row=7, column=1, padx=5, pady=2)
        self.bandwidth.insert(0, "2400000")

        ttk.Label(scrollable_frame, text="Channels:*").grid(row=8, column=0, sticky=tk.W, padx=5)
        self.channels = ttk.Entry(scrollable_frame, width=30)
        self.channels.grid(row=8, column=1, padx=5, pady=2)
        self.channels.insert(0, "2048")

        # Timing Settings
        ttk.Label(scrollable_frame, text="Timing Configuration", font=('Arial', 10, 'bold')).grid(row=9, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))

        ttk.Label(scrollable_frame, text="Sample Time (s):*").grid(row=10, column=0, sticky=tk.W, padx=5)
        self.t_sample = ttk.Entry(scrollable_frame, width=30)
        self.t_sample.grid(row=10, column=1, padx=5, pady=2)
        self.t_sample.insert(0, "1.0")

        ttk.Label(scrollable_frame, text="Duration (s):").grid(row=11, column=0, sticky=tk.W, padx=5)
        self.duration = ttk.Entry(scrollable_frame, width=30)
        self.duration.grid(row=11, column=1, padx=5, pady=2)
        self.duration.insert(0, "60")

        ttk.Label(scrollable_frame, text="Start In (s):").grid(row=12, column=0, sticky=tk.W, padx=5)
        self.start_in = ttk.Entry(scrollable_frame, width=30)
        self.start_in.grid(row=12, column=1, padx=5, pady=2)
        self.start_in.insert(0, "0")

        # Output Settings
        ttk.Label(scrollable_frame, text="Output Configuration", font=('Arial', 10, 'bold')).grid(row=13, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))

        ttk.Label(scrollable_frame, text="Observation File:").grid(row=14, column=0, sticky=tk.W, padx=5)
        self.obs_file = ttk.Entry(scrollable_frame, width=30)
        self.obs_file.grid(row=14, column=1, padx=5, pady=2)
        self.obs_file.insert(0, "observation.dat")

        ttk.Label(scrollable_frame, text="Waterfall FITS:").grid(row=15, column=0, sticky=tk.W, padx=5)
        self.waterfall_fits = ttk.Entry(scrollable_frame, width=30)
        self.waterfall_fits.grid(row=15, column=1, padx=5, pady=2)
        self.waterfall_fits.insert(0, "waterfall.fits")

        ttk.Label(scrollable_frame, text="Spectra CSV:").grid(row=16, column=0, sticky=tk.W, padx=5)
        self.spectra_csv = ttk.Entry(scrollable_frame, width=30)
        self.spectra_csv.grid(row=16, column=1, padx=5, pady=2)
        self.spectra_csv.insert(0, "spectra.csv")

        ttk.Label(scrollable_frame, text="Power CSV:").grid(row=17, column=0, sticky=tk.W, padx=5)
        self.power_csv = ttk.Entry(scrollable_frame, width=30)
        self.power_csv.grid(row=17, column=1, padx=5, pady=2)
        self.power_csv.insert(0, "power.csv")

        ttk.Label(scrollable_frame, text="Plot File:").grid(row=18, column=0, sticky=tk.W, padx=5)
        self.plot_file = ttk.Entry(scrollable_frame, width=30)
        self.plot_file.grid(row=18, column=1, padx=5, pady=2)
        self.plot_file.insert(0, "plot.png")

        # Advanced Settings
        ttk.Label(scrollable_frame, text="Advanced Settings", font=('Arial', 10, 'bold')).grid(row=19, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))

        self.db_scale = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text="Use dB Scale", variable=self.db_scale).grid(row=20, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)

        ttk.Label(scrollable_frame, text="Median Filter (Freq):").grid(row=21, column=0, sticky=tk.W, padx=5)
        self.median_freq = ttk.Entry(scrollable_frame, width=30)
        self.median_freq.grid(row=21, column=1, padx=5, pady=2)

        ttk.Label(scrollable_frame, text="Median Filter (Time):").grid(row=22, column=0, sticky=tk.W, padx=5)
        self.median_time = ttk.Entry(scrollable_frame, width=30)
        self.median_time.grid(row=22, column=1, padx=5, pady=2)

        ttk.Label(scrollable_frame, text="Rest Frequency (Hz):").grid(row=23, column=0, sticky=tk.W, padx=5)
        self.rest_frequency = ttk.Entry(scrollable_frame, width=30)
        self.rest_frequency.grid(row=23, column=1, padx=5, pady=2)
        self.rest_frequency.insert(0, "1420405752")

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Control buttons
        control_frame = ttk.Frame(left_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        self.start_btn = ttk.Button(control_frame, text="Start Observation", command=self.start_observation)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(control_frame, text="Stop Observation", command=self.stop_observation, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="Load Preset: HI Line", command=self.load_hi_preset).pack(side=tk.LEFT, padx=5)

        # Right panel - Live Display
        right_frame = ttk.Frame(self.observation_tab)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Status display
        status_frame = ttk.LabelFrame(right_frame, text="Status")
        status_frame.pack(fill=tk.X, padx=5, pady=5)

        self.status_text = scrolledtext.ScrolledText(status_frame, height=8, wrap=tk.WORD)
        self.status_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_status("Virgo GUI initialized. Ready to observe.")

        # Live spectrum display
        plot_frame = ttk.LabelFrame(right_frame, text="Live Spectrum Display")
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax1 = self.fig.add_subplot(211)
        self.ax2 = self.fig.add_subplot(212)

        self.ax1.set_title("Average Spectrum")
        self.ax1.set_xlabel("Frequency (MHz)")
        self.ax1.set_ylabel("Power")
        self.ax1.grid(True)

        self.ax2.set_title("Power vs Time")
        self.ax2.set_xlabel("Time (s)")
        self.ax2.set_ylabel("Power")
        self.ax2.grid(True)

        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(self.canvas, plot_frame)
        toolbar.update()

    def setup_calibration_tab(self):
        """Setup the calibration tab"""
        # Instructions
        info_frame = ttk.LabelFrame(self.calibration_tab, text="Calibration Instructions")
        info_frame.pack(fill=tk.X, padx=10, pady=10)

        info_text = """
        Calibration Procedure:
        1. Perform an observation of a cold sky region (reference/calibration observation)
        2. Save the calibration observation file
        3. Perform your target observation
        4. Load both files in the Analysis tab to compute calibrated spectrum

        For best results:
        - Use the same observation parameters for both calibration and target
        - Point at a region with minimal radio sources for calibration
        - Calibration should be done regularly (daily recommended)
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
        preset_frame = ttk.LabelFrame(self.calibration_tab, text="Quick Calibration Settings")
        preset_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(preset_frame, text="These settings will be copied to the Observation tab:").pack(padx=10, pady=5)

        btn_frame = ttk.Frame(preset_frame)
        btn_frame.pack(padx=10, pady=5)

        ttk.Button(btn_frame, text="HI Line (1420 MHz)",
                  command=lambda: self.load_preset("HI")).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Continuum (1400 MHz)",
                  command=lambda: self.load_preset("continuum")).pack(side=tk.LEFT, padx=5)

    def setup_analysis_tab(self):
        """Setup the analysis and plotting tab"""
        # File selection
        file_frame = ttk.LabelFrame(self.analysis_tab, text="File Selection")
        file_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(file_frame, text="Observation File:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.analysis_obs_file = ttk.Entry(file_frame, width=50)
        self.analysis_obs_file.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(file_frame, text="Browse", command=self.browse_obs_file).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(file_frame, text="Calibration File:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.analysis_cal_file = ttk.Entry(file_frame, width=50)
        self.analysis_cal_file.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(file_frame, text="Browse", command=self.browse_analysis_cal_file).grid(row=1, column=2, padx=5, pady=5)

        # Processing options
        proc_frame = ttk.LabelFrame(self.analysis_tab, text="Processing Options")
        proc_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(proc_frame, text="RFI Mitigation - Median Filter (Frequency):").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.analysis_median_freq = ttk.Entry(proc_frame, width=20)
        self.analysis_median_freq.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(proc_frame, text="RFI Mitigation - Median Filter (Time):").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.analysis_median_time = ttk.Entry(proc_frame, width=20)
        self.analysis_median_time.grid(row=1, column=1, padx=5, pady=5)

        self.analysis_db = tk.BooleanVar(value=True)
        ttk.Checkbutton(proc_frame, text="Use dB Scale", variable=self.analysis_db).grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)

        ttk.Label(proc_frame, text="Rest Frequency (Hz):").grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        self.analysis_rest_freq = ttk.Entry(proc_frame, width=20)
        self.analysis_rest_freq.grid(row=3, column=1, padx=5, pady=5)
        self.analysis_rest_freq.insert(0, "1420405752")

        ttk.Label(proc_frame, text="Output Plot File:").grid(row=4, column=0, sticky=tk.W, padx=10, pady=5)
        self.analysis_plot_file = ttk.Entry(proc_frame, width=20)
        self.analysis_plot_file.grid(row=4, column=1, padx=5, pady=5)
        self.analysis_plot_file.insert(0, "analysis_plot.png")

        # Buttons
        btn_frame = ttk.Frame(self.analysis_tab)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

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

    def log_status(self, message):
        """Log a status message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)

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
                'dev_args': self.dev_args.get(),
                'rf_gain': float(self.rf_gain.get()) if self.rf_gain.get() else 30,
                'if_gain': float(self.if_gain.get()) if self.if_gain.get() else 25,
                'bb_gain': float(self.bb_gain.get()) if self.bb_gain.get() else 18,
                'frequency': float(self.frequency.get()),
                'bandwidth': float(self.bandwidth.get()),
                'channels': int(self.channels.get()),
                't_sample': float(self.t_sample.get()),
                'duration': float(self.duration.get()) if self.duration.get() else 60,
            }

            obs_file = self.obs_file.get() or "observation.dat"
            start_in = float(self.start_in.get()) if self.start_in.get() else 0

            self.log_status(f"Starting observation: {obs_file}")
            self.log_status(f"Frequency: {obs_params['frequency']/1e6:.2f} MHz, BW: {obs_params['bandwidth']/1e6:.2f} MHz")

            # Disable start button, enable stop
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.is_observing = True

            # Run observation in separate thread
            self.observation_thread = threading.Thread(
                target=self._run_observation,
                args=(obs_params, obs_file, start_in)
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

    def _run_observation(self, obs_params, obs_file, start_in):
        """Run the observation (in separate thread)"""
        try:
            observe(obs_params, obs_file=obs_file, start_in=start_in)
            self.root.after(0, self.log_status, f"Observation complete: {obs_file}")
            self.current_obs_file = obs_file

            # Auto-generate plot if enabled
            self.root.after(0, self._auto_plot)

        except Exception as e:
            self.root.after(0, self.log_status, f"Observation failed: {e}")
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
                        # Data has been updated, refresh plot
                        self.root.after(0, self._update_live_plot, obs_file)
                        last_size = current_size
                time.sleep(2)  # Update every 2 seconds
            except Exception as e:
                print(f"Monitor error: {e}")
                break

    def _update_live_plot(self, obs_file):
        """Update the live spectrum plot"""
        try:
            # Read observation data
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
            self.ax1.plot(freqs, avg_spectrum)
            self.ax1.set_title("Average Spectrum (Live)")
            self.ax1.set_xlabel("Frequency (MHz)")
            self.ax1.set_ylabel("Power")
            self.ax1.grid(True)

            # Update time series
            time_series = np.mean(data, axis=1)
            times = np.arange(len(time_series))

            self.ax2.clear()
            self.ax2.plot(times, time_series)
            self.ax2.set_title("Power vs Time (Live)")
            self.ax2.set_xlabel("Sample")
            self.ax2.set_ylabel("Average Power")
            self.ax2.grid(True)

            self.fig.tight_layout()
            self.canvas.draw()

        except Exception as e:
            print(f"Plot update error: {e}")

    def _observation_complete(self):
        """Called when observation completes"""
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def _auto_plot(self):
        """Auto-generate final plot after observation"""
        if self.current_obs_file and os.path.exists(self.current_obs_file):
            try:
                plot_file = self.plot_file.get() or "plot.png"

                # Build plot arguments
                plot_args = {
                    'obs_file': self.current_obs_file,
                    'plot_file': plot_file,
                }

                # Add optional arguments
                if self.waterfall_fits.get():
                    plot_args['waterfall_fits'] = self.waterfall_fits.get()
                if self.spectra_csv.get():
                    plot_args['spectra_csv'] = self.spectra_csv.get()
                if self.power_csv.get():
                    plot_args['power_csv'] = self.power_csv.get()
                if self.rest_frequency.get():
                    plot_args['f_rest'] = float(self.rest_frequency.get())
                if self.db_scale.get():
                    plot_args['dB'] = True
                if self.median_freq.get():
                    plot_args['n'] = int(self.median_freq.get())
                if self.median_time.get():
                    plot_args['m'] = int(self.median_time.get())

                plot(**plot_args)
                self.log_status(f"Plot generated: {plot_file}")

            except Exception as e:
                self.log_status(f"Failed to generate plot: {e}")

    def stop_observation(self):
        """Stop the current observation"""
        self.is_observing = False
        self.log_status("Stopping observation...")
        # Note: GNU Radio flowgraph doesn't have a clean stop mechanism
        # User will need to manually kill the process if needed

    def load_hi_preset(self):
        """Load HI line preset parameters"""
        self.frequency.delete(0, tk.END)
        self.frequency.insert(0, "1420405752")
        self.bandwidth.delete(0, tk.END)
        self.bandwidth.insert(0, "2400000")
        self.channels.delete(0, tk.END)
        self.channels.insert(0, "2048")
        self.rest_frequency.delete(0, tk.END)
        self.rest_frequency.insert(0, "1420405752")
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
        # Set a default calibration filename
        cal_filename = f"calibration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.dat"
        self.obs_file.delete(0, tk.END)
        self.obs_file.insert(0, cal_filename)

        self.log_status("Starting calibration observation...")
        self.log_status("Point your antenna at a cold sky region (away from the galactic plane)")

        # Switch to observation tab and start
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

            self.log_status("Generating plot...")
            plot(**plot_args)

            # Load and display the plot
            from PIL import Image
            img = Image.open(plot_args['plot_file'])

            self.analysis_fig.clear()
            ax = self.analysis_fig.add_subplot(111)
            ax.imshow(img)
            ax.axis('off')
            self.analysis_canvas.draw()

            self.log_status(f"Plot generated: {plot_args['plot_file']}")
            messagebox.showinfo("Success", f"Plot saved to {plot_args['plot_file']}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate plot: {e}")
            self.log_status(f"Plot generation failed: {e}")

    def export_fits(self):
        """Export data to FITS format"""
        try:
            obs_file = self.analysis_obs_file.get()
            if not obs_file:
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

                plot(**plot_args)

                # Clean up temp plot
                if os.path.exists('temp_plot.png'):
                    os.remove('temp_plot.png')

                self.log_status(f"FITS file saved: {fits_file}")
                messagebox.showinfo("Success", f"FITS file saved to {fits_file}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to export FITS: {e}")

    def export_csv(self):
        """Export data to CSV format"""
        try:
            obs_file = self.analysis_obs_file.get()
            if not obs_file:
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

                plot(**plot_args)

                # Clean up temp plot
                if os.path.exists('temp_plot.png'):
                    os.remove('temp_plot.png')

                self.log_status(f"CSV file saved: {csv_file}")
                messagebox.showinfo("Success", f"CSV file saved to {csv_file}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to export CSV: {e}")

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
            self.notebook.select(2)  # Switch to analysis tab

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
        # Create a new window for prediction
        pred_window = tk.Toplevel(self.root)
        pred_window.title("Source Position Prediction")
        pred_window.geometry("400x300")

        ttk.Label(pred_window, text="Source Prediction Tool", font=('Arial', 12, 'bold')).pack(pady=10)
        ttk.Label(pred_window, text="Enter source coordinates and observer location").pack(pady=5)

        # Add input fields for prediction parameters
        # This is a placeholder - full implementation would require more fields
        ttk.Label(pred_window, text="Feature coming soon...").pack(pady=20)

    def show_simulate(self):
        """Show HI profile simulation"""
        sim_window = tk.Toplevel(self.root)
        sim_window.title("HI Profile Simulation")
        sim_window.geometry("400x300")

        ttk.Label(sim_window, text="HI Line Simulation", font=('Arial', 12, 'bold')).pack(pady=10)
        ttk.Label(sim_window, text="Simulate 21 cm hydrogen line profile").pack(pady=5)

        ttk.Label(sim_window, text="Feature coming soon...").pack(pady=20)

    def show_rfi_monitor(self):
        """Show RFI monitoring tool"""
        rfi_window = tk.Toplevel(self.root)
        rfi_window.title("RFI Monitor")
        rfi_window.geometry("400x300")

        ttk.Label(rfi_window, text="RFI Monitoring", font=('Arial', 12, 'bold')).pack(pady=10)
        ttk.Label(rfi_window, text="Monitor radio frequency interference").pack(pady=5)

        ttk.Label(rfi_window, text="Feature coming soon...").pack(pady=20)

    def show_about(self):
        """Show about dialog"""
        about_text = """
Virgo Radio Telescope GUI
Version 1.0

A graphical interface for the Virgo spectrometer and radiometer.

Virgo is a versatile software-defined radio (SDR) spectrometer
for radio astronomy observations.

Documentation: https://virgo.readthedocs.io
GitHub: https://github.com/0xCoto/Virgo

Created with Python, Tkinter, and GNU Radio
        """
        messagebox.showinfo("About Virgo GUI", about_text)


def main():
    """Main entry point"""
    root = tk.Tk()
    app = VirgoGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
