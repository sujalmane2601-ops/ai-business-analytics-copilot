import pandas as pd

df = pd.read_csv('online_retail_II.csv', encoding='latin1',
                 dtype={'Invoice': str, 'StockCode': str})
print(df.shape)
print(df.isna().sum())
print(df['Invoice'].str.startswith('C').sum(), 'cancelled lines')
print((df['Price'] <= 0).sum(), 'zero or negative price lines')
print(df['StockCode'][df['StockCode'].str.match('^[A-Za-z]+$', na=False)].unique())