# Copyright 2018 The glTF-Blender-IO authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import bpy
from .gltf2_blender_mesh import *
from .gltf2_blender_camera import *
from .gltf2_blender_skin import *
from ..com.gltf2_blender_conversion import *

class BlenderNode():

    @staticmethod
    def create(gltf, node_idx, parent):

        pynode = gltf.data.nodes[node_idx]

        # Blender attributes initialization
        pynode.blender_object = ""
        pynode.parent = parent

        if pynode.mesh is not None:

            if gltf.data.meshes[pynode.mesh].blender_name is not None:
                # Mesh is already created, only create instance
                mesh = bpy.data.meshes[gltf.data.meshes[pynode.mesh].blender_name]
            else:
                if pynode.name:
                    gltf.log.info("Blender create Mesh node " + pynode.name)
                else:
                    gltf.log.info("Blender create Mesh node")

                mesh = BlenderMesh.create(gltf, pynode.mesh, node_idx, parent)

            if pynode.name:
                name = pynode.name
            else:
                # Take mesh name if exist
                if gltf.data.meshes[pynode.mesh].name:
                    name = gltf.data.meshes[pynode.mesh].name
                else:
                    name = "Object_" + str(node_idx)

            obj = bpy.data.objects.new(name, mesh)
            obj.rotation_mode = 'QUATERNION'
            bpy.data.scenes[gltf.blender_scene].objects.link(obj)

            # Transforms apply only if this mesh is not skinned
            # See implementation node of gltf2 specification
            if not (pynode.mesh and pynode.skin is not None):
                BlenderNode.set_transforms(gltf, node_idx, pynode, obj, parent)
            pynode.blender_object = obj.name
            BlenderNode.set_parent(gltf, pynode, obj, parent)

            BlenderMesh.set_mesh(gltf, gltf.data.meshes[pynode.mesh], mesh, obj)

            if pynode.children:
                for child_idx in pynode.children:
                    BlenderNode.create(gltf, child_idx, node_idx)

            return


        if pynode.camera is not None:
            if pynode.name:
                gltf.log.info("Blender create Camera node " + pynode.name)
            else:
                gltf.log.info("Blender create Camera node")
            obj = BlenderCamera.create(gltf, pynode.camera)
            BlenderNode.set_transforms(gltf, node_idx, pynode, obj, parent) #TODO default rotation of cameras ?
            pynode.blender_object = obj.name
            BlenderNode.set_parent(gltf, pynode, obj, parent)

            return


        if pynode.is_joint:
            if pynode.name:
                gltf.log.info("Blender create Bone node " + pynode.name)
            else:
                gltf.log.info("Blender create Bone node")
            # Check if corresponding armature is already created, create it if needed
            if gltf.data.skins[pynode.skin_id].blender_armature_name is None:
                BlenderSkin.create_armature(gltf, pynode.skin_id, parent)

            BlenderSkin.create_bone(gltf, pynode.skin_id, node_idx, parent)

            if pynode.children:
                for child_idx in pynode.children:
                    BlenderNode.create(gltf, child_idx, node_idx)

            return

        # No mesh, no camera. For now, create empty #TODO

        if pynode.name:
            gltf.log.info("Blender create Empty node " + pynode.name)
            obj = bpy.data.objects.new(pynode.name, None)
        else:
            gltf.log.info("Blender create Empty node")
            obj = bpy.data.objects.new("Node", None)
        obj.rotation_mode = 'QUATERNION'
        bpy.data.scenes[gltf.blender_scene].objects.link(obj)
        BlenderNode.set_transforms(gltf, node_idx, pynode, obj, parent)
        pynode.blender_object = obj.name
        BlenderNode.set_parent(gltf, pynode, obj, parent)

        if pynode.children:
            for child_idx in pynode.children:
                BlenderNode.create(gltf, child_idx, node_idx)


    @staticmethod
    def set_parent(gltf, pynode, obj, parent):

        if parent is None:
            return

        for node_idx, node in enumerate(gltf.data.nodes):
            if node_idx == parent:
                if node.is_joint == True:
                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.data.objects[node.blender_armature_name].select = True
                    bpy.context.scene.objects.active = bpy.data.objects[node.blender_armature_name]
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.data.objects[node.blender_armature_name].data.edit_bones.active = bpy.data.objects[node.blender_armature_name].data.edit_bones[node.blender_bone_name]
                    bpy.ops.object.mode_set(mode='OBJECT')
                    bpy.ops.object.select_all(action='DESELECT')
                    obj.select = True
                    bpy.data.objects[node.blender_armature_name].select = True
                    bpy.context.scene.objects.active = bpy.data.objects[node.blender_armature_name]
                    bpy.ops.object.parent_set(type='BONE', keep_transform=True)

                    return
                if node.blender_object:
                    obj.parent = bpy.data.objects[node.blender_object]
                    return

        gltf.log.error("ERROR, parent not found")

    @staticmethod
    def set_transforms(gltf, node_idx, pynode, obj, parent):
        if parent is None:
            obj.matrix_world =  Conversion.matrix_gltf_to_blender(pynode.transform)
            return

        for idx, node in enumerate(gltf.data.nodes):
            if idx == parent:
                if node.is_joint == True:
                    obj.matrix_world = Conversion.matrix_gltf_to_blender(pynode.transform)
                    return
                else:
                    obj.matrix_world = Conversion.matrix_gltf_to_blender(pynode.transform)
                    return