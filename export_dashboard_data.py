import sqlite3

import pandas as pd

con = sqlite3.connect('retail.db')
df = pd.read_sql_query('SELECT * FROM sales', con)
df['month'] = df['invoice_date'].str[:7]
df.to_csv('sales_clean.csv', index=False)
print(len(df), 'rows exported')
con.close()