import csv
from pathlib import Path
p = Path('data/Sales.csv')
print('File:', p.resolve())

header = None
bad = []
with p.open(newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    try:
        header = next(reader)
    except StopIteration:
        print('Empty file')
        raise SystemExit(0)
    header_n = len(header)
    total = 1
    for i,row in enumerate(reader, start=2):
        total += 1
        if len(row) != header_n:
            bad.append((i, len(row), row))
            if len(bad) >= 50:
                break

print('Header fields:', header_n)
print('Scanned rows (so far):', total)
print('Bad rows found (first 50):', len(bad))
for ln, cnt, row in bad[:10]:
    print(f'Line {ln}: fields={cnt} sample=', row[:12])

# full count if none found early
if not bad:
    cnt_bad = 0
    total = 1
    with p.open(newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for i,row in enumerate(reader, start=2):
            total += 1
            if len(row) != header_n:
                cnt_bad += 1
    print('Full scan rows:', total)
    print('Total bad rows:', cnt_bad)
