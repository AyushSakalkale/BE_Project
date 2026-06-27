import os
import subprocess
import sys

# Orchestration script to run the entire HDFS log anomaly detection pipeline

def run_script(script_path, args=[]):
    print(f"--- Running {script_path} ---")
    python_exe = sys.executable
    
    # Ensure current directory is in PYTHONPATH for submodule imports
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd() + os.pathsep + env.get("PYTHONPATH", "")
    
    result = subprocess.run([python_exe, script_path] + args, capture_output=False, env=env)
    if result.returncode != 0:
        print(f"Error running {script_path}")
        sys.exit(1)

def main():
    # 1. Parse Logs
    print("Step 1/4: Parsing Logs...")
    run_script("preprocessing/parser.py")

    # 2. Sequential Data Creation
    print("Step 2/4: Creating Sequences and Time-Series Data...")
    run_script("preprocessing/sequencer.py")

    # 3. Training
    print("Step 3/4: Training Models...")
    run_script("training/train_lstm.py")
    run_script("training/train_prophet.py")
    run_script("training/train_isolation_forest.py")

    # 4. Evaluation (Placeholder for generating plots)
    print("Step 4/4: Pipeline Complete. Models saved in models/ directory.")

if __name__ == "__main__":
    main()
