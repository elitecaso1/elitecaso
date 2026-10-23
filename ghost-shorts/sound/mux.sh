#!/bin/bash
# mux.sh shortN  -> renders/shortN_sound.mp4 (video + renders/shortN.wav)
cd "$(dirname "$0")/.."
ffmpeg -y -loglevel error -i renders/$1.mp4 -i renders/$1.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/$1_sound.mp4
ls -la renders/$1_sound.mp4
