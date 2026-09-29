"""Declared device scenarios; these labels do not emulate Android hardware."""


DEVICE_PROFILES = {
    "android-low-mid-4gb": {
        "device_class": "low-to-mid-range Android phone",
        "architecture": "ARM64 (target assumption)",
        "total_ram_mb": 4096,
        "network": "offline",
        "generative_model": "disabled",
        "execution_level": "behavioral profile with synthetic in-memory retrieval",
        "physical_device_validated": False,
        "not_emulated": [
            "Android process memory limits or memory reclamation",
            "ARM64 execution speed, thermal throttling, and battery use",
            "native Android packaging and model loading",
        ],
    }
}
