#!/usr/bin/env bash
# Per-repo flag capture: produce compile_commands.json (or raw_flags.json)
# for each repo, without necessarily building.
set -u
ROOT=/mnt/c/Users/danie/swesweep-parasoft-benchmark
R=$ROOT/repos
A=$ROOT/analysis
mkdir -p "$A"

cfg() { # name, lang, then command
  local name=$1; shift
  echo "=== $name: $*"
  ( cd "$R/$name" && timeout 1200 "$@" ) > "$A/$name.cfg.log" 2>&1
  echo "  exit=$?"
}

# --- CMake repos -----------------------------------------------------------
cfg libexpat cmake -S . -B build -G Ninja -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
  -DEXPAT_BUILD_EXAMPLES=OFF -DEXPAT_BUILD_TESTS=OFF -DEXPAT_BUILD_DOCS=OFF -DEXPAT_SHARED_LIBS=OFF
cfg z3       cmake -S . -B build -G Ninja -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DZ3_BUILD_EXAMPLES=OFF 2>/dev/null || true
cfg hdf5     cmake -S . -B build -G Ninja -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DBUILD_TESTING=OFF \
  -DHDF5_BUILD_EXAMPLES=OFF -DHDF5_BUILD_TOOLS=OFF -DHDF5_BUILD_UTILS=OFF -DHDF5_BUILD_HL_LIB=OFF
cfg jerryscript cmake -S . -B build -G Ninja -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
  -DJERRY_CMDLINE=OFF -DJERRY_CLI=OFF 2>/dev/null || true
cfg proj     cmake -S . -B build -G Ninja -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DBUILD_TESTING=OFF \
  -DENABLE_TIFF=OFF -DENABLE_CURL=OFF -DENABLE_SQLITE3=OFF -DENABLE_IPOD=OFF 2>/dev/null || true
cfg tarantool cmake -S . -B build -G Ninja -DCMAKE_EXPORT_COMPILE_COMMANDS=ON 2>/dev/null || true
cfg cvc5     cmake -S . -B build -G Ninja -DCMAKE_EXPORT_COMPILE_COMMANDS=ON 2>/dev/null || true
cfg duckdb   cmake -S . -B build -G Ninja -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
  -DBUILD_UNITTESTS=OFF -DBUILD_SHELL=OFF -DENABLE_SANITIZER=OFF -DBUILD_PARQUET_EXTENSION=OFF 2>/dev/null || true
cfg arrow    cmake -S . -B build -G Ninja -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DARROW_BUILD_TESTS=OFF \
  -DARROW_PARQUET=OFF -DARROW_COMPUTE=OFF -DARROW_DATASET=OFF -DARROW_FILESYSTEM=OFF \
  -DARROW_HDFS=OFF -DARROW_PYTHON=OFF 2>/dev/null || true
cfg opencv   cmake -S . -B build -G Ninja -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DBUILD_TESTS=OFF \
  -DBUILD_EXAMPLES=OFF -DBUILD_opencv_apps=OFF -DBUILD_opencv_python3=OFF -DBUILD_opencv_java=OFF 2>/dev/null || true
cfg gdal     cmake -S . -B build -G Ninja -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DBUILD_TESTING=OFF 2>/dev/null || true

# --- make / scons repos: dump compile lines without building ---------------
echo "=== php-src configure+make -n"
( cd "$R/php-src" && ./configure --disable-all --disable-cgi --without-pear > "$A/php-src.cfg.log" 2>&1 && make -n > "$A/php-src.make-n.log" 2>&1 ); echo "  exit=$?"

echo "=== micropython make -n (mpy-cross)"
( cd "$R/micropython/mpy-cross" && make -n V=1 > "$A/micropython.make-n.log" 2>&1 ); echo "  exit=$?"

echo "=== godot scons -n"
( cd "$R/godot" && timeout 600 scons -n platform=linuxbsd > "$A/godot.scons-n.log" 2>&1 ); echo "  exit=$?"

echo DONE
