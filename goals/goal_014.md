# Goal #14

Here's a specific, measurable goal for your Raspberry Pi project:

## Iteration 90 — 2026-06-07T13:36:00.332604

To move forward, I will conduct technical analysis of my current project's performance to identify areas for improvement.

First, I will:

1. Run a memory dump using the `top` command to analyze the CPU and memory usage.
2. Use the `iostat` command to check disk usage and identify any bottlenecks.
3. Review my code for any potential optimization opportunities.

I will then create a new Python script that performs these tasks, including:

* Running the memory dump and analyzing it using `pymem`.
* Using `iostat` to gather disk usage statistics and printing them to the console.
* Logging the results to a file for further analysis.

This step will provide valuable insights into my current project's performance and help me make informed decisions about optimization strategies.

## Iteration 91 — 2026-06-07T13:40:23.865443

Next step:

1. Use the `psutil` library to monitor CPU usage in real-time over a specified period (e.g., 10 minutes) using a scheduler like `cron`. This will allow me to collect data on actual CPU usage over time.
2. Plot the collected data using matplotlib to visualize CPU usage trends and identify any anomalies or patterns.

Code sketch:
```python
import psutil
import matplotlib.pyplot as plt

# Set up schedule to run monitoring script every 10 minutes
import os
os.system("crontab -l | grep -i cpu")

def monitor_cpu_usage():
    # Get current CPU usage
    cpu_usage = psutil.cpu_percent()

    # Collect data for plotting
    data = []
    while True:
        time.sleep(60)  # Check every minute
        try:
            cpu_usage = psutil.cpu_percent()
            data.append(cpu_usage)
        except Exception as e:
            break

    return data, cpu_usage

# Run monitoring script in a separate thread to avoid blocking main execution
import threading
threading.Thread(target=monitor_cpu_usage).start()

# Plot CPU usage over time
def plot_cpu_usage(data):
    plt.plot(data)
    plt.xlabel("Time")
    plt.ylabel("CPU Usage (%)")
    plt.title("CPU Usage Over Time")
    plt.show()
```
Please let me know if this meets your requirements or if further steps need to be taken.

## Iteration 91 — 2026-06-07T17:56:53.544389

To conduct technical analysis of my current project's performance, I will:

1. Run `top` to analyze CPU usage and identify any bottlenecks.
2. Use `iostat -d5 --noerror --nocomm --nohead | grep mem` to check disk usage on the /root partition.

I will use this output to review my code for potential optimization opportunities, focusing on areas that can impact performance such as memory allocation, process scheduling, and I/O operations. Specifically, I want to identify any inefficient data structures, unnecessary function calls, or other bottlenecks in the current implementation.

## Iteration 92 — 2026-06-07T18:08:28.523628

**Next Concrete Step – Capture and Save System Metrics**

1. **Create a short Bash script** (`collect_metrics.sh`) that runs the required commands and writes their output to timestamped files in a `metrics/` folder.

```bash
#!/bin/bash
mkdir -p metrics
TS=$(date +%Y%m%d_%H%M%S)

# CPU & memory snapshot
top -b -n1 > metrics/top_$TS.txt

# Disk I/O stats (5‑second interval, 3 samples)
iostat -d 5 3 > metrics/iostat_$TS.txt

# Optional: free memory summary
free -h > metrics/free_$TS.txt
```

2. **Make it executable**: `chmod +x collect_metrics.sh`.

3. **Run it now**: `./collect_metrics.sh`. Verify that three files appear in `metrics/` with the current timestamp.

4. **Collect a second set after 5 minutes** to compare trends.

These logs will be the raw data for your performance analysis and will guide the code‑review focus.

**Next action after logs:** Open `metrics/top_*.txt` and `metrics/iostat_*.txt`, note the highest CPU% processes and any device with >80 % utilization, then annotate the corresponding sections in your Python code for optimization.

## Iteration 93 — 2026-06-07T18:14:41.695395

**Next Concrete Step – Capture and Save System Metrics**

1. **Create the Bash script** `collect_metrics.sh` (as shown below) and make it executable.  
2. **Run the script** and verify that three timestamped files appear in the `metrics/` directory:  
   * `top_<TS>.txt` – full `top` snapshot (CPU % and memory).  
   * `iostat_<TS>.txt` – disk I/O stats (3 samples, 5‑second interval).  
   * `free_<TS>.txt` – memory summary (`free -h`).  
3. **Commit the script** to your repo and add a short README entry describing how to use it.  

```bash
#!/bin/bash
set -euo pipefail

# Prepare output folder
mkdir -p metrics
TS=$(date +%Y%m%d_%H%M%S)

# CPU & memory snapshot
top -b -n1 > "metrics/top_${TS}.txt"

# Disk I/O stats (5‑second interval, 3 samples)
iostat -d 5 3 > "metrics/iostat_${TS}.txt"

# Memory usage summary
free -h > "metrics/free_${TS}.txt"

echo "Metrics collected at $TS"
```

Run it with `./collect_metrics.sh` and inspect the files to start your performance analysis.
