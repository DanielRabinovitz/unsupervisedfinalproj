import pandas as pd
import trolldata_utils as utils
from mlxtend.frequent_patterns import fpgrowth, association_rules
from sklearn.preprocessing import MultiLabelBinarizer
from tqdm import tqdm
import time

def prepare_emoji_word_data(test_mode=False, min_support=0.001):
    """
    Prepare emoji and word data for market basket analysis
    Args:
        test_mode (bool): If True, only process first 100 rows
        min_support (float): Minimum support threshold for items. Items appearing less 
                           frequently than this will be removed
    Returns:
        pd.DataFrame: One-hot encoded data where each row represents a tweet
        and each column represents the presence/absence of an emoji or word
    """
    # Load and clean data
    data = utils.load_troll_dataset(remove_nulls_from=['content'])
    
    # Remove links first
    data = utils.remove_links(data)
    
    if test_mode:
        data = data.head(100)
        print("Processing first 100 elements...")
    else:
        print("Processing full dataset...")

    # Process content to get unique words and emojis
    processed_content = data['content'].apply(utils.unique_vals)
    
    # Convert each string into a list of unique items (words and emojis)
    transactions = processed_content.apply(
        lambda x: x.split() if isinstance(x, str) else []
    ).tolist()
    
    # Count item frequencies
    print("Counting item frequencies...")
    item_counts = {}
    total_transactions = len(transactions)
    for transaction in transactions:
        for item in transaction:
            item_counts[item] = item_counts.get(item, 0) + 1
    
    # Filter items by support
    min_count = int(min_support * total_transactions)
    frequent_items = {item for item, count in item_counts.items() 
                     if count >= min_count}
    
    print(f"Filtered items from {len(item_counts)} to {len(frequent_items)} "
          f"using minimum support of {min_support}")
    
    # Filter transactions to only include frequent items
    filtered_transactions = [
        [item for item in transaction if item in frequent_items]
        for transaction in transactions
    ]
    
    # Create and return onehot matrix
    print("Creating one-hot matrix...")
    mlb = MultiLabelBinarizer(sparse_output=False)
    onehot_data = mlb.fit_transform(filtered_transactions)
    return pd.DataFrame(onehot_data, columns=mlb.classes_).astype(bool)

'''
onehot = the onehot matrix
support, confidence = support, confidence

lift_distance is the lift's distance from 1, e.g. lift_distance = 0.2 means a minimum lift of 1.2.

If find_negative_correlations = True then lift tolerance will also look at lifts below 1, 
e.g. lift_distance = 0.2 means lifts outside the range 0.8 < x < 1.2
'''
def market_basket_analyzer(onehot, support, confidence, lift_distance, find_negative_correlations=False):
    print(f"Starting analysis with parameters:")
    print(f"Support: {support}, Confidence: {confidence}, Lift distance: {lift_distance}")
    
    start_time = time.time()
    
    # Show progress for frequent itemsets generation
    print("Generating frequent itemsets...")
    frequent_itemsets = fpgrowth(onehot, min_support=support, use_colnames=True)
    
    if frequent_itemsets.empty:
        return {'itemsets': pd.DataFrame(), 'rules': pd.DataFrame()}

    print(f"Found {len(frequent_itemsets)} frequent itemsets")
    
    # Show progress for rules generation
    print("Generating association rules...")
    rules = association_rules(frequent_itemsets, num_itemsets=len(frequent_itemsets), 
                            metric="confidence", min_threshold=confidence)
    
    total_rules = len(rules)
    print(f"Generated {total_rules} initial rules")
    
    # Filter by lift with progress indication
    print("Filtering by lift...")
    tqdm.pandas(desc="Applying lift filter")
    if find_negative_correlations:
        mask = rules.progress_apply(
            lambda row: row['lift'] >= 1 + lift_distance or row['lift'] <= 1 - lift_distance, 
            axis=1
        )
        rules = rules[mask]
    else:
        mask = rules.progress_apply(
            lambda row: row['lift'] >= 1 + lift_distance, 
            axis=1
        )
        rules = rules[mask]
    
    print(f"Remaining rules after lift filter: {len(rules)}")
    
    # Remove duplicates with progress indication
    print("Removing duplicate rules...")
    tqdm.pandas(desc="Removing duplicates")
    
    def check_duplicate(row):
        idx = row.name
        # Get the index list of the DataFrame
        index_list = rules.index.tolist()
        # Find the position of current index in the list
        current_pos = index_list.index(idx)
        if current_pos > 0:  # If not the first row
            prev_row = rules.iloc[current_pos-1]
            return (row['antecedents'] == prev_row['consequents'] and 
                   row['consequents'] == prev_row['antecedents'])
        return False
    
    mask = rules.progress_apply(check_duplicate, axis=1)
    rules = rules[~mask]
    
    elapsed_time = time.time() - start_time
    print(f"\nAnalysis completed in {elapsed_time:.2f} seconds")
    print(f"Final results: {len(frequent_itemsets)} itemsets, {len(rules)} rules")
    
    return {'itemsets': frequent_itemsets, 'rules': rules}

#given the result of a market_basket_analyzer, print the contents
def save_mba(mba):
    path = "./analysis_code/Daniel/analysis_results/market_basket"
    
    # Save frequent itemsets
    itemsets_path = f"{path}/emoji_word_frequent_itemsets.csv"
    mba['itemsets'].to_csv(itemsets_path, index=False)
    
    # Save association rules
    rules_path = f"{path}/emoji_word_association_rules.csv"
    mba['rules'].to_csv(rules_path, index=False)
    
    print(f"Results saved to:\n{itemsets_path}\n{rules_path}")
#iterate over varying paramter ranges to find ones near a 2 to 1 ratio between rules and itemsets]

if __name__ == "__main__":
    # Log start time
    start_time = time.time()
    start_datetime = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"\nStarting analysis at {start_datetime}")
    
    # Ask user if they want to run in test mode
    test_mode = input("Run in test mode with first 100 elements? (y/n): ").lower() == 'y'
    
    # Prepare data with minimum support filtering
    onehot_df = prepare_emoji_word_data(
        test_mode=test_mode,
        min_support=0.003  # 0.3%, 9000 or more occurences
    )

    print('Analyzing...')
    
    # Run MBA analysis with adjusted parameters for the larger item set
    mba_results = market_basket_analyzer(
        onehot=onehot_df,
        support=0.001,  # Might need to adjust these parameters
        confidence=0.1,  # since we'll have many more items now
        lift_distance=0.2,
        find_negative_correlations=True
    )
    
    print('Saving results...')
    
    # Save results
    save_mba(mba_results)

    # Log end time and total duration
    end_time = time.time()
    end_datetime = time.strftime('%Y-%m-%d %H:%M:%S')
    total_runtime = end_time - start_time
    
    print(f"\nAnalysis completed at {end_datetime}")
    print(f"Total runtime: {total_runtime:.2f} seconds ({total_runtime/60:.2f} minutes)")
    print('Done!')
