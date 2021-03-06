#!/usr/bin/python

# (C) 2015-2018 Lumina Networks, Inc.
# 2077 Gateway Place, Suite 500, San Jose, CA 95110
# Use of the software files and documentation is subject to license terms.
# Author: Luis Gomez

"""
Overview: Script to analyze network impact of single failure (link or node) when
devices are programmed for fast failover (max two paths for every destination).

Intructions:
1) Fill topology using topo.node_add and topo.link_add below.
2) Run script and check results report, the script will:
    - fill the routing table for all nodes in the network.
    - simulate all posssible network single failres (link or node).
    - analize the impact of the failure (ok, drop, loop) in all paths.

"""

import collections
import copy
import time

class RoutingTable(set):
    """
    Overview: Class to store the routing table for all nodes in the network:
        routes = {node:{dst_node:[next_hop_node]}}

    Methods:
    - add_route: add route to node = dst_node -> next_hop.
    - delete_route_link: delete all concerned routes when link goes down.
    - delete_route_node: delete all concerned routes when node goes down.
    - print_table: print all nodes routing table.

    """

    def __init__(self, nodes):
        self.routes = {}
        for node in nodes:
            self.routes[node] = collections.defaultdict(list)

    def add_route(self, node, dst_node, next_hop):
        self.routes[node][dst_node].append(next_hop)

    def delete_route_link(self, node1, node2):
        # delete all routes in node1 with next_hop node2
        for dst_node in self.routes[node1]:
            try:
                self.routes[node1][dst_node].remove(node2)
            except:
                continue

        # delete all routes in node2 with next_hop node1
        for dst_node in self.routes[node2]:
            try:
                self.routes[node2][dst_node].remove(node1)
            except:
                continue

    def delete_route_node(self, node):
        for src_node in self.routes:
            if src_node is node:
                # delete all routes from node to neighbors
                for dst_node in self.routes[src_node]:
                    self.routes[src_node][dst_node][:] = []
            else:
                # delete all routes from neighbors to node
                for dst_node in self.routes[src_node]:
                    try:
                        self.routes[src_node][dst_node].remove(node)
                    except:
                        continue

    def print_table(self):
        for node in self.routes:
            print "** " + node + " routes:"
            for dst_node in rt.routes[node]:
                print dst_node + ": " + str(rt.routes[node][dst_node])
            print ""

class Graph:
    """
    Overview: Class to store the graph nodes, links, node edges and distances:
        nodes = (nodes)
        links = ((node1,node2))
        edges = {node:[next_hop_list]}
        distances = {(node1,node2):distance}

    Methods:
    - add_node: add node to topology.
    - add_link: add link with cost to topology.
    - delete_link: delete link from topology.

    """

    def __init__(self):
        self.nodes = set()
        self.links = set()
        self.edges = collections.defaultdict(list)
        self.distances = {}

    def add_node(self, value):
        self.nodes.add(value)

    def add_link(self, node1, node2, distance):
        self.links.add((node1, node2))
        self.edges[node1].append(node2)
        self.edges[node2].append(node1)
        self.distances[(node1, node2)] = distance
        self.distances[(node2, node1)] = distance

    def delete_link(self, node1, node2):
        try:
            self.links.remove((node1, node2))
        except:
            self.links.remove((node2, node1))
        self.edges[node1].remove(node2)
        self.edges[node2].remove(node1)
        self.distances.pop((node1, node2), None)
        self.distances.pop((node2, node1), None)

def dijsktra(graph, initial):
    """
    Overview: Function to calculate best path to node in a graph.

    Arguments:
    - graph: topology to calculate best path.
    - initial: node to calculate best path to.

    Returns:
    - visited: nodes best path cost to initial.
        visited = {src_node:path_cost}
    - path: nodes best path next_hop to initial.
        path = {src_node:next_hop_node}

    """

    visited = {initial: 0}
    path = {}

    nodes = set(graph.nodes)

    while nodes: 
        min_node = None
        for node in nodes:
            if node in visited:
                if min_node is None:
                    min_node = node
                elif visited[node] < visited[min_node]:
                   min_node = node

        if min_node is None:
            break

        nodes.remove(min_node)
        current_weight = visited[min_node]

        for edge in graph.edges[min_node]:
            try:
                weight = current_weight + graph.distances[(min_node, edge)]
            except:
                continue
            if edge not in visited or weight < visited[edge]:
                visited[edge] = weight
                path[edge] = min_node

    return visited, path

def test_path (routes, src_node, dst_node):
    """
    Overview: Function to test a path from src_node to dst_node.

    Arguments:
    - routes: nodes routing table.
    - src_node: path source.
    - dst_node: path destination.

    Returns:
    - status: path status (e.g. ok, drop, loop).
    - path: current path sequence.
        path = [node]

    """

    status = "ok"
    last_node = None
    current_node = src_node
    path = [current_node]

    while current_node is not dst_node:
        try:
            # try best next_hop
            next_node = routes[current_node][dst_node][0]
        except:
            status = "drop"
            break
        if next_node is last_node:
            try:
                # if traffic is coming from best next_hop try second best next_hop
                next_node = routes[current_node][dst_node][1]
            except:
                status = "drop"
                break
        if next_node in path:
            # if next_hop is stored in path we have a loop
            path.append(next_node)
            status = "loop"
            break
        path.append(next_node)
        last_node = current_node
        current_node = next_node

    return status, path

def test_paths (routes, nodes, down_node=None):
    """
    Overview: Function to test all paths in the network.

    Arguments:
    - routes: nodes routing table.
    - nodes: nodes in the network.
    - down_node: in case a node goes down, there are expected path drops.

    Returns:
    - count_exp_drop: expected path drops due to node down
    - count_drops: path drops due to fast failover
    - count_loops: path loops due to fast failover
    - count_ok: path ok count

    """

    count_exp_drop = 0
    count_drop = 0
    count_loop = 0
    count_ok = 0

    for src_node in nodes:
        other_nodes = set(nodes)
        other_nodes.remove(src_node)
        for dst_node in other_nodes:
            status, path = test_path(routes, src_node, dst_node)
            print src_node + "->" + dst_node + ":" + str(path) + " status:" + status
            if status == "drop" and (src_node is down_node or dst_node is down_node):
                # if the path drop is because src or dst node is down it is expected
                count_exp_drop += 1
            elif status == "drop":
                count_drop += 1
            elif status == "loop":
                count_loop += 1
            else:
                count_ok += 1

    return count_exp_drop, count_drop, count_loop, count_ok

if __name__ == "__main__":

    # fill the graph
    topo = Graph()

    # nodes
    topo.add_node("1010001")
    topo.add_node("1020001")
    topo.add_node("1030001")
    topo.add_node("1040001")
    topo.add_node("2010001")
    topo.add_node("2010002")
    topo.add_node("2020001")
    topo.add_node("2020002")
    topo.add_node("2030001")
    topo.add_node("2030002")
    topo.add_node("2090001")
    topo.add_node("2090002")
    topo.add_node("3010001")
    topo.add_node("3020001")
    topo.add_node("3020002")
    topo.add_node("3030001")
    topo.add_node("3030002")
    topo.add_node("3080001")
    topo.add_node("3090001")
    topo.add_node("3090002")
    topo.add_node("5010001")
    topo.add_node("5010002")
    topo.add_node("5020001")
    topo.add_node("7010001")
    topo.add_node("7010002")
    topo.add_node("7020001")
    topo.add_node("7020002")
    topo.add_node("8010001")
    topo.add_node("8020001")

    # links
    topo.add_link("1010001", "1020001", 1)
    topo.add_link("1040001", "1030001", 1)
    topo.add_link("1010001", "1040001", 1)
    topo.add_link("1020001", "1030001", 1)
    topo.add_link("1010001", "2010001", 1)
    topo.add_link("1020001", "2020001", 1)
    topo.add_link("2010001", "2020001", 1)
    topo.add_link("2010002", "2020002", 1)
    topo.add_link("2030001", "2030002", 1)
    topo.add_link("2090001", "2090002", 1)
    topo.add_link("2010001", "2010002", 1)
    topo.add_link("2010001", "2030001", 1)
    topo.add_link("2010001", "2090001", 1)
    topo.add_link("2010001", "8010001", 1)
    topo.add_link("2010001", "7010001", 1)
    topo.add_link("2020001", "2020002", 1)
    topo.add_link("2020001", "2030002", 1)
    topo.add_link("2020001", "2090002", 1)
    topo.add_link("2020001", "8020001", 1)
    topo.add_link("2020001", "7020001", 1)
    topo.add_link("2020001", "3020001", 1)
    topo.add_link("3010001", "3020001", 1)
    topo.add_link("3030001", "3030002", 1)
    topo.add_link("3090001", "3090002", 1)
    topo.add_link("3010001", "3020002", 1)
    topo.add_link("3010001", "3030001", 1)
    topo.add_link("3010001", "3080001", 1)
    topo.add_link("3010001", "3090001", 1)
    topo.add_link("3010001", "5010001", 1)
    topo.add_link("3020001", "3020002", 1)
    topo.add_link("3020001", "3030002", 1)
    topo.add_link("3020001", "3080001", 1)
    topo.add_link("3020001", "3090002", 1)
    topo.add_link("3020001", "5020001", 1)
    topo.add_link("5010001", "5020001", 1)
    topo.add_link("5010001", "5010002", 1)
    topo.add_link("5010001", "7010001", 1)
    topo.add_link("5020001", "7020002", 1)
    topo.add_link("7010001", "7020001", 1)
    topo.add_link("7010002", "7020002", 1)
    topo.add_link("7010001", "7010002", 1)
    topo.add_link("7020001", "7020002", 1)
    topo.add_link("8010001", "8020001", 1)

    # fill the routing tables
    start_time = time.time()
    compute_count = 0
    rt = RoutingTable(topo.nodes)
    for dst_node in topo.nodes:
        visited, path = dijsktra(topo, dst_node)
        compute_count += 1
        for src_node in path:
            # add best path to dst_node
            rt.add_route(src_node, dst_node, path[src_node])

            # add second best path (if available) to dst_node
            topo.delete_link(src_node, path[src_node])
            second_visited, second_path = dijsktra(topo, dst_node)
            compute_count += 1
            if src_node in second_path:
                rt.add_route(src_node, dst_node, second_path[src_node])
            topo.add_link(src_node, path[src_node], 1)

    elapsed_time = time.time() - start_time

    # print routing tables
    rt.print_table()

    # test paths
    total_exp_drop=0
    total_drop=0
    total_loop=0
    total_ok=0

    # test all link failures
    for node1, node2 in topo.links:
        rt_temp = copy.deepcopy(rt)
        print "** fail link " + node1 + "-" + node2
        rt_temp.delete_route_link(node1, node2)
        count_exp_drop, count_drop, count_loop, count_ok = test_paths(rt_temp.routes, topo.nodes)
        total_exp_drop += count_exp_drop
        total_drop += count_drop
        total_loop += count_loop
        total_ok += count_ok

    # test all node failures
    for node in topo.nodes:
        rt_temp = copy.deepcopy(rt)
        print "** fail node " + node
        rt_temp.delete_route_node(node)
        count_exp_drop, count_drop, count_loop, count_ok = test_paths(rt_temp.routes, topo.nodes, node)
        total_exp_drop += count_exp_drop
        total_drop += count_drop
        total_loop += count_loop
        total_ok += count_ok

    total_tested = total_exp_drop + total_drop + total_loop + total_ok
        
    # print results
    print ""
    print "** Test Results:"
    print "number of nodes: " + str(len(topo.nodes))
    print "number of links: " + str(len(topo.links))
    print ""
    print "path compute cycles: " + str (compute_count)
    print "path compute time: " + str(elapsed_time)
    print ""
    print "path tested: " + str(total_tested)
    print "path expected drop: " + str(total_exp_drop)
    print "path drop: " + str(total_drop)
    print "path loop: " + str(total_loop)
    print "path ok: " + str(total_ok)
    print ""
    print "expected drop: " + str("{:.1%}".format(float(total_exp_drop) / float(total_tested)))
    print "drop: " + str("{:.1%}".format(float(total_drop) / float(total_tested)))
    print "loop: " + str("{:.1%}".format(float(total_loop) / float(total_tested)))
    print "ok: " + str("{:.1%}".format(float(total_ok) / float(total_tested)))
    print ""

