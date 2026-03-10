import os
import shutil
import sys

site_packages = os.path.join(os.path.dirname(sys.executable), "Lib", "site-packages")
print(f"Site packages: {site_packages}")

targ_dir = os.path.join(site_packages, "zuberabot")
if os.path.exists(targ_dir):
    print(f"Deleting rogue package directory: {targ_dir}")
    shutil.rmtree(targ_dir)
else:
    print(f"Not found: {targ_dir}")

for item in os.listdir(site_packages):
    if item.startswith("nanobot-") and item.endswith(".dist-info"):
        targ = os.path.join(site_packages, item)
        print(f"Deleting dist-info: {targ}")
        shutil.rmtree(targ)

print("Cleanup complete.")
