import numpy as np
from numba import jit
from numba.types import void, int32, boolean, float32
from . import planar_graph_constructor, triangulator, utils
from .planar_graph import PlanarGraph, planar_graph_nb_type
from .planar_graph_edges import PlanarGraphEdges


class PlanarGraphGenerator:

    @staticmethod
    def generate_random_tree(size, random_vertex_costs=False):

        return _generate_random_tree(size, random_vertex_costs)

    @staticmethod
    def generate_random_graph(size, density, random_vertex_costs=False):

        return _generate_random_graph(size, density, random_vertex_costs)


@jit(planar_graph_nb_type(int32, boolean), nopython=True)
def _generate_random_tree(size, random_vertex_costs):

    if size < 2:
        raise RuntimeError('The minimum size of 2 is allowed.')

    if random_vertex_costs:
        # Hacks to make numba work
        vertex_costs = np.array([np.random.uniform(0, 1) for _ in range(size)], dtype=float32)
    else:
        vertex_costs = np.ones(size, dtype=np.float32)

    vertex_costs /= vertex_costs.sum()

    edges = PlanarGraphEdges(size - 1)

    edges.append(0, 1)
    edges.set_next_edge(0, 0, 0)
    edges.set_next_edge(0, 1, 0)

    incident_edge_example_indices = np.zeros(size, dtype=np.int32)

    for index in range(size - 2):

        vertex = np.random.choice(index + 2)
        new_vertex = index + 2

        incident_edge_index = incident_edge_example_indices[vertex]

        new_edge_index = edges.size

        edges.append(vertex, new_vertex)

        edges.set_next_edge(new_edge_index, new_vertex, new_edge_index)

        incident_edge_example_indices[new_vertex] = new_edge_index

        incident_edge_next_edge_index = edges.get_next_edge_index(incident_edge_index, vertex)

        edges.set_next_edge(incident_edge_index, vertex, new_edge_index)
        edges.set_next_edge(new_edge_index, vertex, incident_edge_next_edge_index)

    return PlanarGraph(vertex_costs, incident_edge_example_indices, edges)

@jit(planar_graph_nb_type(planar_graph_nb_type), nopython=True)
def _remove_double_edges(graph):

    is_adjacent_vertex_mask = utils.repeat_bool(False, graph.size)

    edge_indices_mask = utils.repeat_bool(True, graph.edges_count)

    for vertex in range(graph.size):

        for edge_index in graph.get_incident_edge_indices(vertex):

            adjacent_vertex = graph.edges.get_opposite_vertex(edge_index, vertex)

            if is_adjacent_vertex_mask[adjacent_vertex]:
                edge_indices_mask[edge_index] = False
            else:
                if edge_indices_mask[edge_index]:
                    is_adjacent_vertex_mask[adjacent_vertex] = True

        for edge_index in graph.get_incident_edge_indices(vertex):

            adjacent_vertex = graph.edges.get_opposite_vertex(edge_index, vertex)
            is_adjacent_vertex_mask[adjacent_vertex] = False

    _, _, graph = planar_graph_constructor.construct_subgraph(graph,
            utils.repeat_bool(True, graph.size), edge_indices_mask)

    return graph

@jit(planar_graph_nb_type(planar_graph_nb_type), nopython=True)
def _normalize_vertex_costs(graph):

    vertex_costs = graph.vertex_costs.copy()

    vertex_costs /= vertex_costs.sum()

    return PlanarGraph(vertex_costs, graph.incident_edge_example_indices, graph.edges)

@jit(planar_graph_nb_type(int32, float32, boolean), nopython=True)
def _generate_random_graph(size, density, random_vertex_costs):

    tree = _generate_random_tree(size, random_vertex_costs)

    _, triangulated_tree = triangulator.triangulate(tree)

    edges_to_leave_count = int(density*triangulated_tree.edges_count)
    edges_to_delete_count = triangulated_tree.edges_count - edges_to_leave_count

    random_edges_mask = np.concatenate((utils.repeat_bool(True, edges_to_leave_count),
            utils.repeat_bool(False, edges_to_delete_count)))

    np.random.shuffle(random_edges_mask)

    _, _, graph = planar_graph_constructor.construct_subgraph(triangulated_tree,
            utils.repeat_bool(True, triangulated_tree.size), random_edges_mask)

    graph = _remove_double_edges(graph)

    graph = _normalize_vertex_costs(graph)

    return graph
