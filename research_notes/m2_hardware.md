# 📱 M2: Hardware Benchmarks (Android 10 / 4GB RAM)
## Latency & Memory Analysis
- **Model Target:** Gemma-2B / Llama-3.2-1B/3B (4-bit Quantization).
- **RAM Footprint:** 
    - 1B Model: ~800MB - 1.2GB.
    - 3B Model: ~2.1GB - 2.8GB.
- **Estimated Performance:**
    - 1B Model: 8-12 tokens/sec.
    - 3B Model: 3-6 tokens/sec.
- **Bottleneck:** Memory bandwidth (LPDDR4X) is the primary constraint.
- **Mitigation:** Use `mmap` for weights to prevent OOM crashes.
