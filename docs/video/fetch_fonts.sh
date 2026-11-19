#!/bin/bash
# Downloads the IBM Plex fonts (SIL Open Font License) used to draw the videos.
set -euo pipefail
cd "$(dirname "$0")"; mkdir -p fonts
base=https://raw.githubusercontent.com/google/fonts/main/ofl
for w in Regular Medium SemiBold Bold; do
  curl -fsSL -o "fonts/IBMPlexSansArabic-$w.ttf" "$base/ibmplexsansarabic/IBMPlexSansArabic-$w.ttf"
  curl -fsSL -o "fonts/IBMPlexSansDevanagari-$w.ttf" "$base/ibmplexsansdevanagari/IBMPlexSansDevanagari-$w.ttf"
done
curl -fsSL -o fonts/OFL.txt "$base/ibmplexsansarabic/OFL.txt"
ls -la fonts
