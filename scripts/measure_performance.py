import time
import os

def measure():
    results = {}
    
    start = time.time()
    os.system("python scripts/generate_dataset.py > /dev/null 2>&1")
    results["dataset_generation"] = time.time() - start
    
    start = time.time()
    os.system("python -m pytest -q > /dev/null 2>&1")
    results["pytest"] = time.time() - start
    
    start = time.time()
    os.system("python scripts/final_demo.py > /dev/null 2>&1")
    results["final_experiment"] = time.time() - start
    
    with open("docs/performance_measurements.md", "w") as f:
        f.write("# Performance Measurements\n\n")
        for k, v in results.items():
            f.write(f"- {k}: {v:.2f} seconds\n")
            
    print("Performance measurements saved.")

if __name__ == "__main__":
    measure()
