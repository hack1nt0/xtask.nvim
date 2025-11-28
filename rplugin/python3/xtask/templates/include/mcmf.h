#ifndef INCLUDED_MAXFLOW_H
#define INCLUDED_MAXFLOW_H
#include "debug.h"

//min cost max flow

struct MCMF {
    
    using vi = vector<int>;
    vector<vi> adj;
    vi s, t, cap, rev, flow, cost;
    int n, m;

    MCMF(int n) :
        adj(n), s(), t(), cap(), rev(), flow(), cost(), n(n), m(0)
    {}

    void emplace_back(int S, int T, int CAP, int COST) {
        auto addedge = [&](int S, int T, int E, int REV, int CAP, int COST) {
            adj[S].push_back(E);
            s.push_back(S);
            t.push_back(T);
            rev.push_back(REV);
            flow.push_back(0);
            cap.push_back(CAP);
            cost.push_back(COST);
        };
        addedge(S, T, m, m + 1, CAP, COST);
        addedge(T, S, m + 1, m, 0, 0);
        m += 2;
    }

    int other(int e, int x) { return x == s[e] ? t[e] : s[e]; }
    
    
    int operator()(int S, int T, int FLOW) {
        using pii = pair<int, int>;
        using vi = vector<int>;
        const int INF = 2e9;
        int ret = 0;
        while (FLOW > 0) {
            vector<pii> dist(g.n, {INF, INF});
            queue<int> que;
            dist[S] = {0, -INF};
            que.push(S);
            vi pre(g.n);
            while (que.size()) {
                int x = que.front(); que.pop();
                for (int e: g.adj[x]) {
                    int y = g.other(e, x);
                    if (!(g.cap[e] - g.flow[e] > 0)) continue;
                    pii disty{dist[x].first + g.cost[e], -min(-dist[x].second, g.cap[e])};
                    if (disty < dist[y]) {
                        dist[y] = disty;
                        pre[y] = e;
                        que.push(y);
                    }
                }
            }
            if (dist[T].first == INF) break;
            LOG(dist[T])
            int flowdel = min(FLOW, -dist[T].second);
            ret += dist[T].first * flowdel;
            FLOW -= flowdel;
            int V = T;
            while (V != S) {
                int e = pre[V];
                g.flow[e] += flowdel;
                g.cap[g.rev[e]] += flowdel;
                V = g.other(e, V);
            }
        }
        return ret;
}

};


#ifdef DEBUG
void PLT(MCMF& g) {
    cerr << "digraph { ";
    for (int e = 0; e < g.m; ++e) {
        cerr << g.s[e] << "->" << g.t[e];
        cerr << "[label=<";
        if (g.flow[e]) {
            cerr << g.flow[e] << "/" << g.cap[e];
            if (g.cost[e]) cerr << "=" << g.cost[e] * g.flow[e];
        }
        cerr << ">]; ";
    }
    cerr << "{rank=source; " << 0 << ";} ";
    cerr << "{rank=sink; " << g.n - 1 << ";} ";
    cerr << "{rank=same;} ";
    cerr << "rankdir=LR; ";
    cerr << "}\n";
}
#endif

#endif
