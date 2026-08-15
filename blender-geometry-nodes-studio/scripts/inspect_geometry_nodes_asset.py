"""Read-only Blender Geometry Nodes graph inspector for reference assets."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy


def socket_name(socket):
    return socket.name or socket.identifier


def absolute_location(node):
    location = node.location.copy()
    parent = node.parent
    while parent is not None:
        location += parent.location
        parent = parent.parent
    return location


def node_center(node):
    location = absolute_location(node)
    return (location.x + node.width * 0.5, location.y - node.height * 0.5)


def interface_sockets(group):
    items = getattr(group.interface, "items_tree", [])
    result = []
    for item in items:
        if getattr(item, "item_type", None) != "SOCKET":
            continue
        result.append({
            "name": item.name,
            "identifier": item.identifier,
            "in_out": item.in_out,
            "socket_type": getattr(item, "socket_type", None),
        })
    return result


def inspect_group(group):
    nodes = []
    for node in group.nodes:
        absolute = absolute_location(node)
        nodes.append({
            "name": node.name,
            "label": node.label,
            "type": node.bl_idname,
            "location": [round(node.location.x, 3), round(node.location.y, 3)],
            "absolute_location": [round(absolute.x, 3), round(absolute.y, 3)],
            "size": [round(node.width, 3), round(node.height, 3)],
            "parent_frame": node.parent.name if node.parent else None,
            "is_muted": node.mute,
            "input_count": len(node.inputs),
            "output_count": len(node.outputs),
        })
    node_by_name = {node.name: node for node in group.nodes}
    links = []
    dx_values, dy_values, distances = [], [], []
    direct_distances, reroute_distances = [], []
    backward = 0
    for link in group.links:
        source = link.from_node
        target = link.to_node
        sx, sy = node_center(source)
        tx, ty = node_center(target)
        dx, dy = tx - sx, ty - sy
        distance = math.hypot(dx, dy)
        dx_values.append(dx)
        dy_values.append(dy)
        distances.append(distance)
        if source.bl_idname == "NodeReroute" or target.bl_idname == "NodeReroute":
            reroute_distances.append(distance)
        else:
            direct_distances.append(distance)
        if dx < 0:
            backward += 1
        links.append({
            "from_node": source.name,
            "from_type": source.bl_idname,
            "from_socket": socket_name(link.from_socket),
            "to_node": target.name,
            "to_type": target.bl_idname,
            "to_socket": socket_name(link.to_socket),
            "delta": [round(dx, 3), round(dy, 3)],
            "distance": round(distance, 3),
        })
    frames = [node for node in group.nodes if node.bl_idname == "NodeFrame"]
    node_types = {}
    for node in group.nodes:
        node_types[node.bl_idname] = node_types.get(node.bl_idname, 0) + 1
    instance_nodes = sum(1 for node in group.nodes if "Instance" in node.bl_idname)
    realize_nodes = sum(1 for node in group.nodes if node.bl_idname == "GeometryNodeRealizeInstances")
    return {
        "name": group.name,
        "is_modifier": group.is_modifier,
        "nodes": nodes,
        "links": links,
        "interface": interface_sockets(group),
        "stats": {
            "node_count": len(nodes),
            "link_count": len(links),
            "frame_count": len(frames),
            "backward_link_count": backward,
            "instance_node_count": instance_nodes,
            "realize_instances_count": realize_nodes,
            "node_types": node_types,
            "mean_link_delta": [round(sum(dx_values) / len(dx_values), 3), round(sum(dy_values) / len(dy_values), 3)] if dx_values else [0, 0],
            "mean_link_distance": round(sum(distances) / len(distances), 3) if distances else 0,
            "mean_direct_link_distance": round(sum(direct_distances) / len(direct_distances), 3) if direct_distances else 0,
            "mean_reroute_link_distance": round(sum(reroute_distances) / len(reroute_distances), 3) if reroute_distances else 0,
            "max_link_distance": round(max(distances), 3) if distances else 0,
        },
    }


def main():
    if "--" not in sys.argv:
        raise SystemExit("Expected -- <output-json-path>")
    output = Path(sys.argv[sys.argv.index("--") + 1])
    groups = [group for group in bpy.data.node_groups if group.bl_idname == "GeometryNodeTree"]
    modifiers = []
    for obj in bpy.data.objects:
        for modifier in obj.modifiers:
            if modifier.type == "NODES":
                modifiers.append({"object": obj.name, "modifier": modifier.name, "node_group": modifier.node_group.name if modifier.node_group else None})
    payload = {
        "blend": bpy.data.filepath,
        "blender_version": bpy.app.version_string,
        "geometry_node_groups": [inspect_group(group) for group in groups],
        "geometry_nodes_modifiers": modifiers,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    # Some legacy .blend node names contain invalid display code points. ASCII
    # escapes keep the inspection artifact valid without altering source data.
    output.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    print(json.dumps({"groups": len(groups), "output": str(output)}, ensure_ascii=True))


if __name__ == "__main__":
    main()
