# ESP32 Wi-Fi CSI FYP

Custom live CSI demo, recording, analysis, training and ESP32 configuration utilities.
The sensing backend is the upstream [RuView](https://github.com/ruvnet/RuView) Docker image, not code authored in this project. Its source is not vendored here.

## What is actually implemented

The custom page compares variance, motion-band power and spectral power to a 60-second empty-room baseline. It is a threshold-based change detector, not a validated human-presence or pose model. A displayed possible presence is a signal deviation, not proof of a person. The page does not run the saved RVF model. Loading an RVF in RuView alone does not demonstrate inference accuracy.

Known limitations: missing features currently default to zero; the demo does not reliably reject offline/stale/simulated streams or distinguish disconnected hardware from empty-room readings. Check the RuView node status before calibration and testing. Stationary people can be missed and environmental changes can trigger false positives. The threshold has not been validated on held-out trials. Previous model evaluations were poor; do not report an accuracy claim from a successful model load.

## Arch Linux: first setup

```sh
sudo pacman -Syu --needed git docker docker-compose python python-pip
sudo systemctl enable --now docker
git clone https://github.com/irfan347/wifi-csi-fyp.git
cd wifi-csi-fyp
mkdir -p work/ruview-data/models work/ruview-data/recordings
sudo docker compose up -d
sudo docker compose logs --tail=60 sensing
```

Open http://localhost:3000/ui/index.html for RuView and http://localhost:8088 for the custom demo. Server startup can take over a minute. Existing services using those ports must be stopped first. Use the hotspot as a trusted isolated test network; the backend API and UDP input are unauthenticated.

## Move the ESP32 setup to the second laptop

1. Connect the Arch laptop to the same hotspot as the boards. Find its Wi-Fi IPv4 address with `ip -4 addr` (do not use a Docker bridge address).
2. Update both ESP32 destination addresses to the Arch laptop IPv4 and UDP port 5005. They currently target the Windows laptop, so moving the code alone is insufficient.
3. Check the hotspot BSSID (`iw dev YOUR_WIFI_INTERFACE link`, install `iw` if needed). If it changed, update the boards' CSI MAC filter to that BSSID too.
4. Allow inbound UDP 5005 from the boards in any active host firewall. Keep the boards powered and hardware positions fixed.
5. Confirm both nodes are active and real CSI packets are arriving before testing. Calibrate with the monitored room empty, then run separate empty/occupied trials.

The scripts in work/esp32 are historical Windows configuration utilities with hard-coded COM ports, old addresses, and required backup filenames. Do NOT run flash-writing preparation utilities unchanged on Arch. Serial names on Linux are typically /dev/ttyUSB* or /dev/ttyACM*. Use an inspected partition backup and the correct hardware identity before writing any NVS update. Never commit NVS backups: they can contain Wi-Fi passwords.

## Optional recording/training tools

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Run from repository root, only when the stated room condition is true:
python work/record_empty.py --label empty --setup-id final_room
# Other labels: person_still, person_walking. Each capture lasts 120 seconds.
python work/audit_train.py
```

Inspect scripts before reuse: validation helpers refer to historical recording IDs and some utilities are specific to Windows. Requirements are not a tested lockfile. The recording helper requires two active nodes. Training needs recordings and label metadata; restore them with `python restore_recordings.py`.

## Restore existing models and recordings

Models are included in the clone. Run `python restore_recordings.py` from the repository root for the historical recordings. Session secrets and hardware flash backups are excluded. The RVF models and preliminary Random Forest models are included. Recordings are available in the data-v1 GitHub release; run `python restore_recordings.py` to download and restore them. To request startup model loading, append `--model` and `/app/data/models/YOUR_MODEL.rvf` to the sensing command in compose.yaml, then run `sudo docker compose up -d`. This does not validate predictions or make the custom demo use the model.

## Daily use

```sh
sudo docker compose up -d
sudo docker compose logs --tail=60 sensing
sudo docker compose down
```

To get updates: `git pull` then `sudo docker compose up -d`. To save code changes: `git status`, `git add PATH`, `git commit -m "Describe changes"`, `git push`. Raw recordings are distributed as a release archive. Secrets, local environments and tools remain excluded.

## Published Wi-Fi settings

`wifi-settings.json` contains the hotspot SSID and readable password, published at the owner's explicit request. GitHub credentials, session secrets and NVS flash backups are not published. Configure the hotspot with these settings or provision the boards for another network. Changing machines still requires updating the ESP32 destination IP and checking the hotspot BSSID filter.
