import bpy

from .utils import ADDON_VERSION


# -------------------------------------------------------------------
# Custom UIList to display the collection
# -------------------------------------------------------------------
class FACET_UL_Table(bpy.types.UIList):
    """A UIList behaves like a dynamic table view"""
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        # `item` is an instance of CutTableRow
        row = layout.row(align=True)
        row.prop(item, "name", text="", emboss=False)
        row.prop(item, "disable", text="")
        row.prop(item, "side", text="")
        row.prop(item, "facet_angle", text="")
        row.prop(item, "batch_indices", text="")
        row.prop(item, "comment", text="")
        row.prop(item, "tool_pointer", text="")
        row.prop(item, "stone_height", text="")
        row.prop(item, "stone_position", text="")
        row.prop(item, "mandrel_position", text="")
        row.prop(item, "mandrel_rotation", text="")


class FACET_PT_ConcavePanel:
    """Creates a Panel in the tools"""
    bl_label = "RayCarve - Concave Machine"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RayCarve"
    bl_context = "objectmode"


class FACET_PT_ConcavePanel_Main(FACET_PT_ConcavePanel, bpy.types.Panel):
    bl_idname = "FACET_PT_ConcavePanel_Main"
    bl_label = f"RayCarve {ADDON_VERSION}"

    def draw(self, context):
        pass


class FACET_PT_ConcavePanel_ImportStone(FACET_PT_ConcavePanel, bpy.types.Panel):
    """Creates a Sub Panel concave panel"""
    bl_label = "1. Stone import"
    bl_parent_id = "FACET_PT_ConcavePanel_Main"

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        box = layout.box()
        # Round Mandrel creation
        box.label(text="Import stone")
        row = box.row(align=True)
        row.operator("import_scene.gcs_file")
        row = box.row(align=True)
        row.operator("object.import_stl_file")
        row = box.row(align=True)
        box.label(text="Resize stone to length:")
        row = box.row()
        row.prop(scene.concave_machine, "stone_length")
        if scene.concave_machine.stone_pointer:
            obj = scene.concave_machine.stone_pointer
            row = box.row()
            row.label(text="Dimensions:")
            # Display the dimensions as read-only vector property
            row = box.row()
            # We use layout.label instead of layout.prop to make it readonly
            row.label(text=f"W: {obj.dimensions.x:.2f}, L: {obj.dimensions.y:.2f}, H: {obj.dimensions.z:.2f}")


class FACET_PT_ConcavePanel_MandrelCreation(FACET_PT_ConcavePanel, bpy.types.Panel):
    """Creates a Sub Panel concave panel"""
    bl_label = "2. Mandrel Creation"
    bl_parent_id = "FACET_PT_ConcavePanel_Main"

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        box = layout.box()
        row = box.row(align=True)
        row.prop(scene.concave_machine, "mandrel_resolution")
        row = box.row(align=True)
        # Round Mandrel creation
        box.label(text="Create Round Mandrel")
        row = box.row(align=True)
        row.prop(scene.concave_machine, "mandrel_diameter")
        row = box.row(align=True)
        row.operator("object.create_mandrel")

        box = layout.box()
        # V-Mandrel creation
        box.label(text="Create V-Mandrel")
        row = box.row(align=True)
        row.prop(scene.concave_machine, "v_mandrel_angle")
        row = box.row(align=True)
        row.prop(scene.concave_machine, "v_mandrel_diameter")
        row = box.row(align=True)
        row.prop(scene.concave_machine, "v_mandrel_width")
        row = box.row(align=True)
        row.prop(scene.concave_machine, "v_mandrel_bevel_offset")
        row = box.row(align=True)
        row.prop(scene.concave_machine, "v_mandrel_bevel_segments")
        row = box.row(align=False)
        row.operator("object.create_v_mandrel_slot")
        row = box.row(align=False)
        row.operator("object.create_v_mandrel_round")


class FACET_PT_ConcavePanel_MachineSetup(FACET_PT_ConcavePanel, bpy.types.Panel):
    """Creates the Machine Setup panel"""
    bl_label = "3. Concave Machine Setup"
    bl_parent_id = "FACET_PT_ConcavePanel_Main"

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        # Create a simple row.
        layout.label(text="Objects:")
        row = layout.row()
        row.prop(scene.concave_machine, "stone_pointer")
        row = layout.row()
        row.prop(scene.concave_machine, "mandrel_pointer")

        # Create an row where the buttons are aligned to each other.
        layout.label(text="Index gear:")
        row = layout.row()
        row.prop(scene.concave_machine, "index_gear")


class FACET_PT_ConcavePanel_Carve(FACET_PT_ConcavePanel, bpy.types.Panel):
    """Creates the Carve panel"""
    bl_label = "4. Carve"
    bl_parent_id = "FACET_PT_ConcavePanel_Main"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        if scene.concave_machine.stone_pointer is None or scene.concave_machine.mandrel_pointer is None:
            layout.label(text="Please select Stone and Mandrel first!")
        else:
            row = layout.row()
            row.prop(scene.concave_machine, "faceting_side", expand=True)
            layout.label(text="Faceting mast:")
            row = layout.row()
            row.prop(scene.concave_machine, "index")
            row = layout.row()
            row.prop(scene.concave_machine, "facet_angle")
            row = layout.row()
            row.prop(scene.concave_machine, "stone_height")
            row = layout.row()
            row.prop(scene.concave_machine, "stone_position")

            layout.label(text="Concave machine:")
            row = layout.row()
            row.prop(scene.concave_machine, "mandrel_position")
            row = layout.row()
            row.prop(scene.concave_machine, "mandrel_rotation")

            # Commands
            layout.label(text="Commands:")
            row = layout.row(align=True)
            if scene.concave_machine.stone_pointer.modifiers.get('ConcaveBoolean') is None:
                row.operator("object.concave_boolean")
            else:
                row.operator("object.cancel_concave_boolean")
            if scene.concave_machine.stone_pointer.modifiers.get('ConcaveBoolean') is not None:
                row.operator("object.concave_apply")
            row = layout.row(align=True)
            if scene.concave_machine.mandrel_pointer.hide_get():
                row.operator("object.show_mandrel")
            else:
                row.operator("object.hide_mandrel")


class FACET_PT_ConcavePanel_CarveRow(FACET_PT_ConcavePanel, bpy.types.Panel):
    """Creates the Carve Row panel"""
    bl_label = "Carve Row"
    bl_parent_id = "FACET_PT_ConcavePanel_Main"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        if scene.concave_machine.stone_pointer is None or scene.concave_machine.mandrel_pointer is None:
            layout.label(text="Please select Stone and Mandrel first!")
        else:
            # Batch
            row = layout.row()
            row.prop(scene.concave_machine, "symmetry")
            row.prop(scene.concave_machine, "mirror")

            layout.label(text="Row:  ex: 6-12-18")
            row = layout.row(align=True)
            row.prop(scene.concave_machine, "batch_indices")
            row = layout.row(align=True)
            row.operator("object.concave_batch")


class FACET_PT_ConcavePanel_CutTable(FACET_PT_ConcavePanel, bpy.types.Panel):
    """Creates the Cut Table panel"""
    bl_label = "Cut Table"
    bl_parent_id = "FACET_PT_ConcavePanel_Main"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row()
        row.template_list(
            "FACET_UL_Table", "",
            scene, "cut_table",
            scene, "cut_table_index",
            rows=5
        )

        col = row.column(align=True)
        col.operator("raycarve.add_row", icon="ADD", text="")
        col.operator("raycarve.remove_row", icon="REMOVE", text="")
        col.operator("raycarve.redo_cutting", icon="FILE_REFRESH", text="")


class FACET_PT_ConcavePanel_SaveInstructions(FACET_PT_ConcavePanel, bpy.types.Panel):
    """Creates the Save Instructions panel"""
    bl_label = "5. Save instructions"
    bl_parent_id = "FACET_PT_ConcavePanel_Main"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        row = layout.row(align=True)
        row.operator("object.save_cut_log")


class FACET_PT_ConcavePanel_Troubleshoot(FACET_PT_ConcavePanel, bpy.types.Panel):
    """Creates the Troubleshoot panel"""
    bl_label = "Troubleshoot"
    bl_parent_id = "FACET_PT_ConcavePanel_Main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        if scene.concave_machine.stone_pointer is None or scene.concave_machine.mandrel_pointer is None:
            layout.label(text="Please select Stone and Mandrel first!")
        else:
            # Fix Boolean
            layout.label(text="Fixing boolean:")
            row = layout.row(align=True)
            row.operator("object.recalculate_normals")
            row.operator("object.merge_by_distance")


class FACET_PT_ConcavePanel_RenderSync(FACET_PT_ConcavePanel, bpy.types.Panel):
    """Creates the render sync panel"""
    bl_label = "Render synchronisation"
    bl_parent_id = "FACET_PT_ConcavePanel_Main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        box = layout.box()
        row = box.row(align=True)
        row.prop(scene.concave_machine, "sync_enabled")
        box.label(text="Synchronisation Status:")
        box.label(text=f"{scene.concave_machine.sync_status}")
        row = box.row(align=False)
        row.operator("object.send_data_to_webgl")
