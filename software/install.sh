#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root: sudo software/install.sh" >&2
  exit 1
fi

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
install_root=/opt/rover-bean

getent group robot >/dev/null || groupadd --system robot
id agent >/dev/null 2>&1 || useradd --create-home --shell /bin/bash agent
usermod -a -G robot,dialout agent

python3 -m venv "${install_root}/venv"
"${install_root}/venv/bin/pip" install --no-deps "${repo_root}/software/robotd"
install -D -m 0644 "${repo_root}/software/systemd/robotd.service" /etc/systemd/system/robotd.service
install -d -o agent -g robot -m 0750 /var/log/robotd
install -d -o agent -g robot -m 0750 /mnt/robot-audit

systemctl daemon-reload
systemctl enable robotd.service

echo "Installed robotd. Keep the motor branch physically isolated."
echo "Before starting: enable /dev/serial0 UART, flash the Pico through its service cable,"
echo "mount the off-host audit target at /mnt/robot-audit, then run commissioning."
