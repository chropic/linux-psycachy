#!/usr/bin/env python3
"""Fail on unexpected loss or change of enabled SP12 seed symbols.

Known toolchain and non-SP12 changes remain unreviewed exceptions, not an
approval to release the candidate configuration.
"""
import argparse
import hashlib
import json
import pathlib
import re
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXCEPTIONS = {
    **{name: ("y", "toolchain or compiler capability") for name in (
        "CONFIG_CC_IS_GCC", "CONFIG_AS_IS_GNU", "CONFIG_LD_IS_BFD", "CONFIG_CC_CAN_LINK",
        "CONFIG_RUST_IS_AVAILABLE", "CONFIG_RUSTC_HAS_SPAN_FILE", "CONFIG_RUSTC_HAS_UNNECESSARY_TRANSMUTES",
        "CONFIG_RUSTC_HAS_FILE_WITH_NUL", "CONFIG_RUSTC_HAS_FILE_AS_C_STR", "CONFIG_CC_NO_ARRAY_BOUNDS",
        "CONFIG_CC_NO_STRINGOP_OVERFLOW", "CONFIG_GCC_SUPPORTS_DYNAMIC_FTRACE_WITH_ARGS",
        "CONFIG_CC_HAS_MIN_FUNCTION_ALIGNMENT", "CONFIG_CC_HAS_UBSAN_BOUNDS_STRICT", "CONFIG_UBSAN_BOUNDS_STRICT")},
    **{name: ("m", "non-SP12 device symbol; replacement not established") for name in (
        "CONFIG_GPIO_MACSMC", "CONFIG_POWER_RESET_MACSMC", "CONFIG_SENSORS_MACSMC_HWMON",
        "CONFIG_MFD_MACSMC", "CONFIG_REGULATOR_DA903X", "CONFIG_RTC_DRV_MACSMC")},
    **{name: ("y", "non-SP12 GPU option or sample; replacement not established") for name in (
        "CONFIG_DRM_AMD_DC_FP", "CONFIG_DRM_AMD_SECURE_DISPLAY", "CONFIG_SAMPLE_AUXDISPLAY",
        "CONFIG_SAMPLE_WATCHDOG")},
}
POLICY_REMOVALS = {
    "CONFIG_KEXEC": ("y", "n", "legacy unsigned kexec disabled by Phase 1 policy"),
    "CONFIG_KEXEC_HANDOVER": ("y", "n", "kexec handover disabled by Phase 1 policy"),
    "CONFIG_KEXEC_HANDOVER_DEBUGFS": ("y", None, "handover debugfs controls removed with handover"),
    "CONFIG_KEXEC_HANDOVER_ENABLE_DEFAULT": ("y", None, "handover default removed with handover"),
    "CONFIG_LIBFDT": ("y", None, "handover-only dependency removed with handover"),
    "CONFIG_LIVEUPDATE": ("y", None, "live update removed with handover"),
    "CONFIG_LIVEUPDATE_MEMFD": ("y", None, "live update removed with handover"),
    "CONFIG_MEMBLOCK_KHO_SCRATCH": ("y", None, "handover-only scratch support removed with handover"),
    "CONFIG_LOCK_DOWN_KERNEL_FORCE_NONE": ("y", "n", "integrity lockdown selected by Phase 1 policy"),
}
POLICY_ADDITIONS = {
    "CONFIG_ARCH_SUPPORTS_KEXEC_SIG_FORCE": ("y", "ARM64 force-signature capability patch"),
    "CONFIG_KEXEC_SIG_FORCE": ("y", "mandatory file-based kexec signatures"),
    "CONFIG_LOCK_DOWN_KERNEL_FORCE_INTEGRITY": ("y", "integrity lockdown default"),
    "CONFIG_MODULE_SIG_FORCE": ("y", "reject unsigned and untrusted modules"),
}
# Required SP12 camera/media and Type-C PHY configuration from the authenticated
# CachyOS 7.3.1 Kconfig/Makefiles. Keep tristate values exact: the module audit
# below requires the corresponding .ko files in modules.order and the build.
REQUIRED_SP12_CONFIG = {
    "CONFIG_OF": "y",
    "CONFIG_ARM64": "y",
    "CONFIG_ARCH_QCOM": "y",
    "CONFIG_COMMON_CLK": "y",
    "CONFIG_HAVE_CLK": "y",
    "CONFIG_IOMMU_DMA": "y",
    "CONFIG_GPIOLIB": "y",
    "CONFIG_REGULATOR": "y",
    "CONFIG_PM": "y",
    "CONFIG_I2C": "y",
    "CONFIG_I2C_QCOM_CCI": "m",
    "CONFIG_REGMAP_I2C": "y",
    "CONFIG_MEDIA_SUPPORT": "m",
    "CONFIG_MEDIA_CAMERA_SUPPORT": "y",
    "CONFIG_MEDIA_PLATFORM_SUPPORT": "y",
    "CONFIG_VIDEO_CAMERA_SENSOR": "y",
    "CONFIG_VIDEO_DEV": "m",
    "CONFIG_MEDIA_CONTROLLER": "y",
    "CONFIG_VIDEO_V4L2_I2C": "y",
    "CONFIG_VIDEO_V4L2_SUBDEV_API": "y",
    "CONFIG_V4L2_FWNODE": "m",
    "CONFIG_V4L2_ASYNC": "m",
    "CONFIG_V4L2_CCI": "m",
    "CONFIG_V4L2_CCI_I2C": "m",
    "CONFIG_DMA_SHARED_BUFFER": "y",
    "CONFIG_V4L_PLATFORM_DRIVERS": "y",
    "CONFIG_VIDEO_QCOM_CAMSS": "m",
    "CONFIG_PHY_QCOM_MIPI_CSI2": "m",
    "CONFIG_VIDEO_OV02C10": "m",
    "CONFIG_VIDEO_OV13858": "m",
    "CONFIG_VIDEOBUF2_CORE": "m",
    "CONFIG_VIDEOBUF2_MEMOPS": "m",
    "CONFIG_VIDEOBUF2_V4L2": "m",
    "CONFIG_VIDEOBUF2_DMA_SG": "m",
    "CONFIG_PHY_QCOM_QMP": "m",
    "CONFIG_PHY_QCOM_QMP_COMBO": "m",
    "CONFIG_GENERIC_PHY": "y",
    "CONFIG_PHY_SNPS_EUSB2": "m",
    "CONFIG_PHY_QCOM_EUSB2_REPEATER": "m",
    "CONFIG_MFD_SYSCON": "y",
    "CONFIG_REGMAP_MMIO": "y",
    "CONFIG_DRM_BRIDGE": "y",
    "CONFIG_DRM_AUX_BRIDGE": "m",
    "CONFIG_COMMON_CLK_QCOM": "y",
    "CONFIG_CLK_X1P42100_CAMCC": "m",
    "CONFIG_CLK_X1E80100_GCC": "m",
    "CONFIG_QCOM_GDSC": "y",
    "CONFIG_PM_GENERIC_DOMAINS": "y",
    "CONFIG_RATIONAL": "y",
    "CONFIG_RESET_CONTROLLER": "y",
    "CONFIG_INTERCONNECT": "y",
    "CONFIG_INTERCONNECT_CLK": "y",
}
ASSIGN = re.compile(r"^(CONFIG_[A-Za-z0-9_]+)=(.*)$")
DISABLED = re.compile(r"^# (CONFIG_[A-Za-z0-9_]+) is not set$")


def read_config(path):
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = ASSIGN.fullmatch(line)
        disabled = DISABLED.fullmatch(line)
        if not match and not disabled:
            continue
        key, value = (match.group(1), match.group(2)) if match else (disabled.group(1), "n")
        if key in result:
            raise ValueError(f"duplicate config symbol: {key}")
        result[key] = value
    return result


def compare(seed, candidate):
    exceptions, policy_changes, unexpected = [], [], []
    for key, before in seed.items():
        if before not in ("y", "m"):
            continue
        after = candidate.get(key)
        if after == before:
            continue
        allowed = EXCEPTIONS.get(key)
        policy = POLICY_REMOVALS.get(key)
        item = {"symbol": key, "before": before, "after": after}
        if policy and before == policy[0] and after == policy[1]:
            item["reason"] = policy[2]
            policy_changes.append(item)
        elif allowed and before == allowed[0] and after is None:
            item["reason"] = allowed[1]
            exceptions.append(item)
        else:
            unexpected.append(item)
    policy_additions, required_config_additions, newly_enabled = [], [], []
    for key, value in candidate.items():
        if value not in ("y", "m") or seed.get(key) in ("y", "m"):
            continue
        required = REQUIRED_SP12_CONFIG.get(key)
        if required == value:
            required_config_additions.append({"symbol": key, "before": seed.get(key),
                                              "after": value,
                                              "reason": "required SP12 camera/media/PHY closure"})
            continue
        approved = POLICY_ADDITIONS.get(key)
        if approved and value == approved[0]:
            policy_additions.append({"symbol": key, "before": seed.get(key),
                                     "after": value, "reason": approved[1]})
        else:
            newly_enabled.append({"symbol": key, "before": seed.get(key), "after": value})
    required_config_mismatches = [
        {"symbol": key, "expected": value, "actual": candidate.get(key)}
        for key, value in REQUIRED_SP12_CONFIG.items()
        if candidate.get(key) != value
    ]
    return {"schema": 1, "enabled_seed_symbols": sum(v in ("y", "m") for v in seed.values()),
            "known_unreviewed_exceptions": exceptions, "approved_policy_changes": policy_changes,
            "approved_policy_additions": policy_additions, "unexpected_changes": unexpected,
            "required_sp12_config": REQUIRED_SP12_CONFIG,
            "required_sp12_config_additions": required_config_additions,
            "required_sp12_config_mismatches": required_config_mismatches,
            "newly_enabled_unreviewed": newly_enabled,
            "limitations": ["added or previously disabled symbols still require review",
                            "passing does not establish runtime or hardware support"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=pathlib.Path)
    parser.add_argument("--seed", type=pathlib.Path, default=ROOT / "targets/sp121-arm64/config.seed")
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    report = compare(read_config(args.seed), read_config(args.candidate))
    report["seed_sha256"] = hashlib.sha256(args.seed.read_bytes()).hexdigest()
    report["candidate_sha256"] = hashlib.sha256(args.candidate.read_bytes()).hexdigest()
    rendered = json.dumps(report, indent=2) + "\n"
    if report["unexpected_changes"] or report["required_sp12_config_mismatches"]:
        print(rendered, file=sys.stderr, end="")
        raise SystemExit("SP12 configuration audit failed")
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
