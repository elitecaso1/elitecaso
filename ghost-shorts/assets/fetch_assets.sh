#!/bin/bash
# Downloads the car models + HDRIs used by the shorts into this folder (see CREDITS.md).
set -e
cd "$(dirname "$0")"
R=https://raw.githubusercontent.com
G=$R/gkjohnson/3d-demo-data/main
mkdir -p hdri
curl -fsSLo challenger.glb $G/models/blendswap/dodge-challenger.glb
curl -fsSLo supra.glb      $G/models/vehicles/toyota-supra-gt300.glb
curl -fsSLo ferrari.glb    $R/mrdoob/three.js/dev/examples/models/gltf/ferrari.glb
curl -fsSLo CarConcept.glb $R/KhronosGroup/glTF-Sample-Assets/main/Models/CarConcept/glTF-Binary/CarConcept.glb
for h in moonless_golf_1k narrow_moonlit_road_2k st_peters_square_night_2k kloppenheim_05_2k autoshop_01_2k wasteland_clouds_puresky_2k; do
  curl -fsSLo hdri/$h.hdr $G/hdri/$h.hdr 2>/dev/null || curl -fsSLo hdri/$h.hdr $R/mrdoob/three.js/dev/examples/textures/equirectangular/$h.hdr
done
echo "assets ready"
