#!/bin/sh
set -eu
cd "$(dirname "$0")"
mkdir -p out
find src -name '*.java' | LC_ALL=C sort > out/sources.txt
javac -encoding UTF-8 --release 17 -Xlint:all -d out @out/sources.txt
