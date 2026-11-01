import os
import re
import sqlite3

import pandas as pd

MODEL = os.getenv('COPILOT_MODEL', 'qwen2.5-coder:3b')  # or 'qwen2.5-coder:7b' for larger model
DB_PATH = 'retail.db'
MAX_RETRIES = 2

SCHEMA_DOC = '''
SQLite database of an online gift retailer (Dec 2009 - Dec 2011).

VIEW sales -- USE THIS FOR ALL REVENUE, ORDER, PRODUCT AND CUSTOMER QUESTIONS
  Valid product sales only (cancellations, postage and fees removed).
  invoice TEXT         -- order id; one invoice has many lines
  stock_code TEXT      -- product id
  description TEXT     -- product name
  quantity INTEGER
  invoice_date TEXT    -- 'YYYY-MM-DD HH:MM:SS'; month = SUBSTR(invoice_date, 1, 7)
  unit_price REAL      -- GBP
  customer_id INTEGER  -- NULL for guest checkouts
  country TEXT
  line_total REAL      -- quantity * unit_price in GBP. Revenue = SUM(line_total)

VIEW returns -- cancelled or returned lines (line_total is NEGATIVE). Same columns as sales.

BUSINESS RULES
- Revenue = SUM(line_total) from sales. Currency is GBP.
- Number of orders = COUNT(DISTINCT invoice), NOT COUNT(*).
- Number of customers = COUNT(DISTINCT customer_id); exclude NULL customer_id.
- Average order value = revenue / COUNT(DISTINCT invoice).
- Return rate = ABS(SUM(line_total) from returns) / SUM(line_total) from sales.
- A product is identified by stock_code. Product questions must GROUP BY stock_code only. Show stock_code, and optionally MAX(description) AS description.
- Percentages are numbers from 0 to 100 rounded to 2 decimals (3.61 means 3.61 percent), never fractions.
- Return and refund questions must use the returns view, never sales. Wrap return sums in ABS().
- A repeat customer is a customer with more than one DISTINCT invoice. Count customers, not order lines.
'''

EXAMPLES = '''
Examples:
Q: What is the total value of returns for the United Kingdom?
SQL: SELECT ROUND(ABS(SUM(line_total)), 2) AS returned_value FROM returns WHERE country = 'United Kingdom'

Q: How many customers placed exactly one order?
SQL: SELECT COUNT(*) AS customers FROM (SELECT customer_id FROM sales WHERE customer_id IS NOT NULL GROUP BY customer_id HAVING COUNT(DISTINCT invoice) = 1)

Q: What are the 5 products with the highest quantity sold?
SQL: SELECT stock_code, MAX(description) AS description, SUM(quantity) AS units FROM sales GROUP BY stock_code ORDER BY units DESC LIMIT 5

Q: How many orders were placed each month?
SQL: SELECT SUBSTR(invoice_date, 1, 7) AS month, COUNT(DISTINCT invoice) AS orders FROM sales GROUP BY month ORDER BY month

'''


SQL_SYSTEM = f'''You are a careful analytics engineer. Convert the user's business
question into ONE read-only SQLite query using the schema below.



{SCHEMA_DOC}

Rules:
- Output only the SQL query. No explanation.
- SELECT or WITH only. Never modify data.
- Use only the tables, views and columns listed above. Never invent columns.
- Round money to 2 decimals and give columns clear aliases.
'''


def chat(system, messages, max_tokens=800):
    import ollama
    resp = ollama.chat(
        model=MODEL,
        messages=[{'role': 'system', 'content': system}] + messages,
        options={'temperature': 0, 'num_predict': max_tokens, 'num_ctx': 4096},
    )
    return resp['message']['content']


def extract_sql(text):
    fence = chr(96) * 3
    m = re.search(fence + r'(?:sql)?\s*(.*?)' + fence, text, re.S | re.I)
    if m:
        text = m.group(1)
    else:
        m = re.search(r'\b(select|with)\b.*', text, re.S | re.I)
        text = m.group(0) if m else text
    return text.strip().split(';')[0].strip()


def is_safe(sql):
    s = sql.strip().lower()
    if not (s.startswith('select') or s.startswith('with')):
        return False
    banned = r'\b(insert|update|delete|drop|alter|create|attach|pragma|replace)\b'
    return re.search(banned, s) is None


def run_sql(sql):
    if not is_safe(sql):
        raise ValueError('Blocked: only a single read-only SELECT is allowed.')
    con = sqlite3.connect(f'file:{DB_PATH}?mode=ro', uri=True)  # read-only
    try:
        return pd.read_sql_query(sql, con)
    finally:
        con.close()


def generate_sql(history):
    return extract_sql(chat(SQL_SYSTEM, history))


def summarize(question, df):
    table = df.head(30).to_csv(index=False)
    system = ('You are a business analyst writing for a non-technical stakeholder. '
              'Use ONLY the numbers in the table provided. Never calculate new '
              'figures or add facts that are not in the table. Write 2-3 short '
              'sentences plus one suggested next step. Currency is GBP.')
    msgs = [{'role': 'user', 'content': f'Question: {question}\n\nResult table:\n{table}'}]
    return chat(system, msgs, max_tokens=400).strip()


def ask(question, with_summary=True):
    history = [{'role': 'user', 'content': question}]
    sql, error, df = '', None, None
    for attempt in range(MAX_RETRIES + 1):
        sql = generate_sql(history)
        try:
            df = run_sql(sql)
            error = None
            break
        except Exception as e:
            error = str(e)
            history += [{'role': 'assistant', 'content': sql},
                        {'role': 'user', 'content': f'That query failed: {error}. Fix it.'}]
    out = {'question': question, 'sql': sql, 'df': df, 'error': error,
           'attempts': attempt + 1, 'summary': None}
    if df is not None and with_summary and not df.empty:
        out['summary'] = summarize(question, df)

    return out

def sanity_warnings(df):
    warnings = []
    for col in df.columns:
        name = col.lower()
        if ('pct' in name or 'percent' in name or 'rate' in name) and df[col].dtype != object:
            if (df[col] > 100).any() or (df[col] < 0).any():
                warnings.append(f"'{col}' is outside 0-100, so this result is probably wrong.")
    if df.empty:
        warnings.append('The query returned no rows.')
    return warnings