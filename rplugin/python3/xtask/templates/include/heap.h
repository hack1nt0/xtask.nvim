#ifndef INCLUDED_HEAP_H
#define INCLUDED_HEAP_H

#include "debug.h"

template<typename T>
using MinHeap = priority_queue<T, vector<T>, greater<T>>;

template<typename T>
using MaxHeap = priority_queue<T, vector<T>, less<T>>;

template<typename T, int K, class C=std::less<T>>
struct KthHeap {
    multiset<T, C> c;
    void push(const T& v) {
        c.insert(v);
        if (c.size() > K) c.erase(prev(c.end()));
    }
    const T& top() { return *c.begin(); }
    void pop() { c.erase(c.begin()); }
    int size() { return c.size(); }
};

template<typename T, int K>
using KthMaxHeap = KthHeap<T, K, greater<T>>;

template<typename T, int K>
using KthMinHeap = KthHeap<T, K, less<T>>;

#endif
