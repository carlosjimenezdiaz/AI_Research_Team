import subprocess
import sys
import time
import os

def run_script(name, file):
    print(f"\n🚀 Running {name}...\n")
    start = time.time()
    result = subprocess.run([sys.executable, file])
    elapsed = time.time() - start

    if result.returncode == 0:
        print(f"✅ {name} completed successfully in {elapsed:.2f} seconds\n")
        return True
    else:
        print(f"❌ {name} failed with return code {result.returncode} after {elapsed:.2f} seconds\n")
        return False

if __name__ == "__main__":
    total_start = time.time()

    agents = [
        ("Research Assistant", "Research_Assistant.py"),
        ("Private Banker", "Private_Banker.py"),
        ("Create DB", "create_db.py")
    ]

    for name, script in agents:
        if not run_script(name, script):
            print(f"🚨 Aborting pipeline due to failure in '{name}'.")
            sys.exit(1)

    # ✅ Run ticker_matching.py after all agents
    ticker_matching_path = os.path.join("Tools", "ticker_matching.py")
    if not run_script("Ticker Matching", ticker_matching_path):
        print(f"🚨 Final step failed: Ticker Matching.")
        sys.exit(1)

    # ✅ Run return_calculations.py after all agents
    calculations_path = os.path.join("Tools", "return_calculations.py")
    if not run_script("Return Calculations", calculations_path):
        print(f"🚨 Final step failed: Return Calculations.")
        sys.exit(1)

    total_elapsed = time.time() - total_start
    mins, secs = divmod(total_elapsed, 60)
    print(f"\n🎉 All agents and tools completed successfully in {int(mins)}m {secs:.2f}s")
