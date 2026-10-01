import bpy
import bmesh


def ensureObjectMode():
    # bpy.ops.object.mode_set() needs an active object in its poll(), even when
    # we're already in Object Mode. Only call it when a switch is actually needed.
    active = bpy.context.view_layer.objects.active
    if active is not None and active.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')


def meshHasNonManifold(obj):
    # A plain bmesh edge.is_manifold check only catches edges shared by != 2
    # faces. It misses boundary loops, non-contiguous normals, wire edges and
    # non-manifold vertices - all of which also make the boolean modifier's
    # MANIFOLD solver fail. Reuse Blender's own "Select Non-Manifold" logic
    # (Edit Mode > Select > All by Trait > Non-Manifold) for a reliable check.
    view_layer = bpy.context.view_layer
    prev_active = view_layer.objects.active
    prev_selected = [o for o in bpy.context.selected_objects]
    was_hidden = obj.hide_get()
    if was_hidden:
        obj.hide_set(False)

    ensureObjectMode()
    bpy.ops.object.select_all(action='DESELECT')
    view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_non_manifold(
        extend=False,
        use_wire=True,
        use_boundary=True,
        use_multi_face=True,
        use_non_contiguous=True,
        use_verts=True,
    )

    bm = bmesh.from_edit_mesh(obj.data)
    has_non_manifold = (
        any(v.select for v in bm.verts)
        or any(e.select for e in bm.edges)
        or any(f.select for f in bm.faces)
    )

    bpy.ops.object.mode_set(mode='OBJECT')
    if was_hidden:
        obj.hide_set(True)
    bpy.ops.object.select_all(action='DESELECT')
    for o in prev_selected:
        try:
            o.select_set(True)
        except ReferenceError:
            pass
    try:
        view_layer.objects.active = prev_active
    except ReferenceError:
        view_layer.objects.active = obj

    return has_non_manifold


def recalculateNormalsByPointer(pointer):
    ensureObjectMode()
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = pointer
    pointer.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')


def recalculateStoneAndMandrelNormals(context):
    scene = context.scene
    mandrelHide = scene.concave_machine.mandrel_pointer.hide_get();
    scene.concave_machine.mandrel_pointer.hide_set(False)
    recalculateNormalsByPointer(scene.concave_machine.mandrel_pointer)
    recalculateNormalsByPointer(scene.concave_machine.stone_pointer)
    scene.concave_machine.mandrel_pointer.hide_set(mandrelHide)
    return {'FINISHED'}


def cleanMesh(context):
    scene = context.scene
    pointer = scene.concave_machine.stone_pointer
    ensureObjectMode()
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = pointer
    pointer.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles()
    bpy.ops.object.mode_set(mode='OBJECT')
    return {'FINISHED'}
