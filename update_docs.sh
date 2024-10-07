#!/bin/bash
cd docs
make markdown
cp build/markdown/index.md ../README.md
cp build/markdown/docs.md ../docs.md
