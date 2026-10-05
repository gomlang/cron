// Independent oracle. Run from this directory: go run .
package main

import (
	"compress/gzip"
	"fmt"
	cron "github.com/robfig/cron/v3"
	"math/rand"
	"os"
	"time"
)

func main() {
	file, err := os.Create("../examples/basic/tests/data/ordinary.tsv.gz")
	if err != nil {
		panic(err)
	}
	defer file.Close()
	out := gzip.NewWriter(file)
	defer out.Close()
	parser := cron.NewParser(cron.Minute | cron.Hour | cron.Dom | cron.Month | cron.Dow)
	specs := []string{"* * * * *", "*/15 9-17 * * MON-FRI", "5/17 2,18 13 * FRI", "0 0 29 FEB *", "0 0 13 * MON", "0 0 */2 * MON", "0 0 */1 * MON", "0 0 1-31 * MON", "0 0 1,*/1 * MON", "0 0 * JAN-MAR SUN", "0 0 31 * *", "0 0 30 FEB *"}
	rng := rand.New(rand.NewSource(82317))
	for n := 0; n < 148; n++ {
		mins := []string{"*", "*/7", fmt.Sprint(rng.Intn(60)), "3,17,41", "11-59/13"}
		hours := []string{"*", "*/5", fmt.Sprint(rng.Intn(24)), "4-17/3"}
		days := []string{"*", "*/1", "*/2", "1,15,31", fmt.Sprint(1 + rng.Intn(31))}
		months := []string{"*", "*/3", "FEB,AUG", "JAN-DEC/2"}
		weekdays := []string{"*", "SUN", "MON-FRI", "0,3,6", "*/2"}
		specs = append(specs, fmt.Sprintf("%s %s %s %s %s", mins[rng.Intn(len(mins))], hours[rng.Intn(len(hours))], days[rng.Intn(len(days))], months[rng.Intn(len(months))], weekdays[rng.Intn(len(weekdays))]))
	}
	starts := []string{"1999-12-31T23:59:59Z", "2024-02-28T00:00:00Z", "2024-09-13T12:30:00Z", "2099-12-31T23:59:59.999999999Z"}
	count := 0
	for _, spec := range specs {
		s, err := parser.Parse(spec)
		if err != nil {
			panic(err)
		}
		for _, start := range starts {
			after, err := time.Parse(time.RFC3339Nano, start)
			if err != nil {
				panic(err)
			}
			until := after.AddDate(5, 0, 0)
			next := s.Next(after)
			expected := "none"
			if !next.IsZero() && !next.After(until) {
				expected = next.UTC().Format(time.RFC3339Nano)
			}
			match := s.Next(after.Add(-time.Nanosecond)).Equal(after)
			fmt.Fprintf(out, "%s\t%s\t%s\t%t\t%s\n", spec, start, until.Format(time.RFC3339Nano), match, expected)
			count++
		}
	}
	fmt.Println("robfig/cron v3.0.1 vectors:", count)
}
