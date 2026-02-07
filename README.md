# fli_save_editor.py
ImGui based GUI to parse save json based on a pattern file.
Includes fli_bin2sav and fli_sav2json to enable loading/saving of any bin, sav, json files
#### usage info:  
Save files are usually located:  
`Steam/userdata/<your steam ID>/2993780/remote/002DAE74-00-gamedata.bin`  
Save Data (Useful) contains some of the more useful data, and formats inventory into tables including "Delete" and "Duplicate" options  
Save Data (Full) contains all save data   
Type information is taken from the pattern file and usually listed next to each field. e.g. if the type is s32 ensure that you only input a signed 32-bit number.
#### requirements:  
    imgui-bundle  
	pycrptodome
	
# fli_bin2sav.py  
Converts between encrypted compressed .bin and decrypted uncompressed .sav  
#### usage:  
 `fli_bin2sav decrypt input.bin output.sav`  
 `fli_bin2sav encrypt input.sav output.bin`  
#### optional arguments:  
	`--key` if encryption key is changed from default  
#### note:
zlib was changed in python 3.10.6, resulting in re-compressing not being bitwise identical.  
This should not affect functionality.  
3.10.5 is used for the pyinstaller exe versions.
#### requirements:  
    pycryptodome

 
# fli_sav2json.py
Uses a pattern file to parse save data and convert into JSON
#### usage:  
`fli_sav2json sav2json input.sav output.json`  
`fli_sav2json json2sav input.json output.sav`  
#### optional arguments:  
	`--patternfile` to use a different pattern file to `fli_sav_pattern.txt`
 
## Pattern file notes:
This is actually an ImHex-compatible pattern file

## Tools
Creates a fli save pattern from a usmap.  
see tools/readme.md for full info