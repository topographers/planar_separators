import numpy as np
from .queue import Queue
from .separation_class import SeparationClass


def repeat_int(value, count):

    array = np.zeros(count, dtype=np.int32)
    array[:] = value

    return array

def repeat_bool(value, count):

    array = np.zeros(count, dtype=np.bool_)
    array[:] = value

    return array

def repeat_float(value, count): 

    array = np.zeros(count, dtype=np.float32)
    array[:] = value

    return array

def make_traverse_graph_via_bfs(callback):
    """
        callback(vertex, incident_edge, result) - callback function
    """

    def traverse_graph_via_bfs(start_vertex, graph, used_vertex_flags, result):

        queue = Queue()
        queue.append(start_vertex)

        used_vertex_flags[start_vertex] = True

        while not queue.is_empty():

            vertex = queue.popleft()

            for incident_edge_index in graph.get_incident_edge_indices(vertex):

                adjacent_vertex = graph.edges.get_opposite_vertex(incident_edge_index, vertex)

                if not used_vertex_flags[adjacent_vertex]:

                    callback(vertex, graph.edges, incident_edge_index, result)
                    used_vertex_flags[adjacent_vertex] = True
                    queue.append(adjacent_vertex)

    return traverse_graph_via_bfs

def _color_adjacent_vertex(vertex, edges, incident_edge_index, colors):

    adjacent_vertex = edges.get_opposite_vertex(incident_edge_index, vertex)
    colors[adjacent_vertex] = colors[vertex]

_mark_connected_component = make_traverse_graph_via_bfs(_color_adjacent_vertex)

def color_connected_components(graph):

    colors = repeat_int(-1, graph.size)
    current_color = -1

    used_vertex_flags = repeat_bool(False, graph.size)

    for vertex in range(graph.size):
        if not used_vertex_flags[vertex]:

            current_color += 1
            colors[vertex] = current_color
            _mark_connected_component(vertex, graph, used_vertex_flags, colors)

    return colors

def make_traverse_graph_via_post_order_dfs(callback):

    def traverse_graph_via_post_order_dfs(start_vertex, graph, edges_mask, result):

        parent_edge_indices = repeat_int(-1, graph.size)

        used_vertex_flags = repeat_bool(False, graph.size)
        used_vertex_flags[start_vertex] = True

        stack = [start_vertex]

        while len(stack) != 0:

            vertex = stack.pop()
            stack.append(vertex)

            new_vertices_added_to_stack = False

            for incident_edge_index in graph.get_incident_edge_indices(vertex):
                if edges_mask[incident_edge_index]:

                    adjacent_vertex = graph.edges.get_opposite_vertex(incident_edge_index, vertex)

                    if not used_vertex_flags[adjacent_vertex]:

                        parent_edge_indices[adjacent_vertex] = incident_edge_index

                        used_vertex_flags[adjacent_vertex] = True
                        stack.append(adjacent_vertex)

                        new_vertices_added_to_stack = True

            if not new_vertices_added_to_stack:

                stack.pop()

                parent_edge_index = parent_edge_indices[vertex]

                if parent_edge_index != -1:
                    callback(vertex, graph.edges, parent_edge_index, result)

        return parent_edge_indices

    return traverse_graph_via_post_order_dfs

def iterate_subgraph_incidence_indices(graph, subgraph_edges_mask, possible_incidences_mask,
        start_vertex_in_subgraph, start_edge_index_in_subgraph):

    current_vertex = start_vertex_in_subgraph
    current_edge_index = graph.edges.get_next_edge_index(start_edge_index_in_subgraph,
            start_vertex_in_subgraph)

    current_opposite_vertex = graph.edges.get_opposite_vertex(current_edge_index, current_vertex)

    while current_edge_index != start_edge_index_in_subgraph or \
            current_opposite_vertex != start_vertex_in_subgraph:

        if subgraph_edges_mask[current_edge_index]:
            current_vertex, current_opposite_vertex = current_opposite_vertex, \
                    current_vertex
        elif possible_incidences_mask[current_edge_index]:
            yield current_edge_index

        current_edge_index = graph.edges.get_next_edge_index(current_edge_index, current_vertex)
        current_opposite_vertex = graph.edges.get_opposite_vertex(current_edge_index,
                current_vertex)
