import sqlite3

con = sqlite3.connect('retail.db')
print(con.execute('SELECT ROUND(SUM(line_total), 2) FROM sales').fetchone())
print(con.execute('SELECT COUNT(DISTINCT customer_id) FROM sales').fetchone())