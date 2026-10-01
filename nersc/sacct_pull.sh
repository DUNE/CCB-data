#!/bin/bash
# Pull Slurm job accounting for the DUNE NERSC projects, in date chunks.
#
# Run this on a Perlmutter login node.  Output goes to sacct_<project>.txt in
# the current directory; gzip them and drop them in nersc/data/, where
# sacct_jobs.py will read them (gzipped or not).
#
#   ./sacct_pull.sh [START] [END] [CHUNK_DAYS]
#   ./sacct_pull.sh 2025-01-01 2026-10-01 30      # defaults
#
# Three things that are easy to get wrong, all of them silent:
#
#   -a            without it sacct reports only YOUR jobs, so a query for a
#                 production account returns nothing and no error.
#   m3249_g       Perlmutter GPU allocations are SEPARATE Slurm accounts with
#                 a "_g" suffix.  Querying only "m3249" misses every GPU job.
#   chunking      wide date ranges fail on this cluster.  30-day chunks work;
#                 drop to 7 if a chunk comes back empty with a nonzero rc.
#
# Jobs that span a chunk boundary are returned in both chunks and de-duplicated
# on JobID at the end.  Slurm accounting retention is finite - if the first
# chunks return nothing, those records have aged out, which is itself worth
# knowing.

START=${1:-2025-01-01}
END=${2:-$(date +%F)}
CHUNK=${3:-30}
FMT="JobID,JobName%60,Account,User,Partition,NNodes,NCPUS,Elapsed,Start,End,State"

run() {  # run <label> <account-list>
  OUT="sacct_$1.txt"; TMP="${OUT}.tmp"; : > "$TMP"
  echo "=== $1  (accounts: $2) ==="
  cur="$START"
  while [[ "$cur" < "$END" ]]; do
    nxt=$(date -d "$cur +$CHUNK days" +%F)
    [[ "$nxt" > "$END" ]] && nxt="$END"
    out=$(sacct -a -A "$2" -S "$cur" -E "$nxt" --format="$FMT" -X -P)
    rc=$?
    n=$(printf '%s\n' "$out" | grep -vc '^JobID')
    printf "  %s -> %s  rc=%d  %6s rows\n" "$cur" "$nxt" "$rc" "$n"
    printf '%s\n' "$out" >> "$TMP"
    cur="$nxt"
  done
  grep -m1 '^JobID' "$TMP" > "$OUT" 2>/dev/null
  grep -v '^JobID' "$TMP" | grep -v '^$' | sort -u -t'|' -k1,1 >> "$OUT"
  rm -f "$TMP"
  echo "  -> $OUT  ($(( $(wc -l < "$OUT") - 1 )) unique jobs)"
}

run m3249 "m3249,m3249_g"
run dune  "dune,dune_g"
