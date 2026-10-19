import bpy
import sys

# Blender keeps submodules cached in sys.modules. When the extension is
# reinstalled, disabled/enabled, or reloaded with F3 > "Reload Scripts", only
# this __init__ gets re-executed and the old carve_ops/mesh_utils/... code would
# keep running. Drop the cached submodules so they are imported fresh.
for _name in [n for n in sys.modules if n.startswith(__name__ + ".")]:
    del sys.modules[_name]

from . import properties
from . import carve_ops
from . import import_ops
from . import mandrel_ops
from . import sync
from . import panels

# Single list of classes for more streamlined registration
classes = (
    properties.CutTableRow,
    carve_ops.FACET_OT_AddRow,
    carve_ops.FACET_OT_RemoveRow,
    carve_ops.FACET_OT_RedoCutting,
    panels.FACET_UL_Table,
    panels.FACET_PT_ConcavePanel_Main,
    panels.FACET_PT_ConcavePanel_ImportStone,
    panels.FACET_PT_ConcavePanel_MandrelCreation,
    panels.FACET_PT_ConcavePanel_MachineSetup,
    panels.FACET_PT_ConcavePanel_Carve,
    panels.FACET_PT_ConcavePanel_CarveRow,
    panels.FACET_PT_ConcavePanel_CutTable,
    panels.FACET_PT_ConcavePanel_SaveInstructions,
    panels.FACET_PT_ConcavePanel_RenderSync,
    panels.FACET_PT_ConcavePanel_Troubleshoot,
    properties.ConcaveMachineAddonProperties,
    import_ops.Import_OT_stl_file,
    carve_ops.ConcaveBoolean,
    carve_ops.CancelConcaveBoolean,
    carve_ops.ConcaveApply,
    carve_ops.HideMandrel,
    carve_ops.ShowMandrel,
    carve_ops.ConcaveBatch,
    mandrel_ops.CreateMandrel,
    mandrel_ops.CreateVMandrelSlot,
    mandrel_ops.CreateVMandrelRound,
    sync.SendDataToWebgl,
    carve_ops.RecalculateOutsideNormals,
    carve_ops.CleanMesh,
    carve_ops.SaveCutLog,
    import_ops.ImportGCSFileOperator,
    import_ops.Export_OT_source_file,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.concave_machine = bpy.props.PointerProperty(type=properties.ConcaveMachineAddonProperties)
    bpy.types.Scene.cut_table = bpy.props.CollectionProperty(type=properties.CutTableRow)
    bpy.types.Scene.cut_table_index = bpy.props.IntProperty(default=0)
    sync.register()


def unregister():
    sync.unregister()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.concave_machine
    del bpy.types.Scene.cut_table
    del bpy.types.Scene.cut_table_index


if __name__ == "__main__":
    register()
