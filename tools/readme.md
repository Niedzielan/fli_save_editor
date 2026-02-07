usmap created by trumank : https://github.com/trumank/jmap

To create a fli_sav_pattern:

1. 
get a .usmap file for Fantasy Life i (either dumped via UE4SS or from https://github.com/DRayX/FLi-FModel)

2.
drag it onto usmap_to_json_DRAG_HERE.bat 
or run 
usmap to-json Mapping.usmap Mapping.json

3.
run usmap_json_to_structs.py
This parses the usmap into an ImHex-like pattern file

4.
run usmap2structs_patch.py
This converts the usmap2structs.txt from the previous step and changes specific entries, as the usmap does not map completely to the custom FLi save format
The resulting usmap2structs_patched.txt may be able to be renamed to fli_sav_pattern.txt and used directly
To debug: Load a save and a pattern file into ImHex, and figure out what other entries need adjusting.