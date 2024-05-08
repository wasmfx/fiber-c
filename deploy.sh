#!/usr/bin/env bash

git checkout inc
git checkout origin/main -- inc/fiber.h
git mv inc/fiber.h fiber.h
git rm -rf inc
git add fiber.h
git commit -m "Deploy header file"
git push origin inc

git checkout src
git checkout origin/main -- src/asyncify
git mv src/asyncify asyncify
git checkout origin/main -- src/wasmfx
git mv src/wasmfx wasmfx
git rm -rf src
git commit -m "Deploy implementation files"
git push origin src

git checkout main
