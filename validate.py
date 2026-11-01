import pandas as pd

from copilot import MODEL, ask, run_sql
from ground_truth import GROUND_TRUTH


def is_num(s):
    return pd.api.types.is_numeric_dtype(s)


def same_values(a, b, tol=0.01):
    if is_num(a) != is_num(b):
        return False
    if is_num(a):
        x = sorted(a.fillna(0).astype(float))
        y = sorted(b.fillna(0).astype(float))
        return all(abs(i - j) <= tol for i, j in zip(x, y))
    return sorted(a.astype(str)) == sorted(b.astype(str))


def frames_match(truth, got):
    # every ground-truth column must appear in the AI result (any name, any order)
    if len(truth) != len(got):
        return False
    return all(any(same_values(truth[t], got[g]) for g in got.columns)
               for t in truth.columns)


def main():
    rows = []
    for item in GROUND_TRUTH:
        truth = run_sql(item['sql'])
        res = ask(item['question'], with_summary=False)
        passed = res['df'] is not None and frames_match(truth, res['df'])
        rows.append({'model': MODEL, 'question': item['question'], 'passed': passed,
                     'attempts': res['attempts'], 'error': res['error'],
                     'ai_sql': res['sql'], 'truth_sql': item['sql']})
        print('PASS' if passed else 'FAIL', '-', item['question'])
    log = pd.DataFrame(rows)
    log.to_csv('eval_log.csv', index=False)
    print(f'Model: {MODEL}')
    print(f'Accuracy: {log.passed.mean():.0%} ({log.passed.sum()}/{len(log)})')


if __name__ == '__main__':
    main()