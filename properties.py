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


def setStoneLength(self, context):
    scene = context.scene
    if scene.concave_machine.stone_pointer is None:
        return
    factor = scene.concave_machine.stone_length / scene.concave_machine.stone_pointer.dimensions[1]
    bpy.ops.transform.resize(value=(factor, factor, factor), orient_type='GLOBAL')
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return {'FINISHED'}


def setIndex(self, context):
    scene = context.scene
    if(scene.concave_machine.index > scene.concave_machine.index_gear):
        scene.concave_machine.index = scene.concave_machine.index % scene.concave_machine.index_gear;
    recalculateBatchIndices(self,context)
    setStoneAngles(self, context)


def setFacetAngle(self, context):
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
    stone_pointer: bpy.props.PointerProperty(name="Stone", type=bpy.types.Object)
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
