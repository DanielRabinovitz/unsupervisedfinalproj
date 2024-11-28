import pandas as pd

df = pd.read_csv('russian_troll_dataset/IRAhandle_tweets_1.csv')

# categories = df[['account_type', 'account_category']]
# print("Unique account types:")
# print(categories['account_type'].unique())
# print("\nUnique account categories:")
# print(categories['account_category'].unique())

content = df['content']
pd.set_option('display.max_colwidth', None)
#print(content.head(10))

print('\u0001f44d')