import itertools
import random

from hypothesis import given, strategies as st, note

import fmt
import _types as types
from score import maximal_covering


def test_pprint_board():
    def random_boardstack():
        i = random.randint(0, 4)
        if i == 0:
            return types.BoardStack(height=i, color=None)
        return types.BoardStack(
            height=i, color=random.choice(list(types.Color))
        )

    board = [[random_boardstack() for _x in range(4)] for _y in range(4)]
    fmt.format_board(board)


def test_maximal_covering_examples():

    # cliques always have a maximal covering of 1
    for clique_size in range(1, 20):
        nodes = range(clique_size)
        edges = itertools.combinations(nodes, 2)
        assert len(maximal_covering(nodes, edges)) == 1

    #  1--2
    #     |
    #  3--4--5
    # maximal covering: 1, 3, 5
    nodes = [1, 2, 3, 4, 5]
    edges = [(1, 2), (3, 4), (2, 4), (4, 5)]
    assert len(maximal_covering(nodes, edges)) == 3

    # 1  2--3
    # |  |
    # 4--5--6
    # |  |
    # 7  8
    # maximal covering: 1, 2, 6, 7, 8
    nodes = [1, 2, 3, 4, 5, 6, 7, 8]
    edges = [(1, 4), (2, 5), (2, 3), (4, 5), (5, 6), (4, 7), (5, 8)]
    assert len(maximal_covering(nodes, edges)) == 5


@st.composite
def graphs(draw):
    r = draw(st.randoms(use_true_random=False))
    n_nodes = draw(st.integers(min_value=2, max_value=30))
    nodes = list(range(n_nodes))
    # for a graph with n nodes the maximum number of edges is n*(n-1)/2 if
    # every possible edge is chosen
    n_edges = draw(
        st.integers(min_value=0, max_value=int(n_nodes * (n_nodes - 1) / 2))
    )
    all_possible_edges = list(itertools.combinations(nodes, 2))
    edges = r.choices(all_possible_edges, k=n_edges)

    return nodes, edges


@given(graphs())
def test_maximal_covering_does_not_include_adjacent_nodes(graph):
    nodes, edges = graph
    note(f"{nodes=}")
    note(f"{edges=}")
    covering = maximal_covering(nodes, edges)
    note(f"{covering=}")

    # maximal covering never includes adjacent nodes
    covering_has_adjacent_nodes = any(
        (u, v) in edges or (v, u) in edges
        for (u, v) in itertools.combinations(covering, 2)
    )
    assert not covering_has_adjacent_nodes


@given(graphs(), st.data())
def test_adding_node_to_maximal_covering_does_not_decrease_covering_size(
    graph, data
):
    nodes, edges = graph
    note(f"{nodes=}")
    note(f"{edges=}")
    covering1 = maximal_covering(nodes, edges)
    note(f"{covering1=}")

    # add up to 5 new nodes
    new_nodes = list(
        range(
            max(nodes) + 1,
            max(nodes) + 1 + data.draw(st.integers(min_value=1, max_value=5)),
        )
    )

    # pick a random sampling of the new edges
    possible_new_edges = [(u, v) for u in nodes for v in new_nodes]
    r = data.draw(st.randoms(use_true_random=False))
    new_edges = r.choices(
        possible_new_edges,
        k=data.draw(
            st.integers(min_value=1, max_value=len(possible_new_edges))
        ),
    )

    # form a covering over the new graph and assert that it's >= the old
    # covering
    covering2 = maximal_covering(nodes + new_nodes, edges + new_edges)
    note(f"{nodes + new_nodes}")
    note(f"{edges + new_edges}")
    note(f"{covering2=}")
    assert len(covering1) <= len(covering2)
