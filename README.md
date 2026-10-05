# cron

`ecosystem::cron` parses five-field cron schedules, matches instants in an explicit
`ecosystem::datetime::TimeZone`, and finds the earliest matching instant strictly
after a supplied instant. Implementation is pure GoML; Gregorian calendar and
TZif/POSIX timezone behavior come from datetime. Requires GoML 0.1.57 or newer.

```goml
use ecosystem::cron as cron;
use ecosystem::datetime as dt;

fn next_workday(after: dt::UtcInstant, until: dt::UtcInstant,
                zone: dt::TimeZone) -> Result[dt::UtcInstant, cron::Error] {
    let schedule = cron::Schedule::parse("30 9 * * MON-FRI")?;
    schedule.next(after, zone, cron::Search::new(until))
}
```

## Grammar

Fields are **minute hour day-of-month month day-of-week**, separated by one or
more ASCII whitespace bytes (space, tab, CR, LF, vertical tab, form feed).
Leading/trailing whitespace is accepted. Input is ASCII and at most 4096 bytes.

| Field | Values | Names |
| --- | --- | --- |
| Minute | 0–59 | — |
| Hour | 0–23 | — |
| Day of month | 1–31 | — |
| Month | 1–12 | JAN through DEC |
| Day of week | 0–7; 0 and 7 are Sunday | SUN through SAT |

Names accept ASCII case variants. Each field accepts comma-separated unions of
`*`, a value, an ascending inclusive `start-end` range, or any of these followed
by `/step`. A single `N/step` means `N-maximum/step`; a range starts stepping at
its first value. Steps are decimal integers 1–9999, including values larger than
the field: `*/9999` selects only its minimum. Duplicates are harmless. Signs,
empty list members, empty operands, descending/wrapping ranges and out-of-range
values are errors. Leading numeric zeroes are accepted.

For day-of-week, ranges/steps operate on 0–7 **before** converting 7 to Sunday:
`5-7` is Friday/Saturday/Sunday, `1/2` is Monday/Wednesday/Friday/Sunday, while
`SUN-SAT` stops at 6. `FRI-MON` is an error. `values(Field)` returns a new sorted
snapshot with Sunday canonicalized to 0.

Day-of-month and day-of-week use the traditional wildcard-sensitive rule: if
either field contains `*` or `*/1` as a list member, **both** fields must match;
otherwise **either** may match. `*/2` does not carry the wildcard marker.
Thus `0 0 13 * MON` means every Monday **or** the 13th, `0 0 * * MON` means
Mondays, and `0 0 1-31 * MON` means every valid date. Month/hour/minute always
combine with the day rule using AND. This marker rule agrees with
[robfig/cron v3.0.1](https://github.com/robfig/cron/blob/v3.0.1/spec.go).

Impossible dates remain valid schedules: `0 0 30 FEB *` has no occurrence.
There is no sixth seconds field or year field, descriptor (`@daily`, `@every`),
`?`, `L`, `W`, `#`, comment, command suffix, `TZ=` or `CRON_TZ=` syntax.
Timezone selection belongs to the API, never the process environment.

## Instants, DST and search bounds

`Schedule::matches(instant, zone, fold)` matches only **local** second 0 and
nanosecond 0. Historical offsets can make a matching UTC instant fall at a
nonzero UTC second. Dates use datetime's proleptic Gregorian years 1–9999.

`Fold::Both` includes both instants in a repeated local minute. `Earlier` or
`Later` includes only that occurrence, even when `after` lies between the two.
Missing local times (DST gaps, including skipped whole dates) are skipped; they
are never shifted to another clock time. The same policy applies to `matches`
and `next`. Callers wanting one execution across a repeated minute must choose
an explicit single-occurrence policy.

`next(after, zone, Search { until, max_steps, fold })` returns the least UTC
instant in **(after, until]** that matches. `Search::new(until)` sets
`max_steps = 1000000` and `fold = Both`. `until` must exceed `after`, and the
work limit must be 1–10000000, otherwise `InvalidOptions` is returned before
timezone work. There is no unbounded or implicit “next five years” search.

Search skips unselected months, checks dates in selected months, then resolves
only allowed hour/minute combinations on matching dates. It does not scan every
elapsed minute across years. Each visited date (or skipped month) and each
local-time resolution costs one step. Small fixed field scans and datetime's
bounded timezone resolution are included in each step, not separately charged.
The counter is local to each call. Exhaustion returns `WorkLimit`, even when a
candidate has been found but its minimality has not yet been established.
This is a deterministic work bound, not a wall-clock deadline or cancellation
token.

Datetime's `Offset::from_seconds` bounds offsets to ±93599 seconds
(25:59:59). Search begins at the earliest possible local date using this bound,
retains the least valid UTC candidate, and stops only when all later local
minutes must map at or after that candidate or beyond `until`. This accounts for
backward clock changes even if `after` is already inside a fold. The conservative
window may resolve several thousand minutes for an every-minute expression;
it is bounded independently of a distant `until` once a match is found.

`NoMatch` means the supplied interval has been completely searched without a
representable occurrence; it is not a global proof of impossibility. At calendar
edges, local minutes whose UTC conversion is outside datetime's supported range
are skipped. Date iteration ends safely at 9999-12-31. Other timezone failures
(including unknown TZif future rules or unsupported multiple folds) propagate
as `DateTime(dt::Error)`; timezone uncertainty is never turned into `NoMatch`.
`matches` likewise propagates failed instant-to-local conversions. Parse errors
have a zero-based `field` (0–4); -1 denotes input/field-count errors. `Parse`,
`InvalidOptions`, `WorkLimit`, `NoMatch` and `DateTime` are recoverable errors.

## Ownership and capabilities

Schedules contain only private scalar bitsets and flags. Copies can be used
concurrently, parsing retains no mutable input collection, and changing a
`values` result cannot change any schedule. Search state is per call. Supplied
datetime timezone handles are immutable parsed snapshots; cron adds no global
cache, process timezone setting, file access or clock read.

This package computes calendar occurrences. A background daemon, timers, worker
execution, persisted queues, catch-up/misfire policies, retries, distributed
locking and exactly-once job execution are separate capabilities and are not
provided by this package.

## Validation

From this repository:

```sh
goml test --timeout 120s
goml verify --timeout 300s
goml run --example basic
GOFLAGS=-race CGO_ENABLED=1 goml test --target-dir _artifact/race --timeout 300s
```

Tests cover parser rejection/normalization, wildcard day semantics, snapshots,
shared concurrent handles, strict/nanosecond boundaries, budget exhaustion,
calendar endpoints and a 400-year impossible schedule. The example's independent
consumer tests replay 640 results from robfig/cron v3.0.1 and 900 results from
Python's UTC timeline enumeration with the exact bundled TZif bytes. Tests run
offline from frozen compressed vectors; Python and the Go oracle dependency are
needed only to regenerate them. See [reference provenance](examples/basic/tests/data/README.md)
and [timezone fixtures](examples/basic/testdata/zones/README.md).
