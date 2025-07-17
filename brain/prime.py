# brain/prime.py
import os
import json
import subprocess
import datetime

def build_directory_structure(base_path):
    def recurse(path):
        tree = {"_files": [], "_dirs": {}}
        for entry in os.listdir(path):
            full_path = os.path.join(path, entry)
            if os.path.isfile(full_path):
                tree["_files"].append(entry)
            elif os.path.isdir(full_path):
                tree["_dirs"][entry] = recurse(full_path)
        return tree

    structure = recurse(base_path)
    return structure

def get_neofetch_output():
    """Get neofetch output or return a fallback message if neofetch is not available."""
    try:
        result = subprocess.run(['neofetch', '--stdout'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return "Neofetch command failed or not available"
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        return f"Neofetch not available: {str(e)}"

def get_installed_applications():
    """Generate a comprehensive list of installed applications from various package managers."""
    applications = []
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    applications.append(f"INSTALLED APPLICATIONS INVENTORY - Generated: {timestamp}")
    applications.append("=" * 60)
    
    # APT/DPKG packages (Debian/Ubuntu)
    try:
        result = subprocess.run(['dpkg', '--get-selections'], capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            apt_packages = [line.split()[0] for line in result.stdout.strip().split('\n') if '\tinstall' in line]
            applications.append(f"\nAPT/DPKG PACKAGES ({len(apt_packages)} installed):")
            applications.append("-" * 40)
            for pkg in sorted(apt_packages):
                applications.append(f"  {pkg}")
    except Exception as e:
        applications.append(f"\nAPT/DPKG PACKAGES: Error retrieving - {str(e)}")
    
    # Flatpak applications
    try:
        result = subprocess.run(['flatpak', 'list', '--app'], capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            flatpak_apps = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        flatpak_apps.append(f"{parts[0]} ({parts[1]})")
            applications.append(f"\nFLATPAK APPLICATIONS ({len(flatpak_apps)} installed):")
            applications.append("-" * 40)
            for app in sorted(flatpak_apps):
                applications.append(f"  {app}")
    except Exception as e:
        applications.append(f"\nFLATPAK APPLICATIONS: Error retrieving - {str(e)}")
    
    # Snap packages
    try:
        result = subprocess.run(['snap', 'list'], capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            snap_packages = []
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:  # Skip header line
                for line in lines[1:]:
                    parts = line.split()
                    if len(parts) >= 2:
                        snap_packages.append(f"{parts[0]} ({parts[1]})")
            applications.append(f"\nSNAP PACKAGES ({len(snap_packages)} installed):")
            applications.append("-" * 40)
            for pkg in sorted(snap_packages):
                applications.append(f"  {pkg}")
    except Exception as e:
        applications.append(f"\nSNAP PACKAGES: Error retrieving - {str(e)}")
    
    # Python packages (pip)
    try:
        result = subprocess.run(['pip3', 'list'], capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            pip_packages = []
            lines = result.stdout.strip().split('\n')
            if len(lines) > 2:  # Skip header lines
                for line in lines[2:]:
                    parts = line.split()
                    if len(parts) >= 2:
                        pip_packages.append(f"{parts[0]} ({parts[1]})")
            applications.append(f"\nPYTHON PACKAGES (pip3) ({len(pip_packages)} installed):")
            applications.append("-" * 40)
            for pkg in sorted(pip_packages):
                applications.append(f"  {pkg}")
    except Exception as e:
        applications.append(f"\nPYTHON PACKAGES: Error retrieving - {str(e)}")
    
    # Desktop applications from /usr/share/applications
    try:
        desktop_apps = []
        desktop_dirs = ['/usr/share/applications', '/usr/local/share/applications', 
                       os.path.expanduser('~/.local/share/applications')]
        
        for desktop_dir in desktop_dirs:
            if os.path.exists(desktop_dir):
                for app_file in os.listdir(desktop_dir):
                    if app_file.endswith('.desktop'):
                        desktop_apps.append(app_file[:-8])  # Remove .desktop extension
        
        applications.append(f"\nDESKTOP APPLICATIONS ({len(set(desktop_apps))} found):")
        applications.append("-" * 40)
        for app in sorted(set(desktop_apps)):
            applications.append(f"  {app}")
    except Exception as e:
        applications.append(f"\nDESKTOP APPLICATIONS: Error retrieving - {str(e)}")
    
    # Write to file
    try:
        with open('installed_applications.txt', 'w') as f:
            f.write('\n'.join(applications))
        return f"\nINSTALLED APPLICATIONS: Complete inventory saved to 'installed_applications.txt' ({len(applications)} total entries)"
    except Exception as e:
        return f"\nINSTALLED APPLICATIONS: Error saving inventory - {str(e)}"

def compose_priming_message(dir_json):
    dir_text = json.dumps(dir_json, indent=2)
    neofetch_output = get_neofetch_output()
    applications_info = get_installed_applications()

    priming_message = f"""
You are being activated within the Marina Agentic Intelligence Framework.

Marina is a decentralized, modular AI system comprised of multiple tools, modules, and agents. These tools interact across GUI, CLI, and autonomous daemon loops. The purpose of this system is to create a self-improving, self-aware assistant capable of managing its own state, memory, and modular logic through coordinated agent swarming.

SYSTEM INFORMATION:
{neofetch_output}
{applications_info}

Below is a full JSON representation of Marina's system file structure. This shows the files, subsystems, and active code used throughout the system:
{dir_text}

ACTION ENGINE SYNTAX:
You have direct access to the host system through the action_engine module. To execute shell commands, use the following syntax:

[action] <command>

Examples:
- [action] ls -la
- [action] pwd
- [action] cd /home/user/documents
- [action] git status
- [action] python3 script.py
- [action] pip install requests
- [action] cat file.txt
- [action] mkdir new_folder
- [action] rm unwanted_file.txt

Command Aliases (automatically normalized):
- dir → ls
- list → ls
- remove → rm
- copy → cp
- move → mv
- make → mkdir
- clone → git clone
- update → apt update
- install → apt install
- who → whoami
- where → pwd

Important Notes:
- Commands are executed in the current working directory
- Use absolute paths when needed
- The 'cd' command will change the working directory for subsequent commands
- Output (stdout) and errors (stderr) are captured and displayed
- Commands run with your current user permissions
- Be mindful of system security and only execute safe commands

From this point on:
- Each time the user sends a prompt, it will be **prefixed with the full responses of all other LLMs to the previous prompt**.
- You are to **interpret the current prompt** not just in isolation, but in light of how other LLMs processed the last one.
- This gives you **perception of inter-LLM dynamics**, enabling you to respond with more context-awareness, coordination, and inference capacity.
- You can execute system commands using the [action] syntax to interact with the host system directly.

This is designed to help Marina operate as a collaborative system of intelligent agents with direct system access.

IMPORTANT - RESPONSE GUIDELINES:
When responding to user requests, provide COMPLETE and ROBUST instruction sets, not just the first command to run. This means:

1. **Comprehensive Steps**: Break down complex tasks into clear, sequential steps
2. **Context & Explanation**: Explain WHY each step is necessary and what it accomplishes
3. **Prerequisites**: Identify any dependencies, required tools, or setup steps
4. **Error Handling**: Include common troubleshooting steps and error recovery
5. **Validation**: Provide ways to verify each step worked correctly
6. **Complete Workflow**: Cover the entire process from start to finish, not just the initial action
7. **Alternative Approaches**: When applicable, mention different methods or considerations
8. **Best Practices**: Include relevant security, performance, or maintenance considerations

Example of GOOD response structure:
- Overview of what we're going to accomplish
- Prerequisites and setup requirements
- Step-by-step instructions with explanations
- Verification steps to confirm success
- Common issues and how to resolve them
- Next steps or follow-up actions

This comprehensive approach ensures Marina operates effectively and users can successfully complete their objectives.

Awaiting first user prompt...
""".strip()

    return priming_message

if __name__ == "__main__":
    marina_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    dir_json = build_directory_structure(marina_root)
    message = compose_priming_message(dir_json)
    print(message)
