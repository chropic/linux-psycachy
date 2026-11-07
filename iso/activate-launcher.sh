#!/usr/bin/env bash
# Open activation only until it has succeeded.
set -Eeuo pipefail
[[ -e /var/lib/psycachy/installer-activated ]] && exit 0
exec xterm -hold -title 'PsyCachy activation' -e sudo /bin/bash /usr/local/lib/psycachy/activate.sh
