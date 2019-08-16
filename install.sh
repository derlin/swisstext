#!/usr/bin/env bash

editable_mode=''
install_extra=''

function show_help {
cat <<'EOF'
Usage: install.sh [-d] [-e]
  -d : install in develop/editable mode
  -e : also install extra dependencies
EOF
}

while getopts "h?de" opt; do
    case "$opt" in
    h|\?)
        show_help
        exit 0
        ;;
    d)  editable_mode='-e'
        ;;
    e)  install_extra='[extra]'
        ;;
    esac
done

dirs="mongo backend frontend"

for dir in $dirs; do
    cd $dir
    echo "======== installing $dir ..."
    pip install $editable_mode .$install_extra
    [ $? -ne 0 ] && echo Something went wrong. Stopping... && exit 1
    cd ..
done