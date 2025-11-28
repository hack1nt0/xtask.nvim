#include "debug.h"

// dancing links + Algorithm X
struct DLX {
    int sz, ncols;
    vector<int> X, Y, L, R, U, D;
    DLX(int ncols) : sz(ncols + 1), ncols(1), X(sz), Y(sz), L(sz), R(sz), U(sz), D(sz) {
        for (int c = 0; c <= ncols; c++) {
            Y[c] = 0, X[c] = c;
            L[c] = (c - 1 + sz) % (sz); 
            R[c] = (c + 1) % (sz);
            U[c] = D[c] = c;
        }
    }

    // add a new row
    void insert(vector<int>&& xs) {
        for (int i = 0; i < xs.size(); i++) {
            int cur = sz + i;
            int pre = sz + (i - 1 + xs.size()) % xs.size();
            int nxt = sz + (i + 1) % xs.size();
            int top = U[xs[i]];
            int bot = xs[i];
            U[cur] = top, D[top] = cur, U[bot] = cur, D[cur] = bot;
            L[cur] = pre, R[cur] = nxt;
            X[cur] = xs[i], Y[cur] = ncols;
        }
        sz += xs.size();
        ncols++;
    }

    vector<int> solve() {
        vector<int> ans;
        auto remove = [&](int x) -> void {
            L[R[x]] = L[x], R[L[x]] = R[x];
            for (int i = D[x]; i != x; i = D[i])
            for (int j = R[i]; j != i; j = R[j]) U[D[j]] = U[j], D[U[j]] = D[j];
        };
        auto regret = [&](int x) -> void {
            L[R[x]] = x, R[L[x]] = x;
            for (int i = D[x]; i != x; i = D[i])
            for (int j = R[i]; j != i; j = R[j]) U[D[j]] = j, D[U[j]] = j;
        };
        auto dfs = [&](auto& self) -> bool {
            int x = R[0];
            if (x == 0) {
                return true;
            }
            remove(x);
            for (int i = D[x]; i != x; i = D[i]) {
                ans.push_back(Y[i]);
                for (int j = R[i]; j != i; j = R[j]) remove(X[j]);
                bool res = self(self);
                for (int j = L[i]; j != i; j = L[j]) regret(X[j]);
                if (res) return true;
                else ans.pop_back();
            }
            regret(x);
            return false;
        };
        if (!dfs(dfs)) assert(ans.size() == 0);
        return ans;
    }
};