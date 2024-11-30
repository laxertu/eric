#!/bin/bash
cd docs
#make markdown
make html
cp build/markdown/index.md ../README.md
cp build/markdown/docs.md ../docs.md
rm -rf ../docs_html/
cp -rf build/html/ ../docs_html/
