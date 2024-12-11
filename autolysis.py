import os
import sys
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import httpx
import chardet

# Constants
API_URL = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
AIPROXY_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIzZjMwMDEzNDVAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.PTZAXBR-1QiqAwQEbW-b2Inbca95E-uXhGteNRiDccI"

def load_data(file_path):
    """
    Load data from a CSV file with automatic encoding detection.
    """
    try:
        with open(file_path, 'rb') as f:
            result = chardet.detect(f.read())
        encoding = result['encoding']
        print(f"Detected encoding: {encoding}")
        return pd.read_csv(file_path, encoding=encoding)
    except UnicodeDecodeError:
        print("Encoding issue detected. Retrying with 'utf-8'.")
        return pd.read_csv(file_path, encoding='utf-8')
    except FileNotFoundError:
        print(f"File {file_path} not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)

def analyze_data(df):
    """
    Analyze the data and return a summary, missing values, and correlation matrix.
    """
    try:
        numeric_df = df.select_dtypes(include=['number'])
        if numeric_df.empty:
            print("No numeric columns found for correlation.")
        else:
            print(f"Numeric columns: {numeric_df.columns.tolist()}")
        
        analysis = {
            'summary': df.describe(include='all', datetime_is_numeric=True).to_dict(),
            'missing_values': df.isnull().sum().to_dict(),
            'correlation': numeric_df.corr().to_dict() if not numeric_df.empty else {}
        }
        return analysis
    except Exception as e:
        print(f"Error analyzing data: {e}")
        sys.exit(1)

def visualize_data(df):
    """
    Generate and save histograms for numeric columns in the data.
    """
    try:
        sns.set(style="whitegrid")
        numeric_columns = df.select_dtypes(include=['number']).columns
        print(f"Numeric columns for visualization: {numeric_columns}")
        if numeric_columns.empty:
            print("No numeric columns to visualize.")
            return

        for column in numeric_columns:
            try:
                plt.figure()
                sns.histplot(df[column].dropna(), kde=True)
                plt.title(f'Distribution of {column}')
                output_file = f'{column}_distribution.png'
                plt.savefig(output_file)
                print(f"Saved plot for {column} to {output_file}")
                plt.close()
            except Exception as e:
                print(f"Failed to plot {column}: {e}")
    except Exception as e:
        print(f"Error in visualization: {e}")
        sys.exit(1)

def generate_narrative(analysis):
    """
    Generate a narrative summary using an AI API based on the data analysis.
    """
    headers = {
        'Authorization': f'Bearer {AIPROXY_TOKEN}',
        'Content-Type': 'application/json'
    }
    prompt = f"Provide a detailed analysis based on the following data summary: {analysis}"
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        print("Sending request to API...")
        response = httpx.post(API_URL, headers=headers, json=data, timeout=30.0)
        response.raise_for_status()
        print(f"Response received: {response.status_code}")
        return response.json().get('choices', [{}])[0].get('message', {}).get('content', "No content returned.")
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e}, Response: {response.text}")
    except httpx.RequestError as e:
        print(f"Request error occurred: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    return "Narrative generation failed due to an error."

def main(file_path):
    """
    Main function to load, analyze, visualize, and generate a narrative for the dataset.
    """
    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist.")
        sys.exit(1)

    try:
        print("Loading data...")
        df = load_data(file_path)
        print("Analyzing data...")
        analysis = analyze_data(df)
        print("Visualizing data...")
        visualize_data(df)
        print("Generating narrative...")
        narrative = generate_narrative(analysis)
        with open('README.md', 'w') as f:
            f.write(narrative)
        print("Analysis and narrative generation completed successfully.")
    except Exception as e:
        print(f"Error during execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python autolysis.py <dataset.csv>")
        sys.exit(1)
    main(sys.argv[1])
