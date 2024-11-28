'''
File for quick handling of the troll dataset.
'''

import pandas as pd
import re
import emoji

def load_troll_dataset(folder_path="./russian_troll_dataset", remove_nulls_from=None):
    '''
    Loads and combines all troll dataset CSV files from the specified folder.
    
    Args:
        folder_path (str): path to the folder containing the dataset
        remove_nulls_from (list): list of column names to remove null values from
    
    Returns:
        pd.DataFrame: Combined dataset of all tweets
    '''
    tweets = pd.DataFrame()
    
    # Iterate through all 13 CSV files and append them
    for i in range(1, 14):
        csv_path = folder_path + f'/IRAhandle_tweets_{i}.csv'
        df = pd.read_csv(csv_path)
        tweets = pd.concat([tweets, df], ignore_index=True)
    
    # Remove null values from specified columns if any are provided
    if remove_nulls_from:
        # Verify all columns exist
        missing_cols = [col for col in remove_nulls_from if col not in tweets.columns]
        if missing_cols:
            raise ValueError(f"Columns not found in dataset: {missing_cols}")
            
        # Drop rows where any of the specified columns have null values
        tweets = tweets.dropna(subset=remove_nulls_from)
    
    return tweets

def remove_links(df):
    '''
    Removes links from the content column of the dataframe
    
    Args:
        df (pd.DataFrame): Input dataframe
    
    Returns:
        pd.DataFrame: Dataframe with links removed from content
    '''
    df = df.copy()
    df['content'] = df['content'].str.replace(r'http\S+', '', regex=True).str.strip()
    return df

def emoji_only(input_data):
    """Extract only emojis from text or DataFrame
    
    Args:
        input_data: Either a string or DataFrame. If DataFrame, processes the 'content' column
    
    Returns:
        If string input: string containing only emojis
        If DataFrame input: DataFrame with emojis extracted from content column
    """
    # Handle string input
    if isinstance(input_data, str):
        return ''.join(c for c in input_data if c in emoji.EMOJI_DATA)
    
    # Handle DataFrame input
    df = input_data.copy()
    df['content'] = df['content'].apply(lambda x: ''.join(c for c in x if c in emoji.EMOJI_DATA) if isinstance(x, str) else '')
    return df

def unique_vals(input_data):
    '''
    Removes repeated strings or emojis from text.
    
    Args:
        input_data: Either a string or DataFrame. If DataFrame, processes the 'content' column
    
    Returns:
        If string input: string with unique words and emojis
        If DataFrame input: DataFrame with processed content column
    '''
    def process_text(text):
        if not isinstance(text, str):
            return ''
        
        # Split into words and process each
        words = text.split()
        unique_words = []
        for word in words:
            # If word contains only emojis, remove duplicates at character level
            if all(c in emoji.EMOJI_DATA for c in word):
                unique_chars = ''.join(dict.fromkeys(word))
                unique_words.append(unique_chars)
            else:
                unique_words.append(word)
        # Remove duplicate words
        return ' '.join(dict.fromkeys(unique_words))
    
    # Handle string input
    if isinstance(input_data, str):
        return process_text(input_data)
    
    # Handle DataFrame input
    df = input_data.copy()
    df['content'] = df['content'].apply(process_text)
    return df

if __name__ == "__main__":
    # Load the dataset
    print("Loading dataset...")
    df = load_troll_dataset()
    print(f"Loaded {len(df)} tweets")
    
    # Test remove_links
    print("\nTesting remove_links...")
    sample_with_links = df[df['content'].str.contains('http', na=False)].head()
    print("Before:")
    print(sample_with_links['content'].values)
    print("After:")
    print(remove_links(sample_with_links)['content'].values)
    
    # Test emoji_only
    print("\nTesting emoji_only...")
    sample_with_emoji = df[df['content'].str.contains('😊|😂|❤️', na=False)].head()
    print("Before:")
    print(sample_with_emoji['content'].values)
    print("After:")
    print(emoji_only(sample_with_emoji)['content'].values)

        # Test unique_vals
    print("\nTesting unique_vals...")
    # Create a sample dataframe with duplicate content
    sample_duplicates = pd.DataFrame({
        'content': [
            'hello hello world 😊😊😊',
            'test test test xyz xyz 😂😂 ❤️❤️',
            'one two two three three three 🌟🌟🌟🌟'
        ]
    })
    print("Before:")
    print(sample_duplicates['content'].values)
    print("After:")
    print(unique_vals(sample_duplicates)['content'].values)