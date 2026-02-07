import struct
import json
import argparse

class SaveData:
    save_dict = {}
    save_binary = b''
    save_structs = {}
    save_enums = {}
    debug_txt = ""
    debug_log = False

    def parsePatternFile(self, patternFile = "fli_sav_pattern.txt"):
        print(f"Parsing pattern file {patternFile}")
        self.save_structs = {}
        self.save_enums = {}
        with open(patternFile, "r") as patternFileHandle:
            patternDataLines = patternFileHandle.readlines()
        current_struct_name = ""
        current_enum_name = ""
        skip_current_struct = False
        batch_comment = False
        for line in patternDataLines:
            # Skip non-structs and comments
            if line == "" or line == "\n" or line.lstrip().startswith("//") or line.lstrip().startswith("import"):
                continue
            elif line.startswith("/*"):
                if "*/" not in line:
                    batch_comment=True
                    continue
                else:
                    continue
            elif batch_comment and "*/" in line:
                batch_comment = False
            elif batch_comment:
                continue
            # Duplicate self.save_structs if #define X Y
            if line.startswith("#define"):
                _, target, source = line.strip().split(" ")
                target = target.strip()
                source = source.strip()
                if source not in self.save_structs:
                    print(f"#define {target} {source} but no {source}, assuming handled directly and setting struct to {{}}")
                    self.save_structs[target] = {}
                else:
                    self.save_structs[target] = self.save_structs[source]
            elif line.startswith("enum"):
                tmp1, tmp2 = line.split(":") # enum guaranteed to have a type, # enum name : type {
                current_enum_name = tmp1[tmp1.find("enum ")+5:].strip() # enum [name] : type {
                enum_type = tmp2[:tmp2.find("{")-1].strip() # enum name : [type] {
                self.save_enums[current_enum_name] = {"type": enum_type, "entries": {}}
            elif line.startswith("struct"):
                skip_current_struct = False # new struct, not current
                current_struct_super = None
                inners = [] # inners are inner parameters e.g. TMap<T1, T2> inners are ["T1", "T2"]
                if ":" in line: # super
                    tmp1, tmp2 = line.split(":")
                    current_struct_name = tmp1[tmp1.find("struct ")+6:].strip() # struct [X] : Y {
                    current_struct_super = tmp2[:tmp2.find("{")-1].strip() # struct X : [Y] {
                else: # no super
                    current_struct_name = line[line.find("struct ")+6:line.find("{")].strip() # struct [X] {
                if "<" in current_struct_name: # e.g. TYPE<T>
                    inners = current_struct_name[current_struct_name.find("<")+1:current_struct_name.find(">")].split(",") # TYPE<[T1, T2, T3]>
                    current_struct_name = current_struct_name[:current_struct_name.find("<")] # [TYPE]<T1, T2, T3>
                self.save_structs[current_struct_name] = {"super": current_struct_super, # None or super
                                                "parameters": {}} # initialize parameter dict
                if len(inners) > 0:
                    self.save_structs[current_struct_name]["generic_types"] = [inner.strip() for inner in inners] # Copy inner types to dict
            elif line.lstrip().startswith("};") or "};" in line: # end of struct
                current_struct_name = ""
                current_enum_name = ""
                skip_current_struct = False
            elif line.startswith("if "): # currently conditional struct elements are not supported
                print(f"\"if\" in struct currently not supported. Setting struct {current_struct_name} to empty and skipping")
                skip_current_struct = True
                #if current_struct_name in self.save_structs:
                #    del self.save_structs[current_struct_name]
                self.save_structs[current_struct_name] = {} # keep in self.save_structs but empty ? Unsure which is better
            elif skip_current_struct: # In a struct, but skipping until next struct
                continue
            elif current_struct_name != "": # regular struct content
                line_ignore_comments = line.split(";")[0] # [Type parameter]; // comment stuff
                parameter =  line_ignore_comments.split(" ")[-1] # Type [parameter] # parameter guaranteed to have no space
                types = "".join(line_ignore_comments.split(" ")[:-1]) # [Type] parameter # type could have space e.g. TMap<T1, T2>
                if "<" in types: # Contains another inner type e.g Type<T1, T2, T3>
                    main_type = types[:types.find("<")] # [Type]<T1, T2, T3>
                    sub_types = types[types.find("<")+1:types.find(">")].split(",") # Type<[T1, T2, T3]>
                    if main_type not in self.save_structs:
                        print(f"Unknown outer type: {main_type} of line {line}")
                    elif len(sub_types) != len(self.save_structs[main_type]["generic_types"]):
                        print(f"Mismatched inner type count: {main_type} of line {line} for struct {self.save_structs[main_type]}")
                    self.save_structs[current_struct_name]["parameters"][parameter] = (main_type, sub_types) # {"parameters": (TYPE, [T1, T2, T3])}
                else: # No inner type
                    self.save_structs[current_struct_name]["parameters"][parameter] = types
            elif current_enum_name != "":
                name, value = line.split(" = ")
                value = value.split(",")[0]
                self.save_enums[current_enum_name]["entries"][name] = value
        return self.save_structs

    def loadSaveFile(self, fileName):
        with open(fileName, "rb") as sav_file:
            self.save_binary = sav_file.read()

    def saveSaveFile(self, fileName, data = None):
        if data is None:
            data = self.save_binary
        with open(fileName, "wb") as sav_file:
            sav_file.write(data)

    def loadJsonFile(self, fileName):
        with open(fileName, "rb") as json_file:
            self.save_dict = json.load(json_file)

    def saveJsonFile(self, fileName, data = None):
        if data is None:
            data = self.save_dict
        with open(fileName, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, indent=2, ensure_ascii=False)

    def unpackValFromBin(self, binary, type_name):
        size = 0
        value = None
        return value, size

    def getValFromBinOffset(self, binary_offset, type_name):
        size = 0
        data = None
        if (self.debug_log):
            self.debug_txt += f"type_name {type_name} at binary_offset {binary_offset} = {hex(binary_offset)[2:]}\n"
        if type(type_name) == tuple:
            subtypes = type_name[1]
            type_name = type_name[0]
        if type_name in ["TMap", "Map"]:
            length = struct.unpack("<I", self.save_binary[binary_offset:binary_offset+4])[0]
            binary_offset += 4 # set binary_offset directly since we need it immediately
            data = []
            if length > 80000:
                #raise Exception("abnormal size TMap?")
                if (self.debug_log):
                    self.debug_txt += f"abnormal size Map? size {length} at binary_offset {binary_offset} = {hex(binary_offset)[2:]}\n"
                print(f"abnormal size Map? size {length} at binary_offset {binary_offset} = {hex(binary_offset)[2:]}")
            for i in range(length):
                data_key, binary_offset = self.getValFromBinOffset(binary_offset, subtypes[0])
                data_value, binary_offset = self.getValFromBinOffset(binary_offset, subtypes[1])
                data.append({"key": data_key, "value": data_value})
        elif type_name in ["TArray", "Array"] or type_name in ["TSet", "Set"]:
            length = struct.unpack("<I", self.save_binary[binary_offset:binary_offset+4])[0]
            binary_offset += 4
            data = []
            if length > 80000: # note FCraftStatusInfoP m_CraftStatus has a 65,535 length array
                #raise Exception("abnormal size TArray?")
                if (self.debug_log):
                    self.debug_txt += f"abnormal size Array? size {length} at binary_offset {binary_offset} = {hex(binary_offset)[2:]}\n"
                print(f"abnormal size Array? size {length} at binary_offset {binary_offset} = {hex(binary_offset)[2:]}")
                
            for i in range(length):
                data_val, binary_offset = self.getValFromBinOffset(binary_offset, subtypes[0])
                data.append(data_val)
        ## NUMBERS
        elif type_name == "u8" or type_name == "ENum":
            size = 1
            data = struct.unpack("<B", self.save_binary[binary_offset:binary_offset+size])[0]
        elif type_name == "u16":
            size = 2
            data = struct.unpack("<H", self.save_binary[binary_offset:binary_offset+size])[0]
        elif type_name == "u32":
            size = 4
            data = struct.unpack("<I", self.save_binary[binary_offset:binary_offset+size])[0]   
        elif type_name == "u64":
            size = 8
            data = struct.unpack("<Q", self.save_binary[binary_offset:binary_offset+size])[0]  
        elif type_name == "u128":
            size = 16
            tmp_data = struct.unpack("<QQ", self.save_binary[binary_offset:binary_offset+size])
            data = tmp_data[0] | (tmp_data[1]<<64)
        elif type_name == "s8":
            size = 1
            data = struct.unpack("<b", self.save_binary[binary_offset:binary_offset+size])[0]
        elif type_name == "s16":
            size = 2
            data = struct.unpack("<h", self.save_binary[binary_offset:binary_offset+size])[0]
        elif type_name == "s32":
            size = 4
            data = struct.unpack("<i", self.save_binary[binary_offset:binary_offset+size])[0]
        elif type_name == "s64":
            size = 8
            data = struct.unpack("<q", self.save_binary[binary_offset:binary_offset+size])[0]  
        elif type_name == "u128":
            size = 16
            tmp_data = struct.unpack("<qq", self.save_binary[binary_offset:binary_offset+size])
            data = tmp_data[0] | (tmp_data[1]<<64)
        elif type_name == "float":
            size = 4
            data = struct.unpack("<f", self.save_binary[binary_offset:binary_offset+size])[0]
        elif type_name == "double":
            size = 8
            data = struct.unpack("<d", self.save_binary[binary_offset:binary_offset+size])[0]
        ## VECTORS
        elif type_name in ["FVector4", "Vector4"]:
            size = 8*4
            data = list(struct.unpack("<dddd", self.save_binary[binary_offset:binary_offset+size])) # JSON turns tuple into list anyway, this allows consistency loading dict directly
        elif type_name in ["FVector3", "Vector3"] or type_name in ["FVector", "Vector"] or type_name in ["FRotator", "Rotator"]:
            # TODO: split FVector and FRotator to add property names x, y, z vs pitch, yaw, roll
            size = 8*3
            data = list(struct.unpack("<ddd", self.save_binary[binary_offset:binary_offset+size])) # JSON turns tuple into list anyway, this allows consistency loading dict directly
        elif type_name in ["FVector2D", "Vector2D"]:
            size = 8*2
            data = list(struct.unpack("<dd", self.save_binary[binary_offset:binary_offset+size])) # JSON turns tuple into list anyway, this allows consistency loading dict directly
        ## STRINGS
        elif type_name in ["FString", "Str"] or type_name in ["FName", "Name"]:
            size = 4
            length = struct.unpack("<i", self.save_binary[binary_offset:binary_offset+size])[0]
            if length > 1000 or length < -1000:
                if (self.debug_log):
                    self.debug_txt += f"string length: {length} at binary_offset {binary_offset} = {hex(binary_offset)[2:]}\n"
                else:
                    self.debug_txt += "!!!!!"
                print(f"string length: {length} at binary_offset {binary_offset} = {hex(binary_offset)[2:]}")
                raise Exception("abnormal size FString?")
            if length < 0:
                data = struct.unpack(f"{-2*length}s", self.save_binary[binary_offset+size:binary_offset+size+-2*length])[0]
                data = data.decode("utf-16")[:-1]
                data = {"content":data, "type":"utf-16-le"}
                size += -2*length
                pass # char16 / wchar_t
            elif length == 0:
                data = None
            else:
                data = struct.unpack(f"{length}s", self.save_binary[binary_offset+size:binary_offset+size+length])[0]
                data = data.decode("utf-8")[:-1] # remove the "\0"
                size += length
        elif type_name in self.save_structs:
            data, binary_offset = self.binToDict(binary_offset, type_name)
        elif type_name in self.save_enums:
            
            enum_base_type = self.save_enums[type_name]["type"]
            #print(f"enum {type_name} = {enum_base_type}")
            data, binary_offset = self.getValFromBinOffset(binary_offset, enum_base_type)
        else:
            print(f"unknown type {type_name} at binary_offset {binary_offset} = {hex(binary_offset)[2:]}") 
        binary_offset += size
        if (self.debug_log):
            self.debug_txt += f"found data {data} at binary_offset {binary_offset} = {hex(binary_offset)[2:]}\n"
        return data, binary_offset

    def packValueToBinData(self, value, type_name):
        data = b''
        ## ARRAYS
        if type(type_name) == tuple:
            subtypes = type_name[1]
            type_name = type_name[0]
        if type_name in ["TMap", "Map"]:
            length = len(value)
            data = struct.pack("<I", length)
            for i in range(length):
                key = value[i]["key"]
                val = value[i]["value"]
                data += self.packValueToBinData(key, subtypes[0])
                data += self.packValueToBinData(val, subtypes[1])
        elif type_name in ["TArray", "Array"] or type_name in ["TSet", "Set"]:
            length = len(value)
            data = struct.pack("<I", length)
            for i in range(length):
                data += self.packValueToBinData(value[i], subtypes[0])
        ## NUMBERS
        elif type_name == "u8" or type_name == "ENum":
            data = struct.pack("<B", value)
        elif type_name == "u16":
            data = struct.pack("<H", value)
        elif type_name == "u32":
            data = struct.pack("<I", value)
        elif type_name == "u64":
            data = struct.pack("<Q", value)
        elif type_name == "u128":
            data = struct.pack("<QQ", value&0xFFFFFFFFFFFFFFFF, value>>64) ## no native 128 bit struct?
        elif type_name == "s8":
            data = struct.pack("<b", value)
        elif type_name == "s16":
            data = struct.pack("<h", value)
        elif type_name == "s32":
            data = struct.pack("<i", value)
        elif type_name == "s64":
            data = struct.pack("<q", value)
        elif type_name == "s128":
            data = struct.pack("<qq",value&0xFFFFFFFFFFFFFFFF, value>>64) ## no native 128 bit struct?)
        elif type_name == "float":
            data = struct.pack("<f", value)
        elif type_name == "double":
            data = struct.pack("<d", value)
        ## VECTORS
        elif type_name in ["FVector4", "Vector4"]:
            data = struct.pack("<dddd", *value)
        elif type_name in ["FVector3", "Vector3"] or type_name in ["FVector", "Vector"] or type_name in ["FRotator", "Rotator"]:
            # TODO: split FVector and FRotator to add property names x, y, z vs pitch, yaw, roll
            data = struct.pack("<ddd", *value)
        elif type_name in ["FVector2D", "Vector2D"]:
            data = struct.pack("<dd", *value)
        ## STRINGS
        elif type_name in ["FString", "Str"] or type_name in ["FName", "Name"]:
            if value is None:
                data = struct.pack("<i", 0)
            elif type(value) == dict:
                #utf-16-le
                encoding = value["type"]
                tmp_str = value["content"] + "\0"
                length = -(len(tmp_str))
                tmp_str = tmp_str.encode("utf-16-le")
                data = struct.pack("<i", length)
                data += tmp_str
            else:
                tmp_str = value.encode("utf-8") + b"\0"
                length = len(tmp_str)
                data = struct.pack("<i", length)
                data += tmp_str
        elif type_name in self.save_structs:
            data = self.dictToBin(value, type_name)
        elif type_name in self.save_enums:
            enum_base_type = self.save_enums[type_name]["type"]
            data = self.packValueToBinData(value, enum_base_type)
        else:
            print(f"!!! unknown type {type_name}") 
        return data

    def binToDict(self, binary_offset = 0, struct_name = "SaveFile"):
        temp_dict = {}
        if struct_name not in self.save_structs:
            print(f"struct {struct_name} not in known structs")
        if self.save_structs[struct_name]["super"]:
            temp_dict, binary_offset = self.binToDict(binary_offset, self.save_structs[struct_name]["super"])
##        if struct_name == "GDDTextLogP":
##            print(f"debug print at offset {binary_offset} = {hex(binary_offset)[2:]}")
##            self.debug_log = True
##        elif struct_name == "GenerateStatusP":
##            print(f"debug print end at offset {binary_offset} = {hex(binary_offset)[2:]}")
##            self.debug_log = False
        for param in self.save_structs[struct_name]["parameters"]:
            repeat = 1
            if struct_name == "GDDTextLogP":
                self.debug_txt += f"Trying to find property {param} in struct {struct_name} at offset {binary_offset} = {hex(binary_offset)[2:]}\n"
            #print(f"Trying to find property {param} in struct {struct_name} at offset {binary_offset} = {hex(binary_offset)[2:]}")
            if "[" in param and param.endswith("]"):
                tmp_param_name, tmp_param_inner = param.split("[")
                tmp_param_inner = tmp_param_inner[:-1] # remove the "]"
                if tmp_param_inner.startswith("0x"):
                    repeat = int(tmp_param_inner,16)
                elif tmp_param_inner.isdigit():
                    repeat = int(tmp_param_inner)
                else:
                    pass
            elif "[" in param or "]" in param:
                print(f"??? array in {struct_name} : {param} but doesn't end with ]???")
            param_name = param
            for i in range(repeat):
                temp_dict[param_name], binary_offset = self.getValFromBinOffset(binary_offset, self.save_structs[struct_name]["parameters"][param])
                param_name = param + f"_{i+1}"
        return temp_dict, binary_offset

    def binToDict2(self, binary_offset = 0, struct_name = "SaveFile"):
        print("Converting binary to json")
        self.save_dict, end_offset = self.binToDict(binary_offset, struct_name)
        if end_offset == len(self.save_binary):
            pass # reached EoF
        else:
            print("Not all binary read?")

    def dictToBin(self, input_dict = None, struct_name = "SaveFile"):
        if input_dict is None:
            input_dict = self.save_dict
        temp_data = b''
        if self.save_structs[struct_name]["super"]:
            temp_data = self.dictToBin(input_dict, self.save_structs[struct_name]["super"])
        for param in self.save_structs[struct_name]["parameters"]:
##            print(f"Trying to set property {param} in struct {struct_name}")
            repeat = 1
            if "[" in param and param.endswith("]"):
                tmp_param_name, tmp_param_inner = param.split("[")
                tmp_param_inner = tmp_param_inner[:-1] # remove the "]"
                if tmp_param_inner.startswith("0x"):
                    repeat = int(tmp_param_inner,16)
                elif tmp_param_inner.isdigit():
                    repeat = int(tmp_param_inner)
                else:
                    pass
            elif "[" in param or "]" in param:
                print(f"??? array in {struct_name} : {param} but doesn't end with ]???")
            param_name = param
            for i in range(repeat):
##                print(f"{param_name} = {input_dict[param_name]}")
##                print(f'{self.save_structs[struct_name]["parameters"][param]}')
                temp_data += self.packValueToBinData(input_dict[param_name], self.save_structs[struct_name]["parameters"][param])
                param_name = param + f"_{i+1}"
        return temp_data

    def dictToBin2(self, input_dict = None, struct_name = "SaveFile"):
        print("Converting json to binary")
        if input_dict is None:
            input_dict = self.save_dict
        self.save_binary = self.dictToBin(input_dict, struct_name)

    # TODO: def (get offset of parameter in binary) e.g. magic number -> offset

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices = ("sav2json", "json2sav"))
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--patternfile", "-p", default="fli_sav_pattern.txt")
    args = parser.parse_args()
    print(args)
    saveDataCl = SaveData()
    saveDataCl.parsePatternFile(args.patternfile)
    if args.mode == "sav2json":
        saveDataCl.loadSaveFile(args.input)
        saveDataCl.binToDict2()
        saveDataCl.saveJsonFile(args.output)
    elif args.mode == "json2sav":
        saveDataCl.loadJsonFile(args.input)
        saveDataCl.dictToBin2()
        saveDataCl.saveSaveFile(args.output)

if __name__ == "__main__":
    main()

##    saveDataCl = SaveData()
##    print("Test: parse pattern file")
##    saveDataCl.parsePatternFile()
##    print("Test: load save file")
##    saveDataCl.loadSaveFile("gamedata.sav")
##    print("Test: sav binary to dict")
##    saveDataCl.binToDict2()
##    print("Test: save dict")
##    saveDataCl.saveJsonFile("testing.json")
##    saveDataCl.save_binary = b''
##    saveDataCl.save_dict = {}
##    print("Test: load dict")
##    saveDataCl.loadJsonFile("testing.json")
##    print("Test: dict to binary")
##    saveDataCl.dictToBin2()
##    print("Test: save binary save")
##    saveDataCl.saveSaveFile("testing.sav")
    
