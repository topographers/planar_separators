import numpy as np
from numba import jit
from numba.types import Tuple, int32, boolean
from . import utils
from .planar_graph import PlanarGraph, planar_graph_nb_type
from .planar_graph_edges import PlanarGraphEdges, planar_graph_edges_nb_type


class PlanarGraphConstructor:

    @staticmethod
    def construct_subgraph(graph, subgraph_vertices_mask, subgraph_edges_mask):

        return construct_subgraph(graph, subgraph_vertices_mask, subgraph_edges_mask)

    @staticmethod
    def clone_graph(graph):

        return clone_graph(graph)

    @staticmethod
    def construct_from_ordered_adjacencies(ordered_adjacencies):

        return construct_from_ordered_adjacencies(ordered_adjacencies)


@jit(Tuple((int32[:], int32[:], planar_graph_nb_type))(planar_graph_nb_type, boolean[:],
        boolean[:]), nopython=True)
def construct_subgraph(graph, subgraph_vertices_mask, subgraph_edges_mask):

    vertex_costs = graph.vertex_costs[subgraph_vertices_mask]

    new_vertices_mapping = utils.repeat_int(-1, graph.size)
    current_new_vertex = 0

    for vertex, is_in_subgraph in enumerate(subgraph_vertices_mask):
        if is_in_subgraph:
            new_vertices_mapping[vertex] = current_new_vertex
            current_new_vertex += 1

    edges_count = 0
    new_edge_indices_mapping = utils.repeat_int(-1, graph.edges_count)

    for edge_index in range(graph.edges_count):

        edge_vertex1 = graph.edges.vertex1[edge_index]
        edge_vertex2 = graph.edges.vertex2[edge_index]

        if subgraph_vertices_mask[edge_vertex1] and subgraph_vertices_mask[edge_vertex2] and \
                subgraph_edges_mask[edge_index]:
            new_edge_indices_mapping[edge_index] = edges_count
            edges_count += 1

    edges = PlanarGraphEdges(edges_count)

    for edge_index in range(graph.edges_count):

        edge_vertex1 = graph.edges.vertex1[edge_index]
        edge_vertex2 = graph.edges.vertex2[edge_index]

        if subgraph_vertices_mask[edge_vertex1] and subgraph_vertices_mask[edge_vertex2] and \
                subgraph_edges_mask[edge_index]:
            edges.append(new_vertices_mapping[edge_vertex1], new_vertices_mapping[edge_vertex2])

    incident_edge_example_indices = utils.repeat_int(-1, len(vertex_costs))

    for vertex, is_in_subgraph in enumerate(subgraph_vertices_mask):
        if is_in_subgraph:

            new_vertex = new_vertices_mapping[vertex]

            first_new_edge_index = -1
            previous_new_edge_index = -1

            for edge_index in graph.get_incident_edge_indices(vertex):

                new_edge_index = new_edge_indices_mapping[edge_index]

                if new_edge_index != -1:

                    if previous_new_edge_index == -1:
                        incident_edge_example_indices[new_vertex] = new_edge_index
                        first_new_edge_index = new_edge_index
                    else:
                        edges.set_previous_edge(new_edge_index, new_vertex, previous_new_edge_index)

                    previous_new_edge_index = new_edge_index

            if first_new_edge_index != -1:
                edges.set_previous_edge(first_new_edge_index, new_vertex, previous_new_edge_index)

    return new_vertices_mapping, new_edge_indices_mapping, PlanarGraph(vertex_costs,
            incident_edge_example_indices, edges)

@jit(planar_graph_nb_type(planar_graph_nb_type), nopython=True)
def clone_graph(graph):

    # Creates the same graph up to different incident edge examples
    _, _, graph = construct_subgraph(graph, utils.repeat_bool(True, graph.size),
            utils.repeat_bool(True, graph.edges_count))

    return graph

def _create_edges_and_map_adjacencies(adjacent_vertices):

    edges = PlanarGraphEdges(sum(len(vertices) for vertices in adjacent_vertices)//2)
    edge_indices_by_adjacencies = {}

    for vertex, vertex_adjacent_vertices in enumerate(adjacent_vertices):
        for adjacent_vertex in vertex_adjacent_vertices:

            if (vertex, adjacent_vertex) not in edge_indices_by_adjacencies:

                edge_indices_by_adjacencies[(vertex, adjacent_vertex)] = edges.size
                edge_indices_by_adjacencies[(adjacent_vertex, vertex)] = edges.size
                edges.append(vertex, adjacent_vertex)

    return edges, edge_indices_by_adjacencies

def construct_from_ordered_adjacencies(ordered_adjacencies):
    """
        only normal graphs are supported
    """

    vertices_count = len(ordered_adjacencies)

    vertex_costs = utils.repeat_float(1/vertices_count, vertices_count)

    edges, edge_indices_by_adjacencies = \
            _create_edges_and_map_adjacencies(ordered_adjacencies)

    incident_edge_example_indices = np.zeros(vertices_count, dtype=np.int32)

    for vertex, vertex_ordered_adjacencies in enumerate(ordered_adjacencies):

        adjacent_vertices_count = len(vertex_ordered_adjacencies)

        if adjacent_vertices_count != 0:

            first_adjacent_vertex = vertex_ordered_adjacencies[0]
            first_incident_edge_index = edge_indices_by_adjacencies[(vertex,
                    first_adjacent_vertex)]
            incident_edge_example_indices[vertex] = first_incident_edge_index

            for adjacent_vertex_index, adjacent_vertex in \
                    enumerate(vertex_ordered_adjacencies):

                incident_edge_index = edge_indices_by_adjacencies[(vertex, adjacent_vertex)]

                next_adjacent_vertex_index = (adjacent_vertex_index + 1)%adjacent_vertices_count
                next_adjacent_vertex = \
                        vertex_ordered_adjacencies[next_adjacent_vertex_index]
                next_incident_edge_index = \
                        edge_indices_by_adjacencies[(vertex, next_adjacent_vertex)]

                edges.set_next_edge(incident_edge_index, vertex, next_incident_edge_index)

    return PlanarGraph(vertex_costs, incident_edge_example_indices, edges)
