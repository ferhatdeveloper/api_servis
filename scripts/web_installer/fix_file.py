import re

# Read the file
with open('installer_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the position of "installer = InstallerService()"
match = re.search(r'^installer = InstallerService\(\)\s*$', content, re.MULTILINE)

if match:
    # Keep everything up to and including that line plus 2 newlines
    end_pos = match.end()
    fixed_content = content[:end_pos] + '\n\n'
    
    # Write back
    with open('installer_service.py', 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print("✅ File fixed! Removed duplicate methods.")
else:
    print("❌ Could not find installer instantiation line")
