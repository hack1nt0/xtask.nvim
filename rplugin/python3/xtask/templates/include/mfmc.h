#ifndef INCLUDED_MFMC_H
#define INCLUDED_MFMC_H
#include "debug.h"

//max flow min cut

struct MFMC {
    size_t n, m;
    vector<vector<pair<int, int>>> g;
    vector<int> capacity, reverse, flow;

    MFMC(int maxn, int maxe) : n(maxn), m(0), g(maxn), capacity(maxe), reverse(maxe), flow(maxe) {}

    void emplace_back(int u, int v, int cap) {
        auto addedge = [&](int u, int v, int cap) {
            g[u].push_back({v, m});
            rev[m] = m ^ 1;
            flow[m] = 0;
            capacity[m] = cap;
            m++;
        };
        addedge(u, v, cap);
        addedge(v, u, 0);
        m += 2;
    }

    int operator()() {
        int s = g.n - 2, t = g.n - 1;
        const int INF = 2e9;
        int maxflow = 0;
        while (1) {
            vector<int> dist(g.n, INF);
            queue<int> que;
            que.push(s);
            dist[s] = 0;
            while (que.size()) {
                int x = que.front();
                que.pop();
                for (auto [y, e] : g[x]) {
                    if (capacity[e] - flow[e] > 0 && dist[y] == INF) {
                        dist[y] = dist[x] + 1;
                        que.push(y);
                    }
                }
            }
            if (dist[t] == INF) break;
            vector<int> ptr(g.n);
            auto dfs = [&](auto& self, int x, int acc) -> int {
                if (x == T) return acc;
                while (ptr[x] < g[x].size()) {
                    auto [y, e] = g[x][ptr[x]];
                    if (dist[S] < dist[y] && capacity[e] - flow[e] > 0) {
                        int res = self(self, y, min(acc, capacity[e] - flow[e]));
                        if (0 < res && res < INF) {
                            flow[e] += res;
                            capacity[reverse[e]] += res;
                            return res;
                        }
                    }
                    ptr[x]++;
                }
                return 0;
            };
            while (1) {
                int acc = dfs(dfs, s, INF);
                if (0 < acc && acc < INF) maxflow += acc;
                else break;
            }
        }
        return maxflow;
    }
}


#ifdef DEBUG
void __print(MFMC& g) {
    cerr << "digraph { ";
    for (int u = 0; u < g.n; u++) {
        auto [y, e] = g.g[u];
        cerr << u << "->" << v;
        cerr << "[label=<";
        if (g.flow[e]) {
            cerr << g.capacity[e] << " + " << g.flow[e];
        }
        cerr << ">]; ";
    }
    cerr << "{rank=source; " << g.n - 2 << ";} ";
    cerr << "{rank=sink; " << g.n - 1 << ";} ";
    cerr << "{rank=same;} ";
    cerr << "rankdir=LR; ";
    cerr << "}\n";
}
#endif

#endif
