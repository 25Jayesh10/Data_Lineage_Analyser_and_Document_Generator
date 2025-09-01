import subprocess
import os

# Define the steps for each tool
commands = [
    # Tool3
    ["python", "Tool3/run_tool3.py"],

    # Tool4
    ["python", "Tool4/run_tool4.py"],
]

def run_commands():
    for cmd in commands:
        tool_dir = None

        
        if cmd == ["python", "Tool6.py"]:
            tool_dir = os.path.join(os.getcwd(), "Tool6")

        print(f"\n⚡ Running: {' '.join(cmd)} (cwd={tool_dir or os.getcwd()})")
        try:
            subprocess.run(cmd, check=True, cwd=tool_dir)
        except subprocess.CalledProcessError:
            print(f"❌ Failed: {' '.join(cmd)}")
            break

if __name__ == "__main__":
    run_commands()
