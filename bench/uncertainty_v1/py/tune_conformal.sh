#!/bin/bash
# usage: tune_conformal.sh <seeds> <tag>
cd "$(dirname "$0")"
i=0
for gg in '{"W":300,"HL":150,"gamma":0.01}' '{"W":600,"HL":400,"gamma":0.01}' '{"W":1200,"HL":1000,"gamma":0.01}' '{"W":600,"HL":400,"gamma":0.005}' '{"W":600,"HL":400,"gamma":0.02}'; do
  i=$((i+1)); python3 conformal.py $1 0.6 ../results/ctune_$2_g$i "$gg"
done
