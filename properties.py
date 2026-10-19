import bpy
import math

from mathutils import Matrix, Vector


# -------------------------------------------------------------------
# Define the data structure for one row
# -------------------------------------------------------------------
class CutTableRow(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name")
    side: bpy.props.StringProperty(name="Side")
    facet_angle: bpy.props.FloatProperty(name="Facet angle", min=0, max=math.pi/2, subtype="ANGLE")
    batch_indices: bpy.props.StringProperty(name="Indices")
    comment: bpy.props.StringProperty(name="Comment")
    tool_pointer: bpy.props.PointerProperty(name="Tool", type=bpy.types.Object)
    stone_height: bpy.props.FloatProperty(name="Stone height", subtype="DISTANCE")
    stone_position: bpy.props.FloatProperty(name="Stone position", subtype="DISTANCE")
    mandrel_position: bpy.props.FloatProperty(name="Mandrel position", subtype="DISTANCE")
    mandrel_rotation: bpy.props.FloatProperty(name="Mandrel rotation", default=0, min=-math.pi/2, max=math.pi/2, subtype="ANGLE")
    disable: bpy.props.BoolProperty(name="Disable", default=False)


# Machine settings that are remembered per stone (Object.raycarve_settings)
# and restored when switching stones.
STONE_SETTINGS = ('stone_length', 'mandrel_pointer', 'index_gear', 'faceting_side', 'index',
                  'facet_angle', 'stone_height', 'stone_position', 'mandrel_position',
                  'mandrel_rotation', 'symmetry', 'mirror')


class StoneSettings(bpy.types.PropertyGroup):
    is_stone: bpy.props.BoolProperty(default=False)
    saved: bpy.props.BoolProperty(default=False)
    stone_length: bpy.props.FloatProperty(default=20.0)
    mandrel_pointer: bpy.props.PointerProperty(type=bpy.types.Object)
    index_gear: bpy.props.IntProperty(default=96)
    faceting_side: bpy.props.StringProperty(default='Side_Pavillion')
    index: bpy.props.IntProperty()
    facet_angle: bpy.props.FloatProperty()
    stone_height: bpy.props.FloatProperty()
    stone_position: bpy.props.FloatProperty()
    mandrel_position: bpy.props.FloatProperty()
    mandrel_rotation: bpy.props.FloatProperty()
    symmetry: bpy.props.IntProperty(default=1)
    mirror: bpy.props.IntProperty()


# While settings are restored, the update callbacks must not move, rescale or
# re-cut anything.
_restoring = False


def copyCutTable(src, dst):
    """Append all rows of the cut table collection src to dst."""
    for row in src:
        new_row = dst.add()
        for key, prop in row.bl_rna.properties.items():
            if key != 'rna_type' and not prop.is_readonly:
                setattr(new_row, key, getattr(row, key))


def saveStoneSettings(cm, stone):
    settings = stone.raycarve_settings
    for key in STONE_SETTINGS:
        setattr(settings, key, getattr(cm, key))
    settings.saved = True


def restoreStoneSettings(context, stone):
    global _restoring
    cm = context.scene.concave_machine
    _restoring = True
    try:
        for key in STONE_SETTINGS:
            setattr(cm, key, getattr(stone.raycarve_settings, key))
    finally:
        _restoring = False
    recalculateBatchIndices(None, context)
    if cm.mandrel_pointer is not None:
        setStoneAngles(None, context)


def showOnlyStone(context, stone):
    """Hide all other RayCarve stones so only the active one is visible."""
    for obj in context.view_layer.objects:
        if obj.raycarve_settings.is_stone:
            try:
                obj.hide_set(obj != stone)
            except RuntimeError:
                pass


def onStoneChanged(self, context):
    """Switching stones: remember the old stone's settings, restore the new one's."""
    cm = context.scene.concave_machine
    stone = cm.stone_pointer
    if stone == cm.active_stone:
        return
    if cm.active_stone is not None:
        saveStoneSettings(cm, cm.active_stone)
    cm.active_stone = stone
    if stone is None:
        return
    stone.raycarve_settings.is_stone = True
    if stone.raycarve_settings.saved:
        restoreStoneSettings(context, stone)
    showOnlyStone(context, stone)


def setStoneLength(self, context):
    scene = context.scene
    if _restoring or scene.concave_machine.stone_pointer is None:
        return
    factor = scene.concave_machine.stone_length / scene.concave_machine.stone_pointer.dimensions[1]
    bpy.ops.transform.resize(value=(factor, factor, factor), orient_type='GLOBAL')
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return {'FINISHED'}


def setIndex(self, context):
    if _restoring:
        return
    scene = context.scene
    if(scene.concave_machine.index > scene.concave_machine.index_gear):
        scene.concave_machine.index = scene.concave_machine.index % scene.concave_machine.index_gear;
    recalculateBatchIndices(self,context)
    setStoneAngles(self, context)


def setFacetAngle(self, context):
    if _restoring:
        return
    setStoneAngles(self, context)


def setStoneAngles(self, context):
    scene = context.scene
    if scene.concave_machine.faceting_side == 'Side_Pavillion':
        scene.concave_machine.stone_pointer.rotation_euler[0] = 0
    else:
        scene.concave_machine.stone_pointer.rotation_euler[0] = math.pi

    T_localY = Matrix.Translation(Vector((scene.concave_machine.stone_position, scene.concave_machine.mandrel_position, -scene.concave_machine.stone_height)))
    R_localY = Matrix.Rotation(scene.concave_machine.facet_angle, 4, 'Y')
    R_globalZ = Matrix.Rotation(-2 * math.pi / scene.concave_machine.index_gear * scene.concave_machine.index, 4, 'Z')
    R_localZ = Matrix.Rotation(scene.concave_machine.mandrel_rotation, 4, 'Z')

    # --- Combine: world = globalZ * localY_rotation * localY_translation * localZ_rotation ---
    M_world = R_globalZ @ R_localY @ T_localY @ R_localZ

    scene.concave_machine.mandrel_pointer.matrix_world = M_world


def getSymmetryIndices(start, gears, symmetry):
    step = gears/symmetry
    indices = []
    for x in range(symmetry):
        indices.append(round((start+step*x)%gears))
    indices.sort()
    return indices


def calcMirrorIndices(initIndices, gears, mirror):
    indices = []
    for x in initIndices:
        indices.append((x-mirror)%gears)
        indices.append((x+mirror)%gears)
    indices = list(set(indices))
    indices.sort()
    return indices


def getBatchIndicesString(indicesArray, gears):
    batchIndices = ""
    for x in indicesArray:
        if x == 0:
            batchIndices += f"-{gears}"
        else:
            batchIndices += f"-{x}"
    if batchIndices.endswith("-"): batchIndices = batchIndices[:-1]
    if batchIndices.startswith("-"): batchIndices = batchIndices[1:]
    return batchIndices.strip()


def recalculateBatchIndices(self, context):
    if _restoring:
        return
    scene = context.scene
    res_indices = []
    index = scene.concave_machine.index
    gears = scene.concave_machine.index_gear
    symmetry = scene.concave_machine.symmetry
    mirror = scene.concave_machine.mirror

    res_indices = getSymmetryIndices(index, gears, symmetry)
    if mirror > 0:
        res_indices = calcMirrorIndices(res_indices, gears, mirror)
    scene.concave_machine.batch_indices = getBatchIndicesString(res_indices, gears)


class ConcaveMachineAddonProperties(bpy.types.PropertyGroup):
    stone_length: bpy.props.FloatProperty(name="Stone Length", default=20.0, min=1, subtype="DISTANCE", update=setStoneLength, precision=4)
    mandrel_resolution: bpy.props.IntProperty(name="Mandrel Resolution", default=512, min=3, soft_max=1024)
    mandrel_diameter: bpy.props.FloatProperty(name="Mandrel Diameter", default=8, subtype="DISTANCE", precision=4)
    v_mandrel_angle: bpy.props.FloatProperty(name="V-Mandrel Angle", default=math.pi/2, min=0, max=math.pi/2, subtype="ANGLE", precision=4)
    v_mandrel_diameter: bpy.props.FloatProperty(name="V-Mandrel Diameter", default=25, subtype="DISTANCE", precision=4)
    v_mandrel_width: bpy.props.FloatProperty(name="V-Mandrel Width", default=6.3, subtype="DISTANCE", precision=4)
    v_mandrel_bevel_offset: bpy.props.FloatProperty(name="V-Mandrel Bevel Offset", default=0.02, min=0.001, max=1.0, subtype="DISTANCE", precision=4)
    v_mandrel_bevel_segments: bpy.props.IntProperty(name="V-Mandrel Bevel Segments", default=6, min=1)
    stone_pointer: bpy.props.PointerProperty(name="Stone", type=bpy.types.Object, update=onStoneChanged)
    # The stone whose settings are currently loaded (to detect stone switches)
    active_stone: bpy.props.PointerProperty(type=bpy.types.Object)
    stone_height: bpy.props.FloatProperty(name="Stone height", subtype="DISTANCE", update=setIndex, precision=4)
    stone_position: bpy.props.FloatProperty(name="Stone position", subtype="DISTANCE", update=setIndex, precision=4)
    mandrel_pointer: bpy.props.PointerProperty(name="Mandrel", type=bpy.types.Object)
    mandrel_position: bpy.props.FloatProperty(name="Mandrel position", subtype="DISTANCE", update=setIndex, precision=4)
    mandrel_rotation: bpy.props.FloatProperty(name="Mandrel rotation", default=0, min=-math.pi/2, max=math.pi/2, subtype="ANGLE", update=setIndex, precision=4)
    index_gear: bpy.props.IntProperty(name="Index gear", default=96, min=1, max=360, update=setIndex)
    faceting_side: bpy.props.EnumProperty( name="Faceting side", description="Side", items=[('Side_Pavillion', "Pavillion", "The Pavillion"),('Side_Crown', "Crown", "The Crown"), ], default='Side_Pavillion', update=setIndex)
    index: bpy.props.IntProperty(name="Index", min=0, update=setIndex)
    facet_angle: bpy.props.FloatProperty(name="Facet angle", min=0, max=math.pi/2, update=setFacetAngle, subtype="ANGLE", precision=4)
    batch_indices: bpy.props.StringProperty(name="Row Indices")
    sync_enabled: bpy.props.BoolProperty(name="Auto. sync. enabled", default=False)
    sync_status: bpy.props.StringProperty(name="Sync. Status", default="Ok")
    symmetry: bpy.props.IntProperty(name="Symmetry", default=1, min=1, subtype="UNSIGNED", update=recalculateBatchIndices)
    mirror: bpy.props.IntProperty(name="Mirror", default=0, min=0, subtype="UNSIGNED", update=recalculateBatchIndices)
