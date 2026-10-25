#!/usr/bin/env bash
# Chay script goc realworld.py (khong sua) de doi chieu so dung/tong voi eval_realworld_probs.py.
# Chay: bash audit/scripts/run_realworld_official.sh   (tu C:/AL-PLR)
set -e
cd "$(dirname "$0")/../../garbage_classifier"
mkdir -p ../audit/eval_realworld/official
SETS="../realworld_test ../realworld_test2 ../realworld_clothes_test ../realworld_pin_test ../realworld_mta_test ../realworld_bdw_test ../realworld_bower_test ../realworld_rw5_test ../realworld_curated ../realworld_loai_bo/realworld_test ../realworld_loai_bo/realworld_test2"
for run in v2_r18 v4_r18 v5_r18 v6b_r18; do
  for th in 0.5 0.3; do
    echo "### $run nguong $th"
    PYTHONPATH=src .venv/Scripts/python.exe -m garbage_classifier.realworld --checkpoint artifacts/$run/best_model.pt \
      --nguong-pin $th --output ../audit/eval_realworld/official/${run}_pin${th}.json $SETS
  done
done
