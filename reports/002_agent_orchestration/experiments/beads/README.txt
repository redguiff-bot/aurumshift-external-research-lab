Build: cp -r /tmp/lab/beads /tmp/lab/work/beads/src; go build -tags gms_pure_go -o bd ./cmd/bd (CGO build fails without ICU headers; ~60s w/ warm modules, first build incl. module download ~4min). bd 1.3.0, 214MB binary.
Results (race N=2,4,8: exactly 1 winner each; kill-9; lease expiry) are summarized in /tmp/lab/notes/beads.md
