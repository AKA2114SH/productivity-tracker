"""
Productivity Tracker with Activity Monitoring
Features: Clock In/Out, Break tracking, Idle detection, Auto-start on boot,
          System sleep/shutdown detection
Requirements: pip install pynput
Optional: pip install pywin32 (for Windows enhanced features)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import time
import threading
import json
import os
import sys
import platform
from datetime import datetime, timedelta
from pynput import mouse, keyboard

if platform.system() == 'Windows':
    try:
        import win32api
        import win32con
        import win32gui
        import win32ts
        import ctypes
        WINDOWS_ADVANCED = True
    except ImportError:
        WINDOWS_ADVANCED = False
        print("⚠️  pywin32 not installed. Advanced Windows features disabled.")
        print("   Install with: pip install pywin32")

# Configuration
CONFIG_FILE = "tracker_config.json"
LOG_FILE = "activity_log.json"

class ProductivityTracker:
    def __init__(self):
        # State variables
        self.is_logged_in = False
        self.is_on_break = False
        self.last_activity_time = time.time()
        self.clock_in_time = None
        self.break_start_time = None
        self.total_active_time = 0
        self.total_break_time = 0
        
        # Configuration
        self.idle_timeout_seconds = 300  # 5 minutes
        self.check_interval_seconds = 10
        
        # Activity listeners
        self.mouse_listener = None
        self.keyboard_listener = None
        self.idle_checker_thread = None
        self.ui_updater_thread = None
        self.running = True
        
        # Activity log
        self.activity_log = []
        
        # Load previous state
        self.load_state()
        
        # Setup UI
        self.setup_ui()
        
        # Check for unexpected shutdown
        self.check_unexpected_shutdown()
        
    def setup_ui(self):
        self.root = tk.Tk()
        self.root.title("Productivity Tracker")
        self.root.geometry("600x700")
        self.root.configure(bg="#f5f5f5")
        
        # Make window stay on top initially
        self.root.attributes('-topmost', True)
        self.root.after(2000, lambda: self.root.attributes('-topmost', False))
        
        # Main frame
        main_frame = tk.Frame(self.root, bg="#f5f5f5", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title = tk.Label(main_frame, text="⏱️ Productivity Tracker", 
                        font=("Arial", 20, "bold"), bg="#f5f5f5", fg="#2196F3")
        title.pack(pady=10)
        
        # Status frame
        status_frame = tk.LabelFrame(main_frame, text="Current Status", 
                                    font=("Arial", 12, "bold"), bg="white", padx=15, pady=15)
        status_frame.pack(fill=tk.X, pady=10)
        
        # Status badge
        self.status_label = tk.Label(status_frame, text="⚫ Logged Out", 
                                     font=("Arial", 14, "bold"), bg="white", fg="#666")
        self.status_label.pack(pady=5)
        
        # Time displays
        time_frame = tk.Frame(status_frame, bg="white")
        time_frame.pack(fill=tk.X, pady=10)
        
        self.active_time_label = tk.Label(time_frame, text="Active: 00:00:00", 
                                          font=("Arial", 12), bg="white")
        self.active_time_label.pack(side=tk.LEFT, expand=True)
        
        self.idle_time_label = tk.Label(time_frame, text="Idle: 00:00:00", 
                                       font=("Arial", 12), bg="white")
        self.idle_time_label.pack(side=tk.LEFT, expand=True)
        
        self.last_activity_label = tk.Label(status_frame, text="Last activity: Never", 
                                           font=("Arial", 10), bg="white", fg="#666")
        self.last_activity_label.pack(pady=5)
        
        # Control buttons
        control_frame = tk.Frame(main_frame, bg="#f5f5f5")
        control_frame.pack(pady=15)
        
        self.clock_in_btn = tk.Button(control_frame, text="▶️ Clock In", 
                                      command=self.clock_in, font=("Arial", 12, "bold"),
                                      bg="#4CAF50", fg="white", padx=20, pady=10,
                                      cursor="hand2", relief=tk.RAISED, bd=3)
        self.clock_in_btn.pack(side=tk.LEFT, padx=5)
        
        self.break_btn = tk.Button(control_frame, text="⏸️ Break", 
                                   command=self.take_break, font=("Arial", 12, "bold"),
                                   bg="#FF9800", fg="white", padx=20, pady=10,
                                   cursor="hand2", relief=tk.RAISED, bd=3, state=tk.DISABLED)
        self.break_btn.pack(side=tk.LEFT, padx=5)
        
        self.clock_out_btn = tk.Button(control_frame, text="⏹️ Clock Out", 
                                       command=self.clock_out, font=("Arial", 12, "bold"),
                                       bg="#F44336", fg="white", padx=20, pady=10,
                                       cursor="hand2", relief=tk.RAISED, bd=3, state=tk.DISABLED)
        self.clock_out_btn.pack(side=tk.LEFT, padx=5)
        
        # Settings frame
        settings_frame = tk.LabelFrame(main_frame, text="Settings", 
                                      font=("Arial", 12, "bold"), bg="white", padx=15, pady=15)
        settings_frame.pack(fill=tk.X, pady=10)
        
        idle_frame = tk.Frame(settings_frame, bg="white")
        idle_frame.pack(fill=tk.X, pady=5)
        tk.Label(idle_frame, text="Idle timeout (minutes):", bg="white").pack(side=tk.LEFT)
        self.idle_timeout_var = tk.IntVar(value=5)
        idle_spinbox = tk.Spinbox(idle_frame, from_=1, to=60, textvariable=self.idle_timeout_var,
                                  width=10, command=self.update_settings)
        idle_spinbox.pack(side=tk.RIGHT)
        
        # Activity log
        log_frame = tk.LabelFrame(main_frame, text="Activity Log", 
                                 font=("Arial", 12, "bold"), bg="white", padx=10, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        log_scroll = tk.Scrollbar(log_frame)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(log_frame, height=10, width=50, 
                               yscrollcommand=log_scroll.set, font=("Courier", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        log_scroll.config(command=self.log_text.yview)
        
        # Load existing logs
        self.refresh_log_display()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        if platform.system() == 'Windows' and WINDOWS_ADVANCED:
            self.root.update_idletasks()
            self.hwnd = int(self.root.wm_frame(), 16)
    
    def setup_system_event_handlers(self):
        """Setup platform-specific system event handlers"""
        system = platform.system()
        
        if system == 'Windows':
            self.setup_windows_handlers()
        elif system == 'Darwin':  # macOS
            self.setup_macos_handlers()
        elif system == 'Linux':
            self.setup_linux_handlers()
        
        self.sleep_detector_thread = threading.Thread(
            target=self.detect_sleep_by_time_gap, daemon=True
        )
        self.sleep_detector_thread.start()
    
    def setup_windows_handlers(self):
        """Setup Windows-specific shutdown and sleep handlers"""
        if not WINDOWS_ADVANCED:
            return
        
        try:
            wc = win32gui.WNDCLASS()
            wc.lpfnWndProc = self.windows_message_handler
            wc.lpszClassName = 'ProductivityTrackerListener'
            wc.hInstance = win32api.GetModuleHandle(None)
            
            class_atom = win32gui.RegisterClass(wc)
            self.hwnd = win32gui.CreateWindow(
                class_atom,
                'ProductivityTrackerListener',
                0,  # No visible window
                0, 0, 0, 0,
                0, 0, wc.hInstance, None
            )
            
            win32ts.WTSRegisterSessionNotification(self.hwnd, win32ts.NOTIFY_FOR_THIS_SESSION)
            
            threading.Thread(target=self.windows_message_pump, daemon=True).start()
            
            self.log_activity("SYSTEM_INIT", "Windows system event monitoring enabled")
        except Exception as e:
            self.log_activity("SYSTEM_INIT", f"Windows handler setup failed: {e}")
    
    def windows_message_handler(self, hwnd, msg, wparam, lparam):
        """Handle Windows system messages"""
        try:
            if msg == win32con.WM_QUERYENDSESSION:
                self.log_activity("SHUTDOWN_WARNING", "System shutdown/logoff initiated")
                if self.is_logged_in:
                    self.clock_out(auto=True, reason="System shutdown detected")
                return True
            
            elif msg == win32con.WM_ENDSESSION:
                self.shutdown_initiated = True
                self.log_activity("SHUTDOWN_CONFIRMED", "System shutdown confirmed")
                self.save_state()
                return 0
            
            elif msg == win32con.WM_POWERBROADCAST:
                if wparam == 0x0004:  # PBT_APMSUSPEND
                    self.log_activity("SYSTEM_SUSPEND", "System entering sleep mode")
                    if self.is_logged_in:
                        self.clock_out(auto=True, reason="System sleep detected")
                
                elif wparam == 0x0012:  # PBT_APMRESUMEAUTOMATIC
                    self.log_activity("SYSTEM_RESUME", "System resumed from sleep")
                    if not self.is_logged_in:
                        self.root.after(2000, self.prompt_clock_in_after_resume)
                
                return True
            
            elif msg == 0x02B1:  # WM_WTSSESSION_CHANGE
                if wparam == win32ts.WTS_SESSION_LOCK:
                    self.log_activity("SESSION_LOCK", "Workstation locked")
                elif wparam == win32ts.WTS_SESSION_UNLOCK:
                    self.log_activity("SESSION_UNLOCK", "Workstation unlocked")
                    self.last_activity_time = time.time()
                return 0
            
        except Exception as e:
            print(f"Error in message handler: {e}")
        
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)
    
    def windows_message_pump(self):
        """Run Windows message pump"""
        try:
            win32gui.PumpMessages()
        except Exception as e:
            print(f"Message pump error: {e}")
    
    def setup_macos_handlers(self):
        """Setup macOS-specific handlers"""
        try:
            import Foundation
            import objc
            
            class SleepNotificationObserver(Foundation.NSObject):
                def init_with_tracker(self, tracker):
                    self = objc.super(SleepNotificationObserver, self).init()
                    if self is None:
                        return None
                    self.tracker = tracker
                    return self
                
                def receiveSleepNote_(self, notification):
                    self.tracker.log_activity("SYSTEM_SUSPEND", "macOS entering sleep")
                    if self.tracker.is_logged_in:
                        self.tracker.clock_out(auto=True, reason="System sleep detected")
                
                def receiveWakeNote_(self, notification):
                    self.tracker.log_activity("SYSTEM_RESUME", "macOS resumed from sleep")
                    if not self.tracker.is_logged_in:
                        self.tracker.root.after(2000, self.tracker.prompt_clock_in_after_resume)
            
            workspace = Foundation.NSWorkspace.sharedWorkspace()
            notification_center = workspace.notificationCenter()
            
            observer = SleepNotificationObserver.alloc().init_with_tracker(self)
            
            notification_center.addObserver_selector_name_object_(
                observer,
                'receiveSleepNote:',
                'NSWorkspaceWillSleepNotification',
                None
            )
            
            notification_center.addObserver_selector_name_object_(
                observer,
                'receiveWakeNote:',
                'NSWorkspaceDidWakeNotification',
                None
            )
            
            self.log_activity("SYSTEM_INIT", "macOS system event monitoring enabled")
        except ImportError:
            self.log_activity("SYSTEM_INIT", "macOS PyObjC not available, using time-gap detection")
    
    def setup_linux_handlers(self):
        """Setup Linux-specific handlers (systemd/D-Bus)"""
        try:
            import dbus
            from dbus.mainloop.glib import DBusGMainLoop
            
            DBusGMainLoop(set_as_default=True)
            bus = dbus.SystemBus()
            
            def sleep_callback(sleeping):
                if sleeping:
                    self.log_activity("SYSTEM_SUSPEND", "Linux entering sleep")
                    if self.is_logged_in:
                        self.clock_out(auto=True, reason="System sleep detected")
                else:
                    self.log_activity("SYSTEM_RESUME", "Linux resumed from sleep")
                    if not self.is_logged_in:
                        self.root.after(2000, self.prompt_clock_in_after_resume)
            
            bus.add_signal_receiver(
                sleep_callback,
                'PrepareForSleep',
                'org.freedesktop.login1.Manager',
                'org.freedesktop.login1'
            )
            
            self.log_activity("SYSTEM_INIT", "Linux D-Bus system event monitoring enabled")
        except ImportError:
            self.log_activity("SYSTEM_INIT", "D-Bus not available, using time-gap detection")
        except Exception as e:
            self.log_activity("SYSTEM_INIT", f"Linux handler setup: {e}")
    
    def detect_sleep_by_time_gap(self):
        """Universal sleep detector based on time gaps"""
        while self.running:
            current_time = time.time()
            time_gap = current_time - self.last_check_time
            
            if time_gap > 120:  # 2 minutes
                self.log_activity("SYSTEM_RESUME", 
                                f"Detected system wake (gap: {int(time_gap/60)}m)")
                
                if self.is_logged_in:
                    self.clock_out(auto=True, 
                                 reason=f"System was sleeping ({int(time_gap/60)} minutes)")
                    self.root.after(2000, self.prompt_clock_in_after_resume)
            
            self.last_check_time = current_time
            time.sleep(30)  # Check every 30 seconds
    
    def prompt_clock_in_after_resume(self):
        """Prompt user to clock in after system resume"""
        if not self.is_logged_in:
            response = messagebox.askyesno(
                "System Resumed",
                "Your system just resumed from sleep/shutdown.\n\n"
                "Would you like to clock in now?"
            )
            if response:
                self.clock_in()
        
    def update_activity_time(self):
        """Callback for pynput to update last activity timestamp"""
        self.last_activity_time = time.time()
        
    def start_activity_monitoring(self):
        """Start keyboard and mouse listeners"""
        if not self.mouse_listener:
            self.mouse_listener = mouse.Listener(
                on_move=lambda x, y: self.update_activity_time(),
                on_click=lambda x, y, button, pressed: self.update_activity_time()
            )
            self.mouse_listener.start()
        
        if not self.keyboard_listener:
            self.keyboard_listener = keyboard.Listener(
                on_press=lambda key: self.update_activity_time(),
                on_release=lambda key: self.update_activity_time()
            )
            self.keyboard_listener.start()
            
    def stop_activity_monitoring(self):
        """Stop keyboard and mouse listeners"""
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
            
    def check_idle_status(self):
        """Continuously check if user has been idle too long"""
        while self.running:
            if self.is_logged_in and not self.is_on_break:
                current_idle_time = time.time() - self.last_activity_time
                if current_idle_time > self.idle_timeout_seconds:
                    self.log_activity("IDLE_TIMEOUT", f"Idle for {int(current_idle_time/60)} minutes")
                    self.clock_out(auto=True, reason="Idle timeout")
            time.sleep(self.check_interval_seconds)
            
    def ui_updater(self):
        """Update UI elements periodically"""
        while self.running:
            if self.is_logged_in:
                self.update_time_displays()
            time.sleep(1)
            
    def update_time_displays(self):
        """Update time labels in UI"""
        if self.clock_in_time:
            if self.is_on_break:
                # Calculate active time excluding current break
                active = self.total_active_time
            else:
                # Calculate current active time
                active = self.total_active_time + (time.time() - self.clock_in_time)
            
            active_str = str(timedelta(seconds=int(active)))
            self.active_time_label.config(text=f"Active: {active_str}")
        
        # Update idle time
        idle_seconds = int(time.time() - self.last_activity_time)
        idle_str = str(timedelta(seconds=idle_seconds))
        self.idle_time_label.config(text=f"Idle: {idle_str}")
        
        # Update last activity
        if idle_seconds < 60:
            self.last_activity_label.config(text=f"Last activity: {idle_seconds}s ago")
        else:
            self.last_activity_label.config(text=f"Last activity: {idle_seconds//60}m ago")
    
    def clock_in(self):
        """Clock in to start tracking"""
        self.is_logged_in = True
        self.clock_in_time = time.time()
        self.last_activity_time = time.time()
        self.total_active_time = 0
        self.total_break_time = 0
        
        self.status_label.config(text="🟢 Active", fg="#4CAF50")
        self.clock_in_btn.config(state=tk.DISABLED)
        self.break_btn.config(state=tk.NORMAL)
        self.clock_out_btn.config(state=tk.NORMAL)
        
        self.start_activity_monitoring()
        
        # Start idle checker
        if not self.idle_checker_thread or not self.idle_checker_thread.is_alive():
            self.idle_checker_thread = threading.Thread(target=self.check_idle_status, daemon=True)
            self.idle_checker_thread.start()
        
        # Start UI updater
        if not self.ui_updater_thread or not self.ui_updater_thread.is_alive():
            self.ui_updater_thread = threading.Thread(target=self.ui_updater, daemon=True)
            self.ui_updater_thread.start()
        
        self.log_activity("CLOCK_IN", "Started work session")
        self.save_state()
        
    def take_break(self):
        """Start a break"""
        if not self.is_on_break:
            self.is_on_break = True
            self.break_start_time = time.time()
            
            # Save active time before break
            if self.clock_in_time:
                self.total_active_time += (time.time() - self.clock_in_time)
            
            self.status_label.config(text="🟡 On Break", fg="#FF9800")
            self.break_btn.config(text="▶️ Resume")
            
            self.log_activity("BREAK_START", "Started break")
            self.save_state()
        else:
            self.resume_work()
    
    def resume_work(self):
        """Resume work after break"""
        if self.is_on_break:
            # Calculate break duration
            break_duration = time.time() - self.break_start_time
            self.total_break_time += break_duration
            
            self.is_on_break = False
            self.clock_in_time = time.time()  # Reset clock in time for new active period
            self.last_activity_time = time.time()
            
            self.status_label.config(text="🟢 Active", fg="#4CAF50")
            self.break_btn.config(text="⏸️ Break")
            
            self.log_activity("BREAK_END", f"Resumed work (break: {int(break_duration/60)}m)")
            self.save_state()
    
    def clock_out(self, auto=False, reason="Manual clock out"):
        """Clock out and stop tracking"""
        if not self.is_logged_in:
            return
            
        # Calculate final times
        if self.is_on_break:
            break_duration = time.time() - self.break_start_time
            self.total_break_time += break_duration
        else:
            if self.clock_in_time:
                self.total_active_time += (time.time() - self.clock_in_time)
        
        self.is_logged_in = False
        self.is_on_break = False
        
        self.status_label.config(text="⚫ Logged Out", fg="#666")
        self.clock_in_btn.config(state=tk.NORMAL)
        self.break_btn.config(state=tk.DISABLED, text="⏸️ Break")
        self.clock_out_btn.config(state=tk.DISABLED)
        
        self.stop_activity_monitoring()
        
        # Log the session summary
        active_str = str(timedelta(seconds=int(self.total_active_time)))
        break_str = str(timedelta(seconds=int(self.total_break_time)))
        
        self.log_activity("CLOCK_OUT", 
                         f"{reason} | Active: {active_str} | Breaks: {break_str}")
        
        # Reset times
        self.clock_in_time = None
        self.total_active_time = 0
        self.total_break_time = 0
        
        self.save_state()
        
        if auto:
            messagebox.showwarning("Auto Clock Out", 
                                  f"You have been automatically clocked out due to: {reason}")
    
    def log_activity(self, event_type, details):
        """Add entry to activity log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "timestamp": timestamp,
            "event": event_type,
            "details": details
        }
        self.activity_log.append(entry)
        
        # Keep only last 100 entries
        if len(self.activity_log) > 100:
            self.activity_log = self.activity_log[-100:]
        
        self.save_log()
        self.refresh_log_display()
    
    def refresh_log_display(self):
        """Update log text widget"""
        self.log_text.delete(1.0, tk.END)
        for entry in reversed(self.activity_log[-20:]):  # Show last 20
            log_line = f"[{entry['timestamp']}] {entry['event']}: {entry['details']}\n"
            self.log_text.insert(tk.END, log_line)
    
    def update_settings(self):
        """Update settings from UI"""
        self.idle_timeout_seconds = self.idle_timeout_var.get() * 60
        self.save_state()
    
    def check_unexpected_shutdown(self):
        """Check if app was closed while logged in"""
        if hasattr(self, '_was_logged_in') and self._was_logged_in:
            self.log_activity("UNEXPECTED_SHUTDOWN", 
                            "Detected unexpected shutdown - auto-clocking in")
            messagebox.showinfo("Welcome Back", 
                              "Detected previous session was interrupted. Auto-clocking you in.")
            self.root.after(1000, self.clock_in)
    
    def save_state(self):
        """Save current state to file"""
        state = {
            "is_logged_in": self.is_logged_in,
            "is_on_break": self.is_on_break,
            "idle_timeout_minutes": self.idle_timeout_var.get(),
            "last_save": datetime.now().isoformat()
        }
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(state, f)
        except Exception as e:
            print(f"Error saving state: {e}")
    
    def load_state(self):
        """Load previous state from file"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    state = json.load(f)
                    self._was_logged_in = state.get("is_logged_in", False)
                    if "idle_timeout_minutes" in state:
                        self.idle_timeout_seconds = state["idle_timeout_minutes"] * 60
        except Exception as e:
            print(f"Error loading state: {e}")
            self._was_logged_in = False
    
    def save_log(self):
        """Save activity log to file"""
        try:
            with open(LOG_FILE, 'w') as f:
                json.dump(self.activity_log, f, indent=2)
        except Exception as e:
            print(f"Error saving log: {e}")
    
    def load_log(self):
        """Load activity log from file"""
        try:
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, 'r') as f:
                    self.activity_log = json.load(f)
        except Exception as e:
            print(f"Error loading log: {e}")
            self.activity_log = []
    
    def on_closing(self):
        """Handle window close"""
        if self.is_logged_in:
            if messagebox.askokcancel("Quit", 
                "You are still clocked in. Do you want to clock out and quit?"):
                self.clock_out(reason="Application closed")
                self.cleanup_and_exit()
        else:
            self.cleanup_and_exit()
    
    def cleanup_and_exit(self):
        """Clean up resources and exit"""
        self.running = False
        
        self.stop_activity_monitoring()
        
        if platform.system() == 'Windows' and WINDOWS_ADVANCED and self.hwnd:
            try:
                win32ts.WTSUnRegisterSessionNotification(self.hwnd)
                win32gui.DestroyWindow(self.hwnd)
            except:
                pass
        
        self.root.destroy()
    
    def run(self):
        """Start the application"""
        self.load_log()
        self.root.mainloop()

# Startup functions
def set_windows_startup(enable=True):
    """Add or remove app from Windows startup (Windows only)"""
    try:
        import winreg
        import sys
        
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "ProductivityTracker"
        app_path = os.path.abspath(sys.argv[0])
        
        if enable:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, 
                                winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
            winreg.CloseKey(key)
            print(f"✓ {app_name} added to startup")
        else:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, 
                                winreg.KEY_SET_VALUE)
            try:
                winreg.DeleteValue(key, app_name)
                print(f"✓ {app_name} removed from startup")
            except FileNotFoundError:
                print(f"✓ {app_name} was not in startup")
            winreg.CloseKey(key)
    except ImportError:
        print("⚠️  Windows registry functions not available (not on Windows)")
    except Exception as e:
        print(f"❌ Error modifying startup: {e}")

if __name__ == "__main__":
    import sys
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--enable-startup":
            set_windows_startup(True)
            sys.exit(0)
        elif sys.argv[1] == "--disable-startup":
            set_windows_startup(False)
            sys.exit(0)
    
    # Run the tracker
    app = ProductivityTracker()
    app.run()
