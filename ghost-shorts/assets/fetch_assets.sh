#!/bin/bash
# Downloads the car models + HDRIs used by the shorts into this folder.
set -e
cd "$(dirname "$0")"
R=https://raw.githubusercontent.com
mkdir -p hdri
curl -fsSLo ferrari.glb    $R/mrdoob/three.js/dev/examples/models/gltf/ferrari.glb
curl -fsSLo CarConcept.glb $R/KhronosGroup/glTF-Sample-Assets/main/Models/CarConcept/glTF-Binary/CarConcept.glb
for h in moonless_golf_1k venice_sunset_1k blouberg_sunrise_2_1k quarry_01_1k; do
  curl -fsSLo hdri/$h.hdr $R/mrdoob/three.js/dev/examples/textures/equirectangular/$h.hdr
done
echo "assets ready"
