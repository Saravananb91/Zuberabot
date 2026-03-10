import sys
import subprocess

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

packages = ["sqlalchemy", "pgvector", "sentence-transformers", "python-dotenv"]
for pkg in packages:
    try:
        install(pkg)
        print(f"Successfully installed {pkg}")
    except Exception as e:
        print(f"Failed to install {pkg}: {e}")
