import re
import pandas as pd
import os
from tqdm import tqdm

class LogParser:
    def __init__(self, log_format, out_dir="data"):
        self.log_format = log_format
        self.out_dir = out_dir
        self.templates = {}
        self.regex_patterns = [
            (r'blk_-?\d+', 'blk_<*>'), # Block ID
            (r'\d+\.\d+\.\d+\.\d+', 'IP'), # IP Address
            (r'/\d+\.\d+\.\d+\.\d+:\d+', 'Source/Dest'), # Source/Dest with Port
            (r'\b\d+\b', '<*>') # Generic Numbers
        ]
        
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

    def parse_line(self, line):
        # Format: 081109 203518 143 INFO dfs.DataNode$DataXceiver: Receiving block blk_-1608999687919862906 ...
        # Simplified parser for HDFS logs
        tokens = line.strip().split()
        if len(tokens) < 5:
            return None
        
        date = tokens[0]
        time = tokens[1]
        timestamp = f"20{date[:2]}-{date[2:4]}-{date[4:6]} {time[:2]}:{time[2:4]}:{time[4:6]}"
        
        level = tokens[3]
        component = tokens[4].rstrip(':')
        message = " ".join(tokens[5:])
        
        # Extract Block ID
        blk_match = re.search(r'blk_-?\d+', message)
        block_id = blk_match.group(0) if blk_match else "None"
        
        # Template Message
        template = message
        for pattern, replacement in self.regex_patterns:
            template = re.sub(pattern, replacement, template)
            
        if template not in self.templates:
            self.templates[template] = f"E{len(self.templates) + 1}"
            
        event_id = self.templates[template]
        
        return {
            "Timestamp": timestamp,
            "BlockID": block_id,
            "Level": level,
            "Component": component,
            "EventID": event_id,
            "Message": message
        }

    def process_log(self, log_path, limit=None):
        parsed_data = []
        with open(log_path, 'r') as f:
            for i, line in enumerate(tqdm(f, desc="Parsing Logs")):
                if limit and i >= limit:
                    break
                res = self.parse_line(line)
                if res:
                    parsed_data.append(res)
        
        df = pd.DataFrame(parsed_data)
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        
        # Save templates
        template_df = pd.DataFrame(list(self.templates.items()), columns=["Template", "EventID"])
        template_df.to_csv(os.path.join(self.out_dir, "templates.csv"), index=False)
        
        df.to_csv(os.path.join(self.out_dir, "parsed_logs.csv"), index=False)
        return df

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    LOG_PATH = os.path.join(base_dir, "hdfs_log/hdfs.log/sorted.log")
    parser = LogParser(log_format="HDFS")
    # For testing, we might want to limit to a reasonable number of lines
    df = parser.process_log(LOG_PATH, limit=100000)
    print(f"Parsed {len(df)} lines. Templates found: {len(parser.templates)}")
