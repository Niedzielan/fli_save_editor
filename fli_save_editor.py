import json
from imgui_bundle import imgui, immapp
from imgui_bundle import portable_file_dialogs as pfd 
from imgui_bundle import ImVec2 
import fli_bin2sav
import fli_sav2json
import copy

VERSION = 0.1

INDENT_LEVEL = 8

DISPLAY_ITEM_NAME_IN_HEADER = True

##open_dialog = None
##save_dialog = None
loaded_save = {}


saveDataCl = None

item_list = {"None": "",
             "":""}

skill_list = {"None": "",
             "":""}

bitflag_list = {}
byteflag_list = {}

search_text_item = ""
search_text_skill = ""
search_inventory = ""

config_loaded = False
item_list_loaded = False
skill_list_loaded = False
flag_list_loaded = False
pattern_file_loaded = False

config_file_location = "./fli_save_editor_config.txt"

item_list_location = "./itemlist.txt"
skill_list_location = "./skilllist.txt"
flag_list_location = "./flaglist.txt"
pattern_file_location = "./fli_sav_pattern.txt"

def init_config(skip_config_check=False):
    global config_file_location
    global item_list_location
    global skill_list_location
    global flag_list_location
    global pattern_file_location
    global config_loaded
    global item_list_loaded
    global skill_list_loaded
    global flag_list_loaded
    global pattern_file_loaded

    global structs
    global enums
    global item_list
    global skill_list
    global bitflag_list
    global byteflag_list
    global saveDataCl
    
    item_list_loaded = False
    skill_list_loaded = False
    flag_list_loaded = False
    pattern_file_loaded = False

    if not skip_config_check:
        try:
            with open(config_file_location, "r", encoding="utf-8") as config_file:
                config_lines = config_file.readlines()
            for line in config_lines:
                line = line.strip()
                if line.startswith("#") or line.startswith(";"):
                    continue
                elif "=" in line:
                    config_setting = line.split("=")
                    config_key = config_setting[0].strip()
                    config_value = "=".join(config_setting[1:]).strip()
                    if config_key == "itemlist":
                        item_list_location = config_value
                    elif config_key == "skilllist":
                        skill_list_location = config_value
                    elif config_key == "flaglist":
                        pattern_file_location = config_value
                    elif config_key == "patternfile":
                        pattern_file_location = config_value
            config_loaded = True
        except FileNotFoundError as fnfe:
            print("No item list file found, creating default")
            try:
                with open(config_file_location, "w", encoding="utf-8") as config_file:
                    config_file.write("""## Config file for FANTASY LIFE i Save Editor
itemlist=./itemlist.txt
skilllist=./skilllist.txt
flaglist=./flaglist.txt
patternfile=./fli_sav_pattern.txt""")
                config_loaded = True
            except:
                print("Couldn't create default config file, using default values internally")

    try:
        with open(item_list_location, "r", encoding="utf-8") as item_list_file:
            item_list_data = item_list_file.readlines()
            current_heading = ""
            for line in item_list_data:
                line = line.strip()
                if line.startswith("##"):
                    current_heading = line.split("##")[-1].strip()
                elif line == "":
                    continue # skip  blank
                elif ":" in line:
                    tmp_line = line.split(":")
                    item_id = tmp_line[0].strip()
                    item_name = ":".join(tmp_line[1:]).strip()
                    item_list[item_id] = item_name

                else:
                    print(f"line {line} not empty or header or name?")
        item_list_loaded = True
    except FileNotFoundError as fnfe:
        print("No item list file found")
        
    try:
        with open(skill_list_location, "r", encoding="utf-8") as skill_list_file:
            skill_list_data = skill_list_file.readlines()
            current_heading = ""
            for line in skill_list_data:
                line = line.strip()
                if line.startswith("##"):
                    current_heading = line.split("##")[-1].strip()
                elif line == "":
                    continue # skip  blank
                elif ":" in line:
                    tmp_line = line.split(":")
                    skill_id = tmp_line[0].strip()
                    skill_name = ":".join(tmp_line[1:]).strip()
                    skill_list[skill_id] = skill_name
                else:
                    print(f"line {line} not empty or header or name?")
            skill_list_loaded = True
    except FileNotFoundError as fnfe:
        print("No skill list file found")
        
    try:
        with open(flag_list_location, "r", encoding="utf-8") as flag_list_file:
            flag_list_data = flag_list_file.readlines()
            current_heading = ""
            for line in flag_list_data:
                line = line.strip()
                if line.startswith("##"):
                    current_heading = line.split("##")[-1].strip()
                elif line == "":
                    continue # skip  blank
                elif ":" in line:
                    tmp_line = line.split(":")
                    flag_idx = tmp_line[0].strip()
                    flag_name = ":".join(tmp_line[1:]).strip()
                    if current_heading == "Global Bit Flag":
                        bitflag_list[flag_idx] = flag_name
                    elif current_heading == "Global Byte Flag":
                        byteflag_list[flag_idx] = flag_name
                else:
                    print(f"line {line} not empty or header or name?")
            flag_list_loaded = True
    except FileNotFoundError as fnfe:
        print("No flag list file found")

        

    try:
        saveDataCl = fli_sav2json.SaveData()
        saveDataCl.parsePatternFile(pattern_file_location)
        structs = saveDataCl.save_structs
        enums = saveDataCl.save_enums
        pattern_file_loaded = True
    except FileNotFoundError as fnfe:
        print("No pattern file found")

init_config()

def imgui_text_nonempty(text):
    if text.strip() == "":
        return False
    elif text.split("##")[0].strip() == "":
        return False
    else:
        imgui.text(text)
        return True

def get_enum_by_val(enum_entries, val):
    for enum in enum_entries["entries"]:
        if enum_entries["entries"][enum] == str(val):
            return enum

def handle_inputs(param, param_type, param_val, do_indent = True, display_name = True):
##    imgui.text("imgui name: " + param)
    changed = False
    if do_indent:
        imgui.indent(INDENT_LEVEL)
##    if param_type in ["u8", "s8", "u16", "s16", "s32"]: #u32, s64, u64 not supported (why???)
##        imgui.text(param.split("##")[0])
##        changed, param_val = imgui.input_int("##"+param, param_val, 0)
##    elif param_type in ["u32", "u64", "s64"]:
    if param_type in ["u8", "s8", "u16", "s16", "u32", "s32", "u64", "s64"]:
        clamp_val = {
            "u8":(0,255),
            "s8":(-128,127),
            "u16":(0,65535),
            "s16":(-32768,32767),
            "u32":(0,4294967295),
            "s32":(-2147483648,2147483647),
            "u64":(0,18446744073709551615),
            "s64":(-9223372036854775808,9223372036854775807)}
        if display_name:
            imgui_text_nonempty(param.split("##")[0])
        if flag_list_loaded and "GlobalBitFlag" in param.split("##")[0]: # [idx] GlobalBitFlag
            flag_idx = param[1:8].split("]")[0]
            if flag_idx in bitflag_list:
                imgui.same_line()
                imgui.text(f"[{bitflag_list[flag_idx]}]")
        elif flag_list_loaded and "GlobalByteFlag" in param.split("##")[0]: # [idx] GlobalByteFlag
            flag_idx = param[1:8].split("]")[0]
            if flag_idx in byteflag_list:
                imgui.same_line()
                imgui.text(f"[{byteflag_list[flag_idx]}]")
        #imgui.text(param.split("##")[0])
        str_val = str(param_val)
##        imgui.text(param)
        changed, str_val = imgui.input_text("##"+param, str_val, imgui.InputTextFlags_.chars_decimal)
        if changed:
            param_val = int(str_val) if (str_val != "" and not str_val.endswith("-") and not str_val.endswith(".") and not str_val.lower().endswith("e")) else 0
            if param_val < clamp_val[param_type][0]:
                param_val = clamp_val[param_type][0]
            elif param_val > clamp_val[param_type][1]:
                param_val = clamp_val[param_type][1]
    elif param_type == "float":
        if display_name:
            imgui_text_nonempty(param.split("##")[0])
        #imgui.text(param.split("##")[0])
        changed, param_val = imgui.input_float("##"+param, param_val, 0)
    elif param_type == "double":
        if display_name:
            imgui_text_nonempty(param.split("##")[0])
        #imgui.text(param.split("##")[0])
        changed, param_val = imgui.input_double("##"+param, param_val, 0)
    elif param_type == "Vector4":
        if display_name:
            imgui_text_nonempty(param.split("##")[0])
        #imgui.text(param.split("##")[0])
        for i in range(4):
            if i > 0:
                imgui.same_line()
            changed, param_val[i] = imgui.input_double("##"+param+"_"+str(i), param_val[i])
    elif param_type == "Vector3" or param_type == "Vector" or param_type == "Rotator":
        if display_name:
            imgui_text_nonempty(param.split("##")[0])
        #imgui.text(param.split("##")[0])
##        print(f"Struct: {param} - {param_type} - {param_val}")
        for i in range(3):
            if i > 0:
                imgui.same_line()
            changed, param_val[i] = imgui.input_double("##"+param+"_"+str(i), param_val[i])
    elif param_type == "Vector2D":
        if display_name:
            imgui_text_nonempty(param.split("##")[0])
        #imgui.text(param.split("##")[0])
        for i in range(2):
            if i > 0:
                imgui.same_line()
            changed, param_val[i] = imgui.input_double("##"+param+"_"+str(i), param_val[i])
    elif param_type == "IntVector":
        if display_name:
            imgui_text_nonempty(param.split("##")[0])
        #imgui.text(param.split("##")[0])
        changed, param_val = imgui.input_int3("##"+param, param_val)       
    elif param_type in ["Name", "Str"]:
        if display_name:
            imgui_text_nonempty(param.split("##")[0])
        #imgui.text(param.split("##")[0])
        if type(param_val) == dict and param_val["type"] == "utf-16-le":
            if display_name:
                imgui.same_line()
            imgui.text("Warning: UTF-16 string. May not display properly")
            imgui.push_item_width(min(max(imgui.get_window_width()-250, 150),max(150, 20+imgui.calc_text_size(param_val["content"])[0])))
            changed, param_val["content"] = imgui.input_text("##"+param, param_val["content"])
            imgui.pop_item_width()
        else:
            display_after = ""
            tmp_flags = 0
            if param_val == "":
                param_val = None
            if param.startswith("ItemId") or param.startswith("expiredItemId") or param.startswith("itemName"):
                if param_val in item_list:
                    display_after = item_list[param_val]
    ##                imgui.same_line()
    ##                imgui.text(item_list[param_val])
                    #tmp_flags = imgui.InputTextFlags_.enter_returns_true
            if "grantSkillId" in param:
                if param_val in skill_list:
                    display_after = skill_list[param_val]
    ##                imgui.same_line()
    ##                imgui.text(skill_list[param_val])
                    #tmp_flags = imgui.InputTextFlags_.enter_returns_true
            if param_val == None:
                param_val = ""
            #imgui.push_item_width(max(150, 8*(1+len(param_val))))
            imgui.push_item_width(min(max(imgui.get_window_width()-250, 150),max(150, 20+imgui.calc_text_size(param_val)[0])))
            changed, param_val = imgui.input_text("##"+param, param_val, flags=tmp_flags)
            imgui.pop_item_width()
            if display_after != "":
                imgui.same_line()
                imgui.text(display_after)
                
    elif param_type in structs:
##        imgui.text(f"Struct: {param} - {param_type} - {param_val}")
##        print(param)
        changed, param_val = handle_struct(param, param_type, param_val)
    elif param_type in enums:
        if display_name:
            imgui_text_nonempty(param.split("##")[0])
        #imgui.text(param.split("##")[0])
##        print(enums[param_type])
        enum_type = enums[param_type]["type"]
        enum_entry = get_enum_by_val(enums[param_type], param_val)
        imgui.push_item_width(min(max(imgui.get_window_width()-250, 150),max(150, 20+imgui.calc_text_size(enum_entry)[0])))
##        imgui.push_item_width(max(150, 8*(3+len(enum_entry))))
        enum_entries = enums[param_type]["entries"]
        enum_entries_keys = list(enum_entries.keys())
        enum_entries_index = enum_entries_keys.index(enum_entry)
##        imgui.text(param)
        changed, new_enum_index = imgui.combo("##"+param, enum_entries_index, enum_entries_keys, len(enum_entries_keys))

        param_val = int(enum_entries[enum_entries_keys[new_enum_index]])
        imgui.pop_item_width()

    else:
        imgui.text(param.split("##")[0])
        imgui.text(f"Currently unsupported: {param_type}")
    if do_indent:
        imgui.indent(-INDENT_LEVEL)
    return changed, param_val

def get_super_struct_parameters(struct_name):
    tmp_struct = structs[struct_name]["parameters"]
    if structs[struct_name]["super"]:
        tmp_struct = get_super_struct_parameters(structs[struct_name]["super"]) | tmp_struct
    return tmp_struct


def handle_struct(param_name, struct_name, param_val):
    changed = False
    param_struct = structs[struct_name]
    if not imgui.tree_node_ex(param_name + " : " + struct_name, imgui.TreeNodeFlags_.allow_overlap):  ## TEST 
####    if not imgui.collapsing_header(param_name + " : " + struct_name):  ## NO TEST 
        return changed, param_val
    struct_parameters = param_struct["parameters"]
    if param_struct["super"]:
        struct_parameters = get_super_struct_parameters(param_struct["super"]) | struct_parameters
##    print(f">{param_name}")
    for param_inner in struct_parameters:
##        print(f">>{param_inner}")
        if "MAGIC_HEADER" in param_inner or "MAGIC_NUMBER" in param_inner:
            continue # skip header
        param_inner_type = struct_parameters[param_inner]
##        print(f">>{param_inner_type}")
        if type(param_inner_type) == tuple:
##            print(f">>>tuple")
            imgui.indent(INDENT_LEVEL)
            if param_inner_type[0] in ["Array", "Set"]:
                element_type = param_inner_type[1][0]
                if not imgui.tree_node_ex(param_inner + " : " + element_type + f" ({len(param_val[param_inner])})" + ("##" + param_name if not param_name.startswith("##") else param_name), imgui.TreeNodeFlags_.allow_overlap): ## TEST 
####                if not imgui.collapsing_header(param_inner + " : " + element_type + f" ({len(param_val[param_inner])})" + "##" + param_name):  ## NO TEST 
                    imgui.unindent(INDENT_LEVEL)
                    continue
##                clipper = imgui.ListClipper()
##                clipper.begin(len(param_val[param_inner]))
##                while clipper.step():  
##                    # Only render visible items  
##                    for element_idx in range(clipper.display_start, clipper.display_end):  
##                        changed, param_val[param_inner][element_idx] = handle_inputs(f"element {element_idx} {param_inner} : {element_type}"+"##"+param_name + "_" + param_inner+"_"+str(element_idx), element_type, param_val[param_inner][element_idx])
##                clipper.end()
                for element_idx in range(len(param_val[param_inner])):
                    name_extra = ""
                    if DISPLAY_ITEM_NAME_IN_HEADER and element_type.startswith("InventoryInfo"):
                        try:
                            inner_item_name = param_val[param_inner][element_idx]["ItemId"]
                            if inner_item_name != "None":
                                name_extra = f"[{inner_item_name}]"
                                if item_list and inner_item_name in item_list:
                                    name_extra += f" = [{item_list[inner_item_name]}]"
                        except KeyError:
                            pass
                    if name_extra != "":
                        tmp_pos = imgui.get_cursor_screen_pos()
                        tmp_name =f"[{element_idx}] {param_inner} : {element_type}"
                    
                    changed, param_val[param_inner][element_idx] = handle_inputs(f"[{element_idx}] {param_inner} : {element_type}"+("##" + param_name if not param_name.startswith("##") else param_name) + "_" + param_inner+"_"+str(element_idx), element_type, param_val[param_inner][element_idx])
                    if name_extra != "":
                        tmp_pos2 = imgui.get_cursor_screen_pos()
                        imgui.set_cursor_screen_pos(ImVec2(tmp_pos.x+40+imgui.calc_text_size(tmp_name).x, tmp_pos.y))
                        imgui.text(name_extra)
                        imgui.set_cursor_screen_pos(tmp_pos2)
                imgui.tree_pop() ## TEST 
            elif param_inner_type[0] == "Map":
                element_types = param_inner_type[1]
                if not imgui.tree_node_ex(param_inner + " : " + ", ".join(element_types) + f" ({len(param_val[param_inner])})" + ("##" + param_name if not param_name.startswith("##") else param_name), imgui.TreeNodeFlags_.allow_overlap):  ## NO TEST 
##                if not imgui.collapsing_header(param_inner + " : " + ", ".join(element_types) + f" ({len(param_val[param_inner])})" + "##" + param_name):  ## NO TEST 
                    imgui.unindent(INDENT_LEVEL)
                    continue
                if imgui.begin_table(param_name + "_" + param_inner, len(element_types), imgui.TableFlags_.sizing_stretch_same | imgui.TableFlags_.row_bg | imgui.TableFlags_.borders | imgui.TableFlags_.resizable):
##                    clipper = imgui.ListClipper()
##                    item_height = imgui.get_text_line_height_with_spacing() 
##                    clipper.begin(len(param_val[param_inner]), 2*item_height)
##                    while clipper.step():
##                        for row in range(clipper.display_start, clipper.display_end):
##                            imgui.table_next_row()
##                            imgui.table_set_column_index(0)
##                            changed, param_val[param_inner][row]["key"] = handle_inputs(f"key : {element_types[0]}##"+param_name + "_" + param_inner+"_key"+str(row), element_types[0], param_val[param_inner][row]["key"])
##                            imgui.table_set_column_index(1)
##                            changed, param_val[param_inner][row]["value"] = handle_inputs(f"value : {element_types[1]}##"+param_name + "_" + param_inner+"_val"+str(row), element_types[1], param_val[param_inner][row]["value"])
                    
                    for row in range(len(param_val[param_inner])):
                        imgui.table_next_row()
                        imgui.table_set_column_index(0)
                        changed, param_val[param_inner][row]["key"] = handle_inputs(f"key : {element_types[0]}"+("##" + param_name if not param_name.startswith("##") else param_name) + "_" + param_inner+"_key"+str(row), element_types[0], param_val[param_inner][row]["key"])
                        imgui.table_set_column_index(1)
                        changed, param_val[param_inner][row]["value"] = handle_inputs(f"value : {element_types[1]}"+("##" + param_name if not param_name.startswith("##") else param_name) + "_" + param_inner+"_val"+str(row), element_types[1], param_val[param_inner][row]["value"])
##                    clipper.end()
                imgui.end_table()
                imgui.tree_pop()  ## TEST 
            else:
                imgui.text(param_inner + f" : TODO TUPLE")
            imgui.unindent(INDENT_LEVEL)
        else:
##            print(f">>>normal")
            repeat = 1
            if "[" in param_inner and param_inner.endswith("]"):
                tmp_param_name, tmp_param_inner = param_inner.split("[")
                tmp_param_inner = tmp_param_inner[:-1] # remove the "]"
                if tmp_param_inner.startswith("0x"):
                    repeat = int(tmp_param_inner,16)
                elif tmp_param_inner.isdigit():
                    repeat = int(tmp_param_inner)
                else:
                    pass
            param_inner_name = param_inner
            for i in range(repeat):
##                print(f">>>>{param_inner_name +' : ' + param_inner_type + '##' + param_name}")
                changed, param_val[param_inner_name] = handle_inputs( param_inner_name +" : " + param_inner_type + ("##" + param_name if not param_name.startswith("##") else param_name), param_inner_type, param_val[param_inner_name])
                param_inner_name = param_inner + f"_{i+1}"
    imgui.tree_pop()  ## TEST 
    return changed, param_val

def try_get_new_handle(handle_list):
    ## Handle seems to be: 0xAAAABCCC
    ## Where AAAA is 4 * (index+1), B is handle_type, CCC is index
    print("try get new handle")
    for handle_idx in range(len(handle_list)-1, -1, -1):
        handle = handle_list[handle_idx]
        new_handle = handle + (4<<16) + 1
        if new_handle not in handle_list:
            return new_handle
    return False


def gui():
    global loaded_save
    global structs
    global enums
##    global open_dialog
##    global save_dialog
    global saveDataCl
    if imgui.button("Load save"):
        open_dialog = pfd.open_file("Select file", filters=["All save formats", "*.bin *.sav *.json", "Encrypted save bin", "*.bin", "Decrypted save sav", "*.sav", "Parsed save json", "*.json"])  
        
        
        
    
##    if open_dialog and open_dialog.ready():  
        selected_files = open_dialog.result()
        if len(selected_files) == 1:
            selected_file = selected_files[0]
            print(f"Selected: {selected_file}")
            imgui.same_line()
            imgui.text(f"Opening: {selected_file}")
            if selected_file.endswith(".json"):
                with open(selected_file, "r", encoding="utf-8") as save_file:
                    loaded_save = json.load(save_file)
            elif selected_file.endswith(".sav"):
                saveDataCl.loadSaveFile(selected_file)
                saveDataCl.binToDict2()
                loaded_save = saveDataCl.save_dict
            elif selected_file.endswith(".bin"):
                with open(selected_file, "rb") as encrypted_save:
                    encrypted_data = encrypted_save.read()
                saveDataCl.save_binary = fli_bin2sav.decrypt(encrypted_data, b'gQPZXDDr8DsT7VU9mTZwJLYa8PnruSEU')
                saveDataCl.binToDict2()
                loaded_save = saveDataCl.save_dict
            imgui.text(f"Opened: {selected_file}")
        open_dialog = None
    if loaded_save:
        imgui.same_line()
        if imgui.button("Save save"):
            save_dialog = pfd.save_file("Save file", filters=["All save formats", "*.bin *.sav *.json", "Encrypted save bin", "*.bin", "Decrypted save sav", "*.sav", "Parsed save json", "*.json"])  
##        if save_dialog and save_dialog.ready():  
            filename = save_dialog.result()
            print(f"Saving: {filename}")
            save_dialog = None
            if filename != "":
                if filename.endswith(".json"):
                    with open(filename, "w", encoding="utf-8")as newsave_file:
                        json.dump(loaded_save, newsave_file, indent=2, ensure_ascii=False)
                elif filename.endswith(".sav"):
                    saveDataCl.save_dict = loaded_save
                    saveDataCl.dictToBin2()
                    saveDataCl.saveSaveFile(filename)
                elif filename.endswith(".bin"):
                    saveDataCl.save_dict = loaded_save
                    saveDataCl.dictToBin2()
                    encrypted_data = fli_bin2sav.encrypt(saveDataCl.save_binary, b'gQPZXDDr8DsT7VU9mTZwJLYa8PnruSEU')
                    with open(filename, "wb") as newsave_encrypted_file:
                        newsave_encrypted_file.write(encrypted_data)
                print(f"Saved: {filename}")
        
##    if not loaded_save:
##        return
    if imgui.begin_tab_bar("Options"):
        if imgui.begin_tab_item("Info")[0]:
            # currently loaded save:
            all_loaded = pattern_file_loaded and item_list_loaded and skill_list_loaded and flag_list_loaded
            if all_loaded:
                tmp_col = imgui.ImVec4(0,255,0,255)
                tmp_txt = "Config loaded"
            else:
                tmp_col = imgui.ImVec4(255,0,0,255)
                tmp_txt = "!! Config not loaded. Please check settings tab !!"
            imgui.text_colored(tmp_col, tmp_txt)

            # instructions
            imgui.push_text_wrap_pos(imgui.get_content_region_avail()[0])
            imgui.text(\
"""NOTE: This is an alpha release. Please contact me if there are errors
\t- Not counting errors when there's a game update before the pattern file gets updated. Those will just waste both our time.
Also feel free to suggest

FANTASY LIFE i Save Editor:
\tPattern file is used to convert a .sav to .json, as well as for displaying save data in this GUI
\t\t(The pattern file is actually an ImHex pattern file, if you want to read saves in a hex editor)
\tThe Item, Skill, and Flag lists are used to display nice names for specific entries
\t\t(e.g. "True Staff of Time" is displayed alongside the internal id "iwp04000200")

Supported file types: .bin, .sav, .json
\tIf you load a .bin, it will convert it to .sav then to .json, loading a .sav, will convert it to .json
\tSimilarly, saving a .sav converts internal json to .sav, saving a .bin converts internal json to .sav then to .bin

Save file location: (usually)
Steam/userdata/<your steam ID>/2993780/remote/002DAE74-00-gamedata.bin

\tIn theory, Switch saves should also work

Tabs:
\tSettings
\t\t- Set the location of Pattern file, Item, Skill, Flag lists.
\t\t\t(Helpful if you want to switch between different versions)

\tSave Data (Useful)
\t\t- Contains some hand-picked pieces of data
\t\t- Includes a table for inventory
\t\t\t- Experimental "Delete" and "Duplicate" options. Please change ItemID after Duplicating.
\t\t\t- I have tried to automatically create a new Handle, but this has not been tested much
\t\t\t\t(Handle appears to be hex AAAABCCC where AAAA is 4x(index+1), B is category, and CCC is index (index starts at 0))

\tSave Data (Full)
\t\t- Contains all save data
\t\t- Currently can't add/remove entries, only edit. If you want to add/remove, please edit the json manually

\tItem/Skill name lookup
\t\t- Searchable lists of Item / Skill names
\t\t\t(Flags aren't searchable but are shown in Save Data (Full) -> m_FlagStatus -> GlobalBitFlat/GlobalByteFlag)

Created By: Niedzielan
Credits To: trumank, DRayX

Sources should be included when redistributing.
If using the .py versions, note that the zlib library was updated in 3.10.6
This means that re-compressing data will NOT be bit-wise identical to the original save if using 3.10.6+
The game should still be able to load the data fine, this is merely notable for aesthetics and debugging
The .exe versions were packaged using python 3.10.5, using pyinstaller
.py requirements:
\timgui-bundle
\tpycryptodome

Changelog:
\t0.1 - Alpha release""")
            imgui.pop_text_wrap_pos()

            imgui.end_tab_item()
        ## SAVE DATA USEFUL
        if loaded_save and imgui.begin_tab_item("Save Data (Useful)")[0]:
            if imgui.collapsing_header("Play Data"):
                pdata = loaded_save["saveData"]["m_PlayData"]
                pstruct = structs["PLAY_DATA_P"]
                nice_name_map = {"Money": "Dosh",
                                 "goddessHerbBlue": "Celestia Gift",
                                 "goddessHerbGold": "Golden Celestia Gift",
                                 "sweetChestnut": "Cashnut"
                                 }
                for i in nice_name_map:
                    istruct = get_super_struct_parameters("PLAY_DATA_P")[i]
##                    istruct = structs["PLAY_DATA_P"]["parameters"][i]
                    changed, pdata[i] = handle_inputs(f"{nice_name_map[i]} : {istruct}##_pd", istruct, pdata[i])
            imgui.end_tab_item()
            if imgui.collapsing_header("Flags"):
                fdata = loaded_save["saveData"]["m_FlagStatus"]
                fstruct = structs["FlagStatus_P"]

                fdata_globalbyteflag = fdata["GlobalByteFlag"]
                fstruct_globalbyteflag = fstruct["parameters"]["GlobalByteFlag"][1][0]
                nice_flag_map = {1602: "Buildable Infrastructure",
                                 1603: "Buildable Vegetable Field"}
                for i in nice_flag_map:
                    changed, fdata_globalbyteflag[i] = handle_inputs(f"{nice_flag_map[i]} : {fstruct_globalbyteflag}##_pd", fstruct_globalbyteflag, fdata_globalbyteflag[i])
            if imgui.collapsing_header("Inventory"):
                idata = loaded_save["saveData"]["m_InventoryStatus"]
                istruct = structs["InventoryStatusDataP"]
                nice_item_map = {"invConsume": "Consumables",
                                 "invWeapon": "Weapons",
                                 "invLifeTools": "Tools",
                                 "invShield": "Shields",
                                 "invArmor": "Armor",
                                 "invMaterial": "Materials",
                                 "invImportant": "Valuables",
                                 "invMount": "Mounts"}
                if imgui.begin_tab_bar("inventorytabs"):
                    for i in nice_item_map:
                        if imgui.begin_tab_item(nice_item_map[i]+"##"+i)[0]:
                            idata_i = idata[i]
                            istruct_i = get_super_struct_parameters("InventoryStatusDataP")[i][1][0]
                            istruct_item = get_super_struct_parameters(istruct_i)
                            imgui.text("Search: ")
                            imgui.same_line()
                            global search_inventory
                            imgui.push_item_width(min(max(imgui.get_window_width()-250, 250),max(250, 20+imgui.calc_text_size(search_inventory)[0])))
                            changed, search_inventory = imgui.input_text("##searchInventoryNames", search_inventory)
                            imgui.pop_item_width()
                            if imgui.begin_table("table"+i, len(istruct_item), flags=imgui.TableFlags_.sizing_stretch_prop|imgui.TableFlags_.resizable|imgui.TableFlags_.scroll_y|imgui.TableFlags_.borders|imgui.TableFlags_.row_bg):
                                imgui.table_setup_scroll_freeze(0, 1)
                                for param in istruct_item:
                                    if param == "MAGIC_NUMBER":
                                        continue
                                    imgui.table_setup_column(f"{param}\n{istruct_item[param]}", flags=imgui.TableColumnFlags_.width_stretch)
                                imgui.table_setup_column("inventoryOptions", flags=imgui.TableColumnFlags_.width_stretch)
                                imgui.table_headers_row()
                                to_delete = -1
                                to_copy = -1
                                tmp_handle_list = []
                                last_empty_idx = -1
                                for item_idx in range(len(idata_i)):
                                    item = idata_i[item_idx]
                                    if item["ItemId"] in ["", "None", None]:
                                        if last_empty_idx < 0:
                                            last_empty_idx = item_idx
                                        continue
                                    else:
                                        last_empty_idx = -1
                                        if search_inventory and search_inventory != "":
                                            if search_inventory.lower() not in item["ItemId"].lower() and (item_list and item["ItemId"] in item_list and search_inventory.lower() not in item_list[item["ItemId"]].lower()):
                                                continue
                                    imgui.table_next_row()
                                    #imgui.text(item["ItemId"])
                                    for param in istruct_item:
                                        if param == "MAGIC_NUMBER":
                                            continue
                                        imgui.table_next_column()
                                        if param == "Handle":
                                            changed, item[param]["handle"] = handle_inputs(f"##{param} : {istruct_item[param]} : {item_idx}", get_super_struct_parameters(istruct_item[param])["handle"], item[param]["handle"], do_indent=False, display_name=False)
                                            tmp_handle_list.append(item[param]["handle"])
                                        elif type(istruct_item[param]) == tuple:
                                            if istruct_item[param][0] in ["Array", "Set"]:
                                                for element_idx in range(len(item[param])):
                                                    extra = "" if (istruct_item[param][1][0] not in structs or istruct_item[param][1][0] in ["Name", "Str"]) else f"{istruct_item[param][1][0]}"
                                                    changed, item[param][element_idx] = handle_inputs(f"{extra}##{param} : {istruct_item[param][1][0]} : {item_idx} : {element_idx}", istruct_item[param][1][0], item[param][element_idx], do_indent=False, display_name=False)
                                            elif istruct_item[param][0] in ["Map"]:
                                                imgui.text("TODO: MAP")
                                        else:
                                            changed, item[param] = handle_inputs(f"{param}## : {istruct_item[param]} : {item_idx}", istruct_item[param], item[param], do_indent=False, display_name=False)
                                    imgui.table_next_column()
                                    if imgui.button(f"Delete##{item_idx}"):
                                        to_delete = item_idx
                                        print("delete")
                                    imgui.same_line()
                                    if imgui.button(f"Duplicate##{item_idx}"):
                                        to_copy = item_idx
                                        print("duplicate")
                                if to_copy >= 0:
                                    new_item = copy.deepcopy(idata_i[to_copy])
                                    new_handle = try_get_new_handle(tmp_handle_list)
                                    if new_handle:
                                        new_item["Handle"]["handle"] = new_handle
                                    idata["getOrderCount"] += 1
                                    new_item["getOrder"] = idata["getOrderCount"]
                                    #idata_i.insert(to_copy, new_item)
                                    #idata_i.append(new_item) # HANDLE HAS TO BE IN ORDER! Can't insert in position
                                    idata_i[last_empty_idx] = new_item # Can't extend list, have to put in empty slot - for safety make it the first empty slot after all other items
                                    ## got to find empty
                                if to_delete >= 0:
                                    idata_i.pop(to_delete)
                                tmp_handle_list.clear()
                                del tmp_handle_list
                                imgui.end_table()
                            imgui.end_tab_item()
                    imgui.end_tab_bar()
            if imgui.collapsing_header("Character"):
                # table of life : rank star skillpts lv exp
                cdata = loaded_save["saveData"]["m_CharaStatus"]["m_stAvatarP"][0]
                #cstruct = structs["AvatarCharaStatusP"]
                cstruct = get_super_struct_parameters("AvatarCharaStatusP")

                cdata_lstatus = cdata["m_lifeStatus"]
                cstruct_lstatus = get_super_struct_parameters("LifeStatus")
                cdata_llv = cdata["m_lv"]
                cstruct_llv = cstruct["m_lv"][1][1]
                cdata_lexp = cdata["m_exp"]
                cstruct_lexp = cstruct["m_exp"][1][1]
                nice_life_map = {
                    "life0000":"Brand New",
                    "life0001":"Paladin",
                    "life0002":"Mercenary",
                    "life0003":"Hunter",
                    "life0004":"Magician",
                    "life0005":"Miner",
                    "life0006":"Woodcutter",
                    "life0007":"Angler",
                    "life0008":"Farmer",
                    "life0009":"Cook",
                    "life0010":"Blacksmith",
                    "life0011":"Carpenter",
                    "life0012":"Tailor",
                    "life0013":"Alchemist",
                    "life0014":"Artist",
                    }
                if imgui.begin_table("tableCharaLife", 6, flags=imgui.TableFlags_.sizing_stretch_prop|imgui.TableFlags_.resizable|imgui.TableFlags_.scroll_y|imgui.TableFlags_.borders|imgui.TableFlags_.row_bg):
                    imgui.table_setup_scroll_freeze(0, 1)
                    for i in ["Life\nName", "Rank\nELicenseType", "Stars\nu32", "Max Skill Points\ns32", "Level\nu16", "EXP\nu32"]:
                        imgui.table_setup_column(i, flags=imgui.TableColumnFlags_.width_stretch)
                    imgui.table_headers_row()
                    for lstatus_idx in range(len(cdata_lstatus)):
                        lstatus = cdata_lstatus[lstatus_idx]
                        llv = cdata_llv[lstatus_idx]
                        lexp = cdata_lexp[lstatus_idx]
                        imgui.table_next_row()
                        imgui.table_next_column()
                        imgui.text(f"{lstatus['key']} | {nice_life_map[lstatus['key']]}")
                        imgui.table_next_column()
                        changed, lstatus["value"]["licenseRank"] = handle_inputs(f"##licenseRank{lstatus_idx}", cstruct_lstatus["licenseRank"], lstatus["value"]["licenseRank"])
                        imgui.table_next_column()
                        changed, lstatus["value"]["star"] = handle_inputs(f"##star{lstatus_idx}", cstruct_lstatus["star"], lstatus["value"]["star"])
                        imgui.table_next_column()
                        changed, lstatus["value"]["skillMaxPoint"] = handle_inputs(f"##skillMaxPoint{lstatus_idx}", cstruct_lstatus["skillMaxPoint"], lstatus["value"]["skillMaxPoint"])
                        imgui.table_next_column()
                        changed, llv["value"] = handle_inputs(f"##lv{lstatus_idx}", cstruct_llv, llv["value"])
                        imgui.table_next_column()
                        changed, lexp["value"] = handle_inputs(f"##exp{lstatus_idx}", cstruct_lexp, lexp["value"])
                    imgui.end_table()
                
            if imgui.collapsing_header("Guild / Bulletin Board Level"):
                gudata = loaded_save["saveData"]["m_GuildStatus"]
                gustruct = get_super_struct_parameters("GDDGuildStatusP")
                nice_guild_map = {0:"Base Camp",
                                  1:"Mysteria Island",
                                  2:"Faraway Island",
                                  3:"Tropica Isles",
                                  4:"Swolean Island"}
                if imgui.begin_table("tableGuild", 3, flags=imgui.TableFlags_.sizing_stretch_prop|imgui.TableFlags_.resizable|imgui.TableFlags_.scroll_y|imgui.TableFlags_.borders|imgui.TableFlags_.row_bg):
                    imgui.table_setup_scroll_freeze(0, 1)
                    for i in ["Area", "Level\n" + gustruct["LvList"][1][0], "Exp\n"+gustruct["ExpList"][1][0]]:
                        imgui.table_setup_column(i, flags=imgui.TableColumnFlags_.width_stretch)
                    imgui.table_headers_row()
                    for guild_idx in range(len(gudata["LvList"])):
##                        guild_lvl = gudata["LvList"][guild_idx]
##                        guild_exp = gudata["ExpList"][guild_idx]
                        imgui.table_next_row()
                        imgui.table_next_column()
                        imgui.text(f"{guild_idx} {('' if guild_idx not in nice_guild_map else ' | ' + nice_guild_map[guild_idx])}")
                        imgui.table_next_column()
                        changed, gudata["LvList"][guild_idx] = handle_inputs(f"##guildLv{guild_idx}", gustruct["LvList"][1][0], gudata["LvList"][guild_idx])
                        imgui.table_next_column()
                        changed, gudata["ExpList"][guild_idx] = handle_inputs(f"##guildExp{guild_idx}", gustruct["ExpList"][1][0], gudata["ExpList"][guild_idx])
                    imgui.end_table()
            if imgui.collapsing_header("Ginormosia"):
                imgui.text("Ginormosia") # HugeMapStatusP, HugeMapAreaStatusP
                # table of map : nowAreaRank; releaseAreaRank; AreaPoint;
                gdata = loaded_save["saveData"]["m_HugeMapStatusP"]["areaStatus"]
                gstruct = get_super_struct_parameters("HugeMapAreaStatusP")
                nice_area_map = {
                    "map200000_area001":"West Dryridge Desert",
                    "map200000_area002":"East Dryridge Desert",
                    "map200000_area003":"Viridia Plateau",
                    "map200000_area004":"East Greatgut Plains",
                    "map200000_area005":"West Greatgut Plains",
                    "map200000_area006":"South Greatgut Plains",
                    "map200000_area007":"Pettlewing Woods",
                    "map200000_area008":"Shroomhaven",
                    "map200000_area009":"Wingtip Valley",
                    "map200000_area010":"Moltana Wastes",
                    "map200000_area011":"Scorchrock Mountain",
                    "map200000_area012":"Crickneck Canyon",
                    "map200000_area013":"Drakeseye Valley",
                    "map200000_area014":"Drakesnout Range",
                    "map200000_area015":"Fangshore Isles",
                    }
                if imgui.begin_table("tableGinormosia", 4, flags=imgui.TableFlags_.sizing_stretch_prop|imgui.TableFlags_.resizable|imgui.TableFlags_.scroll_y|imgui.TableFlags_.borders|imgui.TableFlags_.row_bg):
                    imgui.table_setup_scroll_freeze(0, 1)
                    for i in ["Area\nName", "Current Area Rank\n"+gstruct["nowAreaRank"], "Unlocked Area Rank\n"+gstruct["releaseAreaRank"], "Area Points\n"+ gstruct["AreaPoint"]]:
                        imgui.table_setup_column(i, flags=imgui.TableColumnFlags_.width_stretch)
                    imgui.table_headers_row()
                    for area_idx in range(len(gdata)):
                        area = gdata[area_idx]
                        imgui.table_next_row()
                        imgui.table_next_column()
                        imgui.text(f"{area['key']} | {nice_area_map[area['key']]}")
                        imgui.table_next_column()
                        changed, area["value"]["nowAreaRank"] = handle_inputs(f"##nowAreaRank{area_idx}", gstruct["nowAreaRank"], area["value"]["nowAreaRank"])
                        imgui.table_next_column()
                        changed, area["value"]["releaseAreaRank"] = handle_inputs(f"##releaseAreaRank{area_idx}", gstruct["releaseAreaRank"], area["value"]["releaseAreaRank"])
                        imgui.table_next_column()
                        changed, area["value"]["AreaPoint"] = handle_inputs(f"##AreaPoint{area_idx}", gstruct["AreaPoint"], area["value"]["AreaPoint"])
                    imgui.end_table()
                
        ## SAVE DATA FULL
        if loaded_save and imgui.begin_tab_item("Save Data (Full)")[0]:
            imgui.begin_child("saveDataChild")
            imgui.push_item_width(150)
            handle_struct("saveData", "SaveData", loaded_save["saveData"])
            #handle_struct("saveFile", "SaveFile", loaded_save) # no need to display header
            imgui.pop_item_width()
            imgui.end_child()
            imgui.end_tab_item()
        if loaded_save and imgui.begin_tab_item("Item name lookup")[0]:
            imgui.text("Search: ")
            imgui.same_line()
            global search_text_item
            imgui.push_item_width(min(max(imgui.get_window_width()-250, 250),max(250, 20+imgui.calc_text_size(search_text_item)[0])))
            changed, search_text_item = imgui.input_text("##searchItemNames", search_text_item)
            imgui.pop_item_width()
            imgui.begin_child("itemLookupChild")
            imgui.push_item_width(250)
            if imgui.begin_table("itemListTable", 2, imgui.TableFlags_.sizing_fixed_fit | imgui.TableFlags_.row_bg | imgui.TableFlags_.borders | imgui.TableFlags_.resizable):
                for item in item_list:
                    if item in ["", "None"]:
                        continue
                    if search_text_item and search_text_item != "":
                        if search_text_item.lower() not in item.lower() and search_text_item.lower() not in item_list[item].lower():
                            continue
                    imgui.table_next_row()
                    imgui.table_set_column_index(0)
                    imgui.text(item)
                    imgui.table_set_column_index(1)
                    imgui.text(item_list[item])
                imgui.end_table()
            imgui.pop_item_width()
            imgui.end_child()
            imgui.end_tab_item()
        if loaded_save and imgui.begin_tab_item("Skill name lookup")[0]:
            imgui.text("Search: ")
            imgui.same_line()
            global search_text_skill
            imgui.push_item_width(min(max(imgui.get_window_width()-250, 250),max(250, 20+imgui.calc_text_size(search_text_skill)[0])))
            changed, search_text_skill = imgui.input_text("##searchSkillNames", search_text_skill)
            imgui.pop_item_width()
            imgui.begin_child("skillLookupChild")
            imgui.push_item_width(250)
            if imgui.begin_table("skillListTable", 2, imgui.TableFlags_.sizing_fixed_fit | imgui.TableFlags_.row_bg | imgui.TableFlags_.borders | imgui.TableFlags_.resizable):
                for skill in skill_list:
                    if skill in ["", "None"]:
                        continue
                    if search_text_skill and search_text_skill != "":
                        if search_text_skill.lower() not in skill.lower() and search_text_skill.lower() not in skill_list[skill].lower():
                            continue
                    imgui.table_next_row()
                    imgui.table_set_column_index(0)
                    imgui.text(skill)
                    imgui.table_set_column_index(1)
                    imgui.text(skill_list[skill])
                imgui.end_table()
            imgui.pop_item_width()
            imgui.end_child()
            imgui.end_tab_item()
        if imgui.begin_tab_item("Settings")[0]:
            global config_file_location
            global item_list_location
            global skill_list_location
            global flag_list_location
            global pattern_file_location
            # button to save and refresh config
            # Pattern file location
            # item list file location
            # skill list file location
            # flag list location
            if imgui.button("Save and reload config"):
                try:
                    with open(config_file_location, "w", encoding="utf-8") as config_file:
                        config_file.write(f"""## Config file for FANTASY LIFE i Save Editor
itemlist={item_list_location}
skilllist={skill_list_location}
flaglist={flag_list_location}
patternfile={pattern_file_location}""")
                except FileNotFoundError as  fnfe:
                    print(f"Couldn't find {config_file_location}")
                except IOError as ioe:
                    print(f"Couldn't open {config_file_location} for writing")
                init_config(skip_config_check=True)
            imgui.same_line()
            if imgui.button("Reset to default"):
                item_list_location = "./itemlist.txt"
                skill_list_location = "./skilllist.txt"
                flag_list_location = "./flaglist.txt"
                pattern_file_location = "./fli_sav_pattern.txt"
                init_config(skip_config_check=True)
            imgui.text("Pattern File:")
            imgui.same_line(100)
            imgui.push_item_width(min(max(imgui.get_window_width()-250, 250),max(250, 20+imgui.calc_text_size(pattern_file_location)[0])))
            changed, pattern_file_location = imgui.input_text("##pattern_file_location", pattern_file_location)
            imgui.pop_item_width()
            imgui.same_line()
            if imgui.button("Browse##pattern_file_location"):
                open_dialog = pfd.open_file("Select Pattern File")  
                selected_files = open_dialog.result()
                if len(selected_files) == 1:
                    selected_file = selected_files[0]
                    print(f"Selected: {selected_file}")
                    pattern_file_location = selected_file
            if pattern_file_loaded:
                tmp_col = imgui.ImVec4(0,255,0,255)
                tmp_txt = "Loaded"
            else:
                tmp_col = imgui.ImVec4(255,0,0,255)
                tmp_txt = "Not Loaded"
            imgui.same_line()
            imgui.text_colored(tmp_col, f"{tmp_txt}")
            imgui.text("Item List File:")
            imgui.same_line(100)
            imgui.push_item_width(min(max(imgui.get_window_width()-250, 250),max(250, 20+imgui.calc_text_size(item_list_location)[0])))
            changed, item_list_location = imgui.input_text("##item_list_location", item_list_location)
            imgui.pop_item_width()
            imgui.same_line()
            if imgui.button("Browse##item_list_location"):
                open_dialog = pfd.open_file("Select Item List File")  
                selected_files = open_dialog.result()
                if len(selected_files) == 1:
                    selected_file = selected_files[0]
                    print(f"Selected: {selected_file}")
                    item_list_location = selected_file
            if item_list_loaded:
                tmp_col = imgui.ImVec4(0,255,0,255)
                tmp_txt = "Loaded"
            else:
                tmp_col = imgui.ImVec4(255,0,0,255)
                tmp_txt = "Not Loaded"
            imgui.same_line()
            imgui.text_colored(tmp_col, f"{tmp_txt}")
            imgui.text("Skill List File:")
            imgui.same_line(100)
            imgui.push_item_width(min(max(imgui.get_window_width()-250, 250),max(250, 20+imgui.calc_text_size(skill_list_location)[0])))
            changed, skill_list_location = imgui.input_text("##skill_list_location", skill_list_location)
            imgui.pop_item_width()
            imgui.same_line()
            if imgui.button("Browse##skill_list_location"):
                open_dialog = pfd.open_file("Select Skill List File")  
                selected_files = open_dialog.result()
                if len(selected_files) == 1:
                    selected_file = selected_files[0]
                    print(f"Selected: {selected_file}")
                    skill_list_location = selected_file
            if skill_list_loaded:
                tmp_col = imgui.ImVec4(0,255,0,255)
                tmp_txt = "Loaded"
            else:
                tmp_col = imgui.ImVec4(255,0,0,255)
                tmp_txt = "Not Loaded"
            imgui.same_line()
            imgui.text_colored(tmp_col, f"{tmp_txt}")
            imgui.text("Flag List File:")
            imgui.same_line(100)
            imgui.push_item_width(min(max(imgui.get_window_width()-250, 250),max(250, 20+imgui.calc_text_size(flag_list_location)[0])))
            changed, flag_list_location = imgui.input_text("##flag_list_location", flag_list_location)
            imgui.pop_item_width()
            imgui.same_line()
            if imgui.button("Browse##flag_list_location"):
                open_dialog = pfd.open_file("Select Flag List File")  
                selected_files = open_dialog.result()
                if len(selected_files) == 1:
                    selected_file = selected_files[0]
                    print(f"Selected: {selected_file}")
                    flag_list_location = selected_file
            if flag_list_loaded:
                tmp_col = imgui.ImVec4(0,255,0,255)
                tmp_txt = "Loaded"
            else:
                tmp_col = imgui.ImVec4(255,0,0,255)
                tmp_txt = "Not Loaded"
            imgui.same_line()
            imgui.text_colored(tmp_col, f"{tmp_txt}")
            imgui.end_tab_item()
        imgui.end_tab_bar()
    

immapp.run(
    gui_function=gui,  # The Gui function to run
    window_title="FANTASY LIFE i Save Editor" + f" ver {VERSION}",  # the window title
##    window_size_auto=True,  # Auto size the application window given its widgets
    window_size=(1706,960),
    # Uncomment the next line to restore window position and size from previous run
    window_restore_previous_geometry=True
    
)
