# THE GHOST – Shorts (Blender)

5 vertical shorts (1080×1920, 30 fps, Eevee). Har short ek Python (`bpy`) script hai jo
poora scene, animation aur camera cuts bana deta hai. Sirf cars, roads, terrain, light,
camera — koi insaan nahi.

| Short | Script | Length |
| --- | --- | --- |
| 1 – Mirror Mein Kuch Hai | `short1/build.py` | 35 s |
| 2 – Signal Laal Hai | `short2/build.py` | 30 s |
| 3 – Pahad Ka Mod | `short3/build.py` | 40 s |
| 4 – Garage No. 13 | `short4/build.py` | 35 s |
| 5 – 75 Meter | `short5/build.py` | 45 s |

## Chalana (Blender 4.2+)

```bash
cd ghost-shorts
./assets/fetch_assets.sh                      # ek baar: car models + HDRIs (credits: assets/CREDITS.md)
blender -b -P short1/build.py                 # short1/short1.blend banata hai
blender -b -P short1/build.py -- --preview    # 540x960, har 2nd frame -> renders/short1_preview.mp4
blender -b -P short1/build.py -- --render     # final -> renders/short1.mp4
```

Ya `.blend` kholo aur Blender mein Ctrl+F12. Camera cuts timeline markers par bound hain.

## Apne models / photos

- `assets/charger.glb`, `roadster.glb`, `pickup.glb`, `ghost.glb` — ho to procedural
  car ki jagah ye lagenge (front = +Y, wheels Z=0 par, ~5 m lambi).
- `assets/photos/photo1.png … photo13.png` — Short 4 ki diwar wali photos.

`common.py` mein saare shared helpers hain (car builder, road/path, rain, smoke, dashboard,
camera cuts). Music/SFX editor (CapCut/DaVinci) mein lagao.
