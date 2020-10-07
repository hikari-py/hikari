FROM debian:buster

ENV     PATH /usr/local/bin:$PATH
RUN     (mkdir /usr/src || true)
RUN     apt update && apt install -y --no-install-recommends \
            ca-certificates \
            curl \
            dpkg-dev \
            gcc \
            git \
            libbluetooth-dev \
            libbz2-dev \
            libc6-dev \
            libexpat1-dev \
            libffi-dev \
            libgdbm-dev \
            liblzma-dev \
            libncursesw5-dev \
            libreadline-dev \
            libsqlite3-dev \
            libssl-dev \
            make \
            netbase \
            tk-dev \
            uuid-dev \
            wget \
            xz-utils \
            zlib1g-dev \
     && git clone https://github.com/stackless-dev/stackless /usr/src/python --depth=1 -b v3.8.0b3 --progress
WORKDIR /usr/src/python
RUN     ./configure \
            --enable-loadable-sqlite-extensions \
            --enable-option-checking=fatal \
            --enable-shared \
            --with-system-expat \
            --with-system-ffi \
            LDFLAGS="-Wl,-rpath /usr/local/lib" \
     && make -j$(nproc) \
     && make install \
     && cd /usr/local/bin \
     && ln -fs python3.8 python3 \
     && ln -fs python3 python \
     && wget -O get-pip.py https://github.com/pypa/get-pip/raw/5578af97f8b2b466f4cdbebe18a3ba2d48ad1434/get-pip.py \
     && python get-pip.py \
            --disable-pip-version-check \
            --no-cache-dir \
            "pip==20.2.1" \
     && rm get-pip.py \
     && python -m pip install -U pip \
     && cd / \
     && apt-get purge -y --auto-remove \
     && rm -rf /usr/src/python /var/lib/apt/lists/* \
     && python -V
