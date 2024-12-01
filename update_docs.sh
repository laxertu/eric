#!/bin/bash
cd docs
rm -rf build/html/
rm -rf build/markdown/

make markdown
make html

rm -rf ../docs_html/
rm -rf ../docs_markdown/

cp -rf build/html/ ../docs_html/
cp -rf build/html/ ../docs_markdown/
