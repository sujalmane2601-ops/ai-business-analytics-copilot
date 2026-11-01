import sqlite3

import pandas as pd

log = pd.read_csv('eval_log.csv')
con = sqlite3.connect('retail.db')
for _, row in log[~log['passed']].iterrows():
    print('=' * 70)
    print(row['question'])
    print('--- AI SQL ---')
    print(row['ai_sql'])
    try:
        print(pd.read_sql_query(row['ai_sql'], con).head(5).to_string(index=False))
    except Exception as e:
        print('ERROR:', e)
    print('--- TRUTH ---')
    print(pd.read_sql_query(row['truth_sql'], con).head(5).to_string(index=False))