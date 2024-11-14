# backend/check_env.py
import subprocess
import os
from pathlib import Path
import sys

def check_tact_installation():
    print("Checking Tact compiler installation...")
    
    # Check in common locations
    possible_paths = [
        Path(os.path.expanduser("~/.npm-global/bin/tact")),
        Path("/usr/local/bin/tact"),
        Path("/usr/bin/tact"),
        Path(os.path.expanduser("~/AppData/Roaming/npm/tact.cmd")),
    ]
    
    for path in possible_paths:
        if path.exists():
            print(f"Found Tact compiler at: {path}")
            return True
            
    # Try using npm to find tact
    try:
        npm_root = subprocess.getoutput("npm root -g").strip()
        tact_path = os.path.join(npm_root, "@tact-lang", "cli", "bin", "tact")
        if os.path.exists(tact_path):
            print(f"Found Tact compiler at: {tact_path}")
            return True
    except:
        pass
        
    print("Tact compiler not found!")
    print("Please install it using: npm install -g @tact-lang/cli")
    return False

def check_npm():
    print("Checking npm installation...")
    try:
        subprocess.run(["npm", "--version"], check=True, capture_output=True)
        print("npm is installed")
        return True
    except:
        print("npm not found! Please install Node.js and npm")
        return False

def main():
    all_good = True
    
    if not check_npm():
        all_good = False
    
    if not check_tact_installation():
        all_good = False
    
    if all_good:
        print("\nAll dependencies are properly installed!")
    else:
        print("\nSome dependencies are missing. Please install them and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()