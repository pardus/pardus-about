#!/bin/bash

ZIPNAME="pardus_system_report.tar.gz";
if [ $LANG == "tr_TR.UTF-8" ]; then
    ZIPNAME="pardus_sistem_raporu.tar.gz";
fi

desktop=$(xdg-user-dir DESKTOP);
cp /tmp/$ZIPNAME "$desktop"
