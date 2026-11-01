# AI-Powered Business Analytics Copilot

Ask business questions in plain English. A local LLM (Ollama) writes SQL over 1M+ retail transactions, and every answer is checked against hand-written SQL.

## Demo

![Streamlit app](screenshots/01_app_good_answer.png)
![Dashboard](screenshots/06_dashboard.png)

Video walkthrough: <<FILL: your Loom link>>

## Tech stack

Python, SQLite, pandas, Ollama (qwen2.5-coder:3b), Streamlit, Power BI

## Dataset

Online Retail II (UCI Machine Learning Repository): 1,067,371 transaction lines, 5,942 customers, 43 countries and 5,305 products, from Dec 2009 to Dec 2011, in GBP. After cleaning, 1,037,004 lines remain in the `sales` view and 18,285 in the `returns` view.

## How it works

1. `load_data.py` loads the CSV into SQLite and builds two clean views, `sales` and `returns`.
2. `copilot.py` sends the question, the schema and business rules to the local model. The SQL runs on a read-only connection with a SELECT-only guard. If the SQL errors, the error is sent back to the model for up to 2 retries. A second model call writes a short insight using only numbers from the result table.
3. `app.py` is the Streamlit interface: question box, insight, result table, chart and the generated SQL.
4. `copilot.py` also includes a sanity check that warns when a percentage or rate column falls outside 0 to 100.
5. `ground_truth.py` holds <<FILL: N>> hand-written SQL questions with answers I checked myself. `validate.py` runs each question through the model, compares the numbers and writes `eval_log.csv`.
6. `inspect_failures.py` prints the AI's SQL beside the correct SQL for every failed question. `compare_logs.py` compares two logs on the same questions.

## Data cleaning decisions

- Cancelled invoices (invoice numbers starting with "C", negative quantities) are separated into a `returns` view.
- Fee and non-product codes (POST, ADJUST, AMAZONFEE and similar) are excluded from `sales`.
- Lines with no Customer ID (243,007 lines, about 23%) are kept for revenue but excluded from customer counts.
- Zero or negative prices (6,207 lines) are excluded from `sales`.
- Duplicate rows (34,335) are kept, because the same item can be scanned twice on one invoice.
- A product is identified by `stock_code`. 646 stock codes have more than one description, so grouping by description gives different totals.

## Results

All results use the same local model setup. Accuracy means the model's result matched my hand-written SQL result.

| Version | Model | Questions | Accuracy |
|---|---|---|---|
| Baseline | gemma2:2b | 12 | 42% (5/12) |
| Baseline | qwen2.5-coder:3b | 12 | 75% (9/12) |
| After business rules | qwen2.5-coder:3b | <<FILL: N>> | <<FILL: x% (a/N)>> |
| After few-shot examples | qwen2.5-coder:3b | <<FILL: N>> | <<FILL: x% (a/N)>> |

Notes:
- The test set is small, so one question moves the score by 8 points. Treat the comparison as an early result.
- One question (top 10 products) was reworded after I found its answer key was ambiguous, so it is left out of the before-and-after comparison.
- Logs for every run are in this repo (`eval_log_*.csv`).

## Where the AI failed

Qwen2.5-Coder 3B got three of the first 12 questions wrong. Two were real model errors:

**1. Repeat customers**
- Question: What percentage of customers made more than one purchase?
- AI SQL: `SELECT CAST(COUNT(CASE WHEN customer_id IS NOT NULL THEN customer_id ELSE NULL END) AS REAL) * 100 / COUNT(DISTINCT customer_id) FROM sales`
- Wrong answer: 13,715.55%. Correct answer: 72.35%.
- Why: it counted order lines instead of customers with more than one distinct invoice.
- Fix: <<FILL: the rule or example you added, and whether it passed afterwards>>

**2. Return rate**
- Question: What is the return rate by value, as a percent of sales revenue?
- AI SQL: `SELECT CAST(SUM(CASE WHEN line_total < 0 THEN line_total ELSE 0 END) AS REAL) * 100 / SUM(line_total) AS return_rate FROM sales`
- Wrong answer: 0.0%. Correct answer: 3.61%.
- Why: it queried the `sales` view, where cancellations are already removed, instead of the `returns` view. The wrong answer looks plausible, which makes it the dangerous kind.
- Fix: <<FILL: the rule or example you added, and whether it passed afterwards>>

The third failure was a flaw in my test: "top 10 products" has more than one valid answer, so I fixed the answer key and defined a product by `stock_code`.

## Dashboard

A Power BI page built on `sales_clean.csv` (exported from the `sales` view) with revenue, orders, average order value and customers as cards, plus revenue by month, top 10 products, top 10 countries excluding the UK and a country slicer. Total revenue on the dashboard (about 20.11M) matches the SQL answer of 20,110,181.

## How to run

1. Install [Ollama](https://ollama.com) and run: `ollama pull qwen2.5-coder:3b`
2. Create and activate a virtual environment, then run: `pip install -r requirements.txt`
3. Download `online_retail_II.csv` (UCI Online Retail II dataset) into the project folder. It is not included in this repo because of its size.
4. Run: `python load_data.py online_retail_II.csv`
5. Run the app: `streamlit run app.py`
6. Run the evaluation: `python validate.py`

To try another model without editing code on Windows: `set COPILOT_MODEL=gemma2:2b` and then `python validate.py`.

## Limitations

- Small local models make mistakes on ambiguous questions and on window functions.
- The test set is small (<<FILL: N>> questions), so accuracy numbers are approximate.
- The sanity check only flags columns whose names contain "pct", "percent" or "rate".
- Results were measured on one machine with one dataset.
