"""
RateEdge v8.0 - Application Launcher
Professional Interest Rate Analytics
"""
import tkinter as tk
from tkinter import messagebox
import sys
import os

def launch():
    """Launch RateEdge v8.0"""
    try:
        print("=" * 70)
        print("  RateEdge v8.0 - Professional Edition")
        print("  Loading your application...")
        print("=" * 70)
        
        # Add paths
        app_dir = os.path.dirname(os.path.abspath(__file__))
        frontend_dir = os.path.join(app_dir, 'frontend')
        backend_dir = os.path.join(app_dir, 'backend')
        
        sys.path.insert(0, frontend_dir)
        sys.path.insert(0, backend_dir)
        sys.path.insert(0, app_dir)
        
        # Import original GUI
        from swap_rate_gui import SwapRateApp
        
        root = tk.Tk()
        app = SwapRateApp(root)
        
        print("✅ RateEdge loaded!")
        print("\nAll your tools available in Analytics menu")
        print("=" * 70)
        
        root.mainloop()
        
    except Exception as e:
        import traceback
        error_msg = f"Failed to start:\n\n{str(e)}\n\n{traceback.format_exc()}"
        print(error_msg)
        
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Startup Error", error_msg)
        except:
            pass

if __name__ == '__main__':
    launch()
