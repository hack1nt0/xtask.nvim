#ifndef INCLUDED_EPATH_H
#define INCLUDED_EPATH_H

#include "debug.h"

//Hierholzer Algo. [https://oi-wiki.org/graph/euler/]
//how to find cycle?

// eulerain path of undirected graph
vector<int> epath(vector<vector<pair<int, int>>> g) {
    int n = g.size();
    int m = 0;
    for (int i = 0; i < n; i++) for (auto [j, e] : g[i]) m = max(m, e);
    m++;
    vector<int> res;
    vector<bool> vis(m);
    auto dfs = [&](auto& self, int u) -> void {
        res.push_back(u);
        while (g[u].size()) {
            auto [v, e] = g[u].back(); g[u].pop_back();
            if (vis[e]) continue;
            vis[e] = true;
            self(self, v);
        }
    };
    vector<int> st;
    for (int i = 0; i < n; i++) if (g[i].size() % 2) st.push_back(i);
    assert(st.size() == 2 || st.size() == 0);
    int s = 0;
    if (st.size()) s = st.front();
    dfs(dfs, s);
    
    return res;
}



#endif