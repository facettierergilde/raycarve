import bpy
import math

import os
import struct
import xml.etree.ElementTree as ET

from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

from .properties import setStoneLength
from .carve_ops import clearLog


def set_blender_to_mm():
    scene = bpy.context.scene
    # Set unit system to Metric and length to millimeters
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.length_unit = 'MILLIMETERS'
    scene.unit_settings.scale_length = 0.001
    bpy.context.space_data.overlay.grid_scale = 0.001
    bpy.context.space_data.lens = 80


# Custom property on the stone object naming the text block that holds the
# imported source file, per file type.
SOURCE_PROPS = {'GCS': "raycarve_gcs_text", 'STL': "raycarve_stl_text"}


def storeSourceText(name, content):
    """Store an imported file in a text block called like the file (with extension)."""
    text_block = bpy.data.texts.get(name)
    if not text_block:
        text_block = bpy.data.texts.new(name)
    text_block.clear()
    text_block.write(content)
    return text_block


def sourceText(stone, kind):
    """Text block holding the imported source file of the given kind, or None."""
    if stone is None:
        return None
    name = stone.get(SOURCE_PROPS[kind])
    return bpy.data.texts.get(name) if name else None


def setSourceText(stone, kind, text_block):
    """Remember text_block as the stone's source file and forget other kinds."""
    for k, prop in SOURCE_PROPS.items():
        if k == kind:
            stone[prop] = text_block.name
        elif prop in stone:
            del stone[prop]


def stlToAscii(raw, solid_name):
    """Return the STL as ASCII text. Binary STL can't live in a text block, so it is converted."""
    if len(raw) >= 84:
        count = struct.unpack_from("<I", raw, 80)[0]
        if 84 + count * 50 == len(raw):
            lines = [f"solid {solid_name}"]
            for i in range(count):
                v = struct.unpack_from("<12f", raw, 84 + i * 50)
                lines.append(f"  facet normal {v[0]:e} {v[1]:e} {v[2]:e}")
                lines.append("    outer loop")
                for j in (3, 6, 9):
                    lines.append(f"      vertex {v[j]:e} {v[j+1]:e} {v[j+2]:e}")
                lines.append("    endloop")
                lines.append("  endfacet")
            lines.append(f"endsolid {solid_name}")
            return "\n".join(lines) + "\n"
    return raw.decode('utf-8', errors='replace')


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
        set_blender_to_mm()
        if "Cube" in bpy.data.objects:
            bpy.data.objects["Cube"].select_set(True)
            bpy.ops.object.delete()

        filepath = self.filepath
        bpy.ops.wm.stl_import(filepath=filepath, use_mesh_validate=self.use_mesh_validate, filter_glob=self.filter_glob)
        scene = context.scene
        scene.concave_machine.stone_pointer = bpy.context.object
        clearLog()
        # Keep a copy of the STL in a text block so it can be exported again.
        with open(filepath, 'rb') as file:
            raw = file.read()
        file_name = bpy.path.basename(filepath)
        setSourceText(bpy.context.object, 'STL',
                      storeSourceText(file_name, stlToAscii(raw, os.path.splitext(file_name)[0])))
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

        # Save content to Blender Text Editor, named like the file incl. extension
        text_name = bpy.path.display_name_from_filepath(filepath)
        text_block = storeSourceText(bpy.path.basename(filepath), content)

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
        setSourceText(obj, 'GCS', text_block)
        clearLog()

        if bpy.context.object.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')

        bpy.ops.mesh.convex_hull()
        bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.transform.rotate(value=math.pi/2, orient_axis='Z', orient_type='GLOBAL')
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        setStoneLength(self, context)

        self.report({'INFO'}, f"GCS file imported and object created: {text_name}")
        return {'FINISHED'}


class Export_OT_source_file(Operator):
    """Export the imported source file (GCS or STL) of the current stone"""
    bl_idname = "object.export_source_file"
    bl_label = "Export source file"

    kind: EnumProperty(items=[('GCS', "GCS", ""), ('STL', "STL", "")], options={'HIDDEN'})
    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.gcs;*.stl", options={'HIDDEN'})

    @classmethod
    def description(cls, context, properties):
        return f"Save the imported {properties.kind} file of the current stone to disk"

    def invoke(self, context, event):
        text = sourceText(context.scene.concave_machine.stone_pointer, self.kind)
        if text is None:
            self.report({'ERROR'}, f"No {self.kind} file stored for this stone")
            return {'CANCELLED'}
        self.filter_glob = "*." + self.kind.lower()
        self.filepath = text.name
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        text = sourceText(context.scene.concave_machine.stone_pointer, self.kind)
        if text is None:
            self.report({'ERROR'}, f"No {self.kind} file stored for this stone")
            return {'CANCELLED'}
        filepath = bpy.path.ensure_ext(self.filepath, "." + self.kind.lower())
        with open(filepath, 'w', encoding='utf-8', newline='') as file:
            file.write(text.as_string())
        self.report({'INFO'}, f"Saved {filepath}")
        return {'FINISHED'}
