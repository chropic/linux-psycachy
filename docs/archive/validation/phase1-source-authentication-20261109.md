# SP12 Phase 1 source authentication — 2026-11-09

The pinned `cachyos-7.3.1-1` source archive is staged under ignored
`output/phase1/source/`. Its SHA-256 matches the repository pin:

`3dba29aa8e7dcda43aee6898e4c66dfbfd997eb5d902510b0faeacc696ddfb3f`

The detached signature verifies with `gpgv` against the signer fingerprint
pinned in `config/source-pin.sh`. The raw archive, signature, public key, and
verification status are retained under `output/phase1/source/`. No kernel
package build has been run yet; the pinned build prerequisites still need
operator installation. This source check does not approve the candidate
configuration or authorize tuning.
