
template <typename E, typename V>
struct DGraph {
    int n, m;
    vector<E> edge;
    vector<V> node;
    vector<vector<pair<int, int>>> g;

    DGraph(int n, int maxe) : n(n), m(0), edge(maxe), node(n), g(n);
    
    void insert(int u, int v, E e, V v) {
        edge[m] = e;
        g[u].emplace_back(v, m++);
        g[v].emplace_back(v, m++);
    }

    
    
};

struct UGraph : DGraph {
    
}