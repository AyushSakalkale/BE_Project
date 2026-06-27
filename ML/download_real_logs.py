import os
import urllib.request
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

def download_hdfs_2k():
    url = "https://raw.githubusercontent.com/logpai/loghub/master/HDFS/HDFS_2k.log"
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(base_dir, "hdfs_log/hdfs.log/sorted.log")
    
    print(f"Downloading real HDFS 2k logs from {url}...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        urllib.request.urlretrieve(url, output_path)
        print(f"Successfully downloaded real logs to {output_path}")
        size = os.path.getsize(output_path)
        print(f"File size: {size / 1024:.2f} KB")
    except Exception as e:
        print(f"Failed to download: {e}")

if __name__ == "__main__":
    download_hdfs_2k()
