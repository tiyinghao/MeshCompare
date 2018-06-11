import logging
import math

import maya.api.OpenMaya as om
import maya.cmds as mc

logging.basicConfig()
logger = logging.getLogger('MeshCompare')
logger.setLevel(logging.DEBUG)


def static_compare(mesh, target, clamp=10, world=True, saturation=0.8):
    """
    Compares two meshes on a given static frame.
    Sets a vertex color value to show the distance values.
    Colors will go from green at the least to red at the point of clamping.
    
    :param mesh: The name or path to the mesh to visualize on.
    :param target: The name or path of the mesh we are comparing against.
    :param clamp: The value to clamp against. All values be scaled accordingly.
                  i.e if you clamp at 10, absolute red will be 10 units
    :param world: Whether to compare in world space or object space.
    :param saturation: The maximum saturation value to use
    """
    # Get the Dag Paths to the mesh shapes
    mesh = get_shape(mesh)
    target = get_shape(target)

    # Turn on visualization of the vertex colors on the shape
    mesh_path = mesh.fullPathName()
    mc.polyOptions(mesh_path, colorShadedDisplay=True)

    # Get Mesh objects from the shapes.
    mesh_mesh = om.MFnMesh(mesh)
    target_mesh = om.MFnMesh(target)

    # For each mesh, get their points
    space = om.MSpace.kWorld if world else om.MSpace.kObject
    mesh_points = mesh_mesh.getPoints(space)
    target_points = target_mesh.getPoints(space)
    
    if len(mesh_points) != len(target_points):
        raise RuntimeError("Meshes do not have the same vertex count")

    colors = om.MColorArray()
    ids = []

    # Loop through to calculate the colors
    for i, mpoint in enumerate(mesh_points):
        tpoint = target_points[i]

        # Get the distance between the vertices.
        distance = math.sqrt(
            ((mpoint.x - tpoint.x) ** 2) +
            ((mpoint.y - tpoint.y) ** 2) +
            ((mpoint.z - tpoint.z) ** 2)
        )

        hue = 0
        sat = 0
        val = 0.5
        # If our distance is not zero, then process it
        if distance:
            sat = saturation
            val = 1
            # First scale according to the clamp value
            scaled = distance / clamp
            # Then clamp it off at 1
            clamped = min(scaled, 1)
            hue = 180 - ((360*clamped)/2)
        

        # Start from 50% grey and bias to the red channel as distance grows
        color = om.MColor((
            hue, sat, val), om.MColor.kHSV)

        colors.append(color)
        ids.append(i)

    # Apply the colors
    mesh_mesh.setVertexColors(colors, ids)


def get_shape(path):
    """
    For a given node path, get its Dag object.
    Does validation against the scene.
    """
    nodes = mc.ls(path, long=True)

    # Make sure our given path is unique
    if not nodes:
        raise RuntimeError("No node matches name: %s" % (path))
    if len(nodes) > 1:
        raise RuntimeError("More than one node has name: %s" % (path))

    path = nodes[0]

    # Check if we're actually given a mesh.
    if mc.objectType(path) != 'mesh':
        shapes = mc.listRelatives(path, shapes=True, children=True,
                                  type="mesh", fullPath=True)
        if not shapes:
            raise RuntimeError("There are no shapes under %s" % (path))

        if len(shapes) > 1:
            raise RuntimeError("There is more than one shape under %s" % (path))

        # logger.debug("%s is not a mesh. Using %s", node, shapes[0])
        path = shapes[0]

    # Finally convert to a dag object
    sel = om.MSelectionList()
    sel.add(path)
    dag = sel.getDagPath(0)

    return dag


if __name__ == '__main__':
    logger.warning('Running main namespace tests')
    static_compare('pCube2', 'pCube1', clamp=10)
