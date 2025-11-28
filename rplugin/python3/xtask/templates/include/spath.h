#ifndef INCLUDED_SHORTESTPATH_H
#define INCLUDED_SHORTESTPATH_H

#include "debug.h"

template <typename T>
struct SPath {
    int n;
    vector<vector<pair<int, T>>> g;
    vector<T> dist;
    vector<int> prev;
    
    SPath(int n) : n(n), g(n), dist(n), prev(n) {}
    
    void insert(int u, int v, T c) {
        g[u].push_back({v, c});
    }

    /*
        Return: false if negative cycle(s) exists.
    */
    template <class CMP = std::less<>>
    bool operator()(int s, T oo, CMP cmp = {}) {
        fill(dist.begin(), dist.end(), oo);
        fill(prev.begin(), prev.end(), -1);
        vector<int> upds(n, 0);
        queue<pair<int, T>> que;
        que.push({s, 0});
        dist[s] = 0;
        prev[s] = 0;
        while (que.size()) {
            auto [u, du] = que.front();
            que.pop();
            if (cmp(dist[u], du)) continue;
            for (auto [v, duv] : g[u]) if (cmp(du + duv, dist[v])) {
                dist[v] = du + duv;
                prev[v] = u;
                upds[v]++;
                if (upds[v] >= n) return false;
                que.push({v, dist[v]});
            }
        }
        return true;
    }

    T operator[](int i) { return dist[i]; }
    auto begin() { return dist.begin(); }
    auto end() { return dist.end(); }
};

#endif