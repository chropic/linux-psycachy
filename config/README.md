# Configuration provenance

`ubuntu-7.0.0-30-generic.config` is extracted verbatim from
`linux-modules-7.0.0-30-generic_7.0.0-30.30_amd64.deb`, file
`./boot/config-7.0.0-30-generic`.

* Package SHA-256: recorded by the Ubuntu archive at build time; obtain it
  through APT before using a different mirror.
* Extracted configuration SHA-256:
  `b07d3cb0d53236b021d73038e315018801fa6b843529d53129ad94a2a5233bf6`
* `psycachy.fragment` is the complete policy allowlist.

`build.sh --prepare-only` produces `psycachy-7.2.2.config` and
`config-diff.json` in its output directory. Those generated artifacts are not
committed until the required clean Ubuntu 26.04.1 WSL build can run.
