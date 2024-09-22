#!/bin/bash
cd docs
make markdown
cp build/markdown/index.md ../README.md