#!/bin/bash
cd docs

echo "Generating documentation..."
make markdown -q
make html -q

echo "Copying files..."
cp -rf build/html/ ../docs_html/
cp -rf build/markdown/ ../docs_markdown/

# patch
cp -rf source/_static ../docs_markdown/_static
echo "Done"