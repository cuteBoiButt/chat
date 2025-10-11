set(VCPKG_TARGET_ARCHITECTURE x64)
set(VCPKG_CRT_LINKAGE dynamic)
set(VCPKG_CMAKE_SYSTEM_NAME Linux)

# Define the list of ports that should be linked STATICALLY
set(STATICALLY_LINKED_PORTS
    abseil;ada-idna;ada-url;argon2;brotli;bzip2;c-ares;curl;dirent;drogon;
    expat;fontconfig;freetype;harfbuzz;jsoncpp;libcap;libepoxy;libffi;
    libjpeg-turbo;liblzma;libpng;libpq;libuuid;libxml2;lz4;nanosvg;openssl;
    pcre2;pixman;protobuf;pthreads;sdl2;tiff;trantor;utf8-range;wxwidgets;
    zlib;zstd
)
string(REPLACE ";" "|" STATICALLY_LINKED_PORTS_REGEX "${STATICALLY_LINKED_PORTS}")

if(PORT MATCHES "^(${STATICALLY_LINKED_PORTS_REGEX})$")
    # This port is on our special list, so set its linkage to static
    set(VCPKG_LIBRARY_LINKAGE static)
else()
    # For all other ports, set the linkage to dynamic
    set(VCPKG_LIBRARY_LINKAGE dynamic)
    set(VCPKG_FIXUP_ELF_RPATH ON)
endif()
