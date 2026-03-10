import os
import time

def process_dir(d):
    for root, dirs, files in os.walk(d):
        if '.git' in root or 'venv' in root or 'bridge' in root or '__pycache__' in root:
            continue
        for file in files:
            if not file.endswith(('.py', '.toml', '.md', '.sh', '.bat', '.ps1', '.yaml', '.yml')):
                continue
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if 'nanobot' in content:
                    new_content = content.replace('zuberabot.', 'zuberabot.').replace('from zuberabot ', 'from zuberabot ').replace('import zuberabot', 'import zuberabot').replace('zuberabot/', 'zuberabot/')
                    if new_content != content:
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print(f"Updated {path}")
            except Exception as e:
                print(f"Failed {path}: {e}")

process_dir('e:/demo projects/zuberaa/zuberabot/zuberabot')
process_dir('e:/demo projects/zuberaa/zuberabot')
print("Refactoring complete.")
