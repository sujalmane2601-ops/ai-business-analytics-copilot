import sqlite3
from pathlib import Path

import pandas as pd

CSV = 'online_retail_II.csv'
DB = Path('retail.db')

df = pd.read_csv(CSV, encoding='latin1', dtype={'Invoice': str, 'StockCode': str})
df.columns = ['invoice', 'stock_code', 'description', 'quantity',
              'invoice_date', 'unit_price', 'customer_id', 'country']
df['invoice_date'] = pd.to_datetime(df['invoice_date']).dt.strftime('%Y-%m-%d %H:%M:%S')
df['customer_id'] = df['customer_id'].astype('Int64')
df['is_cancellation'] = df['invoice'].str.startswith('C').astype(int)
df['line_total'] = (df['quantity'] * df['unit_price']).round(2)

if DB.exists():
    DB.unlink()
con = sqlite3.connect(DB)
df.to_sql('transactions', con, index=False)

NON_PRODUCT = ("'POST','D','DOT','M','PADS','ADJUST','ADJUST2','BANK CHARGES',"
               "'AMAZONFEE','S','B','CRUK','C2','TEST001','TEST002'")

con.executescript(f'''
CREATE VIEW sales AS
SELECT * FROM transactions
WHERE is_cancellation = 0 AND quantity > 0 AND unit_price > 0
  AND UPPER(stock_code) NOT IN ({NON_PRODUCT})
  AND LOWER(stock_code) NOT LIKE 'gift%';

CREATE VIEW returns AS
SELECT * FROM transactions
WHERE is_cancellation = 1
  AND UPPER(stock_code) NOT IN ({NON_PRODUCT})
  AND LOWER(stock_code) NOT LIKE 'gift%';

CREATE INDEX idx_tx_invoice ON transactions(invoice);
CREATE INDEX idx_tx_customer ON transactions(customer_id);
CREATE INDEX idx_tx_date ON transactions(invoice_date);
''')
con.commit()

for name in ('transactions', 'sales', 'returns'):
    n = con.execute(f'SELECT COUNT(*) FROM {name}').fetchone()[0]
    print(name, n)
con.close()