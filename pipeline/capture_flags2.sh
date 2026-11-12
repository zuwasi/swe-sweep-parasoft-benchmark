#!/usr/bin/env bash
# Second pass: fix flag capture for the repos that failed round 1.
set -u
ROOT=/mnt/c/Users/danie/swesweep-parasoft-benchmark
R=$ROOT/repos
A=$ROOT/analysis
mkdir -p /tmp/buildroot

echo "=== tarantool: VERSION file + cmake"
mkdir -p "$R/tarantool/build" && echo '2.10.0' > "$R/tarantool/build/VERSION"
( cd "$R/tarantool" && timeout 1200 cmake -S . -B build -G Ninja -DCMAKE_EXPORT_COMPILE_COMMANDS=ON ) > "$A/tarantool.cfg2.log" 2>&1; echo "  exit=$?"

echo "=== hdf5: build dir on /tmp"
( cd "$R/hdf5" && timeout 1200 cmake -S . -B /tmp/buildroot/hdf5 -G Ninja -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DBUILD_TESTING=OFF -DHDF5_BUILD_EXAMPLES=OFF -DHDF5_BUILD_TOOLS=OFF -DHDF5_BUILD_UTILS=OFF -DHDF5_BUILD_HL_LIB=OFF ) > "$A/hdf5.cfg2.log" 2>&1; echo "  exit=$?"
[ -f /tmp/buildroot/hdf5/compile_commands.json ] && cp /tmp/buildroot/hdf5/compile_commands.json "$R/hdf5/build/compile_commands.json" 2>/dev/null || (mkdir -p "$R/hdf5/build" && cp /tmp/buildroot/hdf5/compile_commands.json "$R/hdf5/build/" 2>/dev/null); echo "  copied"

echo "=== arrow: cmake -S cpp"
( cd "$R/arrow" && timeout 1200 cmake -S cpp -B build -G Ninja -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DARROW_BUILD_TESTS=OFF -DARROW_PARQUET=OFF -DARROW_COMPUTE=OFF -DARROW_DATASET=OFF -DARROW_FILESYSTEM=OFF -DARROW_HDFS=OFF -DARROW_PYTHON=OFF -DARROW_SIMD_LEVEL=NONE ) > "$A/arrow.cfg2.log" 2>&1; echo "  exit=$?"

echo "=== gdal: build PROJ in /tmp then configure"
if [ ! -d /tmp/buildroot/proj/src/proj.cpp ]; then
  git clone -q --depth 1 --branch 9.2.1 https://github.com/OSGeo/PROJ.git /tmp/buildroot/proj-src 2>/dev/null
  ( cd /tmp/buildroot/proj-src && cmake -S . -B /tmp/buildroot/proj -G Ninja -DCMAKE_BUILD_TYPE=Release -DENABLE_TIFF=OFF -DENABLE_CURL=OFF -DBUILD_TESTING=OFF -DENABLE_IPOD=OFF > /tmp/buildroot/proj-cfg.log 2>&1 && ninja -C /tmp/buildroot/proj > /tmp/buildroot/proj-build.log 2>&1 )
fi
( cd "$R/gdal" && timeout 1800 cmake -S . -B build -G Ninja -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DBUILD_TESTING=OFF -DCMAKE_PREFIX_PATH=/tmp/buildroot/proj -DBUILD_PYTHON_BINDINGS=OFF ) > "$A/gdal.cfg2.log" 2>&1; echo "  exit=$?"

echo "=== php-src: tarball configure + make -n"
if [ ! -f /tmp/buildroot/php-8.2.12/Makefile ]; then
  mkdir -p /tmp/buildroot && cd /tmp/buildroot
  [ -f php-8.2.12.tar.gz ] || curl -sSL -o php-8.2.12.tar.gz https://www.php.net/distributions/php-8.2.12.tar.gz
  [ -d php-8.2.12 ] || tar xzf php-8.2.12.tar.gz
  ( cd php-8.2.12 && ./configure --disable-all --disable-cgi --without-pear > "$A/php-src.cfg2.log" 2>&1 && make -n > "$A/php-src.make-n.log" 2>&1 )
fi; echo "  exit=$?"

echo "=== godot: pip scons + scons -n"
python3 -m pip install --quiet --user scons 2>/dev/null || pip3 install --quiet --user scons 2>/dev/null
( cd "$R/godot" && PATH="$HOME/.local/bin:$PATH" timeout 900 scons -n platform=linuxbsd > "$A/godot.scons-n.log" 2>&1 ); echo "  exit=$?"

echo ALLDONE
