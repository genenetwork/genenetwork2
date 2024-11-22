To run the qtlreaper scripts (QTL_Reaper_v6.py or any other pythonscript that imports "reaper"):

Download the manifest file here - https://github.com/genenetwork/genenetwork2/blob/ca0649f4100125748082a7513b06a555cc9d3f4e/scripts/maintenance/manifest.scm

Create the guix profile:

If updated guix doesn't already exist:

Get channels.scm from ci.genenetwork.org/channels.scm
```bash
guix pull -C channels.scm -p ~/opt/guix-current
```

Create profile:
```bash
~/opt/guix-current/bin/guix package -m manifest.scm -p ~/opt/qtlreaper-profile
```

Source profile:
```bash
unset GUIX_PROFILE
source ~/opt/qtlreaper-profile/etc/profile
```

Then the script should run!
