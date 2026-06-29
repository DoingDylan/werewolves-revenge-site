import unreal
import json
import os
import re
import builtins

# Inline icon decorators used in Unreal RichTextBlock descriptions, written
# as `<img id="Name"/>`. "textureName" is the underlying texture asset name,
# which sometimes differs from the decorator name (e.g. "Perish" -> "Die")
# -- the actual file in public/images/keywords might be saved under either
# name, so resolveKeywordIconFile() below tries both.
KEYWORD_DECORATORS = {
    "Attack": {"textureName": "Attack", "color": "#883532"},
    "UnstoppableAttack": {"textureName": "UnstoppableAttack", "color": "#883532"},
    "Bleed": {"textureName": "Bleed", "color": "#883532"},
    "Ignite": {"textureName": "Ignite", "color": "#883532"},
    "Poison": {"textureName": "Poison", "color": "#883532"},
    "Protect": {"textureName": "Protect", "color": "#5F90C4"},
    "DivineProtection": {"textureName": "DivineProtection", "color": "#5F90C4"},
    "Heal": {"textureName": "Heal", "color": "#5F90C4"},
    "PermanentDefence": {"textureName": "PermanentDefence", "color": "#5F90C4"},
    "Untargetable": {"textureName": "Untargetable", "color": "#839C38"},
    "Exposed": {"textureName": "Exposed", "color": "#839C38"},
    "Frail": {"textureName": "Frail", "color": "#839C38"},
    "Convert": {"textureName": "Convert", "color": "#839C38"},
    "Remove": {"textureName": "Remove", "color": "#ffffff"},
    "Transform": {"textureName": "Transform", "color": "#839C38"},
    "Assume": {"textureName": "Assume", "color": "#839C38"},
    "Redirect": {"textureName": "Redirect", "color": "#839C38"},
    "Meet": {"textureName": "Meet", "color": "#839C38"},
    "ShareFate": {"textureName": "ShareFate", "color": "#839C38"},
    "Share": {"textureName": "Share", "color": "#839C38"},
    "Reveal": {"textureName": "Revealed", "color": "#839C38"},
    "Role": {"textureName": "Role", "color": "#ffffff"},
    "Class": {"textureName": "Class", "color": "#ffffff"},
    "Capability": {"textureName": "Capabilities", "color": "#ffffff"},
    "Targets": {"textureName": "Targets", "color": "#ffffff"},
    "Execute": {"textureName": "Execute", "color": "#883532"},
    "Miss": {"textureName": "Miss", "color": "#839C38"},
    "Learn": {"textureName": "Learn", "color": "#B38FC4"},
    "Faction": {"textureName": "Faction", "color": "#ffffff"},
    "Active": {"textureName": "Active", "color": "#ffffff"},
    "Perish": {"textureName": "Die", "color": "#ffffff"},
    "Hemorrhage": {"textureName": "Hemorrhage_", "color": "#883532"},
    "Incinerate": {"textureName": "Incinerate", "color": "#883532"},
    "Neighbours": {"textureName": "Neighbours", "color": "#ffffff"},
    "Enhance": {"textureName": "Enhance", "color": "#839C38"},
}

# Diagnostic logging that survives a hard editor crash.
# In-editor print() output is lost the moment the editor crashes, so every
# print() in this script is mirrored to a plain text file on disk. flush()
# alone is enough to survive an application-level crash (Python/editor) --
# it pushes the write to the OS, it just wouldn't survive a full power-loss
# event, which isn't the scenario this guards against. os.fsync() forces a
# hardware-level disk flush on every single call, which is dramatically
# slower (especially inside a OneDrive-synced folder) and was overkill for
# what this is actually protecting against.
_log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "export_debug.log")
_log_file = open(_log_path, "w", encoding="utf-8")

def print(*args, **kwargs):
    builtins.print(*args, **kwargs)
    message = " ".join(str(a) for a in args)
    _log_file.write(message + "\n")
    _log_file.flush()

print(f"--- Starting export, logging to {_log_path} ---")

def export_roles_from_sets():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)

    output_path = os.path.join(script_dir, "data", "roles.json").replace("\\", "/")
    img_export_dir = os.path.join(root_dir, "public", "images", "roles").replace("\\", "/")
    ability_img_export_dir = os.path.join(root_dir, "public", "images", "abilities").replace("\\", "/")
    keywords_dir = os.path.join(root_dir, "public", "images", "keywords").replace("\\", "/")
    faction_img_export_dir = os.path.join(root_dir, "public", "images", "factions").replace("\\", "/")
    class_img_export_dir = os.path.join(root_dir, "public", "images", "classes").replace("\\", "/")

    if not os.path.exists(img_export_dir):
        os.makedirs(img_export_dir)
    if not os.path.exists(ability_img_export_dir):
        os.makedirs(ability_img_export_dir)
    if not os.path.exists(keywords_dir):
        os.makedirs(keywords_dir)
    if not os.path.exists(faction_img_export_dir):
        os.makedirs(faction_img_export_dir)
    if not os.path.exists(class_img_export_dir):
        os.makedirs(class_img_export_dir)

    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()

    set_class_name = "PDA_Set_C"
    set_name_variable = "Set Name"
    roles_array_variable = "Roles"

    filter = unreal.ARFilter(
        class_names=[set_class_name],
        recursive_classes=True
    )
    set_assets = asset_registry.get_assets(filter)

    json_data = []
    processed_roles = set()
    factions_registry = {}
    classes_registry = {}
    groups_resources_registry = {}

    # Many roles share the same Group/Resource asset (e.g. every Werewolf
    # shares the "Werewolves" group) -- cache by asset name so it's only
    # actually read/exported once instead of once per role that references it.
    def get_group_or_resource_data(obj):
        if not obj:
            return None
        key = obj.get_name()
        if key not in groups_resources_registry:
            groups_resources_registry[key] = exportGroupOrResource(obj, img_export_dir)
        return groups_resources_registry[key]

    print(f"Found {len(set_assets)} Sets. Starting export...")

    # Only these Sets get exported to the website (any other Set found in
    # Unreal is skipped entirely), and they'll appear in exactly this order
    # everywhere the website lists Sets (e.g. the roles page's Set dropdown)
    # -- reorder this list to change that.
    allowed_sets = ["Standard", "Dark", "Olympia", "Grimm"]

    for set_data in set_assets:
        set_asset = set_data.get_asset()
        current_set_name = str(set_asset.get_editor_property(set_name_variable))

        if current_set_name not in allowed_sets:
            continue

        # allowed_sets is already a hand-ordered list -- reuse its index as
        # the set's sort order instead of adding any new property in Unreal.
        set_order = allowed_sets.index(current_set_name)

        roles_in_set = set_asset.get_editor_property(roles_array_variable)
        if not roles_in_set:
            continue

        for role_asset in roles_in_set:
            if not role_asset:
                continue

            # The role's id only needs to be unique *within* its own set --
            # the website routes roles as /roles/{set}/{id}, so the set
            # segment in the URL already disambiguates same-named roles
            # across different sets (e.g. a "Bodyguard" in both Standard
            # and Dark).
            role_id = str(role_asset.get_editor_property("Name")).lower().replace(" ", "-")
            dedupe_key = (current_set_name, role_id)

            if dedupe_key in processed_roles:
                continue
            processed_roles.add(dedupe_key)

            image_tex = role_asset.get_editor_property("Image")
            image_filename = exportImage(image_tex, img_export_dir, "default_image.png")

            portrait_tex = role_asset.get_editor_property("Portrait")
            portrait_filename = exportImage(portrait_tex, img_export_dir, "default_portrait.png")

            print(f"-> {role_id}")
            faction_obj = role_asset.get_editor_property("Faction")
            class_obj = role_asset.get_editor_property("Class")

            if faction_obj:
                faction_key = faction_obj.get_name()
                if faction_key not in factions_registry:
                    print(f"  -> exporting new Faction asset '{faction_key}'")
                    factions_registry[faction_key] = exportFaction(faction_obj, faction_img_export_dir)

            if class_obj:
                class_key = class_obj.get_name()
                if class_key not in classes_registry:
                    print(f"  -> exporting new Class asset '{class_key}'")
                    classes_registry[class_key] = exportClass(class_obj, class_img_export_dir)

            group_obj = resolveSoftReference(role_asset.get_editor_property("Group"))
            resource_obj = resolveSoftReference(role_asset.get_editor_property("Resource"))
            abilities_in_role = role_asset.get_editor_property("Abilities")

            group_data = get_group_or_resource_data(group_obj)
            resource_data = get_group_or_resource_data(resource_obj)

            abilities_data = []
            for i, ability_ref in enumerate(abilities_in_role or []):
                ability_asset = resolveSoftReference(ability_ref)
                if not ability_asset:
                    print(f"    !! ability[{i}] on {role_id} resolved to None, skipping")
                    continue
                abilities_data.append(exportAbility(ability_asset, ability_img_export_dir, keywords_dir))

            description = str(role_asset.get_editor_property("Description"))

            role_info = {
                "id": role_id,
                "set": current_set_name,
                "setOrder": set_order,
                "name": str(role_asset.get_editor_property("Name")),
                "faction": faction_obj.get_name() if faction_obj else "Unknown",
                "factionName": str(faction_obj.get_editor_property("Name")) if faction_obj else "Unknown",
                "class": class_obj.get_name() if class_obj else "Unknown",
                "description": description,
                "descriptionHtml": convertIcons(description, keywords_dir),
                # Unreal's exporter only writes PNGs
                # You must run `npm run optimize-images` to convert the pngs to webp
                "imageUrl": f"/images/roles/{image_filename.replace('.png', '.webp')}",
                "portraitUrl": f"/images/roles/{portrait_filename.replace('.png', '.webp')}",
                "group": group_data,
                "resource": resource_data,
                "abilities": abilities_data,
            }

            json_data.append(role_info)

    json_data = sorted(json_data, key=lambda k: k['name'])

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2)

    print(f"SUCCESS: Exported {len(json_data)} roles and assets!")

    factions_output_path = os.path.join(script_dir, "data", "factions.json").replace("\\", "/")
    factions_data = sorted(factions_registry.values(), key=lambda f: (f["order"], f["name"]))
    with open(factions_output_path, 'w', encoding='utf-8') as f:
        json.dump(factions_data, f, indent=2)

    print(f"SUCCESS: Exported {len(factions_data)} factions!")

    classes_output_path = os.path.join(script_dir, "data", "classes.json").replace("\\", "/")
    classes_data = sorted(classes_registry.values(), key=lambda c: (c["order"], c["name"]))
    with open(classes_output_path, 'w', encoding='utf-8') as f:
        json.dump(classes_data, f, indent=2)

    print(f"SUCCESS: Exported {len(classes_data)} classes!")

def exportClass(class_obj, class_img_export_dir):
    """Exports a single Class data asset to a plain dict, including its
    icon/color and an "order" read directly from its own "Class" enum
    dropdown's .value (a real Python enum member, e.g. NUM_Class.ELIMINATION:
    0 -- confirmed via diagnostic logging, see chat) -- same shape/approach
    as exportFaction(), except classes are already consistent across every
    set (no per-set renaming), so there's no equivalent to Faction's "Win
    Condition" field."""
    icon_tex = class_obj.get_editor_property("Icon")
    icon_filename = exportImage(icon_tex, class_img_export_dir, "default_image.png")

    order = 99
    try:
        order = class_obj.get_editor_property("Class").value
    except Exception as e:
        print(f"    !! Could not read Class enum on '{class_obj.get_name()}', sorting last: {e}")

    return {
        "id": class_obj.get_name(),
        "name": str(class_obj.get_editor_property("Name")),
        "description": str(class_obj.get_editor_property("Description")),
        "color": linearColorToHex(class_obj.get_editor_property("Colour")),
        "iconUrl": f"/images/classes/{icon_filename.replace('.png', '.webp')}",
        "order": order,
    }

def exportFaction(faction_obj, faction_img_export_dir):
    """Exports a single Faction data asset to a plain dict, including its
    icon/color/win-condition and an "order" read directly from its own
    "Faction" enum dropdown's .value -- get_editor_property("Faction")
    returns a real Python enum member (e.g. NUM_Faction.LESSER_EVIL: 4, not
    a string -- confirmed via diagnostic logging, see chat), and .value is
    already exactly the ordinal Town=0/Werewolf=1/Neutral=2/Evil=3/
    LesserEvil=4 the user confirmed is shared across every set (e.g. Dark's
    "Village" asset has this same enum set to TOWN, only its display Name
    differs)."""
    icon_tex = faction_obj.get_editor_property("Icon")
    icon_filename = exportImage(icon_tex, faction_img_export_dir, "default_image.png")

    order = 99
    try:
        order = faction_obj.get_editor_property("Faction").value
    except Exception as e:
        print(f"    !! Could not read Faction enum on '{faction_obj.get_name()}', sorting last: {e}")

    return {
        "id": faction_obj.get_name(),
        "name": str(faction_obj.get_editor_property("Name")),
        "description": str(faction_obj.get_editor_property("Description")),
        "winCondition": str(faction_obj.get_editor_property("Win Condition")),
        "color": linearColorToHex(faction_obj.get_editor_property("Colour")),
        "iconUrl": f"/images/factions/{icon_filename.replace('.png', '.webp')}",
        "order": order,
    }

def exportImage(texture, img_export_dir, default_filename):
    """Exports a texture asset (Image or Portrait) to img_export_dir as a PNG.

    Returns the resulting filename, falling back to default_filename when
    there is no texture to export.
    """
    if not texture:
        return default_filename

    filename = f"{texture.get_name()}.png"
    export_path = os.path.join(img_export_dir, filename)
    webp_path = os.path.join(img_export_dir, filename.replace(".png", ".webp"))

    # Only export if neither the PNG nor its optimized .webp already exists,
    # since `npm run optimize-images` deletes the PNGs after converting them.
    if not os.path.exists(export_path) and not os.path.exists(webp_path):
        task = unreal.AssetExportTask()
        task.object = texture
        task.filename = export_path
        task.automated = True
        task.replace_identical = True
        unreal.Exporter.run_asset_export_task(task)
        print(f"Exported Image: {filename}")

    return filename

def resolveSoftReference(obj):
    """Resolves a value that might be a TSoftObjectPtr/FSoftObjectPath into a
    real loaded UObject. Reading properties off an unresolved soft reference
    is what causes hard EXCEPTION_ACCESS_VIOLATION crashes in the Python
    plugin, so anything that *might* be a soft reference must go through
    this before get_editor_property()/get_name() is called on it.
    """
    if obj is None:
        return None

    # Already a regular, loaded UObject.
    if isinstance(obj, unreal.Object):
        return obj

    # unreal.SoftObjectPath / unreal.SoftObjectPtr-style wrapper.
    if hasattr(obj, "load_synchronous"):
        print(f"    (resolving soft reference via load_synchronous: {obj})")
        return obj.load_synchronous()
    if hasattr(obj, "load"):
        print(f"    (resolving soft reference via load: {obj})")
        return obj.load()

    # Fallback: treat it as a path string and load it directly.
    try:
        print(f"    (resolving soft reference via load_asset: {obj})")
        return unreal.load_asset(str(obj))
    except Exception as e:
        print(f"    !! Could not resolve soft reference {obj}: {e}")
        return None

def linearColorToHex(colour):
    """Converts an unreal.LinearColor (0-1 float channels, linear color space)
    to a "#rrggbb" hex string (sRGB, gamma-encoded -- what every browser/CSS
    color actually expects). Skipping the linear->sRGB conversion and just
    scaling by 255 produces colors that look noticeably darker/duller than
    what the color picker swatch shows in the Unreal editor.
    """
    if colour is None:
        return None

    def linear_to_srgb(value):
        value = max(0.0, min(1.0, value))
        if value <= 0.0031308:
            srgb = value * 12.92
        else:
            srgb = 1.055 * (value ** (1.0 / 2.4)) - 0.055
        return max(0, min(255, round(srgb * 255)))

    return f"#{linear_to_srgb(colour.r):02x}{linear_to_srgb(colour.g):02x}{linear_to_srgb(colour.b):02x}"

def enumToStr(value):
    """Converts an unreal enum value to a plain string, e.g. "EAbilityType::Active" -> "Active"."""
    if value is None:
        return None
    text = str(value)
    return text.split("::")[-1] if "::" in text else text

_keyword_icon_index_cache = {}

def resolveKeywordIconFile(keywords_dir, candidates):
    """Finds the actual filename in public/images/keywords matching one of
    the given candidate names (case/whitespace-insensitive, extension
    ignored), since files there were added by hand and don't perfectly
    match either the decorator name or the underlying texture name in every
    case (e.g. "Perish" vs its texture "Die").

    Returns the matched filename's base name (no extension), or None.
    """
    if keywords_dir not in _keyword_icon_index_cache:
        index = {}
        if os.path.exists(keywords_dir):
            for f in os.listdir(keywords_dir):
                base, _ext = os.path.splitext(f)
                index[base.strip().lower()] = base.strip()
        _keyword_icon_index_cache[keywords_dir] = index

    index = _keyword_icon_index_cache[keywords_dir]
    for candidate in candidates:
        key = candidate.strip().lower()
        if key in index:
            return index[key]
    return None

def convertIcons(text, keywords_dir):
    """Converts `<img id="Name"/>` inline icon decorators in role/ability
    descriptions into a small masked/tinted icon <span> (see .kw-icon in
    global.css), using KEYWORD_DECORATORS for the color.

    This does NOT add any text styling (bold, color, etc) for other
    decorators -- but it does strip them out (keeping their inner text)
    before converting icons. This isn't a styling feature, it's a safety
    requirement: descriptions also contain other Unreal RichTextBlock
    decorators like "<b>text</>" or "<p>text</>", and some of those (like
    "<b>") happen to be real HTML tags. Left as raw text, the browser parses
    "<b>" as actual unclosed bold HTML (since "</>" isn't valid HTML and
    doesn't close it), which bolds everything after it for the rest of the
    page. Stripping all non-icon tags first avoids that regardless of which
    decorator tag names happen to collide with real HTML elements.
    """
    if not text:
        return text

    # Strip any wrapping decorator -> keep inner text only. Closing tag can
    # be the generic "</>" or repeat the opening tag name (e.g. "<b>x</b>").
    text = re.sub(r"<(\w+)>(.*?)</\1?>", r"\2", text)

    # Strip any other stray/self-closing decorator that isn't the "<img
    # .../>" icon syntax handled below.
    text = re.sub(r"</?(?!img\b)\w+[^>]*>", "", text)

    def replace_icon(match):
        name = match.group(1)
        decorator = KEYWORD_DECORATORS.get(name)
        if not decorator:
            print(f"    !! Unknown icon decorator id '{name}'")
            return ""

        icon_file = resolveKeywordIconFile(keywords_dir, [name, decorator["textureName"]])
        if not icon_file:
            print(f"    !! No keyword icon file found for decorator '{name}' (tried '{name}', '{decorator['textureName']}')")
            return ""

        return (
            f'<span class="kw-icon" style="--kw: {decorator["color"]}; '
            f'--kw-icon: url(\'/images/keywords/{icon_file}.webp\')" '
            f'role="img" aria-label="{name}" title="{name}"></span>'
        )

    return re.sub(r'<img\s+id="(\w+)"\s*/>', replace_icon, text)

def exportGroupOrResource(obj, img_export_dir):
    """Exports a Group or Resource data asset (both share the same Name/Description/Icon/Colour shape).

    Returns None when the role has no Group/Resource set, since both are optional.
    """
    if not obj:
        return None

    icon_tex = obj.get_editor_property("Icon")
    icon_filename = exportImage(icon_tex, img_export_dir, "default_image.png")

    return {
        "id": obj.get_name(),
        "name": str(obj.get_editor_property("Name")),
        "description": str(obj.get_editor_property("Description")),
        "color": linearColorToHex(obj.get_editor_property("Colour")),
        "iconUrl": f"/images/roles/{icon_filename.replace('.png', '.webp')}",
    }

def exportAbility(ability_asset, ability_img_export_dir, keywords_dir):
    """Exports a single Ability data asset to a plain dict, including its icon.

    NOTE: "Ability Type" and "Cost Type" are deliberately NOT read here.
    Reading either of those two enum properties reliably crashes the editor
    with an EXCEPTION_ACCESS_VIOLATION partway through a full export, despite
    extensive isolation testing showing the underlying data/asset is fine in
    isolation (see project history/chat log). Skipping them lets the rest of
    the export (including ability icons, name, description, cost value)
    complete successfully. Revisit once the root cause is found -- likely an
    Unreal Python plugin instability with Blueprint-enum reflection under
    sustained use, not a bug in this script or the data.
    """
    icon_tex = ability_asset.get_editor_property("Image")
    icon_filename = exportImage(icon_tex, ability_img_export_dir, "default_ability.png")

    name = str(ability_asset.get_editor_property("Name"))
    description = str(ability_asset.get_editor_property("Description"))
    cost_value = ability_asset.get_editor_property("Cost Value")

    return {
        "id": ability_asset.get_name(),
        "name": name,
        "description": description,
        "descriptionHtml": convertIcons(description, keywords_dir),
        "iconUrl": f"/images/abilities/{icon_filename.replace('.png', '.webp')}",
        "abilityType": None,
        "costType": None,
        "costValue": cost_value,
    }

KEYWORDS_TABLE_PATH = "/Game/Roles/Keywords/Keywords"

# Maps the "Capability" category on each Keywords DataTable row to the
# color used to render that keyword's icon/badge on the website. Keep in
# sync with src/data/classes.ts's CLASS_THEMES, which uses the same
# category names/colors for role classes.
CAPABILITY_COLORS = {
    "General": "#ffffff",
    "Elimination": "#883532",
    "Protection": "#5F90C4",
    "Manipulation": "#839C38",
    "Investigation": "#B38FC4",
}

def export_keywords():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)

    output_path = os.path.join(script_dir, "data", "keywords.json").replace("\\", "/")
    keywords_img_dir = os.path.join(root_dir, "public", "images", "keywords").replace("\\", "/")

    if not os.path.exists(keywords_img_dir):
        os.makedirs(keywords_img_dir)

    keywords_table = unreal.load_asset(KEYWORDS_TABLE_PATH)
    if not keywords_table:
        print(f"!! Could not load Keywords DataTable at {KEYWORDS_TABLE_PATH}, skipping keyword export")
        return

    # This engine build has no DataTable->JSON helper, and rows aren't plain
    # UObjects (no get_editor_property on the row itself). Instead, read each
    # column as a parallel array of strings via get_data_table_column_as_string
    # -- this also sidesteps the kind of enum-reflection crash seen with
    # Ability Type/Cost Type in exportAbility() above, since it never touches
    # the row struct's properties directly.
    row_names = unreal.DataTableFunctionLibrary.get_data_table_row_names(keywords_table)
    print(f"Found {len(row_names)} keyword rows. Starting export...")

    names_col = unreal.DataTableFunctionLibrary.get_data_table_column_as_string(keywords_table, "Name")
    description_col = unreal.DataTableFunctionLibrary.get_data_table_column_as_string(keywords_table, "Description")
    icon_col = unreal.DataTableFunctionLibrary.get_data_table_column_as_string(keywords_table, "Icon")
    capability_col = unreal.DataTableFunctionLibrary.get_data_table_column_as_string(keywords_table, "Capability")

    def parse_object_path(value):
        """Object-reference columns come back as a stringified UE object
        reference, e.g. "Texture2D'/Game/UI/Icons/Attack.Attack'" -- pull
        just the asset path out of that."""
        if not value:
            return None
        match = re.search(r"'([^']+)'", value)
        return match.group(1) if match else value

    def resolve_ftext_string(value):
        """FText columns (Name, Description) come back from
        get_data_table_column_as_string() as their raw localization source,
        e.g. NSLOCTEXT("[namespace]", "key", "Actual Text"), not the
        resolved display string -- pull out just the third (text) argument
        and unescape it."""
        if not value:
            return value
        match = re.match(r'^\s*NSLOCTEXT\(\s*"(?:[^"\\]|\\.)*"\s*,\s*"(?:[^"\\]|\\.)*"\s*,\s*"((?:[^"\\]|\\.)*)"\s*\)\s*$', value)
        if not match:
            return value
        text = match.group(1)
        return text.replace('\\"', '"').replace("\\'", "'").replace('\\n', '\n').replace('\\\\', '\\')

    json_data = []
    for i, row_name in enumerate(row_names):
        name = resolve_ftext_string(names_col[i]) if i < len(names_col) and names_col[i] else str(row_name)
        description = resolve_ftext_string(description_col[i]) if i < len(description_col) else ""
        capability = enumToStr(capability_col[i] if i < len(capability_col) else None)
        color = CAPABILITY_COLORS.get(capability, CAPABILITY_COLORS["General"])

        icon_filename = "default_image.png"
        icon_path = parse_object_path(icon_col[i] if i < len(icon_col) else None)
        if icon_path:
            icon_tex = unreal.load_asset(icon_path)
            if icon_tex:
                icon_filename = exportImage(icon_tex, keywords_img_dir, "default_image.png")
            else:
                print(f"    !! Keyword '{name}': could not load Icon at '{icon_path}'")

        json_data.append({
            "name": name,
            "color": color,
            "icon": icon_filename.replace(".png", ""),
            "description": description,
            "capability": capability or "General",
        })

    # Display order on the Keywords page groups by capability first (see
    # CAPABILITY_ORDER in src/pages/keywords.astro), then alphabetically
    # within each group.
    json_data = sorted(json_data, key=lambda k: k["name"])

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2)

    print(f"SUCCESS: Exported {len(json_data)} keywords!")

export_roles_from_sets()
export_keywords()
