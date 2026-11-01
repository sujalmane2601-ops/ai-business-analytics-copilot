GROUND_TRUTH = [
    {
        'question': 'What is the total revenue?',
        'sql': 'SELECT ROUND(SUM(line_total), 2) AS total_revenue FROM sales',
    },
    {
        'question': 'What is the monthly revenue?',
        'sql': '''SELECT SUBSTR(invoice_date, 1, 7) AS month,
                         ROUND(SUM(line_total), 2) AS revenue
                  FROM sales GROUP BY month ORDER BY month''',
    },
    {
        'question': 'What are the top 10 products by revenue?',
        'sql': 
                                        '''SELECT
    stock_code,
    MAX(description) AS description,
    SUM(line_total) AS revenue
FROM sales
GROUP BY stock_code
ORDER BY revenue DESC
LIMIT 10;'''
    },
    {
        'question': 'What are the top 5 countries by revenue excluding the United Kingdom?',
        'sql': '''SELECT country, ROUND(SUM(line_total), 2) AS revenue
                  FROM sales WHERE country <> 'United Kingdom'
                  GROUP BY country ORDER BY revenue DESC LIMIT 5''',
    },
    {
        'question': 'What is the average order value?',
        'sql': '''SELECT ROUND(SUM(line_total) * 1.0 / COUNT(DISTINCT invoice), 2)
                         AS avg_order_value FROM sales''',
    },
    {
        'question': 'What percentage of customers made more than one purchase?',
        'sql': '''SELECT ROUND(100.0 * SUM(CASE WHEN n > 1 THEN 1 ELSE 0 END) / COUNT(*), 2)
                         AS repeat_pct
                  FROM (SELECT customer_id, COUNT(DISTINCT invoice) AS n
                        FROM sales WHERE customer_id IS NOT NULL
                        GROUP BY customer_id)''',
    },
    {
        'question': 'What is the return rate by value, as a percent of sales revenue?',
        'sql': '''SELECT ROUND(100.0 * ABS((SELECT SUM(line_total) FROM returns))
                         / (SELECT SUM(line_total) FROM sales), 2) AS return_rate_pct''',
    },

    {
        'question': 'How many unique customers are there?',
        'sql': 'SELECT COUNT(DISTINCT customer_id) AS customers FROM sales',
    },

      {
        'question': 'How many orders were placed in 2010?',
        'sql': '''SELECT COUNT(DISTINCT invoice) AS orders
                  FROM sales
                  WHERE invoice_date LIKE '2010%'
                  ''',
    },

       {
        'question': 'What are the top 5 countries by number of orders?',
        'sql': '''SELECT country, COUNT(DISTINCT invoice) AS orders
                  FROM sales
                  GROUP BY country
                  ORDER BY orders DESC
                  LIMIT 5
                  ''',
    },
        {
        'question': 'How many different products were sold?',
        'sql': '''SELECT COUNT(DISTINCT stock_code) AS products
                  FROM sales
                  ''',
    },
  
        {
        'question': 'What is the average number of items per order?',
        'sql': '''SELECT ROUND(SUM(quantity) * 1.0 / COUNT(DISTINCT invoice), 2) AS avg_items_per_order
                  FROM sales
                  ''',
    },


  
]


if __name__ == '__main__':
    import sqlite3

    import pandas as pd

    con = sqlite3.connect('retail.db')
    for item in GROUND_TRUTH:
        print()
        print(item['question'])
        print(pd.read_sql_query(item['sql'], con).to_string(index=False))
    con.close()