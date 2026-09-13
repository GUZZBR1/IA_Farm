import os
import psutil
import time
from tools.memory_manager import MemoryManager

def create_dummy_file(path, size_mb):
    """Creates a dummy file of a specific size."""
    with open(path, "wb") as f:
        f.write(os.urandom(size_mb * 1024 * 1024))

def get_memory_usage():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def benchmark_mmap():
    print("--- RAM Optimization Benchmark ---")
    file_path = "benchmark_data.bin"
    size_mb = 100
    create_dummy_file(file_path, size_mb)
    
    # Baseline: Standard file read
    start_mem = get_memory_usage()
    with open(file_path, "rb") as f:
        data = f.read()
    mid_mem = get_memory_usage()
    print(f"Standard Load: Memory Usage increase = {mid_mem - start_mem:.2f} MB")
    del data
    
    # mmap: Memory mapped load
    manager = MemoryManager()
    start_mem = get_memory_usage()
    mm, f_obj = manager.mmap_load(file_path)
    mid_mem = get_memory_usage()
    print(f"mmap Load: Memory Usage increase = {mid_mem - start_mem:.2f} MB")
    
    mm.close()
    f_obj.close()
    os.remove(file_path)

def benchmark_cache():
    print("\n--- Context Cache Benchmark ---")
    manager = MemoryManager(cache_file="test_cache.json")
    queries = ["Como plantar soja?", "Qual o melhor adubo para milho?", "Como plantar soja?"]
    
    hits = 0
    for q in queries:
        res = manager.get_cached_context(q)
        if res:
            hits += 1
            print(f"Query '{q}': CACHE HIT")
        else:
            print(f"Query '{q}': CACHE MISS")
            manager.set_cached_context(q, f"Context for {q}")
    
    print(f"Cache Hit Rate: {(hits / len(queries)) * 100:.2f}%")
    if os.path.exists("test_cache.json"):
        os.remove("test_cache.json")

if __name__ == "__main__":
    try:
        benchmark_mmap()
        benchmark_cache()
    except Exception as e:
        print(f"Error during benchmark: {e}")
