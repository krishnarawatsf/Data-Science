import csv
from pathlib import Path
p = Path('data/Sales.csv')
report = Path('scripts/malformed_report.txt')

header = None
bad_rows = []
with p.open(newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    try:
        header = next(reader)
    except StopIteration:
        report.write_text('Empty file')
        raise SystemExit(0)
    header_n = len(header)

# scan line by line using csv.reader on each raw line
with p.open('r', encoding='utf-8', errors='replace') as f:
    next(f)  # skip header raw line
    for i, raw in enumerate(f, start=2):
        raw_str = raw.rstrip('\n')
        # quick heuristic: unbalanced quotes
        if raw_str.count('"') % 2 == 1:
            bad_rows.append((i, 'unbalanced_quotes', raw_str))
            if len(bad_rows) >= 200:
                break
        else:
            # parse with csv to check field count
            try:
                row = next(csv.reader([raw_str]))
                if len(row) != header_n:
                    bad_rows.append((i, f'fields={len(row)}', raw_str))
                    if len(bad_rows) >= 200:
                        break
            except Exception as e:
                bad_rows.append((i, f'parse_error:{e}', raw_str))
                if len(bad_rows) >= 200:
                    break

with report.open('w', encoding='utf-8') as out:
    out.write(f'Header fields: {header_n}\n')
    out.write(f'Bad rows found (first {len(bad_rows)}):\n')
    for ln, reason, raw in bad_rows[:100]:
        out.write(f'Line {ln}: {reason}\n')
        out.write(raw[:1000].replace('\n','\\n') + '\n')
        # include how csv parses this raw line
        try:
            parsed = next(csv.reader([raw]))
            out.write('Parsed fields (len=' + str(len(parsed)) + '):\n')
            for i, val in enumerate(parsed):
                out.write(f'  [{i}] {val!r}\n')
        except Exception as e:
            out.write('Parsed error: ' + str(e) + '\n')

print('Wrote report to', report)
