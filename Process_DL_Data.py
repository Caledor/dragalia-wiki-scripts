import csv
import os
import string
from shutil import copyfile, rmtree
from collections import OrderedDict
import argparse

import pdb

EXT = '.txt'
DEFAULT_TEXT_LABEL = ''
ENTRY_LINE_BREAK = '\n=============================\n'
EDIT_THIS = '<EDIT_THIS>'

ROW_INDEX = '_Id'
EMBLEM_P = 'EMBLEM_NAME_'

TEXT_LABEL = 'TextLabel'
TEXT_LABELS = None
ABILITY_SHIFT_GROUP = 'AbilityShiftGroup'
ABILITY_SHIFT_GROUPS = None
SKILL_DATA_NAME = 'SkillData'
SKILL_DATA_NAMES = None

ROMAN_NUMERALS = [None, 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
ELEMENT_TYPE = [None, 'Flame', 'Water', 'Wind', 'Light', 'Shadow']
CLASS_TYPE = [None, 'Attack', 'Defense', 'Support', 'Healing']
WEAPON_TYPE = [None, 'Sword', 'Blade', 'Dagger', 'Axe', 'Lance', 'Bow', 'Wand', 'Staff']

MATERIAL_NAME_LABEL = 'MATERIAL_NAME_'
WEAPON_CRAFT_DATA_MATERIAL_COUNT = 5

def csv_as_index(path, index=None, value_key=None, tabs=False):
    with open(path, newline='') as csvfile:
        if tabs:
            reader = csv.DictReader(csvfile, dialect='excel-tab')
        else:
            reader = csv.DictReader(csvfile)
        first_row = next(reader)
        key_iter = iter(first_row.keys())
        csvfile.seek(0)
        if not index:
            index = next(key_iter) # get first key as index
        if len(first_row) == 2:
            # load 2 column files as dict[string] = string
            value_key = next(key_iter) # get second key
        if value_key:
            return {row[index]: row[value_key] for row in reader if row[index] != '0'}
        else:
            # load >2 column files as a dict[string] = OrderedDict
            return {row[index]: row for row in reader if row[index] != '0'}

def get_label(key):
    return TEXT_LABELS[key].replace('\\n', ' ') if key in TEXT_LABELS else DEFAULT_TEXT_LABEL

# All process_* functions take in 1 parameter (OrderedDict row) and return 3 values (OrderedDict new_row, str template_name, str display_name)
# Make sure the keys are added to the OrderedDict in the desired output order
def process_AbilityLimitedGroup(row):
    new_row = OrderedDict()
    for k, v in row.items():
        new_row[k.strip('_')] = v
    new_row['AbilityLimitedText'] = get_label(row['_AbilityLimitedText']).format(ability_limit0=row['_MaxLimitedValue'])
    return row, None, None

def process_AbilityData(row):
    new_row = OrderedDict()

    new_row['Id'] = row['_Id']
    new_row['PartyPowerWeight'] = row['_PartyPowerWeight']
    new_row['GenericName'] = '' # EDIT_THIS

    shift_value = ROMAN_NUMERALS[int(row['_ShiftGroupId'])]
    if row['_ShiftGroupId'] in ABILITY_SHIFT_GROUPS:
        shift_group_row = ABILITY_SHIFT_GROUPS[row['_ShiftGroupId']]
        for k, v in shift_group_row.items():
            if k.startswith('_Level') and v == row['_Id']:
                shift_value = ROMAN_NUMERALS[int(k.replace('_Level', ''))]
    # TODO: figure out what actually goes here
    ability_value = EDIT_THIS if row['_AbilityType1UpValue'] == '0' else row['_AbilityType1UpValue']
    new_row['Name'] = get_label(row['_Name']).format(
        ability_shift0  =   shift_value,
        ability_val0    =   ability_value)

    # _ElementalType seems unreliable, use (element) in _Name for now
    detail_label = get_label(row['_Details'])
    if '{element_owner}' in detail_label and ')' in new_row['Name']:
        element = new_row['Name'][1:new_row['Name'].index(')')]
    else:
        element = ELEMENT_TYPE[int(row['_ElementalType'])]
    new_row['Details'] = detail_label.format(
        ability_cond0   =   row['_ConditionValue'],
        ability_val0    =   ability_value,
        element_owner   =   element)

    new_row['AbilityIconName'] = row['_AbilityIconName']
    new_row['AbilityGroup'] = row['_ViewAbilityGroupId1']
    new_row['AbilityLimitedGroupId1'] = row['_AbilityLimitedGroupId1']
    new_row['AbilityLimitedGroupId2'] = row['_AbilityLimitedGroupId2']
    new_row['AbilityLimitedGroupId3'] = row['_AbilityLimitedGroupId3']
    return new_row, 'Ability', new_row['Name']

def process_AmuletData(row):
    new_row = OrderedDict()

    new_row['Id'] = row['_Id']
    new_row['BaseId'] = row['_BaseId']
    new_row['Name'] = get_label(row['_Name'])
    new_row['NameJP'] = '' # EDIT_THIS
    new_row['FeaturedCharacters'] = '' # EDIT_THIS
    new_row['Obtain'] = '' # EDIT_THIS
    new_row['ReleaseDate'] = '' # EDIT_THIS
    new_row['Availability'] = '' # EDIT_THIS
    new_row['Rarity'] = row['_Rarity']
    new_row['AmuletType'] = CLASS_TYPE[int(row['_AmuletType'])]
    new_row['MinHp'] = row['_MinHp']
    new_row['MaxHp'] = row['_MaxHp']
    new_row['MinAtk'] = row['_MinAtk']
    new_row['MaxAtk'] = row['_MaxAtk']
    new_row['VariationId'] = row['_VariationId']
    for i in range(1, 4):
        for j in range(1, 4):
            ab = 'Abilities{}{}'.format(i, j)
            new_row[ab] = row['_' + ab]
    new_row['Ability1Event'] = 0
    new_row['Ability2Event'] = 0
    new_row['Ability3Event'] = 0
    new_row['ArtistCV'] = '' # EDIT_THIS
    for i in range(1, 6):
        new_row['FlavorText{}'.format(i)] = get_label(row['_Text{}'.format(i)])
    new_row['IsPlayable'] = row['_IsPlayable']
    new_row['SellCoin'] = row['_SellCoin']
    new_row['SellDewPoint'] = row['_SellDewPoint']

    return new_row, 'Wyrmprint', new_row['Name']

def process_BuildEventItem(row):
    new_row = OrderedDict()

    new_row['Id'] = row['_Id']
    new_row['Name'] = get_label(row['_Name'])
    new_row['Description'] = get_label(row['_Detail'])
    new_row['Rarity'] = '' # EDIT_THIS
    new_row['QuestEventId'] = row['_EventId']
    new_row['SortId'] = row['_Id']
    new_row['Obtain'] = '\n*' + get_label(row['_Description'])
    new_row['Usage'] = '' # EDIT_THIS
    new_row['MoveQuest1'] = row['_MoveQuest1']
    new_row['MoveQuest2'] = row['_MoveQuest2']
    new_row['MoveQuest3'] = row['_MoveQuest3']
    new_row['MoveQuest4'] = row['_MoveQuest4']
    new_row['MoveQuest5'] = row['_MoveQuest5']
    new_row['PouchRarity'] = row['_PouchRarity']

    return new_row, 'Material', new_row['Name']

def process_CharaData(row):
    new_row = OrderedDict()

    new_row['IdLong'] = row['_Id']
    new_row['Id'] = row['_BaseId']
    new_row['Name'] = get_label(row['_Name'])
    new_row['FullName'] = '{{PAGENAME}}'
    new_row['NameJP'] = '' # EDIT_THIS
    new_row['Title'] = get_label(EMBLEM_P + row['_EmblemId'])
    new_row['TitleJP'] = '' # EDIT_THIS
    new_row['Obtain'] = '' # EDIT_THIS
    new_row['ReleaseDate'] = '' # EDIT_THIS
    new_row['Availability'] = '' # EDIT_THIS
    new_row['WeaponType'] = WEAPON_TYPE[int(row['_WeaponType'])]
    new_row['Rarity'] = row['_Rarity']
    new_row['Gender'] = '' # EDIT_THIS
    new_row['Race'] = '' # EDIT_THIS
    new_row['ElementalType'] = ELEMENT_TYPE[int(row['_ElementalType'])]
    new_row['CharaType'] = CLASS_TYPE[int(row['_CharaType'])]
    new_row['VariationId'] = row['_VariationId']
    new_row['MinHp3'] = row['_MinHp3']
    new_row['MinHp4'] = row['_MinHp4']
    new_row['MinHp5'] = row['_MinHp5']
    new_row['MaxHp'] = row['_MaxHp']
    new_row['PlusHp0'] = row['_PlusHp0']
    new_row['PlusHp1'] = row['_PlusHp1']
    new_row['PlusHp2'] = row['_PlusHp2']
    new_row['PlusHp3'] = row['_PlusHp3']
    new_row['PlusHp4'] = row['_PlusHp4']
    new_row['McFullBonusHp5'] = row['_McFullBonusHp5']
    new_row['MinAtk3'] = row['_MinAtk3']
    new_row['MinAtk4'] = row['_MinAtk4']
    new_row['MinAtk5'] = row['_MinAtk5']
    new_row['MaxAtk'] = row['_MaxAtk']
    new_row['PlusAtk0'] = row['_PlusAtk0']
    new_row['PlusAtk1'] = row['_PlusAtk1']
    new_row['PlusAtk2'] = row['_PlusAtk2']
    new_row['PlusAtk3'] = row['_PlusAtk3']
    new_row['PlusAtk4'] = row['_PlusAtk4']
    new_row['McFullBonusAtk5'] = row['_McFullBonusAtk5']
    new_row['MinDef'] = row['_MinDef']
    new_row['DefCoef'] = row['_DefCoef']
    new_row['Skill1Name'] = get_label(SKILL_DATA_NAMES[row['_Skill1']]) if row['_Skill1'] in SKILL_DATA_NAMES else ''
    new_row['Skill2Name'] = get_label(SKILL_DATA_NAMES[row['_Skill2']]) if row['_Skill2'] in SKILL_DATA_NAMES else ''
    new_row['Abilities11'] = row['_Abilities11']
    new_row['Abilities12'] = row['_Abilities12']
    new_row['Abilities13'] = '0'
    new_row['Abilities14'] = '0'
    new_row['Abilities21'] = row['_Abilities21']
    new_row['Abilities22'] = row['_Abilities22']
    new_row['Abilities23'] = '0'
    new_row['Abilities24'] = '0'
    new_row['Abilities31'] = row['_Abilities31']
    new_row['Abilities32'] = row['_Abilities32']
    new_row['Abilities33'] = '0'
    new_row['Abilities34'] = '0'
    new_row['ExAbilityData1'] = row['_ExAbilityData1']
    new_row['ExAbilityData2'] = row['_ExAbilityData2']
    new_row['ExAbilityData3'] = row['_ExAbilityData3']
    new_row['ExAbilityData4'] = row['_ExAbilityData4']
    new_row['ExAbilityData5'] = row['_ExAbilityData5']
    new_row['ManaCircleName'] = row['_ManaCircleName']
    new_row['JapaneseCV'] = get_label(row['_CvInfo'])
    new_row['EnglishCV'] = get_label(row['_CvInfoEn'])
    new_row['Description'] = get_label(row['_ProfileText'])
    new_row['IsPlayable'] = row['_IsPlayable']
    new_row['MaxFriendshipPoint'] = row['_MaxFriendshipPoint']

    return new_row, 'Adventurer', new_row['Name'] + ' - ' + get_label(row['_SecondName'])

def process_ExAbilityData(row):
    new_row = OrderedDict()

    new_row['Id'] = row['_Id']
    new_row['GenericName'] = '' # EDIT_THIS
    new_row['Name'] = get_label(row['_Name'])
    new_row['Details'] = get_label(row['_Details']).format(
        value1=row['_AbilityType1UpValue0']
    )
    new_row['AbilityIconName'] = row['_AbilityIconName']
    new_row['Category'] = row['_Category']
    new_row['PartyPowerWeight'] = row['_PartyPowerWeight']

    return new_row, 'CoAbility', new_row['Name']

def process_SkillData(row):
    new_row = OrderedDict()

    new_row['SkillId']= row['_Id']
    new_row['Name']= get_label(row['_Name']).replace("\\n", " ")
    new_row['SkillLv1IconName']= row['_SkillLv1IconName']
    new_row['SkillLv2IconName']= row['_SkillLv2IconName']
    new_row['SkillLv3IconName']= row['_SkillLv3IconName']
    new_row['Description1']= get_label(row['_Description1']).replace("\\n", " ")
    new_row['Description2']= get_label(row['_Description2']).replace("\\n", " ")
    new_row['Description3']= get_label(row['_Description3']).replace("\\n", " ")
    new_row['HideLevel3']= '' # EDIT_THIS
    new_row['Sp']= row['_Sp']
    new_row['SpLv2']= row['_SpLv2']
    new_row['SpRegen']= '' # EDIT_THIS
    new_row['IsAffectedByTension']= row['_IsAffectedByTension']
    new_row['ZoominTime']= row['_ZoominTime']
    new_row['Zoom2Time']= row['_Zoom2Time']
    new_row['ZoomWaitTime']= row['_ZoomWaitTime']

    return new_row, 'Skill', new_row['Name']


def process_WeaponData(rowi, skill_data):
    new_row = OrderedDict()

    new_row['Id'] = row['_Id']
    new_row['BaseId'] = row['_BaseId']
    new_row['FormId'] = row['_FormId']
    new_row['WeaponName'] = row['_Name'].replace("\\n", " ")
    new_row['WeaponNameJP'] = '' # EDIT_THIS
    new_row['Type'] = WEAPON_TYPE[int(row['_Type'])]
    new_row['Rarity'] = row['_Rarity']
    # Case when weapons have no elemental type
    try:
        new_row['ElementalType'] = ELEMENTS[int(row['_ElementalType'])]
    except:
        new_row['ElementalType'] = ''
    new_row['Obtain'] = '' # EDIT_THIS
    new_row['ReleaseDate'] = '' # EDIT_THIS
    new_row['Availability'] = '' # EDIT_THIS
    new_row['MinHp'] = row['_MinHp']
    new_row['MaxHp'] = row['_MaxHp']
    new_row['MinAtk'] = row['_MinAtk']
    new_row['MaxAtk'] = row['_MaxAtk']
    new_row['VariationId'] = 1
    new_row['SkillName'] = row['_']
    new_row['Abilities11'] = row['_Abilities11']
    new_row['Abilities21'] = row['_Abilities21']
    new_row['IsPlayable'] = 1
    new_row['FlavorText'] = row['_Text'].replace("\\n", " ")
    new_row['SellCoin'] = row['_SellCoin']
    new_row['SellDewPoint'] = row['_SellDewPoint']

    # WeaponCraftTreeData
    new_row['CraftNodeId'] = row['_CraftNodeId']
    new_row['ParentCraftNodeId'] = row['ParentCraftNodeId']
    new_row['CraftGroupId'] = row['CraftGroupId']

    # WeaponCraftData
    new_row['FortCraftLevel'] = row['_FortCraftLevel']
    new_row['AssembleCoin'] = row['_AssembleCoin']
    new_row['DisassembleCoin'] = row['_DisassembleCoin']
    new_row['MainWeaponId'] = row['_MainWeaponId']
    new_row['MainWeaponQuantity'] = row['_MainWeaponQuantity']

    for i in range(0,WEAPON_CRAFT_DATA_MATERIAL_COUNT):
        curr_id = i + 1
        new_row['CraftMaterialType{}'.format(curr_id)] = row['_CrafEntityType{}'.format(curr_id)]
        new_row['CraftMaterial{}'.format(curr_id)] = get_label("{}{}".format(MATERIAL_NAME_LABEL, row['_CraftEnitityId{}'.format(curr_id)]))
        new_row['CraftMaterialQuantity{}'.format(curr_id)] = row['_CraftEntityQuantity{}'.format(curr_id)]

    return new_row, 'Weapon', new_row['Name']

def process_WeaponCraftData(row):
    new_row = OrderedDict()
    
    new_row['Id'] = row['_Id']
    new_row['FortCraftLevel'] = row['_FortCraftLevel']
    new_row['AssembleCoin'] = row['_AssembleCoin']
    new_row['DisassembleCoin'] = row['_DisassembleCoin']
    new_row['MainWeaponId'] = row['_MainWeaponId']
    new_row['MainWeaponQuantity'] = row['_MainWeaponQuantity']

    for i in range(0,WEAPON_CRAFT_DATA_MATERIAL_COUNT):
        curr_id = i + 1
        new_row['CraftMaterialType{}'.format(curr_id)] = row['_CrafEntityType{}'.format(curr_id)]
        new_row['CraftMaterial{}'.format(curr_id)] = get_label("{}{}".format(MATERIAL_NAME_LABEL, row['_CraftEnitityId{}'.format(curr_id)]))
        new_row['CraftMaterialQuantity{}'.format(curr_id)] = row['_CraftEntityQuantity{}'.format(curr_id)]

    return new_row

def process_WeaponCraftTree(row):
    new_row = OrderedDict()

    new_row['Id'] = row['_Id']
    new_row['CraftNodeId'] = row['_CraftNodeId']
    new_row['ParentCraftNodeId'] = row['ParentCraftNodeId']
    new_row['CraftGroupId'] = row['CraftGroupId']

    return new_row 

DATA_FILE_PROCESSING = {
    'AbilityLimitedGroup': process_AbilityLimitedGroup,
    'AbilityData': process_AbilityData,
    'AmuletData': process_AmuletData, # AKA Wyrmprint
    'BuildEventItem': process_BuildEventItem,
    'CharaData': process_CharaData, # AKA Adventurer
    'ExAbilityData': process_ExAbilityData, # AKA Co-Ability
    'CollectEventItem': None,
    'MissionDailyData': None,
    'DragonData': None,
    'EmblemData': None,
    'EnemyData': None,
    'EventData': None,
    'FortPlantData': None,
    'MaterialData': None,
    'MissionNormalData': None,
    'MissionPeriodData': None,
    'QuestClearType': None,
    'QuestData': None,
    'QuestEvent': None,
    'QuestEventGroup': None,
    'QuestFailedType': None,
    'QuestRewardData': None,
    'RaidEventItem': None,
    'SkillData': process_SkillData,
    #'WeaponData': process_WeaponData,
    #'WeaponCraftData': process_WeaponCraftData,
    #'WeaponCraftTree': process_WeaponCraftTree,
}

def build_wikitext_row(template_name, row, delim='|'):
    row_str = '{{' + template_name + delim
    row_str += delim.join(['{}={}'.format(k, row[k]) for k in row])
    if delim[0] == '\n':
        row_str += '\n'
    row_str += '}}'
    return row_str

def csv_as_wikitext(in_dir, out_dir, data_name):
    with open(in_dir+data_name+EXT, 'r') as in_file, open(out_dir+data_name+EXT, 'w') as out_file:
        reader = csv.DictReader(in_file)
        for row in reader:
            if row[ROW_INDEX] == '0':
                continue
            template_name, display_name = None, None
            if DATA_FILE_PROCESSING[data_name] is not None:
                row, template_name, display_name = DATA_FILE_PROCESSING[data_name](row)
            template_name = data_name if template_name is None else template_name
            if display_name is not None:
                out_file.write(display_name)
                out_file.write(ENTRY_LINE_BREAK)
                out_file.write(build_wikitext_row(template_name, row, delim='\n|'))
                out_file.write(ENTRY_LINE_BREAK)
            else:
                out_file.write(build_wikitext_row(template_name, row))
                out_file.write('\n')

def find_fmt_params(in_dir, out_dir):
    with open('fmt_params.csv', 'w') as out_file:
        out_file.write('file,column,fmt_param,context\n')
        for data_name in DATA_FILE_PROCESSING:
            seen = {}
            with open(in_dir+data_name+EXT, 'r') as in_file:
                reader = csv.DictReader(in_file)
                for row in reader:
                    for k, v in row.items():
                        if k not in seen:
                            seen[k] = []
                        if v in TEXT_LABELS:
                            fmt_params = {s[1]: None for s in string.Formatter().parse(TEXT_LABELS[v]) if s[1] is not None}
                            for p in fmt_params:
                                if p not in seen[k]:
                                    out_file.write(','.join((data_name, k, p)) + '\n')
                                    seen[k].append(p)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process CSV data into Wikitext.')
    parser.add_argument('-i', type=str, help='directory of input text files', required=True)
    parser.add_argument('-o', type=str, help='directory of output text files  (default: ./output)', default='./output')
    parser.add_argument('--delete_old', help='delete older output files', dest='delete_old', action='store_true')

    args = parser.parse_args()
    if args.delete_old:
        if os.path.exists(args.o):
            try:
                rmtree(args.o)
                print('Deleted old {}\n'.format(args.o))
            except Exception:
                print('Could not delete old {}\n'.format(args.o))
    if not os.path.exists(args.o):
        os.makedirs(args.o)

    in_dir = args.i if args.i[-1] == '/' else args.i+'/'
    out_dir = args.o if args.o[-1] == '/' else args.o+'/'

    TEXT_LABELS = csv_as_index(in_dir+TEXT_LABEL+EXT, tabs=True)
    ABILITY_SHIFT_GROUPS = csv_as_index(in_dir+ABILITY_SHIFT_GROUP+EXT)
    SKILL_DATA_NAMES = csv_as_index(in_dir+SKILL_DATA_NAME+EXT, value_key='_Name')

    # find_fmt_params(in_dir, out_dir)
    for data_name in DATA_FILE_PROCESSING:
        if DATA_FILE_PROCESSING[data_name] is not None:
            print('Saved {}{}'.format(data_name, EXT))
            csv_as_wikitext(in_dir, out_dir, data_name)
