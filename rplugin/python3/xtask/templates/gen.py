import random as R
from cyaron import *

def random_tree(n):
    def oper(x):
        return "%d %d" % (x.start, x.end)
    print(n)
    graph = Graph.tree(n, 0.3, 0.3)
    print(graph.to_str(output=oper, shuffle=True))

def random_graph(n):
    def oper(x):
        return "%d %d  weight=%d,%d" % (x.start, x.end, x.weight[0], x.weight[1])
    def wg():
        return [random.randint(3, 5), random.randint(1, 10)]
    graph = Graph.hack_spfa(n, weight_gen=wg)
    print(graph.to_str(output=oper, shuffle=True))


    