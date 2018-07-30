#!/usr/bin/python

import collections
import copy
import time

class RoutingTable(set):
    def __init__(self, nodes):
        self.routes = {}
        for node in nodes:
            self.routes[node] = collections.defaultdict(list)

    def add_route(self, node, dst_node, next_hop):
        self.routes[node][dst_node].append(next_hop)

    def delete_route_link(self, node1, node2):

        for dst_node in self.routes[node1]:
            try:
                self.routes[node1][dst_node].remove(node2)
            except:
                continue

        for dst_node in self.routes[node2]:
            try:
                self.routes[node2][dst_node].remove(node1)
            except:
                continue

    def delete_route_node(self, node):

        for src_node in self.routes:
            if src_node is node:
                for dst_node in self.routes[src_node]:
                    self.routes[src_node][dst_node][:] = []
            else:
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
    status = "ok"
    last_node = None
    current_node = src_node
    path = [current_node]

    while current_node is not dst_node:
        try:
            next_node = routes[current_node][dst_node][0]
        except:
            status = "drop"
            break
        if next_node is last_node:
            try:
                next_node = routes[current_node][dst_node][1]
            except:
                status = "drop"
                break
        if next_node in path:
            path.append(next_node)
            status = "loop"
            break
        path.append(next_node)
        last_node = current_node
        current_node = next_node

    return status, path

def test_paths (routes, nodes):
    count_drop = 0
    count_loop = 0
    count_ok = 0

    for src_node in nodes:
        other_nodes = set(nodes)
        other_nodes.remove(src_node)
        for dst_node in other_nodes:
            status, path = test_path(routes, src_node, dst_node)
            print src_node + "->" + dst_node + ":" + str(path) + " status:" + status
            if status == "drop":
                count_drop += 1
            elif status == "loop":
                count_loop += 1
            else:
                count_ok += 1

    return count_drop, count_loop, count_ok

if __name__ == "__main__":

    # Fill the graph
    topo = Graph()

    # Nodes
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

    # Links
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

    # Fill the routing tables
    start_time = time.time()
    compute_count = 0
    rt = RoutingTable(topo.nodes)
    for dst_node in topo.nodes:
        visited, path = dijsktra(topo, dst_node)
        compute_count += 1
        for src_node in path:
            # Add first path
            rt.add_route(src_node, dst_node, path[src_node])

            # Add second path
            topo.delete_link(src_node, path[src_node])
            second_visited, second_path = dijsktra(topo, dst_node)
            compute_count += 1
            if src_node in second_path:
                rt.add_route(src_node, dst_node, second_path[src_node])
            topo.add_link(src_node, path[src_node], 1)

    elapsed_time = time.time() - start_time

    # Print routing tables
    rt.print_table()

    # Test paths
    total_drop=0
    total_loop=0
    total_ok=0

    for node1, node2 in topo.links:
        rt_temp = copy.deepcopy(rt)
        print "** fail link " + node1 + "-" + node2
        rt_temp.delete_route_link(node1, node2)
        count_drop, count_loop, count_ok = test_paths(rt_temp.routes, topo.nodes)
        total_drop += count_drop
        total_loop += count_loop
        total_ok += count_ok

    for node in topo.nodes:
        rt_temp = copy.deepcopy(rt)
        print "** fail node " + node
        rt_temp.delete_route_node(node)
        count_drop, count_loop, count_ok = test_paths(rt_temp.routes, topo.nodes)
        total_drop += count_drop
        total_loop += count_loop
        total_ok += count_ok

    total_tested = total_drop + total_loop + total_ok
        
    # Print results
    print ""
    print "** Test Results:"
    print "number of nodes: " + str(len(topo.nodes))
    print "number of links: " + str(len(topo.links))
    print ""
    print "path compute cycles: " + str (compute_count)
    print "path compute time: " + str(elapsed_time)
    print ""
    print "path tested: " + str(total_tested)
    print "path drop: " + str(total_drop)
    print "path loop: " + str(total_loop)
    print "path ok: " + str(total_ok)
    print ""
    print "% drop: " + str(total_drop * 100 / total_tested)
    print "% loop: " + str(total_loop * 100 / total_tested)
    print "% ok: " + str(total_ok * 100 / total_tested)
    print ""

