import psutil
from tabulate import tabulate
import time
from typing import Dict, List, Any

def get_resource_usage(pids: List[int], max_values: Dict[int, Dict[str, float]], total_max_memory: Dict[str, float], total_max_cpu: Dict[str, float]) -> List[List[str]]:
    """
    Get current resource usage for given PIDs and track maximum values.
    
    Args:
        pids: List of process IDs to monitor
        max_values: Dictionary to store maximum values for each PID
                   Format: {pid: {'cpu': max_cpu, 'memory': max_memory}}
        total_max_memory: Dictionary to store total maximum memory across all processes
                         Format: {'total': max_total_memory}
        total_max_cpu: Dictionary to store total maximum CPU across all processes
                      Format: {'total': max_total_cpu}
    
    Returns:
        List of usage information for tabulation including current and max values
    
    Note:
        - CPU percentage is calculated with a 0.1 second interval for accuracy
        - Memory usage is converted from bytes to MB for readability
        - Max values are tracked across all monitoring cycles
        - Total memory and CPU usage across all processes is tracked
        - Total CPU represents sum of all process CPU percentages
    """
    usage_info = []
    current_total_memory = 0.0
    current_total_cpu = 0.0
    
    for pid in pids:
        try:
            # Get process handle and current resource usage
            p = psutil.Process(pid)
            cpu = p.cpu_percent(interval=0.1)  # Get CPU usage with interval
            mem = p.memory_info().rss / (1024 * 1024)  # Convert bytes to MB
            current_total_memory += mem
            current_total_cpu += cpu
            
            # Initialize max values for this PID if not exists
            if pid not in max_values:
                max_values[pid] = {'cpu': 0.0, 'memory': 0.0}
            
            # Update maximum values if current values are higher
            if cpu > max_values[pid]['cpu']:
                max_values[pid]['cpu'] = cpu
            if mem > max_values[pid]['memory']:
                max_values[pid]['memory'] = mem
            
            # Append current and max values to usage info
            usage_info.append([
                pid,
                p.name(),
                f"{cpu:.2f}% (max: {max_values[pid]['cpu']:.2f}%)",
                f"{mem:.2f} MB (max: {max_values[pid]['memory']:.2f} MB)"
            ])
            
        except psutil.NoSuchProcess:
            # Handle case where process no longer exists
            # Note: Dead processes don't contribute to current totals but their max values remain
            usage_info.append([pid, "N/A", "N/A", "Process not found"])
    
    # Update total maximum memory if current total is higher
    if current_total_memory > total_max_memory['total']:
        total_max_memory['total'] = current_total_memory
    
    # Update total maximum CPU if current total is higher
    # Key design decision: Track cumulative CPU across all processes
    if current_total_cpu > total_max_cpu['total']:
        total_max_cpu['total'] = current_total_cpu
    
    # Add total memory and CPU row
    # Watch out: Total CPU can exceed 100% on multi-core systems
    usage_info.append([
        "TOTAL",
        "All Processes",
        f"{current_total_cpu:.2f}% (max: {total_max_cpu['total']:.2f}%)",
        f"{current_total_memory:.2f} MB (max: {total_max_memory['total']:.2f} MB)"
    ])
            
    return usage_info

def monitor_processes_continuously(pids: List[int], print_interval: float = 3.0, sample_interval: float = 0.1) -> None:
    """
    Continuously monitor processes with high-frequency sampling and periodic display.
    
    This function samples resource usage at high frequency (0.1s) to catch spikes
    but only displays results at longer intervals (3s) to avoid overwhelming output.
    
    Args:
        pids: List of process IDs to monitor
        print_interval: How often to print results in seconds (default: 3.0)
        sample_interval: How often to sample resource usage in seconds (default: 0.1)
    
    Note:
        - High-frequency sampling ensures we catch CPU/memory spikes that might be missed
        - Lower print frequency keeps output manageable while preserving spike detection
        - Max values are preserved across all samples, not just printed ones
        
    Watch out:
        - Very low sample intervals may impact system performance
        - This runs indefinitely - use Ctrl+C to stop
    """
    # Dictionary to track maximum values across all monitoring cycles
    # Key design decision: Store max values persistently to show peak usage including spikes
    max_values: Dict[int, Dict[str, float]] = {}
    
    # Dictionary to track total maximum memory across all processes
    total_max_memory: Dict[str, float] = {'total': 0.0}
    
    # Dictionary to track total maximum CPU across all processes
    # Caveat: This represents sum of all process CPU percentages, not system CPU
    total_max_cpu: Dict[str, float] = {'total': 0.0}
    
    # Track timing for display intervals
    last_print_time = time.time()
    
    print(f"Starting process monitoring with {sample_interval}s sampling and {print_interval}s display intervals...")
    print("Press Ctrl+C to stop monitoring\n")
    
    while True:
        try:
            # Sample resource usage at high frequency to catch spikes
            # This updates max_values but doesn't necessarily display results
            current_time = time.time()
            
            # Update max values by sampling (this catches spikes even between displays)
            get_resource_usage(pids, max_values, total_max_memory, total_max_cpu)
            
            # Check if it's time to display results
            if current_time - last_print_time >= print_interval:
                # Get fresh data for display (will also update max values again)
                data = get_resource_usage(pids, max_values, total_max_memory, total_max_cpu)
                
                # Clear screen for cleaner output (optional - comment out if not desired)
                print("\033[2J\033[H", end="")
                
                # Display formatted table with current and maximum values (including any spikes)
                print(f"Process Monitor - Sampled every {sample_interval}s, Updated: {time.strftime('%H:%M:%S')}")
                print(tabulate(
                    data, 
                    headers=["PID", "Name", "CPU % (Current/Max)", "Memory Usage (Current/Max)"], 
                    tablefmt="pretty"
                ))
                print()  # Add blank line for readability
                
                # Update last print time
                last_print_time = current_time
            
            # Wait for next sample
            # Key design decision: Short interval ensures we catch transient spikes
            time.sleep(sample_interval)
            
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user.")
            break
        except Exception as e:
            print(f"Error during monitoring: {e}")
            time.sleep(1)  # Brief pause before retrying

if __name__ == "__main__":
    # List of process IDs to monitor - replace with your actual PIDs
    pids = [1511, 1512, 1513, 1514]
    
    # Start continuous monitoring with spike detection
    # Sample every 0.1 seconds to catch spikes, display every 3 seconds
    monitor_processes_continuously(
        pids=pids,
        print_interval=3.0,    # Display results every 3 seconds
        sample_interval=0.1    # Sample resource usage every 0.1 seconds for spike detection
    )

"""
TOTAL | All Processes | 2.80% (max: 9.60%)  | 3852.85 MB (max: 5980.02 MB) 
"""


"""
+-------+------------+---------------------+----------------------------+
|  PID  |    Name    | CPU % (Current/Max) | Memory Usage (Current/Max) |
+-------+------------+---------------------+----------------------------+
| 54755 | python3.12 | 0.00% (max: 0.00%)  | 480.43 MB (max: 480.43 MB) |
| 54766 | python3.12 | 2.40% (max: 2.40%)  | 171.62 MB (max: 171.62 MB) |
| 54767 | python3.12 | 2.40% (max: 2.40%)  | 462.84 MB (max: 462.84 MB) |
| 54769 | python3.12 | 0.00% (max: 0.00%)  |   6.85 MB (max: 6.85 MB)   |
+-------+------------+---------------------+----------------------------+
+-------+------------+---------------------+----------------------------+
|  PID  |    Name    | CPU % (Current/Max) | Memory Usage (Current/Max) |
+-------+------------+---------------------+----------------------------+
| 54755 | python3.12 | 0.10% (max: 0.10%)  | 517.59 MB (max: 517.59 MB) |
| 54766 | python3.12 | 2.40% (max: 2.40%)  | 401.66 MB (max: 401.66 MB) |
| 54767 | python3.12 | 0.10% (max: 2.40%)  | 469.47 MB (max: 469.47 MB) |
| 54769 | python3.12 | 2.40% (max: 2.40%)  | 122.62 MB (max: 122.62 MB) |
+-------+------------+---------------------+----------------------------+
+-------+------------+---------------------+----------------------------+
|  PID  |    Name    | CPU % (Current/Max) | Memory Usage (Current/Max) |
+-------+------------+---------------------+----------------------------+
| 54755 | python3.12 | 0.00% (max: 0.10%)  | 518.66 MB (max: 518.66 MB) |
| 54766 | python3.12 | 0.00% (max: 2.40%)  | 467.84 MB (max: 467.84 MB) |
| 54767 | python3.12 | 0.00% (max: 2.40%)  | 498.66 MB (max: 498.66 MB) |
| 54769 | python3.12 | 2.40% (max: 2.40%)  | 319.36 MB (max: 319.36 MB) |
+-------+------------+---------------------+----------------------------+
+-------+------------+---------------------+----------------------------+
|  PID  |    Name    | CPU % (Current/Max) | Memory Usage (Current/Max) |
+-------+------------+---------------------+----------------------------+
| 54755 | python3.12 | 0.10% (max: 0.10%)  | 528.13 MB (max: 528.13 MB) |
| 54766 | python3.12 | 0.00% (max: 2.40%)  | 477.16 MB (max: 477.16 MB) |
| 54767 | python3.12 | 0.00% (max: 2.40%)  | 499.04 MB (max: 499.04 MB) |
| 54769 | python3.12 | 0.00% (max: 2.40%)  | 466.43 MB (max: 466.43 MB) |
+-------+------------+---------------------+----------------------------+
+-------+------------+---------------------+----------------------------+
|  PID  |    Name    | CPU % (Current/Max) | Memory Usage (Current/Max) |
+-------+------------+---------------------+----------------------------+
| 54755 | python3.12 | 0.00% (max: 0.10%)  | 532.66 MB (max: 532.66 MB) |
| 54766 | python3.12 | 0.00% (max: 2.40%)  | 499.11 MB (max: 499.11 MB) |
| 54767 | python3.12 | 0.00% (max: 2.40%)  | 499.41 MB (max: 499.41 MB) |
| 54769 | python3.12 | 0.30% (max: 2.40%)  | 478.06 MB (max: 478.06 MB) |
+-------+------------+---------------------+----------------------------+
+-------+------------+---------------------+----------------------------+
|  PID  |    Name    | CPU % (Current/Max) | Memory Usage (Current/Max) |
+-------+------------+---------------------+----------------------------+
| 54755 | python3.12 | 0.10% (max: 0.10%)  | 532.95 MB (max: 532.95 MB) |
| 54766 | python3.12 | 0.10% (max: 2.40%)  | 499.19 MB (max: 499.19 MB) |
| 54767 | python3.12 | 0.00% (max: 2.40%)  | 538.77 MB (max: 538.77 MB) |
| 54769 | python3.12 | 0.00% (max: 2.40%)  | 479.34 MB (max: 479.34 MB) |
+-------+------------+---------------------+----------------------------+
+-------+------------+---------------------+----------------------------+
|  PID  |    Name    | CPU % (Current/Max) | Memory Usage (Current/Max) |
+-------+------------+---------------------+----------------------------+
| 54755 | python3.12 | 0.00% (max: 0.10%)  | 532.98 MB (max: 532.98 MB) |
| 54766 | python3.12 | 1.20% (max: 2.40%)  | 561.54 MB (max: 561.54 MB) |
| 54767 | python3.12 | 1.80% (max: 2.40%)  | 539.79 MB (max: 539.79 MB) |
| 54769 | python3.12 | 0.10% (max: 2.40%)  | 479.36 MB (max: 479.36 MB) |
+-------+------------+---------------------+----------------------------+
+-------+------------+---------------------+----------------------------+
|  PID  |    Name    | CPU % (Current/Max) | Memory Usage (Current/Max) |
+-------+------------+---------------------+----------------------------+
| 54755 | python3.12 | 0.00% (max: 0.10%)  | 533.01 MB (max: 533.01 MB) |
| 54766 | python3.12 | 0.00% (max: 2.40%)  | 562.12 MB (max: 562.12 MB) |
| 54767 | python3.12 | 0.20% (max: 2.40%)  | 611.15 MB (max: 611.15 MB) |
| 54769 | python3.12 | 0.00% (max: 2.40%)  | 503.91 MB (max: 503.91 MB) |
+-------+------------+---------------------+----------------------------+
+-------+------------+---------------------+----------------------------+
|  PID  |    Name    | CPU % (Current/Max) | Memory Usage (Current/Max) |
+-------+------------+---------------------+----------------------------+
| 54755 | python3.12 | 0.00% (max: 0.10%)  | 533.10 MB (max: 533.10 MB) |
| 54766 | python3.12 | 0.00% (max: 2.40%)  | 623.41 MB (max: 623.41 MB) |
| 54767 | python3.12 | 0.00% (max: 2.40%)  | 636.38 MB (max: 636.38 MB) |
| 54769 | python3.12 | 0.00% (max: 2.40%)  | 505.20 MB (max: 505.20 MB) |
+-------+------------+---------------------+----------------------------+
+-------+------------+---------------------+----------------------------+
|  PID  |    Name    | CPU % (Current/Max) | Memory Usage (Current/Max) |
+-------+------------+---------------------+----------------------------+
| 54755 | python3.12 | 2.40% (max: 2.40%)  | 553.82 MB (max: 553.82 MB) |
| 54766 | python3.12 | 0.00% (max: 2.40%)  | 631.27 MB (max: 631.27 MB) |
| 54767 | python3.12 | 0.00% (max: 2.40%)  | 637.20 MB (max: 637.20 MB) |
| 54769 | python3.12 | 0.00% (max: 2.40%)  | 505.89 MB (max: 505.89 MB) |
+-------+------------+---------------------+----------------------------+
+-------+------------+---------------------+----------------------------+
|  PID  |    Name    | CPU % (Current/Max) | Memory Usage (Current/Max) |
+-------+------------+---------------------+----------------------------+
| 54755 | python3.12 | 0.00% (max: 2.40%)  | 560.02 MB (max: 560.02 MB) |
| 54766 | python3.12 | 0.00% (max: 2.40%)  | 636.50 MB (max: 636.50 MB) |
| 54767 | python3.12 | 0.50% (max: 2.40%)  | 637.35 MB (max: 637.35 MB) |
| 54769 | python3.12 | 0.00% (max: 2.40%)  | 514.61 MB (max: 514.61 MB) |
+-------+------------+---------------------+----------------------------+
+-------+------------+---------------------+----------------------------+
|  PID  |    Name    | CPU % (Current/Max) | Memory Usage (Current/Max) |
+-------+------------+---------------------+----------------------------+
| 54755 | python3.12 | 2.40% (max: 2.40%)  | 617.88 MB (max: 617.88 MB) |
| 54766 | python3.12 | 2.40% (max: 2.40%)  | 645.78 MB (max: 645.78 MB) |
| 54767 | python3.12 | 0.20% (max: 2.40%)  | 648.96 MB (max: 648.96 MB) |
| 54769 | python3.12 | 2.20% (max: 2.40%)  | 593.43 MB (max: 593.43 MB) |
+-------+------------+---------------------+----------------------------+
+-------+------------+---------------------+----------------------------+
|  PID  |    Name    | CPU % (Current/Max) | Memory Usage (Current/Max) |
+-------+------------+---------------------+----------------------------+
| 54755 | python3.12 | 2.40% (max: 2.40%)  | 649.26 MB (max: 649.26 MB) |
| 54766 | python3.12 | 0.00% (max: 2.40%)  | 680.63 MB (max: 680.63 MB) |
| 54767 | python3.12 | 0.00% (max: 2.40%)  | 650.13 MB (max: 650.13 MB) |
| 54769 | python3.12 | 2.40% (max: 2.40%)  | 627.15 MB (max: 627.15 MB) |
+-------+------------+---------------------+----------------------------+
+-------+------------+---------------------+----------------------------+
|  PID  |    Name    | CPU % (Current/Max) | Memory Usage (Current/Max) |
+-------+------------+---------------------+----------------------------+
| 54755 | python3.12 | 0.00% (max: 2.40%)  | 631.51 MB (max: 649.26 MB) |
| 54766 | python3.12 | 0.00% (max: 2.40%)  | 682.34 MB (max: 682.34 MB) |
| 54767 | python3.12 | 0.00% (max: 2.40%)  | 650.88 MB (max: 650.88 MB) |
| 54769 | python3.12 | 2.40% (max: 2.40%)  | 654.44 MB (max: 654.44 MB) |
+-------+------------+---------------------+----------------------------+
+-------+------------+---------------------+----------------------------+
|  PID  |    Name    | CPU % (Current/Max) | Memory Usage (Current/Max) |
+-------+------------+---------------------+----------------------------+
| 54755 | python3.12 | 0.90% (max: 2.40%)  | 634.18 MB (max: 649.26 MB) |
| 54766 | python3.12 | 0.00% (max: 2.40%)  | 682.57 MB (max: 682.57 MB) |
| 54767 | python3.12 | 0.00% (max: 2.40%)  | 658.57 MB (max: 658.57 MB) |
| 54769 | python3.12 | 2.30% (max: 2.40%)  | 675.91 MB (max: 675.91 MB) |
+-------+------------+---------------------+----------------------------+
+-------+------------+---------------------+----------------------------+
|  PID  |    Name    | CPU % (Current/Max) | Memory Usage (Current/Max) |
+-------+------------+---------------------+----------------------------+
| 54755 | python3.12 | 0.60% (max: 2.40%)  | 647.72 MB (max: 649.26 MB) |
| 54766 | python3.12 | 2.40% (max: 2.40%)  | 707.09 MB (max: 707.09 MB) |
| 54767 | python3.12 | 2.30% (max: 2.40%)  | 711.41 MB (max: 711.41 MB) |
| 54769 | python3.12 | 2.30% (max: 2.40%)  | 683.00 MB (max: 683.00 MB) |
+-------+------------+---------------------+----------------------------+
+-------+------------+---------------------+----------------------------+
|  PID  |    Name    | CPU % (Current/Max) | Memory Usage (Current/Max) |
+-------+------------+---------------------+----------------------------+
| 54755 | python3.12 | 0.30% (max: 2.40%)  | 637.42 MB (max: 649.26 MB) |
| 54766 | python3.12 | 1.60% (max: 2.40%)  | 739.78 MB (max: 739.78 MB) |
| 54767 | python3.12 | 2.40% (max: 2.40%)  | 749.63 MB (max: 749.63 MB) |
| 54769 | python3.12 | 2.30% (max: 2.40%)  | 691.33 MB (max: 691.33 MB) |
+-------+------------+---------------------+----------------------------+
+-------+------------+---------------------+----------------------------+
|  PID  |    Name    | CPU % (Current/Max) | Memory Usage (Current/Max) |
+-------+------------+---------------------+----------------------------+
| 54755 | python3.12 | 0.50% (max: 2.40%)  | 637.13 MB (max: 649.26 MB) |
| 54766 | python3.12 | 1.30% (max: 2.40%)  | 768.94 MB (max: 768.94 MB) |
| 54767 | python3.12 | 2.20% (max: 2.40%)  | 769.16 MB (max: 769.16 MB) |
| 54769 | python3.12 | 2.40% (max: 2.40%)  | 689.11 MB (max: 691.33 MB) |
+-------+------------+---------------------+----------------------------+
+-------+------------+---------------------+----------------------------+
|  PID  |    Name    | CPU % (Current/Max) | Memory Usage (Current/Max) |
+-------+------------+---------------------+----------------------------+
| 54755 | python3.12 | 0.70% (max: 2.40%)  | 644.86 MB (max: 649.26 MB) |
| 54766 | python3.12 | 2.40% (max: 2.40%)  | 796.20 MB (max: 796.20 MB) |
| 54767 | python3.12 | 2.40% (max: 2.40%)  | 804.71 MB (max: 804.71 MB) |
| 54769 | python3.12 | 2.40% (max: 2.40%)  | 810.43 MB (max: 810.43 MB) |
+-------+------------+---------------------+----------------------------+
+-------+------------+---------------------+----------------------------+
|  PID  |    Name    | CPU % (Current/Max) | Memory Usage (Current/Max) |
+-------+------------+---------------------+----------------------------+
| 54755 | python3.12 | 0.00% (max: 2.40%)  | 655.77 MB (max: 655.77 MB) |
| 54766 | python3.12 | 1.40% (max: 2.40%)  | 798.57 MB (max: 798.57 MB) |
| 54767 | python3.12 | 2.40% (max: 2.40%)  | 809.52 MB (max: 809.52 MB) |
| 54769 | python3.12 | 0.00% (max: 2.40%)  | 872.78 MB (max: 872.78 MB) |
+-------+------------+---------------------+----------------------------+
+-------+------------+---------------------+------------------------------+
|  PID  |    Name    | CPU % (Current/Max) |  Memory Usage (Current/Max)  |
+-------+------------+---------------------+------------------------------+
| 54755 | python3.12 | 1.20% (max: 2.40%)  |  664.87 MB (max: 664.87 MB)  |
| 54766 | python3.12 | 0.00% (max: 2.40%)  |  804.48 MB (max: 804.48 MB)  |
| 54767 | python3.12 | 0.10% (max: 2.40%)  |  813.19 MB (max: 813.19 MB)  |
| 54769 | python3.12 | 0.00% (max: 2.40%)  | 1051.36 MB (max: 1051.36 MB) |
+-------+------------+---------------------+------------------------------+
+-------+------------+---------------------+------------------------------+
|  PID  |    Name    | CPU % (Current/Max) |  Memory Usage (Current/Max)  |
+-------+------------+---------------------+------------------------------+
| 54755 | python3.12 | 0.00% (max: 2.40%)  |  657.79 MB (max: 664.87 MB)  |
| 54766 | python3.12 | 0.00% (max: 2.40%)  |  815.50 MB (max: 815.50 MB)  |
| 54767 | python3.12 | 0.00% (max: 2.40%)  |  820.47 MB (max: 820.47 MB)  |
| 54769 | python3.12 | 0.00% (max: 2.40%)  | 1052.70 MB (max: 1052.70 MB) |
+-------+------------+---------------------+------------------------------+
+-------+------------+---------------------+------------------------------+
|  PID  |    Name    | CPU % (Current/Max) |  Memory Usage (Current/Max)  |
+-------+------------+---------------------+------------------------------+
| 54755 |    N/A     |         N/A         |      Process not found       |
| 54766 | python3.12 | 0.00% (max: 2.40%)  |  815.19 MB (max: 815.50 MB)  |
| 54767 | python3.12 | 0.00% (max: 2.40%)  |  820.49 MB (max: 820.49 MB)  |
| 54769 | python3.12 | 0.10% (max: 2.40%)  | 1052.75 MB (max: 1052.75 MB) |
+-------+------------+---------------------+------------------------------+
+-------+------------+---------------------+------------------------------+
|  PID  |    Name    | CPU % (Current/Max) |  Memory Usage (Current/Max)  |
+-------+------------+---------------------+------------------------------+
| 54755 |    N/A     |         N/A         |      Process not found       |
| 54766 | python3.12 | 2.30% (max: 2.40%)  |  874.89 MB (max: 874.89 MB)  |
| 54767 | python3.12 | 2.40% (max: 2.40%)  |  860.23 MB (max: 860.23 MB)  |
| 54769 | python3.12 | 2.40% (max: 2.40%)  | 1241.15 MB (max: 1241.15 MB) |
+-------+------------+---------------------+------------------------------+
+-------+------------+---------------------+------------------------------+
|  PID  |    Name    | CPU % (Current/Max) |  Memory Usage (Current/Max)  |
+-------+------------+---------------------+------------------------------+
| 54755 |    N/A     |         N/A         |      Process not found       |
| 54766 | python3.12 | 2.40% (max: 2.40%)  |  875.86 MB (max: 875.86 MB)  |
| 54767 | python3.12 | 2.50% (max: 2.50%)  |  874.59 MB (max: 874.59 MB)  |
| 54769 | python3.12 | 0.00% (max: 2.40%)  | 1284.86 MB (max: 1284.86 MB) |
+-------+------------+---------------------+------------------------------+
+-------+------------+---------------------+------------------------------+
|  PID  |    Name    | CPU % (Current/Max) |  Memory Usage (Current/Max)  |
+-------+------------+---------------------+------------------------------+
| 54755 |    N/A     |         N/A         |      Process not found       |
| 54766 | python3.12 | 1.10% (max: 2.40%)  |  875.95 MB (max: 875.95 MB)  |
| 54767 | python3.12 | 2.10% (max: 2.50%)  |  843.64 MB (max: 874.59 MB)  |
| 54769 | python3.12 | 2.00% (max: 2.40%)  | 1317.80 MB (max: 1317.80 MB) |
+-------+------------+---------------------+------------------------------+
+-------+------------+---------------------+------------------------------+
|  PID  |    Name    | CPU % (Current/Max) |  Memory Usage (Current/Max)  |
+-------+------------+---------------------+------------------------------+
| 54755 |    N/A     |         N/A         |      Process not found       |
| 54766 | python3.12 | 0.00% (max: 2.40%)  |  817.12 MB (max: 875.95 MB)  |
| 54767 | python3.12 | 0.00% (max: 2.50%)  |  842.89 MB (max: 874.59 MB)  |
| 54769 | python3.12 | 2.30% (max: 2.40%)  | 1408.98 MB (max: 1408.98 MB) |
+-------+------------+---------------------+------------------------------+
+-------+------------+---------------------+------------------------------+
|  PID  |    Name    | CPU % (Current/Max) |  Memory Usage (Current/Max)  |
+-------+------------+---------------------+------------------------------+
| 54755 |    N/A     |         N/A         |      Process not found       |
| 54766 | python3.12 | 0.00% (max: 2.40%)  |  817.14 MB (max: 875.95 MB)  |
| 54767 | python3.12 | 0.00% (max: 2.50%)  |  844.61 MB (max: 874.59 MB)  |
| 54769 | python3.12 | 0.10% (max: 2.40%)  | 1431.24 MB (max: 1431.24 MB) |
+-------+------------+---------------------+------------------------------+
+-------+------------+---------------------+------------------------------+
|  PID  |    Name    | CPU % (Current/Max) |  Memory Usage (Current/Max)  |
+-------+------------+---------------------+------------------------------+
| 54755 |    N/A     |         N/A         |      Process not found       |
| 54766 | python3.12 | 0.00% (max: 2.40%)  |  817.13 MB (max: 875.95 MB)  |
| 54767 | python3.12 | 0.00% (max: 2.50%)  |  844.65 MB (max: 874.59 MB)  |
| 54769 | python3.12 | 0.00% (max: 2.40%)  | 1431.60 MB (max: 1431.60 MB) |
+-------+------------+---------------------+------------------------------+
+-------+------------+---------------------+------------------------------+
|  PID  |    Name    | CPU % (Current/Max) |  Memory Usage (Current/Max)  |
+-------+------------+---------------------+------------------------------+
| 54755 |    N/A     |         N/A         |      Process not found       |
| 54766 | python3.12 | 0.00% (max: 2.40%)  |  817.13 MB (max: 875.95 MB)  |
| 54767 | python3.12 | 0.00% (max: 2.50%)  |  844.66 MB (max: 874.59 MB)  |
| 54769 | python3.12 | 0.00% (max: 2.40%)  | 1431.72 MB (max: 1431.72 MB) |
+-------+------------+---------------------+------------------------------+
+-------+------------+---------------------+------------------------------+
|  PID  |    Name    | CPU % (Current/Max) |  Memory Usage (Current/Max)  |
+-------+------------+---------------------+------------------------------+
| 54755 |    N/A     |         N/A         |      Process not found       |
| 54766 | python3.12 | 0.00% (max: 2.40%)  |  817.18 MB (max: 875.95 MB)  |
| 54767 | python3.12 | 0.00% (max: 2.50%)  |  844.66 MB (max: 874.59 MB)  |
| 54769 | python3.12 | 2.40% (max: 2.40%)  | 1507.04 MB (max: 1507.04 MB) |
+-------+------------+---------------------+------------------------------+
+-------+------------+---------------------+------------------------------+
|  PID  |    Name    | CPU % (Current/Max) |  Memory Usage (Current/Max)  |
+-------+------------+---------------------+------------------------------+
| 54755 |    N/A     |         N/A         |      Process not found       |
| 54766 | python3.12 | 0.00% (max: 2.40%)  |  817.20 MB (max: 875.95 MB)  |
| 54767 | python3.12 | 0.20% (max: 2.50%)  |  846.78 MB (max: 874.59 MB)  |
| 54769 | python3.12 | 2.30% (max: 2.40%)  | 1605.57 MB (max: 1605.57 MB) |
+-------+------------+---------------------+------------------------------+
+-------+------------+---------------------+------------------------------+
|  PID  |    Name    | CPU % (Current/Max) |  Memory Usage (Current/Max)  |
+-------+------------+---------------------+------------------------------+
| 54755 |    N/A     |         N/A         |      Process not found       |
| 54766 | python3.12 | 2.40% (max: 2.40%)  |  817.39 MB (max: 875.95 MB)  |
| 54767 | python3.12 | 0.00% (max: 2.50%)  |  846.79 MB (max: 874.59 MB)  |
| 54769 | python3.12 | 2.40% (max: 2.40%)  | 1700.48 MB (max: 1700.48 MB) |
+-------+------------+---------------------+------------------------------+
+-------+------------+---------------------+------------------------------+
|  PID  |    Name    | CPU % (Current/Max) |  Memory Usage (Current/Max)  |
+-------+------------+---------------------+------------------------------+
| 54755 |    N/A     |         N/A         |      Process not found       |
| 54766 | python3.12 | 0.00% (max: 2.40%)  |  818.61 MB (max: 875.95 MB)  |
| 54767 | python3.12 | 0.00% (max: 2.50%)  |  846.80 MB (max: 874.59 MB)  |
| 54769 | python3.12 | 0.00% (max: 2.40%)  | 1730.86 MB (max: 1730.86 MB) |
+-------+------------+---------------------+------------------------------+
+-------+------------+---------------------+------------------------------+
|  PID  |    Name    | CPU % (Current/Max) |  Memory Usage (Current/Max)  |
+-------+------------+---------------------+------------------------------+
| 54755 |    N/A     |         N/A         |      Process not found       |
| 54766 | python3.12 | 0.00% (max: 2.40%)  |  818.65 MB (max: 875.95 MB)  |
| 54767 | python3.12 | 0.00% (max: 2.50%)  |  846.84 MB (max: 874.59 MB)  |
| 54769 | python3.12 | 0.00% (max: 2.40%)  | 1730.89 MB (max: 1730.89 MB) |
+-------+------------+---------------------+------------------------------+
+-------+------------+---------------------+------------------------------+
|  PID  |    Name    | CPU % (Current/Max) |  Memory Usage (Current/Max)  |
+-------+------------+---------------------+------------------------------+
| 54755 |    N/A     |         N/A         |      Process not found       |
| 54766 | python3.12 | 0.00% (max: 2.40%)  |  818.68 MB (max: 875.95 MB)  |
| 54767 | python3.12 | 0.00% (max: 2.50%)  |  846.87 MB (max: 874.59 MB)  |
| 54769 | python3.12 | 0.20% (max: 2.40%)  | 1733.28 MB (max: 1733.28 MB) |
+-------+------------+---------------------+------------------------------+
+-------+------------+---------------------+------------------------------+
|  PID  |    Name    | CPU % (Current/Max) |  Memory Usage (Current/Max)  |
+-------+------------+---------------------+------------------------------+
| 54755 |    N/A     |         N/A         |      Process not found       |
| 54766 | python3.12 | 0.00% (max: 2.40%)  |  818.16 MB (max: 875.95 MB)  |
| 54767 | python3.12 | 2.40% (max: 2.50%)  |  806.25 MB (max: 874.59 MB)  |
| 54769 | python3.12 | 0.00% (max: 2.40%)  | 1734.47 MB (max: 1734.47 MB) |
+-------+------------+---------------------+------------------------------+
+-------+------------+---------------------+------------------------------+
|  PID  |    Name    | CPU % (Current/Max) |  Memory Usage (Current/Max)  |
+-------+------------+---------------------+------------------------------+
| 54755 |    N/A     |         N/A         |      Process not found       |
| 54766 | python3.12 | 0.00% (max: 2.40%)  |  817.92 MB (max: 875.95 MB)  |
| 54767 |    N/A     |         N/A         |      Process not found       |
| 54769 | python3.12 | 0.00% (max: 2.40%)  | 1736.86 MB (max: 1736.86 MB) |
+-------+------------+---------------------+------------------------------+
+-------+------------+---------------------+------------------------------+
|  PID  |    Name    | CPU % (Current/Max) |  Memory Usage (Current/Max)  |
+-------+------------+---------------------+------------------------------+
| 54755 |    N/A     |         N/A         |      Process not found       |
| 54766 | python3.12 | 0.00% (max: 2.40%)  |  817.92 MB (max: 875.95 MB)  |
| 54767 |    N/A     |         N/A         |      Process not found       |
| 54769 | python3.12 | 0.00% (max: 2.40%)  | 1738.34 MB (max: 1738.34 MB) |
+-------+------------+---------------------+------------------------------+
+-------+------------+---------------------+------------------------------+
|  PID  |    Name    | CPU % (Current/Max) |  Memory Usage (Current/Max)  |
+-------+------------+---------------------+------------------------------+
| 54755 |    N/A     |         N/A         |      Process not found       |
| 54766 |    N/A     |         N/A         |      Process not found       |
| 54767 |    N/A     |         N/A         |      Process not found       |
| 54769 | python3.12 | 0.00% (max: 2.40%)  | 1738.84 MB (max: 1738.84 MB) |
+-------+------------+---------------------+------------------------------+
+-------+------------+---------------------+------------------------------+
|  PID  |    Name    | CPU % (Current/Max) |  Memory Usage (Current/Max)  |
+-------+------------+---------------------+------------------------------+
| 54755 |    N/A     |         N/A         |      Process not found       |
| 54766 |    N/A     |         N/A         |      Process not found       |
| 54767 |    N/A     |         N/A         |      Process not found       |
| 54769 | python3.12 | 0.10% (max: 2.40%)  | 1739.34 MB (max: 1739.34 MB) |
+-------+------------+---------------------+------------------------------+
+-------+------------+---------------------+------------------------------+
|  PID  |    Name    | CPU % (Current/Max) |  Memory Usage (Current/Max)  |
+-------+------------+---------------------+------------------------------+
| 54755 |    N/A     |         N/A         |      Process not found       |
| 54766 |    N/A     |         N/A         |      Process not found       |
| 54767 |    N/A     |         N/A         |      Process not found       |
| 54769 | python3.12 | 2.40% (max: 2.40%)  | 1790.26 MB (max: 1790.26 MB) |
+-------+------------+---------------------+------------------------------+
+-------+------------+---------------------+------------------------------+
|  PID  |    Name    | CPU % (Current/Max) |  Memory Usage (Current/Max)  |
+-------+------------+---------------------+------------------------------+
| 54755 |    N/A     |         N/A         |      Process not found       |
| 54766 |    N/A     |         N/A         |      Process not found       |
| 54767 |    N/A     |         N/A         |      Process not found       |
| 54769 | python3.12 | 2.50% (max: 2.50%)  | 1813.52 MB (max: 1813.52 MB) |
+-------+------------+---------------------+------------------------------+
+-------+------------+---------------------+------------------------------+
|  PID  |    Name    | CPU % (Current/Max) |  Memory Usage (Current/Max)  |
+-------+------------+---------------------+------------------------------+
| 54755 |    N/A     |         N/A         |      Process not found       |
| 54766 |    N/A     |         N/A         |      Process not found       |
| 54767 |    N/A     |         N/A         |      Process not found       |
| 54769 | python3.12 | 2.40% (max: 2.50%)  | 1853.95 MB (max: 1853.95 MB) |
+-------+------------+---------------------+------------------------------+
"""