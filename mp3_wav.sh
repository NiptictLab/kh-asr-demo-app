#!/usr/bin/env bash

file_in=$1

file_out="${file_in%.*}".wav

sox $file_in -r 16000 -c 1 -b 16 $file_out