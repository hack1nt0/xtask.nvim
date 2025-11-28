
#include "debug.h"

#define ALL(x) x.begin(), x.end()
#define MAX(x, y) (x = max(x, y))
#define MIN(x, y) (x = min(x, y))
#define LEN(x) ((int) (x).size())

void solve(int nt) {
}

int main() {
    ios::sync_with_stdio(0), cin.tie(0), cout.tie(0);
    int T; cin >> T;
    for (int i = 1; i <= T; ++i) solve(i);
    return 0;
}

/*
1. order matters!
2. certains on fixed uncertains, i.e. enumerate ina a stupid way
3. <=>: e.g. decompose into subtasks, or tansfer to another classical/easy task...
4. make some observations, At least do something...
5. Nothing works, try DP?

*/
