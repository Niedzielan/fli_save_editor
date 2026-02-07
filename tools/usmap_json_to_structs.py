import json

with open("Mapping.json", "r") as usmapFile:
    usmapJson = json.load(usmapFile)

structure = {}

hardcoded_structs = """struct Str { // handle wide_strings
s32 len;
if (len < 0) {
char16 wchar[-len];
} else {
char data[len];
}
};
struct Name {
Str inner;
};
struct Vector4 {
double x;
double y;
double z;
double w;
};
struct Vector3 {
double x;
double y;
double z;
};
struct Vector2D {
double x;
double y;
};
struct Array<T> {
u32 len;
T data[len];
};
struct Set<T> {
u32 len;
T data[len];
};
struct Map_inner<T, T2> {
T key;
T2 value;
};
struct Map<T, T2> {
u32 len;
Map_inner<T, T2> pair[len];
};
struct ENum {
u32 enum_val;
};
struct DateTime {
u64 time;
};
struct Handle {
s32 handle;
};
struct Byte {
u8 byte;
};
struct Bool {
u8 byte; //only 0 or 1?
};
struct IntVector {
s32 x;
s32 y;
s32 z;
};

"""

final_structs =  """
struct GUID {
u128 guid;
};
struct Header {
u32 magic;
u32 save_game_version;
u32 package_version_ue4;
u32 package_version_ue5;
u16 engine_major;
u16 engine_minor;
u16 engine_patch;
u32 engine_build;
Str engine_version;
u32 customVersionFormat;
Map<GUID, u32> hashableIndexMap;
Str saveDataClassName;
};
struct SaveFile {
Header header;
SaveData saveData;
};
"""

translate_names = {"UInt64": "u64",
                   "UInt32": "u32",
                   "UInt16": "u16",
                   "UInt8": "u8",
                   "Int64": "s64",
                   "Int32": "s32",
                   "Int16": "s16",
                   "Int8": "s8",
                   "Float":"float",
                   "Int": "s32",
                   "Double": "double",
                   "Byte": "u8",
                   "Bool": "u32" ## except u8 when in array???????
                   }

def translate_element_type(ele_type):
    #print("translating: " + ele_type)
    if ele_type in translate_names:
        return translate_names[ele_type]
    return ele_type


default_names = ["Str", "Name", "UInt64", "UInt32", "UInt16", "Int8", "Int64", "Int32", "Int16", "Int8", "Byte", "Bool", "DateTime", "Float", "Int", "Handle", "Vector4", "Double", "IntVector", "Vector2D"]

for i in translate_names:
    if i in default_names and translate_names[i] not in default_names:
        default_names.append(translate_names[i])
        
done_names = default_names[:]

for i in translate_names:
    if translate_names[i] not in done_names:
        done_names.append(translate_names[i])

pending_names = []
structs_list = {}
enums_list = {}

def name_and_super(name):
    if usmapJson["structs"][name]["super_struct"] not in [None, "Object"]:
        return name + " : " + usmapJson["structs"][name]["super_struct"]
    return name

DEBUG_PRINT = False

def getInnerFromElement(element):
    global DEBUG_PRINT
    if type(element) == dict:
        if DEBUG_PRINT:
            print(f"case 1: dict: {element}")
        if "Struct" in element:
            inner = element["Struct"]
            if DEBUG_PRINT:
                print(f"inner: {inner}")
            return [translate_element_type(inner["name"])], translate_element_type(inner["name"])
        elif "Array" in element:
            array_inner = element["Array"]["inner"]
            if DEBUG_PRINT:
                print(f"array inner: {array_inner}")
            els, strtmp = getInnerFromElement(array_inner)
            return els, "Array<"+ ", ".join([translate_element_type(el) for el in els]) + ">"
        elif "Map" in element:
            map_key = element["Map"]["key"]
            els_key, _ = getInnerFromElement(map_key)
            map_val = element["Map"]["value"]
            els_val, _ = getInnerFromElement(map_val)
            els = els_key + els_val
            if DEBUG_PRINT:
                print(f"map inners: {map_key}, {map_val}")
            return els, "Map<" + ", ".join([translate_element_type(el) for el in els]) + ">"
        elif "Set" in element: # basically same as Array
            set_inner = element["Set"]["key"]
            if DEBUG_PRINT:
                print(f"set inner: {set_inner}")
            els, strtmp = getInnerFromElement(set_inner)
            return els, "Set<"+ ", ".join([translate_element_type(el) for el in els]) + ">"
        elif "Enum" in element:
            enum_inner = element["Enum"]["inner"]
            enum_name = element["Enum"]["name"]
            if DEBUG_PRINT:
                print(f"enum {enum_name} is type {enum_inner}")
            if enum_name not in enums_list:
                enums_list[enum_name] = {"type": translate_element_type(enum_inner), "entries": usmapJson["enums"][enum_name]["entries"]}                
            return [translate_element_type(enum_name)], translate_element_type(enum_name)
                            
    else:
        if DEBUG_PRINT:
            print(f"case 2: no dict: {element}")
        return [translate_element_type(element)], translate_element_type(element)

def struct_str(name):
    global DEBUG_PRINT
    if DEBUG_PRINT:
        print(f"generating struct for {name}")
    done_names.append(name)
    structs_list[name] = {"txt":"", "requires": []}
    structs_txt = "struct " + name_and_super(name) + " {\n"
    struct = usmapJson["structs"][name]
    for element in struct["properties"]:
        element_name = element["name"]
        if DEBUG_PRINT:
            print(f"element {element_name} of type {element['inner']}")
        element_types, element_str = getInnerFromElement(element["inner"])
        #element_str += " " + element_name + ";\n"
        if DEBUG_PRINT:
            print(f"element str: {element_str}")
        if DEBUG_PRINT:
            print("")
        for element_type in element_types:
            if element_type == "Double":
                print(f"?? double? {element_type} -> {translate_element_type(element_type)}")
            element_type = translate_element_type(element_type)
            if element_type not in done_names and element_type not in pending_names and element_type not in enums_list:
                pending_names.append(element_type)
            if element_type not in default_names and element_type not in enums_list:
                structs_list[name]["requires"].append(element_type)
        if element["array_dim"] > 1:
            element_str = "Array<" + element_str + ">"
        structs_txt += element_str + " " + element_name + ";\n"
    structs_txt += "};\n"
    structure_super = struct["super_struct"] 
    if structure_super != None and structure_super not in done_names and structure_super not in pending_names:
        pending_names.append(structure_super)
    if structure_super != None and structure_super not in default_names:
        structs_list[name]["requires"].append(structure_super)
    structs_list[name]["txt"] = structs_txt
    return structs_txt

structs_txt = struct_str("SaveData")

loop = 9999

while len(pending_names) > 0:
    print("pending: " + str(len(pending_names)))
    next_struct = pending_names.pop(0)
    print(next_struct)
    if next_struct in ["HugeMapStatusP", "PurposePointPinSaveData"]:
        DEBUG_PRINT = True
    else:
        DEBUG_PRINT = False
    #structs_txt += "\n" + struct_str(next_struct)
    structs_txt = struct_str(next_struct) + "\n" + structs_txt
    loop -= 1
    if loop <=0:
        break
#print(structs_txt)

##enums_txt = ""
##for enum in enums_list:
##    enums_txt += "struct " + enum + " {\n" + enums_list[enum] + " value;\n};\n"

enums_txt= ""
for enum in enums_list:
    enums_txt += "enum " + enum + " : " + enums_list[enum]["type"] + " {\n"
    for entry in enums_list[enum]["entries"]:
        enums_txt += enums_list[enum]["entries"][entry] + " = " + entry + ",\n"
    enums_txt += "};\n"

reorderd_struct_list = {}
done_structs = []

done = 0

while done < len(structs_list):
    for struct_name in structs_list:
        if struct_name in done_structs:
            continue
        required = structs_list[struct_name]["requires"]
        this_run = True
        for req in required:
            if req not in done_structs:
                this_run = False
                break
        if this_run:
            done_structs.append(struct_name)
            done += 1
            reorderd_struct_list[struct_name] = structs_list[struct_name]["txt"]
    print("Ordered: " + str(done) + " / " + str(len(structs_list)))

reordered_structs_txt = ""
for order_struct in reorderd_struct_list:
    reordered_structs_txt += "\n" + reorderd_struct_list[order_struct]



full_txt2 = hardcoded_structs + enums_txt + reordered_structs_txt + final_structs

with open("usmap2structs.txt", "w", encoding="utf-8") as us2strFile:
    us2strFile.write(full_txt2)
