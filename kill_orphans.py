import os
import signal
import sys
import psutil

def kill_orphans():
    current_pid = os.getpid()
    python_procs = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'python' in proc.info['name'].lower():
                # Skip ourselves
                if proc.info['pid'] == current_pid:
                    continue
                    
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                # We specifically want to kill python processes running 'zuberabot'
                if 'nanobot gateway' in cmdline or 'zuberabot' in cmdline or 'zuberabot' in cmdline:
                    print(f"Found orphaned nanobot process: PID {proc.info['pid']} ({cmdline})")
                    python_procs.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
            
    if not python_procs:
        print("No orphaned nanobot python processes found.")
        return

    for p in python_procs:
        try:
            print(f"Terminating PID {p.info['pid']}...")
            p.terminate()
        except:
            pass

if __name__ == "__main__":
    kill_orphans()
