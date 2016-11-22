"""K means"""
from random import sample
from typing import List, Tuple
from warnings import warn

from haversine import haversine

'''
K means using latitude, longitude.
'''


def k_means(data_points: List[Tuple[int, Tuple[float, float]]], k):
    """
    :param data_points: User points to be clustered.
    :param k: Number of clusters to be formed.
    :returns: Cluster, Centroids tuple.
    :rtype: Tuple[List[List[Tuple[int, Tuple[float, float]]]], List[Tuple[float, float]]
    """
    if len(data_points) < k:
        k = len(data_points)
        warn("K is too large", RuntimeWarning)
    if k == 0:
        raise Exception("K cannot be 0")

    if k == data_points:
        clusters = [[point] for point in data_points]  # type: Tuple[List[List[Tuple[int, Tuple[float, float]]]]
        centroids = [loc for user_id, loc in data_points]  # type: List[Tuple[float, float]]
        return clusters, centroids

    centroids = [point[1] for point in sample(data_points, k)]
    clusters = [[] for i in range(k)]
    prev_clusters = (() for i in range(k))

    while True:
        new_centroids = []
        clusters = [[] for i in range(k)]
        distances = [[haversine(centroids[i], point[1]) for point in data_points] for i in range(0, k)]

        dist = 0
        for distance_tuple in zip(*distances):
            indices = [i for i, x in enumerate(distance_tuple) if x == min(distance_tuple)]
            indices.sort()
            clusters[indices[0]].append(data_points[dist])
            dist += 1

        for cluster in clusters:
            lat, lon = 0, 0
            for point in cluster:
                lat += point[1][0]
                lon += point[1][1]
            # Basic latitude and longitude mean.
            # TODO: Replace with proper formula
            lat /= max(len(cluster), 1)
            lon /= max(len(cluster), 1)

            new_centroids.append((round(lat, 4), round(lon, 4)))

        match = 0
        for centroid in centroids:
            if centroid in new_centroids:
                match += 1
        if match == k:
            break
        match = 0
        for cluster in clusters:
            if cluster in prev_clusters:
                match += 1
        if match == k:
            break
        prev_clusters = clusters
        centroids = new_centroids

    return clusters, centroids
