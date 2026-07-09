import os
import json
import argparse
from datetime import datetime

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    version_path = os.path.join(script_dir, "version.json")
    
    # Default initial data
    data = {
        "version": "1.0.0",
        "build": "1",
        "timestamp": datetime.now().strftime("%d %b %Y %I:%M %p")
    }
    
    # Load existing version if it exists
    if os.path.exists(version_path):
        try:
            with open(version_path, "r") as f:
                data = json.load(f)
        except Exception:
            pass
            
    # Set up argument parsing to allow manual version updates
    parser = argparse.ArgumentParser(description="Update version.json metadata")
    parser.add_argument("--set-version", type=str, help="Set specific version string (e.g. 1.0.1)")
    args = parser.parse_args()
    
    if args.set_version:
        data["version"] = args.set_version
        
    # Update build number:
    # If running in GitHub Actions, use GITHUB_RUN_NUMBER as the build number.
    # Otherwise, increment the current build number locally.
    gh_run_number = os.environ.get("GITHUB_RUN_NUMBER")
    if gh_run_number:
        data["build"] = gh_run_number
    else:
        try:
            data["build"] = str(int(data.get("build", 0)) + 1)
        except ValueError:
            data["build"] = "1"
            
    # Update timestamp
    data["timestamp"] = datetime.now().strftime("%d %b %Y %I:%M %p")
    
    # Write updated data back to version.json
    with open(version_path, "w") as f:
        json.dump(data, f, indent=4)
        
    print(f"Updated version.json: version={data['version']}, build={data['build']}, timestamp={data['timestamp']}")

if __name__ == "__main__":
    main()
