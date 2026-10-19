import bpy
import math

from .utils import ADDON_VERSION
from .properties import setIndex, copyCutTable, saveStoneSettings
from .mesh_utils import meshHasNonManifold, cleanMesh, recalculateStoneAndMandrelNormals, ensureObjectMode


# -------------------------------------------------------------------
# Operator to add a new row
# -------------------------------------------------------------------
class FACET_OT_AddRow(bpy.types.Operator):
    bl_idname = "raycarve.add_row"
    bl_label = "Add Row"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene.concave_machine.stone_pointer is not None

    def execute(self, context):
        context.scene.concave_machine.stone_pointer.raycarve_cut_table.add()
        return {'FINISHED'}


# -------------------------------------------------------------------
# Operator to remove selected row
# -------------------------------------------------------------------
class FACET_OT_RemoveRow(bpy.types.Operator):
    bl_idname = "raycarve.remove_row"
    bl_label = "Remove Row"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene.concave_machine.stone_pointer is not None

    def execute(self, context):
        stone = context.scene.concave_machine.stone_pointer
        table = stone.raycarve_cut_table
        index = stone.raycarve_cut_table_index

        if len(table) > 0:
            table.remove(index)
            stone.raycarve_cut_table_index = min(max(0, index - 1), len(table) - 1)

        return {'FINISHED'}


# -------------------------------------------------------------------
# Operator to redo the cutting
# -------------------------------------------------------------------
class FACET_OT_RedoCutting(bpy.types.Operator):
    bl_idname = "raycarve.redo_cutting"
    bl_label = "Redo cutting"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene.concave_machine.stone_pointer is not None

    def execute(self, context):
        scene = context.scene
        clearLog()
        object_name = scene.concave_machine.stone_pointer.name
        backup_object_name = object_name + "_bak"
        bak_obj = bpy.data.objects.get(backup_object_name)
        if not bak_obj:
            self.report({'ERROR'}, "Cannot redo cutting: no backup is available")
            return {'CANCELLED'}
        old_stone = scene.concave_machine.stone_pointer
        # Leave Edit Mode etc. before deleting the (possibly active) stone.
        ensureObjectMode()
        # Put the restored stone back where the old one lived. Don't use
        # bpy.data.collections[0]: it may be the hidden backup collection or
        # one not linked to this scene, which breaks later mode switches.
        target_collections = [c for c in old_stone.users_collection
                              if c.name not in (BACKUP_COLLECTION, LEGACY_BACKUP_COLLECTION)] or [scene.collection]
        obj_copy = bak_obj.copy()
        obj_copy.data = bak_obj.data.copy()
        # The backup holds an outdated cut table and settings: take both over
        # from the stone that is about to be replaced.
        obj_copy.raycarve_cut_table.clear()
        copyCutTable(old_stone.raycarve_cut_table, obj_copy.raycarve_cut_table)
        obj_copy.raycarve_cut_table_index = old_stone.raycarve_cut_table_index
        saveStoneSettings(scene.concave_machine, obj_copy)
        obj_copy.raycarve_settings.is_stone = True
        bpy.data.objects.remove(old_stone, do_unlink=True)
        obj_copy.name = object_name
        for coll in target_collections:
            coll.objects.link(obj_copy)
        obj_copy.hide_set(False)
        # The deleted stone was usually the active object; without a new one
        # bpy.ops.object.mode_set() fails with "Context missing active object".
        for o in context.selected_objects:
            o.select_set(False)
        context.view_layer.objects.active = obj_copy
        obj_copy.select_set(True)
        scene.concave_machine.stone_pointer = obj_copy

        for cutRow in obj_copy.raycarve_cut_table:
            if cutRow.disable:
                continue
            if cutRow.side == 'P':
                scene.concave_machine.faceting_side = 'Side_Pavillion'
            else:
                scene.concave_machine.faceting_side = 'Side_Crown'
            scene.concave_machine.facet_angle = cutRow.facet_angle
            scene.concave_machine.mandrel_pointer = cutRow.tool_pointer
            scene.concave_machine.stone_height = cutRow.stone_height
            scene.concave_machine.stone_position = cutRow.stone_position
            scene.concave_machine.mandrel_position = cutRow.mandrel_position
            scene.concave_machine.mandrel_rotation = cutRow.mandrel_rotation
            setIndex(self, context)
            scene.concave_machine.batch_indices = cutRow.batch_indices
            executeRowCut(self, context)

        return {'FINISHED'}


def executeBoolean(self, context):
        scene = context.scene
        old_modifier = scene.concave_machine.stone_pointer.modifiers.get('ConcaveBoolean')
        if old_modifier is not None:
            return {'FINISHED'}

        stone = scene.concave_machine.stone_pointer
        if meshHasNonManifold(stone):
            if self is not None:
                self.report({'WARNING'}, "Stone mesh is non-manifold. Attempting auto-fix...")
            cleanMesh(context)
            recalculateStoneAndMandrelNormals(context)
            if meshHasNonManifold(stone) and self is not None:
                self.report({'WARNING'}, "Stone mesh still non-manifold after auto-fix; boolean may fail.")

        boolean_mod = stone.modifiers.new('ConcaveBoolean', 'BOOLEAN')
        boolean_mod.object = scene.concave_machine.mandrel_pointer
        boolean_mod.operation = 'DIFFERENCE'
        boolean_mod.solver = 'MANIFOLD'
        boolean_mod.use_self = True
        scene.concave_machine.mandrel_pointer.hide_set(True)
        return {'FINISHED'}


class ConcaveBoolean(bpy.types.Operator):
    """Concave Boolean"""
    bl_idname = "object.concave_boolean"
    bl_label = "Carve"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        cm = context.scene.concave_machine
        return cm.stone_pointer is not None and cm.mandrel_pointer is not None

    def execute(self, context):
        return executeBoolean(self, context)


class CancelConcaveBoolean(bpy.types.Operator):
    """Cancel Concave Boolean"""
    bl_idname = "object.cancel_concave_boolean"
    bl_label = "Cancel"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        cm = context.scene.concave_machine
        return cm.stone_pointer is not None and cm.mandrel_pointer is not None

    def execute(self, context):
        scene = context.scene
        modifier = scene.concave_machine.stone_pointer.modifiers.get('ConcaveBoolean')
        if modifier is not None:
            scene.concave_machine.stone_pointer.modifiers.remove(modifier)
            scene.concave_machine.mandrel_pointer.hide_set(False)
        return {'FINISHED'}


def executeApply(self, context):
    scene = context.scene
    bpy.ops.object.select_all(action='DESELECT')
    scene.concave_machine.stone_pointer.select_set(True)
    bpy.context.view_layer.objects.active = scene.concave_machine.stone_pointer
    result = bpy.ops.object.modifier_apply(modifier='ConcaveBoolean')
    if 'CANCELLED' in result and self is not None:
        self.report({'ERROR'}, "Boolean apply failed (non-manifold mesh). Use 'Fix Boolean'/'Fix Mesh' and retry.")
        return {'CANCELLED'}

    scene.concave_machine.mandrel_pointer.hide_set(False)
    recalculateStoneAndMandrelNormals(context)
    return {'FINISHED'}


def logName(scene):
    """Name of the cut log text block of the current stone, e.g. 'Stone_concaveLog.txt'."""
    stone = scene.concave_machine.stone_pointer
    if stone is None:
        return 'concaveLog.txt'
    return f"{stone.name}_concaveLog.txt"


def clearLog():
    text = bpy.data.texts.get(logName(bpy.context.scene))
    if text is not None:
        text.clear()


def clearCutTable():
    stone = bpy.context.scene.concave_machine.stone_pointer
    if stone is not None:
        stone.raycarve_cut_table.clear()
        stone.raycarve_cut_table_index = 0
    return {'FINISHED'}


def writeLog(scene, isSingleIndex):
    name = logName(scene)
    text = bpy.data.texts.get(name)
    if text is None:
        text = bpy.data.texts.new(name)

    writeLogHeader(scene, text)

    if scene.concave_machine.faceting_side == 'Side_Pavillion':
        text.write(f"\nSide: Pavillion\n")
    else:
        text.write(f"\nSide: Crown\n")

    if isSingleIndex:
        index = scene.concave_machine.index % scene.concave_machine.index_gear
        if index == 0:
            index = scene.concave_machine.index_gear
        text.write(f"Index: {index}\n")
    else:
        text.write(f"Index: {scene.concave_machine.batch_indices}\n")
    text.write(f"Facet Angle: {math.degrees(scene.concave_machine.facet_angle):.2f}°\n")
    text.write(f"Stone Height: {scene.concave_machine.stone_height:.5f}\n")
    text.write(f"Stone Position: {scene.concave_machine.stone_position:.2f}\n")
    text.write(f"Mandrel Position: {scene.concave_machine.mandrel_position:.2f}\n")
    text.write(f"Mandrel Rotation: {math.degrees(scene.concave_machine.mandrel_rotation):.2f}\n")


def writeLogHeader(scene, text):
    text_content = "".join([line.body for line in text.lines])
    if text_content.strip() == "":
        text.write("\n----------------------------------------------------------\n\n")
        text.write(f"RayCarve Version: {ADDON_VERSION} - Facettierer Gilde Schweiz\n")
        text.write("\n----------------------------------------------------------\n\n")
        text.write(f"Stone Name: {scene.concave_machine.stone_pointer.name}\n")
        text.write(f"Stone Size: Width: {scene.concave_machine.stone_pointer.dimensions.x:.2f}, Length: {scene.concave_machine.stone_pointer.dimensions.y:.2f}, Height: {scene.concave_machine.stone_pointer.dimensions.z:.2f}\n")
        text.write(f"Mandrel Name: {scene.concave_machine.mandrel_pointer.name}\n")
        text.write(f"Mandrel Size: {scene.concave_machine.mandrel_pointer.dimensions}\n")
        text.write(f"Index Gear: {scene.concave_machine.index_gear}\n")
        text.write("\n----------------------------------------------------------\n\n")


class ConcaveApply(bpy.types.Operator):
    """Concave Apply"""
    bl_idname = "object.concave_apply"
    bl_label = "Apply"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        cm = context.scene.concave_machine
        return (cm.stone_pointer is not None and cm.mandrel_pointer is not None
                and cm.stone_pointer.modifiers.get('ConcaveBoolean') is not None)

    def execute(self, context):
        scene = context.scene
        addCutTableRow(scene, True)
        backupStone(scene)
        writeLog(scene, True)
        return executeApply(self, context)


class HideMandrel(bpy.types.Operator):
    bl_idname = "object.hide_mandrel"
    bl_label = "Hide Mandrel"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene.concave_machine.mandrel_pointer is not None

    def execute(self, context):
        scene = context.scene
        scene.concave_machine.mandrel_pointer.hide_set(True)
        return {'FINISHED'}


class ShowMandrel(bpy.types.Operator):
    bl_idname = "object.show_mandrel"
    bl_label = "Show Mandrel"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene.concave_machine.mandrel_pointer is not None

    def execute(self, context):
        scene = context.scene
        scene.concave_machine.mandrel_pointer.hide_set(False)
        return {'FINISHED'}


def executeRowCut(self, context):
    scene = context.scene
    indices = scene.concave_machine.batch_indices.split('-')
    writeLog(scene, False)
    for index in indices:
        scene.concave_machine.index = int(index)
        executeBoolean(self, context)
        executeApply(self, context)


class ConcaveBatch(bpy.types.Operator):
    """Concave Batch"""
    bl_idname = "object.concave_batch"
    bl_label = "Carve all"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        cm = context.scene.concave_machine
        return cm.stone_pointer is not None and cm.mandrel_pointer is not None

    def execute(self, context):
        scene = context.scene
        addCutTableRow(scene, False)
        backupStone(scene)
        executeRowCut(self, context)
        return {'FINISHED'}


BACKUP_COLLECTION = "rayCarveBackup"
LEGACY_BACKUP_COLLECTION = "rayFacetBackup"  # name used before the rename to RayCarve


def getBackupCollection(scene):
    collection = bpy.data.collections.get(BACKUP_COLLECTION)
    if collection is None:
        # Files saved with RayFacet: rename the old backup collection so its
        # "_bak" stones keep working for Redo cutting.
        collection = bpy.data.collections.get(LEGACY_BACKUP_COLLECTION)
        if collection is not None:
            collection.name = BACKUP_COLLECTION
    if collection is None:
        collection = bpy.data.collections.new(BACKUP_COLLECTION)
        scene.collection.children.link(collection)
    return collection


def backupStone(scene):
    object_name = scene.concave_machine.stone_pointer.name + "_bak";
    obj = bpy.data.objects.get(object_name)
    collection = getBackupCollection(scene)


    if obj and (object_name in collection.objects):
        return  {'FINISHED'}
    obj_copy = scene.concave_machine.stone_pointer.copy()
    obj_copy.data = scene.concave_machine.stone_pointer.data.copy()
    obj_copy.modifiers.clear()
    # The backup is not a stone of its own: no cut table, never shown on switch.
    obj_copy.raycarve_cut_table.clear()
    obj_copy.raycarve_settings.is_stone = False
    obj_copy.name = object_name
    collection.objects.link(obj_copy)
    collection.hide_viewport = True
    return  {'FINISHED'}


def addCutTableRow(scene, isSingleIndex):
    cutRow = scene.concave_machine.stone_pointer.raycarve_cut_table.add()

    if scene.concave_machine.faceting_side == 'Side_Pavillion':
        cutRow.side = 'P'
    else:
        cutRow.side = 'C'

    if isSingleIndex:
        cutRow.batch_indices = f"{scene.concave_machine.index}"
    else:
        cutRow.batch_indices = scene.concave_machine.batch_indices
    cutRow.facet_angle = scene.concave_machine.facet_angle
    cutRow.comment = ""
    cutRow.tool_pointer = scene.concave_machine.mandrel_pointer
    cutRow.stone_height = scene.concave_machine.stone_height
    cutRow.stone_position = scene.concave_machine.stone_position
    cutRow.mandrel_position = scene.concave_machine.mandrel_position
    cutRow.mandrel_rotation = scene.concave_machine.mandrel_rotation


class RecalculateOutsideNormals(bpy.types.Operator):
    """Recalculate outside Normals"""
    bl_idname = "object.recalculate_normals"
    bl_label = "Fix Boolean"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        cm = context.scene.concave_machine
        return cm.stone_pointer is not None and cm.mandrel_pointer is not None

    def execute(self, context):
        return recalculateStoneAndMandrelNormals(context)


class CleanMesh(bpy.types.Operator):
    """Mesh Merge by distance"""
    bl_idname = "object.merge_by_distance"
    bl_label = "Fix Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene.concave_machine.stone_pointer is not None

    def execute(self, context):
        return cleanMesh(context)


def save_text_file():
    # Cut log of the current stone
    text = bpy.data.texts.get(logName(bpy.context.scene))
    if text:
        # Set it as active in a text editor area
        text_area = bpy.context.screen.areas[0]
        oldType = text_area.type
        text_area.type = 'TEXT_EDITOR'

        text_area.spaces.active.text = text
        # Override context to invoke from text editor
        with bpy.context.temp_override(area=text_area, region=text_area.regions[-1]):
            bpy.ops.text.save_as('INVOKE_DEFAULT', check_existing=True)
        bpy.context.screen.areas[0].type = oldType


class SaveCutLog(bpy.types.Operator):
    """Save Cut Log"""
    bl_idname = "object.save_cut_log"
    bl_label = "Save cut instructions"

    def execute(self, context):
        save_text_file()
        return {'FINISHED'}
