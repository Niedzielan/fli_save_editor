
with open("usmap2structs.txt", "r", encoding="utf-8") as usmap2structsFile:
    usmap2structsLines =  usmap2structsFile.readlines()

patched_usmap2structs = ""
## not everything in SaveData otherwise we'd just add it there
ADD_MAGIC_HEADER = ["HeaderData_P",
                    "PLAY_DATA_P", 
                    "FlagStatus_P",
                    "InventoryInfoCore", # Mostly this one!
                    "QuestStatusP",
                    "DynamicQuestConfigP",
                    "PeriodicBenefitStatusP",
                    "PHASE_INFO_P",
                    "CharaStatusGroupP",
                    "PartyGroupInfoP",
                    "CraftStatusInfoP",
                    "CraftAreaStatusP",
                    "PlantDungeonStatusP",
                    "PlantDungeonBranchStatusP",
                    "GalleryStatusInfoP",
                    "GDDAvatarStatusP",
                    "PickPointStatusP",
                    "WeatherStatusP",
                    "GDDNpcStatusP",
                    "RecipeStatusP",
                    "LotPlaceInfoP",
                    "VegetableFieldStatusP",
                    "GDDMySetStatusP",
                    "GDDGuildStatusP",
                    "MultiPlayStatusP",
                    "DailyMissionStatusP",
                    "GDDShopStatusP",
                    "GDDTraderShopStatusP",
                    "GDDFarmStandStatusP",
                    "HugeMapStatusP",
                    "InstantCharaStatusP",
                    "GDDTextLogP",
                    "EnemyStatusP",
                    "GenerateStatusP",
                    "BlockUserInfoP",
                    "ReportUserInfoP",
                    "GDDRoguelikeStatusP",
                    "MultiplayUserInfo",
                    "BlockInfo",
                    "GDDRoguelikeStrongBossStatusP"]
current_struct = ""
insert = {}

def addInsert(struct_name, property_name, line, where="after"):
    if struct_name not in insert:
        insert[struct_name] = {property_name: {where : [line]}}
    else:
        if property_name not in insert[struct_name]:
            insert[struct_name][property_name] = {where : [line]}
        else:
            if where not in insert[struct_name][property_name]:
                insert[struct_name][property_name][where] = [line]
            else:
                insert[struct_name][property_name][where].append(line)

for line in  usmap2structsLines:
    pre_line = ""
    post_line = ""
    if line.startswith("struct "):
        struct_name = line.split(" ")[1]
        current_struct = struct_name
        if struct_name in ADD_MAGIC_HEADER:
            post_line = "u32 MAGIC_NUMBER;\n"
            
        elif struct_name == "InventoryInfoPlantDungeonBranch":
            post_line = "u32 unk;\n"
            
        elif struct_name == "SortSettingInfo":
            post_line = "u16 unk;\n"
            
        elif struct_name == "ItemCraftAssistCharaSetting":
            #post_line = "u8 unk[0x8];\n"
            post_line = "Array<u32> unk1;\nArray<u32> unk2;\n"
            
        elif struct_name == "DungeonMapJumpFunctionPointData":
            post_line = "Name unk1;\nName unk2;\n"
            
##        elif struct_name == "SaveData":
##            pre_line = """struct CustomRoguelikeShopInfo {
##Str itemName;
##u8 unk[3];
##};
##struct CustomRoguelikeShopData {
##Str shopName;
##Array<CustomRoguelikeShopInfo> inner;
##};
##struct CustomRoguelikeShopDataList {
##u8 unk;
##Array<CustomRoguelikeShopData> roguelikeShopDataList;
##};\n
##"""
    elif line.startswith("}") or line.startswith("\n") or line.strip() == "":
        pass # don't skip, still need to write it
    else: # properties
        tmpsplit = line.split(" ")
        types = " ".join(tmpsplit[:-1])
        name = tmpsplit[-1][:-2] # remove ;\n
        if struct_name == "SaveData":
            if name == "m_InstantCharaStatusP":
                line = "// remove "+line
##            elif name == "m_EnemyStatusP":
##                line = f"Array<{types}> {name}; // make array\n"
##            elif name == "m_RoguelikeStrongBossStatusP":
##                post_line = "CustomRoguelikeShopDataList customRoguelikeShopDataList; // new \n"
##                post_line += "Array<u8> unknownBitArray; // new \n"
                
        elif struct_name == "PLAY_DATA_P":
            if name == "clockValidCheckStruct":
                line = "// remove "+line
            elif name == "purposePointPinDataInfo":
                addInsert(struct_name, "preAddContentRight", line)
                line = "// move "+line
            elif name == "prevHugeMapJumpAreaNo":
                addInsert(struct_name, "prevInHugeMapJumpSubMapId", line)
                line = "// move "+line
                
        elif struct_name == "FlagStatus_P":
            if types == "Array<u32>": 
                line = f"Array<u8> {name}; // bool in Array is u8 not u32\n"
            if name == "GlobalFlightSelectedFlag":
                addInsert(struct_name, "GlobalHonegonFlightUsedFlag", line)
                line = "// move "+line
                
        elif struct_name == "InventoryInfoCore":
            #print(f"{struct_name} - {name} : {types}")
            if name in ["IsFavorite", "isPresented"] and types == "u8":
                line = f"u32 {name}; // bool\n"
                
        elif struct_name == "InventoryInfoEquip":
            if name == "addEquipStatus":
                line = f"Array<{types}> {name}; // make array\n" 
            elif name == "grantSkillId":
                post_line = "u16 equipped; // new field\n"
            elif name == "isBurying":
                line = line.replace("u32", "u8")
                
        elif struct_name == "InventoryStatusDataP":
            if name == "invPlantDungeonBranch":
                addInsert(struct_name, "invItemSlot", line, "after")
                line = "// move " + line
            elif name == "invPowerUp":
                addInsert(struct_name, "invInstantCharaMount", line)
                line = "// move " + line
                
        elif struct_name == "GDId":
            if name == "crc":
                line = "// remove "+line
                
        elif struct_name == "PlantDungeonBranchStatusP":
            if name == "plantDungeonBranchFloorStatusCorePList":
                addInsert(struct_name, "plantDungeonBranchStatusCorePList", line)
                line = "// move " + line
                
        elif struct_name == "PlantDungeonBranchStatusCoreP":
            if name == "bossSpawnInfo":
                addInsert(struct_name, "Handle", line)
                line = "// move " + line
                
        elif struct_name == "GDDAvatarStatusP":
            if name == "playerP":
                line = f"Array<{types}> {name}; // make array\n"
                
        elif struct_name == "MultiPlayStatusP":
            if name == "sessionHostUserId":
                line = "Str sessionHostUserId; // technically Array<u8>\n"
            elif name == "localSessionHostNum":
                addInsert(struct_name, "gotTamagemonoBoxSessionInfo", line)
                line = "// move " + line
            elif name == "joinUserInfoHistoryIndex":
                post_line = "u32 MAGIC_NUMBER_2;\n"
##            elif name == "gotTamagemonoBoxSessionInfo":
##                post_line = "u8 unk[0x4];"
            elif name == "joinUserInfoHistoryNum":
                line = "// remove "+line

        elif struct_name == "HugeMapAreaStatusP":
            if name == "isHintOpenShrine":
                line = "// remove "+line
                
        elif struct_name in ["MultiplayUserInfo", "BlockInfo"]:
            if name == "productUserId":
                post_line = "u8 PlatformType;\n"
            elif name == "platformUserName":
                addInsert(struct_name, "minute", line, "immediate_after")
                line = "// move " + line
            elif name == "roguelikeBossId":
                addInsert(struct_name, "minute", line, "immediate_after")
                line = "// move " + line
            elif name == "plantDungeonGen":
                addInsert(struct_name, "minute", line)
                line = "// move " + line
            elif name == "PlatformType":
                line = "// move " + line
            elif name == "Level":
                addInsert(struct_name, "lifeType", line)
                line = "// move " + line

        elif struct_name == "GDDTextLogP":
            if name == "textList":
                post_line = "u32 unk;\n"
        elif struct_name == "GDDRoguelikeStatusP":
            if name == "GlobalShopPreviewFlag":
                line = line.replace("u32", "u8")
        
        # inserts
        for ins in insert:
            if struct_name == ins and name in insert[ins]:
                if "immediate_after" in insert[ins][name]:
                    for ps_line in insert[ins][name]["immediate_after"]:
                        post_line += ps_line
                if "after" in insert[ins][name]:
                    for ps_line in insert[ins][name]["after"]:
                        post_line += ps_line
                if "before" in insert[ins][name]:
                    for pr_line in insert[ins][name]["before"]:
                        pre_line += pr_line
                if "immediate_before" in insert[ins][name]:
                    for pr_line in insert[ins][name]["immediate_before"]:
                        pre_line += pr_line

    patched_usmap2structs += pre_line
    patched_usmap2structs += line
    patched_usmap2structs += post_line

## Add InHex testing
patched_usmap2structs += """
#pragma array_limit 2000000
#pragma pattern_limit 4000000

SaveFile saveFile @ 0x0;"""

with open("usmap2structs_patched.txt", "w", encoding="utf-8") as usmap2structsPatchedFile:
    usmap2structsPatchedFile.write(patched_usmap2structs)
