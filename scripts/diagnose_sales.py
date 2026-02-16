import pandas as pd
import csv
from pathlib import Path

p = Path('/Users/krishnarawat/Desktop/Data Science/sales.csv')
print('Path exists:', p.exists())


def safe_read(path):
    attempts = [
        {"kwargs": {"low_memory": False}},
        {"kwargs": {"low_memory": False, "engine": "python", "on_bad_lines": "warn"}},
        {"kwargs": {"low_memory": False, "engine": "python", "sep": None, "encoding": "utf-8", "quoting": csv.QUOTE_MINIMAL, "on_bad_lines": "warn"}},
    ]
    last = None
    for a in attempts:
        try:
            return pd.read_csv(path, **a['kwargs'])
        except TypeError:
            try:
                kwargs = a['kwargs'].copy()
                if 'on_bad_lines' in kwargs:
                    kwargs.pop('on_bad_lines')
                kwargs.update({'engine':'python','error_bad_lines':False,'warn_bad_lines':True})
                return pd.read_csv(path, **kwargs)
            except Exception as e:
                last = e
                continue
        except Exception as e:
            last = e
            continue
    raise last if last is not None else ValueError('read failed')


try:
    df = safe_read(p)
except Exception as e:
    print('Failed to read:', repr(e))
    raise SystemExit(1)

print('Rows,Cols:', df.shape)
print('Columns:', df.columns.tolist())

# strip
try:
    df.columns = df.columns.astype(str).str.strip()
except Exception:
    pass

candidates = []
if 'Date' in df.columns:
    candidates.append('Date')

import re
pattern = re.compile(r'date|time', re.I)
candidates += [c for c in df.columns if pattern.search(c) and c not in candidates]
print('Date candidates by name:', candidates)

# sample parse counts
best=None
best_parsed=0
for col in df.columns:
    try:
        s = df[col].dropna().astype(str).head(500)
        if s.empty:
            continue
        parsed = pd.to_datetime(s, errors='coerce', infer_datetime_format=True)
        n = int(parsed.notna().sum())
        print(f"col={col!r} parsed_count={n}")
        if n>best_parsed:
            best_parsed=n; best=col
    except Exception:
        pass
print('Best candidate by sample parse:', best, 'parsed_count=', best_parsed)
if best:
    parsed_full = pd.to_datetime(df[best], errors='coerce', infer_datetime_format=True)
    print('Total parsed in full column:', int(parsed_full.notna().sum()), '/', len(df))
    print('Sample parsed values:', parsed_full.dropna().head(5).tolist())
