# Fixed timezone fixtures

These five TZif files are copied byte-for-byte from ecosystem::datetime's
`examples/basic/testdata/zones`, release 2026c. `VERSION` records that release;
`SHA256SUMS` freezes individual files and ordinary tests verify each hash.
They cover America/New_York, Australia/Lord_Howe, Pacific/Apia, Europe/Dublin and
Asia/Kathmandu. The Dublin file retains datetime's distribution compatibility
encoding. Both GoML datetime and the independent Python zoneinfo reference read
these exact files, so tests do not depend on installed system timezone data.

Compiled IANA timezone data is [public domain](https://data.iana.org/time-zones/tz-link.html).
These are offline test fixtures; cron does not ship or implicitly load a complete
timezone database. Applications can explicitly use datetime::tzdata or their own
chosen datetime timezone source.

`Synthetic/Finite` is the separately authored datetime fixture with TZif v2,
types `STD` (UTC+00:00, standard) and `DST` (UTC+01:00, daylight), one transition at Unix
second 0 to DST, and an empty future-rule footer. It verifies that unsupported
future data remains a recoverable error rather than a claimed absence of matches.
