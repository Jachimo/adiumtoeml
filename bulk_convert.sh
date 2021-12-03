#/usr/bin/env bash
# Bash script to bulk convert chat logs
# Usage: ./bulk_convert.sh rootdir outdir
#  where 'rootdir' is the Adium Logs folder or another subfolder containing log files
# Successfully processed files and their Message-ID headers will be written to stdout and to a log file.

indir=$1
outdir=$2
logfile=converted_`date -I`.log  # `date -I` may not be supported on all systems

mkdir -p "$outdir"  # create output dir if it doesn't already exist

find "$indir" -name '*.chatlog' -exec ./adiumToEml.py {} "$outdir" --no-background \; | tee "$outdir"/"$logfile"

find "$indir" -name '*.AdiumHTMLLog' -exec ./adiumToEml.py {} "$outdir" --no-background \; | tee -a "$outdir"/"$logfile"
find "$indir" -name '*.html' -exec ./adiumToEml.py {} "$outdir" --no-background \; | tee -a "$outdir"/"$logfile"
