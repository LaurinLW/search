# Self written search engine

## Goal
- Index ~1 million Sites
- Query them in under 1 second
- Let this run on my virtual server (6 vCores, 8GB ram, 240GB storage) while also running other services

## Intitial Project Plan
1. Simple Crawler
2. BM25
3. search over cli
4. improve 1 & 2
5. build ui
6. store results of 1 & 2

## Where are we at?
Currently we are at 1. we will implement 2 next

## Current performance
Currently it only makes sense to measure the performance of the Crawler

Crawler:
|  #Sites  |  Spend Time  |
|----------|--------------|
|   1000   |   63.667s    |
|   1000   |   53.047s    |
|   1000   |   59.292s    |
|   10000  |   457.54s    |
