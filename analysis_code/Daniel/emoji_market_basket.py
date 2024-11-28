import pandas as pd
import trolldata_utils as utils
from mlxtend.frequent_patterns import fpgrowth, association_rules
from sklearn.preprocessing import MultiLabelBinarizer
from tqdm import tqdm
import time

def prepare_emoji_data(test_mode=False):
    """
    Prepare emoji data for market basket analysis
    Args:
        test_mode (bool): If True, only process first 100 rows
    Returns:
        pd.DataFrame: One-hot encoded emoji data where each row represents a tweet
        and each column represents the presence/absence of an emoji
    """
    # Load and clean data
    data = utils.load_troll_dataset(remove_nulls_from=['content'])
    
    # Extract just the content column and process it for emojis
    emoji_series = data['content'].apply(utils.emoji_only)
    
    if test_mode:
        emoji_series = emoji_series.head(100)
        print("Processing first 100 elements...")
    else:
        print("Processing full dataset...")

    # Convert each string of emojis into a list of unique emojis
    transactions = emoji_series.apply(lambda x: list(set(x)) if isinstance(x, str) else []).tolist()
    
    # Create and return onehot matrix
    mlb = MultiLabelBinarizer(sparse_output=False)
    onehot_data = mlb.fit_transform(transactions)
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
    itemsets_path = f"{path}/emoji_only_frequent_itemsets.csv"
    mba['itemsets'].to_csv(itemsets_path, index=False)
    
    # Save association rules
    rules_path = f"{path}/emoji_only_association_rules.csv"
    mba['rules'].to_csv(rules_path, index=False)
    
    print(f"Results saved to:\n{itemsets_path}\n{rules_path}")
#iterate over varying paramter ranges to find ones near a 2 to 1 ratio between rules and itemsets]

if __name__ == "__main__":
    # Ask user if they want to run in test mode
    test_mode = input("Run in test mode with first 100 elements? (y/n): ").lower() == 'y'
    
    # Prepare data
    onehot_df = prepare_emoji_data(test_mode)

    print('Analyzing...')
    
    # Run MBA analysis

    #at 0.0001 support, 0.1 confidence, 0.2 lift I found 4 rules.
    mba_results = market_basket_analyzer(
        onehot=onehot_df,
        support=0.0001,
        confidence=0.1, #got nothing at 0.5
        lift_distance=0.1,
        find_negative_correlations=True
    )
    
    print('Saving results...')
    
    # Save results
    save_mba(mba_results)

    print('Done!')
