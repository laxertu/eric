#!/bin/bash
cd docs
make html
rm -rf ../docs_html/
cp -rf build/html/ ../docs_html/
