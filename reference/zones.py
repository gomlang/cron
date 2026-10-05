"""Independent UTC timeline enumeration using Python zoneinfo, not cron search.
Run from reference/. Uses the exact shipped TZif bytes, never system lookup.
"""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
import hashlib
import gzip

root = Path('../examples/basic/testdata/zones')
scenarios = [
    ('America/New_York', '2024-03-10T07:00:00+00:00', 60),
    ('America/New_York', '2024-11-03T06:00:00+00:00', 60),
    ('Australia/Lord_Howe', '2024-04-06T15:00:00+00:00', 60),
    ('Australia/Lord_Howe', '2024-10-05T15:30:00+00:00', 60),
    ('Pacific/Apia', '2011-12-30T10:00:00+00:00', 60),
    ('Europe/Dublin', '2024-03-31T01:00:00+00:00', 60),
    ('Europe/Dublin', '2024-10-27T01:00:00+00:00', 60),
    ('Asia/Kathmandu', '1985-12-31T18:30:00+00:00', 60),
    ('Asia/Kathmandu', '1900-01-01T00:00:00+00:00', 1),
    ('America/New_York', '1880-01-01T00:00:00+00:00', 1),
]
specs = [('* * * * *', None, None), ('30 1 * * *', {30}, {1}),
         ('0 2 * * *', {0}, {2}), ('15,45 * * * *', {15,45}, None),
         ('0 0 * * *', {0}, {0})]

def iso(t): return t.isoformat().replace('+00:00', 'Z')
def ambiguity(local, zone):
    wall = local.replace(tzinfo=None)
    first, last = wall.replace(tzinfo=zone, fold=0), wall.replace(tzinfo=zone, fold=1)
    return first.utcoffset() != last.utcoffset() and all(
        x.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None) == wall
        for x in (first, last))

rows=[]
for name, anchor_text, step in scenarios:
    with (root/name).open('rb') as f: zone = ZoneInfo.from_file(f, key=name)
    anchor=datetime.fromisoformat(anchor_text)
    until=anchor+timedelta(days=2)
    timeline=[]
    current=anchor-timedelta(hours=3)
    while current<=until:
        local=current.astimezone(zone)
        if local.second==0:
            timeline.append((current,local,ambiguity(local,zone)))
        current += timedelta(seconds=step)
    for spec,minutes,hours in specs:
        for delta in [-7200,-1800,-1,0,1800,7200]:
            after=anchor+timedelta(seconds=delta)
            for fold in ['both','earlier','later']:
                candidates=[t for t,local,amb in timeline if t>after
                    and (minutes is None or local.minute in minutes)
                    and (hours is None or local.hour in hours)
                    and (not amb or fold=='both' or local.fold==(fold=='later'))]
                expected=iso(candidates[0]) if candidates else 'none'
                rows.append('\t'.join([spec,iso(after),iso(until),fold,name,expected]))
Path('../examples/basic/tests/data/zones.tsv.gz').write_bytes(gzip.compress(('\n'.join(rows)+'\n').encode(),mtime=0))
names=sorted(set(x[0] for x in scenarios)|{"Synthetic/Finite"})
(root/'SHA256SUMS').write_text(''.join(hashlib.sha256((root/name).read_bytes()).hexdigest()+'  '+name+'\n' for name in names))
print('zoneinfo UTC enumeration vectors:',len(rows))
