#ifndef INCLUDED_HASH_H
#define INCLUDED_HASH_H

#include "debug.h"

template<class T1, class T2>
struct std::hash<pair<T1, T2>>
{
    std::size_t operator()(const pair<T1, T2>& s) const noexcept
    {
        std::size_t h1 = std::hash<T1>{}(s.first);
        std::size_t h2 = std::hash<T2>{}(s.second);
        return h1 ^ (h2 << 1);
    }
};

#endif