#!/bin/sh
set -eu
cd "$(dirname "$0")"
sh build.sh
javac -encoding UTF-8 --release 17 -Xlint:all -cp out -d out test/SelfTest.java
java -cp out SelfTest
