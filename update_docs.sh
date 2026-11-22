#!/bin/bash
# shellcheck disable=SC2164

#CURRENT_VERSION="$(poetry version --short)"
#ARCHIVE_DIR="docs_archive/$CURRENT_VERSION"
#mkdir -p docs_archive
#if [ -d "$ARCHIVE_DIR" ]; then
#  echo "$ARCHIVE_DIR already exists, skipping archive step"
#else
#  echo "Creating $ARCHIVE_DIR"
#  cp -rf docs_markdown/ "$ARCHIVE_DIR"
#  git add "$ARCHIVE_DIR"
#fi

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