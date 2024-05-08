#!/usr/bin/env bash

git checkout inc
git checkout origin/main -- inc/fiber.h
mv inc/fiber.h fiber.h
rmdir inc
git add fiber.h
git commit -m "Deploy header file"
git push origin inc

git checkout src
git checkout origin/main -- src/asyncify
mv src/asyncify asyncify
git checkout origin/main -- src/wasmfx
mv src/wasmfx wasmfx
rmdir src
git commmit -m "Deploy implementation files"
git push origin src

git checkout main
