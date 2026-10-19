import bpy
import math

import xml.etree.ElementTree as ET

from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty
from bpy.types import Operator

from .properties import setStoneLength
from .carve_ops import clearLog, clearCutTable


def set_blender_to_mm():
    scene = bpy.context.scene
    # Set unit system to Metric and length to millimeters
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.length_unit = 'MILLIMETERS'
    scene.unit_settings.scale_length = 0.001
    bpy.context.space_data.overlay.grid_scale = 0.001
    bpy.context.space_data.lens = 80


class Import_OT_stl_file(bpy.types.Operator, ImportHelper):
    """Import an STL File"""
    bl_idname = "object.import_stl_file"
    bl_label = "Import STL file as Stone"
    bl_options = {'REGISTER', 'UNDO'}


    use_mesh_validate: BoolProperty(
        name="Validate Mesh",
        description="Validate mesh for errors after import",
        default=False,
    )

    filter_glob: StringProperty(
        default="*.stl",
        options={'HIDDEN'},
        maxlen=255,
    )

    def execute(self, context):
        clearLog()
        clearCutTable()
        set_blender_to_mm()
        if "Cube" in bpy.data.objects:
            bpy.data.objects["Cube"].select_set(True)
            bpy.ops.object.delete()

        filepath = self.filepath
        bpy.ops.wm.stl_import(filepath=filepath, use_mesh_validate=self.use_mesh_validate, filter_glob=self.filter_glob)
        scene = context.scene
        scene.concave_machine.stone_pointer = bpy.context.object
        bpy.ops.transform.rotate(value=math.pi/2, orient_axis='Z', orient_type='GLOBAL')
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        setStoneLength(self, context)

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class ImportGCSFileOperator(Operator, ImportHelper):
    bl_idname = "import_scene.gcs_file"
    bl_label = "Import GCS File"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".gcs"
    filter_glob: StringProperty(default="*.gcs", options={'HIDDEN'})

    def execute(self, context):
        clearLog()
        clearCutTable()
        set_blender_to_mm()
        if "Cube" in bpy.data.objects:
            bpy.data.objects["Cube"].select_set(True)
            bpy.ops.object.delete()

        filepath = self.filepath
        # Read file content. GCS files aren't guaranteed to be UTF-8 - some
        # exporters write Windows-1252/Latin-1, which breaks on characters
        # like "ü" or "©". Fall back to cp1252 if UTF-8 decoding fails.
        with open(filepath, 'rb') as file:
            raw_content = file.read()
        try:
            content = raw_content.decode('utf-8')
        except UnicodeDecodeError:
            content = raw_content.decode('cp1252')

        # Save content to Blender Text Editor
        text_name = bpy.path.display_name_from_filepath(filepath)
        text_block = bpy.data.texts.get(text_name)
        if not text_block:
            text_block = bpy.data.texts.new(text_name)
        text_block.clear()
        text_block.write(content)

        # Parse GCS XML to extract vertices and faces
        tree = ET.ElementTree(ET.fromstring(content))
        root = tree.getroot()

        faces = []

        # Dictionary to track unique vertices and indices
        vert_dict = {}
        vert_list = []
        index_counter = 0

        def add_vertex(v):
            nonlocal index_counter
            key = (v[0], v[1], v[2])
            if key not in vert_dict:
                vert_dict[key] = index_counter
                vert_list.append(key)
                index_counter += 1
            return vert_dict[key]

        # Loop through facets
        for tier in root.findall('tier'):
            for facet in tier.findall('facet'):
                facet_verts = []
                for vertex in facet.findall('vertex'):
                    x = float(vertex.get('x'))
                    y = float(vertex.get('y'))
                    z = float(vertex.get('z'))
                    vert_index = add_vertex((x, y, z))
                    facet_verts.append(vert_index)
                # Triangulate quads to triangles
                if len(facet_verts) == 3:
                    faces.append(facet_verts)
                elif len(facet_verts) == 4:
                    faces.append([facet_verts[0], facet_verts[1], facet_verts[2]])
                    faces.append([facet_verts[0], facet_verts[2], facet_verts[3]])

        # Create mesh and object
        mesh = bpy.data.meshes.new(text_name)
        mesh.from_pydata(vert_list, [], faces)
        mesh.update()

        obj = bpy.data.objects.new(text_name, mesh)
        context.collection.objects.link(obj)

        # Select and activate the new object
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj
        context.scene.concave_machine.stone_pointer = obj

        if bpy.context.object.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')

        bpy.ops.mesh.convex_hull()
        bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.transform.rotate(value=math.pi/2, orient_axis='Z', orient_type='GLOBAL')
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        setStoneLength(self, context)

        self.report({'INFO'}, f"GCS file imported and object created: {text_name}")
        return {'FINISHED'}
