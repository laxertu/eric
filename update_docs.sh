#!/bin/bash
# shellcheck disable=SC2164

CURRENT_VERSION="$(poetry version --short)"
rm -rf docs_archive/"$CURRENT_VERSION"
cp -rf docs_markdown/  docs_archive/"$CURRENT_VERSION"

git add docs_archive/"$CURRENT_VERSION"/*

cd docs
rm -rf build/html/
rm -rf build/markdown/
rm -rf build/doctrees/

make markdown
make html

rm -rf ../docs_html/
rm -rf ../docs_markdown/

cp -rf build/html/ ../docs_html/
cp -rf build/markdown/ ../docs_markdown/

# patch
cp -rf source/_static ../docs_markdown/_static
