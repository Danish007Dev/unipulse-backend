import subprocess
import re
from datetime import datetime
import sys

def get_latest_tag():
    result = subprocess.run(["git", "tag"], capture_output=True, text=True)
    tags = result.stdout.strip().split("\n")
    if not tags or tags == ['']:
        return "v0.0.0"
    return sorted(tags, key=lambda s: list(map(int, s[1:].split("."))))[-1]

def bump_version(tag, part):
    major, minor, patch = map(int, tag[1:].split("."))
    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    else:  # patch
        patch += 1
    return f"v{major}.{minor}.{patch}"

def generate_changelog(since_tag):
    log_cmd = ["git", "log", f"{since_tag}..HEAD", "--pretty=format:* %s"]
    result = subprocess.run(log_cmd, capture_output=True, text=True)
    return result.stdout.strip()

def update_version_file(version):
    with open("version.txt", "w") as f:
        f.write(version)

def get_current_branch():
    result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True)
    return result.stdout.strip()        

def main():
    allowed_branches = ["main"] #to prevent accidental tagging on other branches, add branch to tag
    current_branch = get_current_branch()

    if not any(current_branch.startswith(prefix) for prefix in allowed_branches):
        print(f"🚫 Tagging is restricted. Current branch: '{current_branch}'.")
        print(f"✅ Allowed branches: {allowed_branches}")
        return

    part = "patch"
    if len(sys.argv) == 2 and sys.argv[1] in ["major", "minor", "patch"]:
        part = sys.argv[1]

    current_tag = get_latest_tag()
    new_tag = bump_version(current_tag, part)
    changelog = generate_changelog(current_tag)

    if not changelog:
        print("❌ No new commits since last tag.")
        return

    today = datetime.today().strftime("%Y-%m-%d")
    entry = f"\n\n## {new_tag} - {today}\n{changelog}\n"

    with open("CHANGELOG.md", "a") as f:
        f.write(entry)

    update_version_file(new_tag)    

    subprocess.run(["git", "add", "CHANGELOG.md"])
    subprocess.run(["git", "commit", "-m", f"chore: release {new_tag}"])
    subprocess.run(["git", "tag", new_tag])
    subprocess.run(["git", "push"])
    subprocess.run(["git", "push", "--tags"])

    print(f"✅ Released {new_tag}")

if __name__ == "__main__":
    main()



# ## 🚀 How to Use It

# # Bump patch version (default- patch)
# python version_bump.py

# # Bump minor version
# python version_bump.py minor

# # Bump major version
# python version_bump.py major    