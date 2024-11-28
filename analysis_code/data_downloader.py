import os
import requests
from urllib.parse import urljoin

def download_troll_tweets():
    # Get parent directory of analysis_code folder
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    
    # Create directory if it doesn't exist
    output_dir = os.path.join(parent_dir, "russian_troll_dataset")
    os.makedirs(output_dir, exist_ok=True)
    
    # Base URL for raw GitHub content
    base_url = "https://raw.githubusercontent.com/fivethirtyeight/russian-troll-tweets/master/"
    
    # List of all CSV files (1-13)
    files = [f"IRAhandle_tweets_{i}.csv" for i in range(1, 14)]
    
    for file in files:
        # Construct full URL
        file_url = urljoin(base_url, file)
        output_path = os.path.join(output_dir, file)
        
        print(f"Downloading {file}...")
        
        try:
            # Download the file
            response = requests.get(file_url, stream=True)
            response.raise_for_status()  # Raise an exception for bad status codes
            
            # Write the file to disk
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            print(f"Successfully downloaded {file}")
            
        except requests.exceptions.RequestException as e:
            print(f"Error downloading {file}: {e}")

if __name__ == "__main__":
    print("Starting download of Russian troll tweet dataset...")
    download_troll_tweets()
    print("Download complete!")