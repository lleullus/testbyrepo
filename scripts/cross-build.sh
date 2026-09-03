#!/bin/bash
#
# Example:
#         env BUILD_TARGET=x86_64 ./scripts/cross-build.sh
#
# The source archives used by this script are checksum-pinned.  New versions
# must be accompanied by an explicit SHA-256 value; an unknown version fails
# closed instead of falling back to an unverified curl | tar pipeline.
#
set -euo pipefail

CROSS_ROOT="${CROSS_ROOT:-/opt/cross}"
STAGE_ROOT="${STAGE_ROOT:-/opt/stage}"
BUILD_ROOT="${BUILD_ROOT:-/opt/build}"
DOWNLOAD_ROOT="${DOWNLOAD_ROOT:-${BUILD_ROOT}/downloads}"
BUILD_TARGET="${BUILD_TARGET:-x86_64}"
TLS_BACKEND="${TLS_BACKEND:-mbedtls}"

# Phase 9 validated defaults.  Individual versions remain overridable so the
# native matrix can be reproduced without changing the script.  OpenSSL 3.6.1
# remains a tested alternative TLS backend, but Mbed TLS 3.6.7 is the selected
# default because it preserves the existing architecture with a much smaller
# static artifact while passing the same protocol and TLS gates.
ZLIB_VERSION="${ZLIB_VERSION:-1.3.2}"
JSON_C_VERSION="${JSON_C_VERSION:-0.19}"
MBEDTLS_VERSION="${MBEDTLS_VERSION:-3.6.7}"
OPENSSL_VERSION="${OPENSSL_VERSION:-3.6.1}"
LIBUV_VERSION="${LIBUV_VERSION:-1.52.1}"
LIBWEBSOCKETS_VERSION="${LIBWEBSOCKETS_VERSION:-4.5.8}"
MUSL_TOOLCHAIN_RELEASE="${MUSL_TOOLCHAIN_RELEASE:-2021-11-23}"

if [ -z "${CMAKE_BIN:-}" ]; then
    if command -v cmake >/dev/null 2>&1; then
        CMAKE_BIN="$(command -v cmake)"
    elif python3 -c 'import cmake' >/dev/null 2>&1; then
        CMAKE_BIN="$(python3 -c 'import cmake; print(cmake.CMAKE_BIN_DIR + "/cmake")')"
    else
        echo "cmake not found" >&2
        exit 1
    fi
fi

cmake_configure() {
    "${CMAKE_BIN}" -DCMAKE_POLICY_VERSION_MINIMUM=3.5 "$@"
}

frozen_checksum() {
    case "$1:$2" in
        zlib:1.3.1) echo 9a93b2b7dfdac77ceba5a558a580e74667dd6fede4585b91eefb60f03b72df23 ;;
        zlib:1.3.2) echo bb329a0a2cd0274d05519d61c667c062e06990d72e125ee2dfa8de64f0119d16 ;;
        json-c:0.17) echo 7550914d58fb63b2c3546f3ccfbe11f1c094147bd31a69dcd23714d7956159e6 ;;
        json-c:0.19) echo 37ad0249902e301bd9052bf712e511fcc6acff4ecaad4b5900aad9ce564e26de ;;
        mbedtls:2.28.5) echo 849e86b626e42ded6bf67197b64aa771daa54e2a7e2868dc67e1e4711959e5e3 ;;
        mbedtls:3.6.7) echo a7e8bcbec0e6f761b4af24f25677626b35f762f68eef79c08677a363212d11f6 ;;
        mbedtls:4.2.0) echo 2bed9d713b4668f76553b097e72b8aa30bc8f112a940d7ae228d524bbde6ffea ;;
        openssl:3.6.1) echo b1bfedcd5b289ff22aee87c9d600f515767ebf45f77168cb6d64f231f518a82e ;;
        openssl:4.0.2) echo 736b467530f916737b7031310ccb21d8218c6229e61e8e160cd1d3458cd543a8 ;;
        libuv:1.44.2) echo ccfcdc968c55673c6526d8270a9c8655a806ea92468afcbcabc2b16040f03cb4 ;;
        libuv:1.52.1) echo 66d511b9e6e334c0e62279eb234fbfb2b3110b1479c09b95b44c7afca8cff9e7 ;;
        libwebsockets:4.3.3) echo 6fd33527b410a37ebc91bb64ca51bdabab12b076bc99d153d7c5dd405e4bdf90 ;;
        libwebsockets:4.5.7) echo d08df7634da0a377a4e077400ed6b2d1d25cf0b239e89397cd39432c5eb437ac ;;
        libwebsockets:4.5.8) echo b6ade658f4af3a823d0dc806ae5ef0623f0f4f5e2aeb895a0f77c4783840c30e ;;
        libwebsockets:5.0.0) echo f853c6582101cfcee3a5a9e28ae92ab19d9735c5f31f0bb2e9794b5106123962 ;;
        *)
            echo "no frozen SHA-256 for $1 $2" >&2
            return 1
            ;;
    esac
}

fetch_verified() {
    local url="$1"
    local sha256="$2"
    local filename="$3"
    local archive="${DOWNLOAD_ROOT}/${filename}"
    local partial="${archive}.part"

    mkdir -p "${DOWNLOAD_ROOT}"

    if [ -f "${archive}" ]; then
        if printf '%s  %s\n' "${sha256}" "${archive}" | sha256sum -c - >/dev/null 2>&1; then
            echo "=== Reusing verified ${filename}" >&2
            printf '%s\n' "${archive}"
            return 0
        fi
        echo "cached checksum mismatch, removing ${archive}" >&2
        rm -f "${archive}"
    fi

    rm -f "${partial}"
    echo "=== Downloading ${url}" >&2
    if ! curl --fail --location --silent --show-error --retry 3 --retry-all-errors \
        --connect-timeout 15 --output "${partial}" "${url}"; then
        rm -f "${partial}"
        return 1
    fi

    if ! printf '%s  %s\n' "${sha256}" "${partial}" | sha256sum -c - >/dev/null; then
        rm -f "${partial}"
        echo "SHA-256 mismatch for ${url}" >&2
        return 1
    fi

    mv "${partial}" "${archive}"
    printf '%s\n' "${archive}"
}

zlib_url() {
    case "${ZLIB_VERSION}" in
        1.3.1) echo "https://zlib.net/fossils/zlib-${ZLIB_VERSION}.tar.gz" ;;
        *) echo "https://zlib.net/zlib-${ZLIB_VERSION}.tar.gz" ;;
    esac
}

mbedtls_url() {
    case "${MBEDTLS_VERSION}" in
        2.*) echo "https://github.com/Mbed-TLS/mbedtls/archive/refs/tags/v${MBEDTLS_VERSION}.tar.gz" ;;
        3.6.7|4.*) echo "https://github.com/Mbed-TLS/mbedtls/releases/download/mbedtls-${MBEDTLS_VERSION}/mbedtls-${MBEDTLS_VERSION}.tar.bz2" ;;
        *) echo "no frozen Mbed TLS release URL for ${MBEDTLS_VERSION}" >&2; return 1 ;;
    esac
}

build_zlib() {
    local sha256="${ZLIB_SHA256:-$(frozen_checksum zlib "${ZLIB_VERSION}")}"
    local archive
    echo "=== Building zlib-${ZLIB_VERSION} (${TARGET})..."
    archive="$(fetch_verified "${ZLIB_URL:-$(zlib_url)}" "${sha256}" "zlib-${ZLIB_VERSION}.tar.gz")"
    tar xzf "${archive}" -C "${BUILD_DIR}"
    pushd "${BUILD_DIR}/zlib-${ZLIB_VERSION}"
        local configure_args=(--static --archs=-fPIC --prefix="${STAGE_DIR}")
        if [ "${ZLIB_VERSION}" = "1.3.2" ]; then
            configure_args+=(--disable-crcvx)
        fi
        env CHOST="${TARGET}" ./configure "${configure_args[@]}"
        make -j"$(nproc)" install
    popd
}

build_json-c() {
    local sha256="${JSON_C_SHA256:-$(frozen_checksum json-c "${JSON_C_VERSION}")}"
    local archive
    echo "=== Building json-c-${JSON_C_VERSION} (${TARGET})..."
    archive="$(fetch_verified "${JSON_C_URL:-https://s3.amazonaws.com/json-c_releases/releases/json-c-${JSON_C_VERSION}.tar.gz}" \
        "${sha256}" "json-c-${JSON_C_VERSION}.tar.gz")"
    tar xzf "${archive}" -C "${BUILD_DIR}"
    pushd "${BUILD_DIR}/json-c-${JSON_C_VERSION}"
        rm -rf build && mkdir -p build && cd build
        cmake_configure -DCMAKE_TOOLCHAIN_FILE="${BUILD_DIR}/cross-${TARGET}.cmake" \
            -DCMAKE_BUILD_TYPE=RELEASE \
            -DCMAKE_INSTALL_PREFIX="${STAGE_DIR}" \
            -DBUILD_SHARED_LIBS=OFF \
            -DBUILD_TESTING=OFF \
            -DDISABLE_THREAD_LOCAL_STORAGE=ON \
            ..
        make -j"$(nproc)" install
    popd
}

build_mbedtls() {
    local sha256="${MBEDTLS_SHA256:-$(frozen_checksum mbedtls "${MBEDTLS_VERSION}")}"
    local archive
    local archive_name="mbedtls-${MBEDTLS_VERSION}.tar.gz"
    local source_dir="mbedtls-${MBEDTLS_VERSION}"
    echo "=== Building mbedtls-${MBEDTLS_VERSION} (${TARGET})..."
    case "${MBEDTLS_VERSION}" in
        3.6.7|4.*) archive_name="mbedtls-${MBEDTLS_VERSION}.tar.bz2" ;;
    esac
    archive="$(fetch_verified "${MBEDTLS_URL:-$(mbedtls_url)}" "${sha256}" "${archive_name}")"
    case "${archive_name}" in
        *.tar.bz2) tar xjf "${archive}" -C "${BUILD_DIR}" ;;
        *) tar xzf "${archive}" -C "${BUILD_DIR}" ;;
    esac
    if [ ! -d "${BUILD_DIR}/${source_dir}" ] && [ -d "${BUILD_DIR}/mbedtls-mbedtls-${MBEDTLS_VERSION}" ]; then
        source_dir="mbedtls-mbedtls-${MBEDTLS_VERSION}"
    fi
    pushd "${BUILD_DIR}/${source_dir}"
        rm -rf build && mkdir -p build && cd build
        cmake_configure -DCMAKE_TOOLCHAIN_FILE="${BUILD_DIR}/cross-${TARGET}.cmake" \
            -DCMAKE_BUILD_TYPE=RELEASE \
            -DCMAKE_INSTALL_PREFIX="${STAGE_DIR}" \
            -DCMAKE_C_FLAGS="-ffile-prefix-map=${BUILD_DIR}=." \
            -DBUILD_SHARED_LIBS=OFF \
            -DENABLE_TESTING=OFF \
            -DENABLE_PROGRAMS=OFF \
            ..
        make -j"$(nproc)" install
    popd
}

map_openssl_target() {
    case "$1" in
        i686) echo linux-generic32 ;;
        x86_64) echo linux-x86_64 ;;
        arm|armhf|armv7l) echo linux-armv4 ;;
        aarch64) echo linux-aarch64 ;;
        mips|mipsel) echo linux-mips32 ;;
        mips64|mips64el) echo linux64-mips64 ;;
        powerpc64) echo linux-ppc64 ;;
        powerpc64le) echo linux-ppc64le ;;
        s390x) echo linux64-s390x ;;
        win32) echo mingw64 ;;
        *) echo "unknown openssl target: $1" >&2; return 1 ;;
    esac
}

build_openssl() {
    local sha256="${OPENSSL_SHA256:-$(frozen_checksum openssl "${OPENSSL_VERSION}")}"
    local archive
    local openssl_target
    local openssl_cflags="-fPIC -latomic"
    openssl_target="$(map_openssl_target "${BUILD_TARGET}")"
    echo "=== Building openssl-${OPENSSL_VERSION} (${openssl_target})..."
    archive="$(fetch_verified "${OPENSSL_URL:-https://www.openssl.org/source/openssl-${OPENSSL_VERSION}.tar.gz}" \
        "${sha256}" "openssl-${OPENSSL_VERSION}.tar.gz")"
    tar xzf "${archive}" -C "${BUILD_DIR}"
    pushd "${BUILD_DIR}/openssl-${OPENSSL_VERSION}"
        case "${BUILD_TARGET}" in
            s390x) openssl_cflags="${openssl_cflags} -march=z10" ;;
        esac
        env CC=gcc CROSS_COMPILE="${TARGET}-" CFLAGS="${openssl_cflags}" \
            ./Configure "${openssl_target}" no-shared no-tests no-docs no-ssl3 no-err \
            -DOPENSSL_SMALL_FOOTPRINT --prefix="${STAGE_DIR}"
        make -s -j"$(nproc)" all
        make -s install_sw
    popd
}

build_libuv() {
    local sha256="${LIBUV_SHA256:-$(frozen_checksum libuv "${LIBUV_VERSION}")}"
    local archive
    echo "=== Building libuv-${LIBUV_VERSION} (${TARGET})..."
    archive="$(fetch_verified "${LIBUV_URL:-https://dist.libuv.org/dist/v${LIBUV_VERSION}/libuv-v${LIBUV_VERSION}.tar.gz}" \
        "${sha256}" "libuv-v${LIBUV_VERSION}.tar.gz")"
    tar xzf "${archive}" -C "${BUILD_DIR}"
    pushd "${BUILD_DIR}/libuv-v${LIBUV_VERSION}"
        rm -rf build && mkdir -p build && cd build
        cmake_configure -DCMAKE_TOOLCHAIN_FILE="${BUILD_DIR}/cross-${TARGET}.cmake" \
            -DCMAKE_BUILD_TYPE=RELEASE \
            -DCMAKE_INSTALL_PREFIX="${STAGE_DIR}" \
            -DBUILD_SHARED_LIBS=OFF \
            -DLIBUV_BUILD_TESTS=OFF \
            -DLIBUV_BUILD_BENCH=OFF \
            ..
        make -j"$(nproc)" install
        rm -f "${STAGE_DIR}"/lib/libuv.so*
        if [ -f "${STAGE_DIR}/lib/libuv_a.a" ]; then
            mv -f "${STAGE_DIR}/lib/libuv_a.a" "${STAGE_DIR}/lib/libuv.a"
        fi
        test -f "${STAGE_DIR}/lib/libuv.a"
    popd
}

install_cmake_cross_file() {
    cat << EOF > "${BUILD_DIR}/cross-${TARGET}.cmake"
SET(CMAKE_SYSTEM_NAME $1)

set(CMAKE_C_COMPILER "${TARGET}-gcc")
set(CMAKE_CXX_COMPILER "${TARGET}-g++")

set(CMAKE_FIND_ROOT_PATH "${STAGE_DIR}")
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)

set(OPENSSL_ROOT_DIR "${STAGE_DIR}")
set(OPENSSL_USE_STATIC_LIBS TRUE)
EOF
}

build_libwebsockets() {
    local sha256="${LIBWEBSOCKETS_SHA256:-$(frozen_checksum libwebsockets "${LIBWEBSOCKETS_VERSION}")}"
    local archive
    local tls_args=()
    echo "=== Building libwebsockets-${LIBWEBSOCKETS_VERSION} (${TARGET}, TLS=${TLS_BACKEND})..."
    archive="$(fetch_verified "${LIBWEBSOCKETS_URL:-https://github.com/warmcat/libwebsockets/archive/refs/tags/v${LIBWEBSOCKETS_VERSION}.tar.gz}" \
        "${sha256}" "libwebsockets-${LIBWEBSOCKETS_VERSION}.tar.gz")"
    tar xzf "${archive}" -C "${BUILD_DIR}"
    pushd "${BUILD_DIR}/libwebsockets-${LIBWEBSOCKETS_VERSION}"
        sed -i 's/ websockets_shared//g' cmake/libwebsockets-config.cmake.in
        case "${TLS_BACKEND}" in
            mbedtls)
                # LWS 4.3.x probes OpenSSL even when Mbed TLS is selected.  The
                # historical workaround is unsafe on newer CMake files, where it
                # can remove flow-control lines and break configuration.
                case "${LIBWEBSOCKETS_VERSION}" in
                    4.3.*)
                        sed -i 's/ OR PC_OPENSSL_FOUND//g' lib/tls/CMakeLists.txt
                        sed -i '/PC_OPENSSL/d' lib/tls/CMakeLists.txt
                        ;;
                esac
                tls_args=(-DLWS_WITH_MBEDTLS=ON)
                ;;
            openssl)
                tls_args=(-DLWS_WITH_SSL=ON -DLWS_WITH_MBEDTLS=OFF -DOPENSSL_USE_STATIC_LIBS=TRUE)
                ;;
            *)
                echo "unknown TLS_BACKEND: ${TLS_BACKEND} (expected mbedtls or openssl)" >&2
                return 1
                ;;
        esac

        rm -rf build && mkdir -p build && cd build
        cmake_configure -DCMAKE_TOOLCHAIN_FILE="${BUILD_DIR}/cross-${TARGET}.cmake" \
            -DCMAKE_BUILD_TYPE=RELEASE \
            -DCMAKE_INSTALL_PREFIX="${STAGE_DIR}" \
            -DCMAKE_FIND_LIBRARY_SUFFIXES=".a" \
            -DCMAKE_EXE_LINKER_FLAGS="-static" \
            -DLWS_WITHOUT_TESTAPPS=ON \
            -DLWS_WITH_LIBUV=ON \
            -DLWS_STATIC_PIC=ON \
            -DLWS_WITH_SHARED=OFF \
            -DLWS_UNIX_SOCK=ON \
            -DLWS_IPV6=ON \
            -DLWS_ROLE_RAW_FILE=OFF \
            -DLWS_WITH_HTTP2=ON \
            -DLWS_WITH_HTTP_BASIC_AUTH=OFF \
            -DLWS_WITH_HTTP_STREAM_COMPRESSION=ON \
            -DLWS_WITH_UDP=OFF \
            -DLWS_WITHOUT_CLIENT=ON \
            -DLWS_WITHOUT_EXTENSIONS=OFF \
            -DLWS_WITH_LEJP=OFF \
            -DLWS_WITH_LEJP_CONF=OFF \
            -DLWS_WITH_LWSAC=OFF \
            -DLWS_WITH_SEQUENCER=OFF \
            -DLWS_WITH_UPNG=OFF \
            -DLWS_WITH_JPEG=OFF \
            -DLWS_WITH_DLO=OFF \
            -DLWS_WITH_SYS_STATE=OFF \
            -DLWS_WITH_SYS_SMD=OFF \
            -DLWS_WITH_SECURE_STREAMS=OFF \
            -DLWS_CTEST_INTERNET_AVAILABLE=OFF \
            "${tls_args[@]}" \
            ..
        make -j"$(nproc)" install
    popd
}

build_ttyd() {
    echo "=== Building ttyd (${TARGET})..."
    rm -rf build && mkdir -p build && cd build
    cmake_configure -DCMAKE_TOOLCHAIN_FILE="${BUILD_DIR}/cross-${TARGET}.cmake" \
        -DCMAKE_INSTALL_PREFIX="${STAGE_DIR}" \
        -DCMAKE_FIND_LIBRARY_SUFFIXES=".a" \
        -DCMAKE_C_FLAGS="-Os -ffunction-sections -fdata-sections -fno-unwind-tables -fno-asynchronous-unwind-tables -flto" \
        -DCMAKE_EXE_LINKER_FLAGS="-static -no-pie -Wl,-s -Wl,-Bsymbolic -Wl,--gc-sections" \
        -DCMAKE_BUILD_TYPE=RELEASE \
        ..
    make install
}

install_verified_toolchain() {
    local components="$1"
    local url_base="https://github.com/tsl0922/musl-toolchains/releases/download/${MUSL_TOOLCHAIN_RELEASE}"
    local filename="${TARGET}-cross.tgz"
    local sha256="${MUSL_CC_SHA256:-}"
    local archive

    if [ -z "${sha256}" ]; then
        case "${MUSL_TOOLCHAIN_RELEASE}:${TARGET}" in
            2021-11-23:x86_64-linux-musl)
                sha256=c5d410d9f82a4f24c549fe5d24f988f85b2679b452413a9f7e5f7b956f2fe7ea
                ;;
            *)
                echo "no frozen toolchain SHA-256 for ${MUSL_TOOLCHAIN_RELEASE} ${TARGET}; set MUSL_CC_SHA256 explicitly" >&2
                return 1
                ;;
        esac
    fi

    archive="$(fetch_verified "${MUSL_CC_URL:-${url_base}/${filename}}" "${sha256}" "${MUSL_TOOLCHAIN_RELEASE}-${filename}")"
    mkdir -p "${CROSS_ROOT}"
    tar xzf "${archive}" -C "${CROSS_ROOT}" --strip-components="${components}"
    export PATH="${PATH}:${CROSS_ROOT}/bin"
    command -v "${TARGET}-gcc" >/dev/null
}

build() {
    TARGET="$1"
    ALIAS="$2"
    STAGE_DIR="${STAGE_ROOT}/${TARGET}"
    BUILD_DIR="${BUILD_ROOT}/${TARGET}"
    local components="1"
    local system="Linux"

    if [ "${ALIAS}" = "win32" ]; then
        components=2
        system="Windows"
    fi

    echo "=== Installing verified toolchain ${ALIAS} (${TARGET})..."
    install_verified_toolchain "${components}"

    echo "=== Building target ${ALIAS} (${TARGET})..."
    rm -rf "${STAGE_DIR}" "${BUILD_DIR}"
    mkdir -p "${STAGE_DIR}" "${BUILD_DIR}"
    export PKG_CONFIG_PATH="${STAGE_DIR}/lib/pkgconfig"

    install_cmake_cross_file "${system}"

    build_zlib
    build_json-c
    build_libuv
    case "${TLS_BACKEND}" in
        mbedtls) build_mbedtls ;;
        openssl) build_openssl ;;
    esac
    build_libwebsockets
    build_ttyd
}

case "${BUILD_TARGET}" in
    amd64) BUILD_TARGET="x86_64" ;;
    arm64) BUILD_TARGET="aarch64" ;;
    armv7) BUILD_TARGET="armv7l" ;;
    ppc64) BUILD_TARGET="powerpc64" ;;
    ppc64le) BUILD_TARGET="powerpc64le" ;;
esac

case "${BUILD_TARGET}" in
    i686|x86_64|aarch64|mips|mipsel|mips64|mips64el|powerpc64|powerpc64le|s390x)
        build "${BUILD_TARGET}-linux-musl" "${BUILD_TARGET}"
        ;;
    arm)
        build "${BUILD_TARGET}-linux-musleabi" "${BUILD_TARGET}"
        ;;
    armhf)
        build arm-linux-musleabihf "${BUILD_TARGET}"
        ;;
    armv7l)
        build armv7l-linux-musleabihf "${BUILD_TARGET}"
        ;;
    win32)
        build x86_64-w64-mingw32 "${BUILD_TARGET}"
        ;;
    *)
        echo "unknown cross target: ${BUILD_TARGET}" >&2
        exit 1
        ;;
esac
