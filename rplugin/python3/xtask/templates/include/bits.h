#ifndef INCLUDED_BITS_H
#define INCLUDED_BITS_H

#include "debug.h"
#include <bit>




template <typename T>
int bitat(T x, int b) {
    return x >> b & 1;
}

template <typename T>
int bitcnt(T x) {
    return popcount(x);
}

template <typename T>
int count_1s(T x) {
    return popcount(x);
}

template <typename T>
int count_0s(T x) {
    return popcount(x);
}

template <size_t N>
vector<int> subsets(bitset<N>& S) {
    log2()
}

#endif
