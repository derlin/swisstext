#!/usr/bin/env bash

editable_mode=''
install_extra=''

function show_help {
cat <<'EOF'
Usage: install.sh [-d] [-e]
  -d : install in develop/editable mode
EOF
}

while getopts "h?d" opt; do
    case "$opt" in
    h|\?)
        show_help
        exit 0
        ;;
    d)  editable_mode='-e'
        ;;
    esac
done

dirs="mongo backend frontend"
cd src
for dir in $dirs; do
    cd $dir
    echo "======== installing $dir ..."

    cmd="pip install $editable_mode ."

    echo "Running $cmd"
    $cmd; [ $? -ne 0 ] && echo Something went wrong. Stopping... && exit 1
    cd ..
done
cd ..