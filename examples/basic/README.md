# Basic cron consumer

Runs a weekday 09:30 schedule in explicit UTC and checks that the occurrence
strictly after Friday's 09:30 is Monday's 09:30. Output: `cron: ok`.

The tests also exercise the public package using an isolated registry snapshot,
with fixed parser and timezone reference vectors. Run `goml run --example basic`,
`goml test` from the library root.
