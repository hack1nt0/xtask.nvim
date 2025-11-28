#ifndef INCLUDED_TRIE_H
#define INCLUDED_TRIE_H

#include "debug.h"

template <typename T>
struct Trie {
    const int null = 0;
    const int root = 1;
    int n = 2;
    vector<map<typename T::value_type, int>> children;
    vector<int> count, leaf;
    Trie(int maxn) : children(maxn), count(maxn), leaf(maxn) {}
    void insert(const T& xs) {
        int u = root;
        for (auto& x : xs) {
            count[u]++;
            int& v = children[u][x];
            if (v == null) v = n++;
            u = v;
        }
        count[u]++;
        leaf[u] = true;
    }

    void erase_prefix_with(const T& xs) {
        if (!contains(xs)) return;
        auto dfs = [&](auto& self, int u, auto it) {
            if (it == xs.end()) {
                count[u] = 0;
                children[u].clear();
                return;
            }
            int v = children[u][*it];
            count[u] -= count[v];
            self(self, v, std::next(it));
            count[u] += count[v];
        };
        dfs(dfs, root, xs.begin());
    }

    bool contains(const T& xs) {
        int u = root;
        for (auto& x : xs) {
            int v = children[u][x];
            if (!v) return false;
            u = v;
        }
        return true;
    }
    bool contains_prefix_of(const T& xs) {
        int u = root;
        for (auto& x : xs) {
            int& v = children[u][x];
            if (!v) break;
            if (leaf[v]) return true;
            u = v;
        }
        return leaf[u];
    }

    T::size_type size() { return count[root]; }
};

#endif
