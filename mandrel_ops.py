import bpy
import math
import bmesh


# Function to calculate equilateral triangle vertices
def equilateral_triangle_edges(theta_rad, width, mandrelDiameter):
    mandrelRadius = mandrelDiameter/2
    hc = width/2
    triangleHeight = hc * math.tan((math.pi-theta_rad)/2)
    vertex_A = [0, -hc, mandrelRadius - triangleHeight]
    vertex_B = [0, 0, mandrelRadius]
    vertex_C = [0, hc, mandrelRadius - triangleHeight]
    return vertex_A, vertex_B, vertex_C


def selectUppmostEdge(obj):
    # Switch to Edit Mode if not already
    if bpy.context.object.mode != 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')

    # Get BMesh
    mesh = bmesh.from_edit_mesh(obj.data)

    upmost_edge = None
    upmost_z = float('-inf')

    # Iterate over all edges
    for edge in mesh.edges:
        # Only consider visible edges (not hidden ones)
        if not edge.hide:
            v1, v2 = edge.verts
            avg_z = (v1.co.z + v2.co.z) / 2
            if avg_z > upmost_z:
                upmost_z = avg_z
                upmost_edge = edge

    # Deselect all edges first
    for edge in mesh.edges:
        edge.select_set(False)

    # Select the upmost edge
    if upmost_edge:
        upmost_edge.select_set(True)
        bmesh.update_edit_mesh(obj.data)


def selectUppmostVertex(obj):
    # Switch to Edit Mode if not already
    if bpy.context.object.mode != 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')

    # Get BMesh
    mesh = bmesh.from_edit_mesh(obj.data)

    upmost_vert = None
    upmost_z = float('-inf')

    # Iterate over all vert
    for vert in mesh.verts:
        # Only consider visible vert (not hidden ones)
        if not vert.hide:
            if vert.co.z > upmost_z:
                upmost_z = vert.co.z
                upmost_vert = vert

    # Deselect all edges first
    for face in mesh.faces:
        face.select_set(False)

    # Deselect all edges first
    for edge in mesh.edges:
        edge.select_set(False)

    # Deselect all verts first
    for vert in mesh.verts:
        vert.select_set(False)

    # Select the upmost vert
    if upmost_vert:
        upmost_vert.select_set(True)
        bmesh.update_edit_mesh(obj.data)


def createBevelForVMandrel(obj):
    scene = bpy.context.scene
    selectUppmostEdge(obj)
    bpy.ops.mesh.bevel(offset=scene.concave_machine.v_mandrel_bevel_offset, offset_pct=0, segments=scene.concave_machine.v_mandrel_bevel_segments, affect='EDGES')


def createBevelForVMandrelRound(obj):
    scene = bpy.context.scene
    selectUppmostVertex(obj)
    bpy.ops.mesh.bevel(offset=scene.concave_machine.v_mandrel_bevel_offset, offset_pct=0, segments=scene.concave_machine.v_mandrel_bevel_segments, affect='VERTICES')


class CreateMandrel(bpy.types.Operator):
    """Create Mandrel"""
    bl_idname = "object.create_mandrel"
    bl_label = "Create Round Mandrel"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        radius = scene.concave_machine.mandrel_diameter / 2.0
        bpy.ops.mesh.primitive_cylinder_add(vertices=scene.concave_machine.mandrel_resolution,  radius=radius, depth=100, enter_editmode=False, location=(0, 0, 0))
        bpy.ops.transform.rotate(value=math.pi/2, orient_axis='X', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, True, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        obj = bpy.context.object
        obj.name = "RoundMandrel"
        scene.concave_machine.mandrel_pointer = obj
        return {'FINISHED'}


class CreateVMandrelSlot(bpy.types.Operator):
    """Create V Mandrel Slot"""
    bl_idname = "object.create_v_mandrel_slot"
    bl_label = "Create V-Mandrel Slot"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        bpy.ops.object.select_all(action='DESELECT')
        # Input length of the mandrel
        length = 100.0
        # Calculate triangle vertices
        vertex_A, vertex_B, vertex_C = equilateral_triangle_edges(scene.concave_machine.v_mandrel_angle, scene.concave_machine.v_mandrel_width, scene.concave_machine.v_mandrel_diameter)
        halfLength = length/2
        vertex_A[0] = -halfLength
        vertex_B[0] = -halfLength
        vertex_C[0] = -halfLength

        # Create a mesh
        mesh = bpy.data.meshes.new("VMandrel")
        obj = bpy.data.objects.new("VMandrel", mesh)
        bpy.context.collection.objects.link(obj)
        # Define vertices and edges
        vertex_D = (-halfLength, vertex_A[1], 0)
        vertex_E = (-halfLength, vertex_C[1], 0)
        mesh.from_pydata([vertex_A, vertex_B, vertex_C, vertex_D, vertex_E], [], [(0, 1, 2), (0, 2, 4, 3)])
        # Update mesh
        mesh.update()
        # Select the object
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        # Extrude the face by length meters
        bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value":(length, 0, 0)})
        # Fix normals
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent(inside=False)

        createBevelForVMandrel(obj)

        # Switch back to Object mode
        bpy.ops.object.mode_set(mode='OBJECT')
        scene.concave_machine.mandrel_pointer = obj
        return {'FINISHED'}


class CreateVMandrelRound(bpy.types.Operator):
    """Create V Mandrel Round"""
    bl_idname = "object.create_v_mandrel_round"
    bl_label = "Create V-Mandrel Round"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        bpy.ops.object.select_all(action='DESELECT')
        # Calculate triangle vertices
        vertex_A, vertex_B, vertex_C = equilateral_triangle_edges(scene.concave_machine.v_mandrel_angle, scene.concave_machine.v_mandrel_width, scene.concave_machine.v_mandrel_diameter)


        # Create a mesh
        mesh = bpy.data.meshes.new("VMandrelR")
        obj = bpy.data.objects.new("VMandrelR", mesh)
        bpy.context.collection.objects.link(obj)
        # Define vertices and edges
        vertex_D = (0, vertex_A[1], 0)
        vertex_E = (0, vertex_C[1], 0)
        mesh.from_pydata([vertex_A, vertex_B, vertex_C, vertex_D, vertex_E], [], [(0, 1, 2), (0, 2, 4, 3)])
        # Update mesh
        mesh.update()
        # Select the object
        bpy.context.view_layer.objects.active = obj
        createBevelForVMandrelRound(obj)
        bpy.ops.mesh.select_all(action='SELECT')
        screwModifier = obj.modifiers.new('screwModifier','SCREW')
        screwModifier.axis = 'Y'
        screwModifier.steps = scene.concave_machine.mandrel_resolution
        screwModifier.render_steps = scene.concave_machine.mandrel_resolution

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.modifier_apply(modifier="screwModifier")

        # Fix normals
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_interior_faces()
        bpy.ops.mesh.delete(type='FACE')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        bpy.ops.mesh.delete_loose()

        # Switch back to Object mode
        bpy.ops.object.mode_set(mode='OBJECT')
        scene.concave_machine.mandrel_pointer = obj
        return {'FINISHED'}
