import os
from datetime import datetime, timedelta

def generate_logs(output_path, num_blocks=3750):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 081109 is November 9, 2008
    start_time = datetime(2008, 11, 9, 20, 30, 0)
    
    with open(output_path, "w") as f:
        current_time = start_time
        for b in range(num_blocks):
            block_id = f"blk_{1000 + b}"
            
            # Step 1: Receiving
            current_time += timedelta(milliseconds=100)
            time_str1 = current_time.strftime("%y%m%d %H%M%S")
            line1 = f"{time_str1} 143 INFO dfs.DataNode$DataXceiver: Receiving block {block_id} src: /10.251.42.84:50689 dest: /10.251.42.84:50010\n"
            f.write(line1)
            
            # Step 2: Terminating
            current_time += timedelta(milliseconds=100)
            time_str2 = current_time.strftime("%y%m%d %H%M%S")
            line2 = f"{time_str2} 143 INFO dfs.DataNode$PacketResponder: PacketResponder 1 for block {block_id} terminating\n"
            f.write(line2)
            
            # Step 3: Received
            current_time += timedelta(milliseconds=100)
            time_str3 = current_time.strftime("%y%m%d %H%M%S")
            line3 = f"{time_str3} 143 INFO dfs.DataNode$DataTransfer: Received block {block_id} src: /10.251.42.84:50689 dest: /10.251.42.84:50010 of size 67108864\n"
            f.write(line3)
            
            # Step 4: addStoredBlock
            current_time += timedelta(milliseconds=100)
            time_str4 = current_time.strftime("%y%m%d %H%M%S")
            line4 = f"{time_str4} 143 INFO dfs.FSNamesystem: BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.251.42.84:50010 is added to {block_id} size 67108864\n"
            f.write(line4)
            
    print(f"Generated {num_blocks * 4} HDFS mock logs at {output_path}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(base_dir, "hdfs_log/hdfs.log/sorted.log")
    generate_logs(log_file)
