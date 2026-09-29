
# 🛠️ INFRASTRUCTURE & STORAGE PROTOCOL (QUOTA BYPASS)

## 🚨 Critical Storage Configuration
The user home directory (`/home/guzzbr`) has a strict disk quota that prevents the installation of heavy ML libraries (PyTorch, etc.) and the storage of large vector indices. 

To bypass this, the project uses a **Storage Redirection Strategy**.

### 📂 Storage Mapping
- **Logical Path:** `/home/guzzbr/meus-projetos/IA_Farm/data`
- **Physical Path:** `/var/tmp/ia_//farm_data` (Symlinked)

**Crucial:** All heavy data, vector indices (`.index`, `.meta`), and large datasets MUST be stored in the `/data` directory. This directory is a symbolic link to `/var/tmp`, which bypasses the home quota and utilizes the server's main disk space (~400GB).

### 📦 Library Management
To avoid quota errors during installation, use the `--target` flag or install libraries in a quota-free zone:
- **Target Zone:** `/tmp/ia_farm_libs` or `/var/tmp/ia_farm_libs`
- **Python Path:** Ensure `sys.path.append("/var/tmp/ia_farm_libs")` is called at the start of the execution if libraries are installed there.

### 🔄 Recovery Procedure
If the `/data` link is broken:
1. `mkdir -p /var/tmp/ia_farm_data`
2. `rm -rf /home/guzzbr/meus-projetos/IA_Farm/data`
3. `ln -s /var/tmp/ia_farm_data /home/guzzbr/meus-projetos/IA_Farm/data`

---
**NOTE TO AGENT:** Always check the integrity of the `/data` symlink upon initialization. Never attempt to save large files directly in the project root or `.venv` without verifying the path.
