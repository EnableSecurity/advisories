#!/bin/bash
contrib/scripts/install_prereq install

./configure --prefix=/opt/asterisk --with-pjproject-bundled --with-jansson-bundled
make menuselect.makeopts

# enable the extra logging
menuselect/menuselect --enable DONT_OPTIMIZE menuselect.makeopts
menuselect/menuselect --enable BETTER_BACKTRACES menuselect.makeopts

# enable opus
menuselect/menuselect --enable codec_opus menuselect.makeopts

# disable stuff we do not need
menuselect/menuselect --disable ODBC_STORAGE menuselect.makeopts
menuselect/menuselect --disable CHAN_IAX2 menuselect.makeopts
menuselect/menuselect --disable CHAN_MGCP menuselect.makeopts
menuselect/menuselect --disable CHAN_SKINNY menuselect.makeopts
menuselect/menuselect --disable CHAN_UNISTIM menuselect.makeopts
menuselect/menuselect --disable CHAN_OSS menuselect.makeopts
menuselect/menuselect --disable CHAN_PHONE menuselect.makeopts
menuselect/menuselect --disable CDR_SQLITE3_CUSTOM menuselect.makeopts
menuselect/menuselect --disable CEL_SQLITE3_CUSTOM menuselect.makeopts
menuselect/menuselect --disable PBX_DUNDI menuselect.makeopts
menuselect/menuselect --disable CHAN_MOBILE menuselect.makeopts
menuselect/menuselect --disable CHAN_OOH323 menuselect.makeopts
menuselect/menuselect --disable APP_MYSQL menuselect.makeopts
menuselect/menuselect --disable APP_DISA menuselect.makeopts
menuselect/menuselect --disable CHAN_DAHDI menuselect.makeopts
menuselect/menuselect --disable CHAN_MOTIF menuselect.makeopts
menuselect/menuselect --disable CHAN_MSIDN menuselect.makeopts
menuselect/menuselect --disable CHAN_NBS menuselect.makeopts
menuselect/menuselect --disable CHAN_VPB menuselect.makeopts

# build
make -j`grep ^cpu\scores /proc/cpuinfo | uniq |  awk '{print $4}'`
make install

