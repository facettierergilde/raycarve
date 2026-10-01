import bpy
import os
import tempfile
import logging
import requests

from bpy.app.handlers import persistent

# Config
SERVER_URL = "http://localhost:3000/upload"

last_state = {}
filepath = ""
filedescriptor = None

log = logging.getLogger(__name__)


def export_and_send(context, ignore_state):
    global last_state
    global filepath
    scene = context.scene
    obj = scene.concave_machine.stone_pointer
    if obj is None:
        return
    state = get_obj_state(bpy.context)
    if last_state != state or ignore_state:
        last_state = state
        if obj.type == 'MESH':
            # Create a temporary copy of the object to export
            # This ensures we don't modify the original
            temp_obj = obj.copy()
            temp_obj.data = obj.data.copy()

            # Link to the scene temporarily
            bpy.context.collection.objects.link(temp_obj)

            temp_obj.select_set(True)

            # Create context override for the export operation
            # This tells Blender which object to export without selecting it
            with bpy.context.temp_override(
                selected_editable_objects=[temp_obj],
                active_object=temp_obj
            ):
                # Export to STL
                bpy.ops.wm.stl_export(
                    filepath=filepath,
                    export_selected_objects=True,
                    ascii_format=False,
                    apply_modifiers=True,
                    up_axis="Y",
                    forward_axis="X"
                )

            try:
                log.info(f"Exported '{obj.name}' to {filepath}")

                with open(filepath, 'rb') as f:
                    try:
                        requests.post(
                            SERVER_URL,
                            files={'file': f},
                            data={'name': obj.name, 'rotX': obj.rotation_euler.x, 'rotY': obj.rotation_euler.y, 'rotZ': obj.rotation_euler.z, 'rot_euler': tuple(obj.rotation_euler), 'pos': tuple(obj.location)},
                            timeout=2,
                        )
                        scene.concave_machine.sync_status = "Ok"
                    except requests.RequestException as e:
                        scene.concave_machine.sync_status = "Syncronisation failed and therefore disabled!"
                        scene.concave_machine.sync_enabled = False
                        log.warning(f"Sync request failed: {e}")
            finally:
                # Clean up: remove the temporary object
                bpy.data.objects.remove(temp_obj, do_unlink=True)


def get_obj_state(context):
    scene = context.scene
    stone = scene.concave_machine.stone_pointer
    mandrel = scene.concave_machine.mandrel_pointer
    return {
        "stone": stone,
        "stone_rotation": tuple(stone.rotation_euler) if stone is not None else None,
        "stone_location": tuple(stone.location) if stone is not None else None,
        "stone_modifiers_count": len(stone.modifiers) if stone is not None else None,
        "mandrel": mandrel,
        "mandrel_rotation": tuple(mandrel.rotation_euler) if mandrel is not None else None,
        "mandrel_location": tuple(mandrel.location) if mandrel is not None else None,
        "index_gear": scene.concave_machine.index_gear,
        "side": scene.concave_machine.faceting_side,
        "index": scene.concave_machine.index,
        "facet_angle": scene.concave_machine.facet_angle,
        "indices": scene.concave_machine.batch_indices,
        "symmetry": scene.concave_machine.symmetry,
        "mirror": scene.concave_machine.mirror,
    }


@persistent
def modifier_update_handler(scene, depsgraph):
    if scene.concave_machine.stone_pointer is None or scene.concave_machine.sync_enabled == False:
        return {'FINISHED'}
    for update in depsgraph.updates:
        if (isinstance(update.id, bpy.types.Object) and
        update.is_updated_geometry and
        'ConcaveBoolean' in update.id.modifiers and
        update.id.name == scene.concave_machine.stone_pointer.name):
            export_and_send(bpy.context, False)


class SendDataToWebgl(bpy.types.Operator):
    """Sync to Web"""
    bl_idname = "object.send_data_to_webgl"
    bl_label = "Manual sync to web"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        scene.concave_machine.sync_status="Manual Sync..."
        export_and_send(context, True)
        return {'FINISHED'}


def register():
    global filepath
    global filedescriptor
    filedescriptor, filepath = tempfile.mkstemp(prefix="ConcaveMachine_", suffix=".stl")
    if modifier_update_handler not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(modifier_update_handler)


def unregister():
    global filepath
    global filedescriptor
    if modifier_update_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(modifier_update_handler)
    os.close(filedescriptor)
    os.unlink(filepath)
