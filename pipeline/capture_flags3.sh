#!/usr/bin/env bash
set -u
ROOT=/mnt/c/Users/danie/swesweep-parasoft-benchmark
A=$ROOT/analysis
echo "=== tarantool cmake (VERSION at root)"
( cd $ROOT/repos/tarantool && timeout 1200 cmake -S . -B build -G Ninja -DCMAKE_EXPORT_COMPILE_COMMANDS=ON ) > $A/tarantool.cfg3.log 2>&1; echo "  exit=$?"
echo "=== PROJ rebuild without apps"
( cd /tmp/buildroot/proj-src && rm -rf /tmp/buildroot/proj && cmake -S . -B /tmp/buildroot/proj -G Ninja -DCMAKE_BUILD_TYPE=Release -DENABLE_TIFF=OFF -DENABLE_CURL=OFF -DBUILD_TESTING=OFF -DBUILD_APPS=OFF > /tmp/buildroot/proj-cfg2.log 2>&1 && ninja -C /tmp/buildroot/proj > /tmp/buildroot/proj-build2.log 2>&1 ); echo "  exit=$?"
echo "=== gdal cmake with PROJ"
( cd $ROOT/repos/gdal && timeout 1800 cmake -S . -B build -G Ninja -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DBUILD_TESTING=OFF -DCMAKE_PREFIX_PATH=/tmp/buildroot/proj -DBUILD_PYTHON_BINDINGS=OFF ) > $A/gdal.cfg3.log 2>&1; echo "  exit=$?"
echo F3DONE
