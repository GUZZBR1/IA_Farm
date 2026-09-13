# MLC LLM Integration Plan: IA_Farm

This document outlines the strategy for deploying the Phi-3 model on Android devices using the MLC LLM framework to achieve high-performance, offline GPU-accelerated inference.

## 1. Compilation Pipeline
The transition from a raw model to a deployable Android APK follows this pipeline:

1.  **Model Selection**: Phi-3 (Mini) - chosen for its high reasoning capabilities relative to parameter count.
2.  **Quantization**: 
    - Use `mlc_llm` to quantize weights to 4-bit (q4f16_1) to reduce memory footprint and increase inference speed.
    - Target: ~2.2GB VRAM requirement.
3.  **MLC Compiler**:
    - Convert the quantized model into MLC-LLM format.
    - Generate target-specific libraries (`.so` files) for Android (ARM64).
4.  **APK Integration**:
    - Integrate the MLC-LLM Android Runtime.
    - Bundle the model weights as external assets or downloadable chunks to keep APK size manageable.

## 2. GPU Acceleration Strategy
To ensure real-time responsiveness in the field, the following acceleration layers will be used:

- **Vulkan API**: The primary backend for Android. It provides cross-vendor GPU acceleration (Adreno, Mali).
- **OpenCL**: Fallback for older devices that do not fully support Vulkan.
- **TVM Unity**: Use the Apache TVM backend to optimize the compute graph specifically for the mobile SoC (System on Chip).

## 3. Weight-Sharding & Low-End Device Strategy
To support devices with limited RAM (4GB-6GB):

- **Weight Sharding**: Divide the model weights into smaller shards. Load only the necessary layers into VRAM during specific inference stages if the OS allows.
- **Memory Mapping (mmap)**: Use `mmap` to load model weights from storage on demand, reducing the initial heap memory pressure.
- **Dynamic KV Cache**: Implement a sliding window or limited KV cache size to prevent OOM (Out of Memory) errors during long conversations.
- **Fallback to CPU**: If GPU initialization fails or VRAM is insufficient, fallback to highly optimized CPU kernels (though with significantly reduced tokens/sec).
