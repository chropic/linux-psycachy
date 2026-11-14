# SP12 SoundWire/audio patch handoff

This is an isolated source rebase in `/tmp/luna-r2-audio-20261113`. The authenticated CachyOS source extraction and shared repository are read-only. No main-worktree, manifest, seed, package pin, or canonical source change was made. No kernel/package/ISO/VM build or hardware operation was run.

## Inputs and identity

- CachyOS source archive SHA-256: `3dba29aa8e7dcda43aee6898e4c66dfbfd997eb5d902510b0faeacc696ddfb3f`.
- Existing signature record: `VALIDSIG E8B9AA39F054E30E8290D492C3C4820857F654FE` in `output/.phase1-closeout-20261110T192001-0700/arm64-prepare-v1/signature-status.txt`.
- Frozen overlay: `miasvanklei/Gentoo-overlay` commit `952f769e1b45f07302d69992d19e5874ee77737`; source range includes `ed20a9946e0136485bbac067e72100b84a0865fd`.
- Only patched source file: `drivers/soundwire/qcom.c`, pristine SHA-256 `30fccf86e735e5e56d3eb6c06b54be578d236892c140aa738cc1f4b22fd91b1f`.
- `overlay-identities.tsv` maps audio patches 00/01/02 to the exact final-overlay Git blobs and preserved-patch SHA-256 values. Patches 00 and 01 are retained only under `reference/` for classification. The SoundWire patch is byte-preserved as sequence patch 01.

## Ordered patches

1. [`patches/rebased/01-soundwire-irq-clock-order.patch`](patches/rebased/01-soundwire-irq-clock-order.patch) — overlay audio file 02, verbatim. It disables the threaded IRQ after FIFO drain and before SoundWire clock-stop handling; it reenables the IRQ after the controller clock and bus clock-stop exit have completed. The original overlay patch applies without context adaptation. Overlay blob `f9f4ba948f90e1e12366b2d7987173700f2fac71`; SHA-256 `b9096e5b7cb9883d1f76fd271dd24729117b42d1020c65977c880dee9e881347`.
2. [`patches/rebased/02-soundwire-suspend-error-unwind.patch`](patches/rebased/02-soundwire-suspend-error-unwind.patch) — small local follow-up, with no upstream attribution claim. It adds `enable_irq(ctrl->irq)` before each of the two suspend error returns after the IRQ was disabled: failed `sdw_bus_prep_clk_stop()` and failed `sdw_bus_clk_stop()`. A failed runtime suspend does not run the resume callback, so without these calls the controller IRQ would stay disabled while the controller clock is still active. The patch only restores that IRQ state on error; success retains patch 01's IRQ-off interval while clocks are gated.

The two patch files have SHA-256 values recorded in `patches.sha256`; expected final `qcom.c` SHA-256 is `c8318198a696f2db5e9f80d636216491f32acbf40eb744a9683367986dbbafc1` (`expected-result.sha256`).

## Replay and focused source-contract check

Run the checker against the pristine extracted source:

```sh
python3 /tmp/luna-r2-audio-20261113/check-sequence.py \
  /var/tmp/sp12-overlay-cachyos-audit-20261112/source/cachyos-7.3.1-1
python3 /tmp/luna-r2-audio-20261113/verify-identities.py
```

Observed: both patches passed sequential `git apply --check`/application to the single touched pristine file; the resulting file hash matched; the preserved overlay patch blobs matched their Git IDs and SHA-256 hashes. Source-contract checks passed for `IRQF_ONESHOT` threaded registration, FIFO drain before IRQ disable, IRQ disable before bus clock-stop and `hclk` gating, resume reenable after bus clock-stop exit, and IRQ restoration before both suspend-error returns. Audio graph checks confirmed the Surface VA/WSA DAI IDs and the baseline 48 kHz/S16 capability. `git diff --check` passed.

This proves patch applicability and source ordering on the exact touched-file subset. It does not prove kernel compilation or runtime repair. Existing SP12 capture shows WSA slaves `UNATTACHED`, auto-enumeration failure (`2048`), bus clash/FIFO overflow, and `-ENODATA` during codec resume/playback. Those symptoms are consistent with the problem described by patch 01, but the available diagnosis explicitly does not establish root cause; retain the patch as a candidate pending rerun after lead integration. Existing log evidence is `speaker-route-active-stream-test-20261112.txt` (SHA-256 `4c35847b578af1c33b285ece5b86c97510381150fb9525368d8f16448d1bb0c0`) and `soundwire-speaker-failure-20261112.txt` (SHA-256 `082228a31d244cd4674f9af0fd8f5f16f0e6c31dc753e74769d89db50d82fce4`) under `output/.unattended-luna-20261111210910Z/qemu-hosting/sp12-live-qualification-20261112/audio-current-20261112/`. The previous diagnosis says those logs do not isolate the fault cause.

## Classification of audio patches 00 and 01

The exact Surface DTS graph routes `VA Capture` through `VA_CODEC_DMA_TX_0` and `WSA Playback` through `WSA_CODEC_DMA_RX_0` on `q6apmbedai`. `q6apm_lpass_dai_dev_probe()` calls `q6dsp_audio_ports_set_config()`, which supplies the common DAI capability table, so patch 00 would widen the WSA/VA CDC-DMA rate capabilities. The SP12 speaker acceptance capture used 48 kHz, `S16_LE`, stereo. Baseline CDC-DMA capabilities already include 48 kHz and `S16_LE`; no source or acceptance evidence requires the extra 192 kHz rates. Patch 00 is therefore not needed for this route/recovery objective.

Patch 01 changes only the Primary through Quinary MI2S DAI format declarations. The Surface VA/WSA graph uses the CDC-DMA entries, not these MI2S entries. Baseline CDC-DMA entries already include `S32_LE`; the current acceptance stream uses `S16_LE`. Patch 01 is not required for the SP12 VA/WSA graph and is not ported.

The source evidence files and SHA-256 values are in `evidence-sources.sha256`. The references themselves remain byte-for-byte under `reference/`; no unsupported rate/format requirement has been inferred.

## Open limitations

- No full-tree/kernel build or hardware test was run. The lead should replay the two-patch sequence in the complete source tree and keep runtime qualification separate.
- The follow-up is a local source correction, not an overlay-originated patch. Preserve the original overlay blob and its notices separately; do not attribute the two error-path additions to the overlay author.
- The SoundWire logs identify a failure mode but do not prove the IRQ-clock race is the cause. The corrected boot/DTB and SoundWire enumeration should be rechecked before declaring the speaker route fixed.
