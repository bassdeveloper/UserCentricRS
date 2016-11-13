import random

import zipcode as zipcode
from haversine import haversine

'''
K medoids using zipcodes. Very slow. May not converge. Won't be fixed. Kept if required later.
K means using latitude, longitude.
'''

# TODO: Change loops to comprehensions


@DeprecationWarning
def k_medoids(zip_list, k):
    if len(zip_list) < k:
        raise Exception("K too large")
    if k == 0:
        raise Exception("K cannot be 0")

    if k == zip_list:
        return zip_list

    medoids = random.sample(zip_list, k)
    past_seen_medoids = []
    clusters = [[] for i in range(k)]

    prev_clusters = (() for i in range(k))
    while True:
        newmedoids = []
        clusters = [[] for i in range(k)]
        coords = lambda code: (code.lat, code.lon)
        distances = [[zipcode.haversine(coords(medoids[i]), coords(code)) for code in zip_list] for i in range(0, k)]

        dist = 0
        for distance_tuple in zip(*distances):
            indices = [i for i, x in enumerate(distance_tuple) if x == min(distance_tuple)]
            zip_to_add_to = medoids[0]
            index = 0
            for i in range(0, len(indices)):
                if medoids[indices[i]].zip < zip_to_add_to.zip:
                    index = i
            clusters[indices[index]].append(zip_list[dist])
            dist += 1

        for cluster in clusters:
            lat, lon = 0, 0
            nearest_zip = None
            for points in cluster:
                lat += points.lat
                lon += points.lon
            # Basic mean of latitude and longitudes.
            # TODO: Using the proper formula.
            lat /= max(len(cluster), 1)
            lon /= max(len(cluster), 1)
            # 12425 is the largest distance between any two cities on earth

            for dist in range(0, 13000, 20):
                nearZips = zipcode.isinradius((lat, lon), dist)
                if len(nearZips) > 0:
                    min_dist = dist * 2
                    for zip_code in nearZips:
                        if zip_code.zip not in [zipp.zip for zipp in newmedoids]:
                            if zipcode.haversine((lat, lon), (zip_code.lat, zip_code.lon)) < min_dist:
                                min_dist = zipcode.haversine((lat, lon), (zip_code.lat, zip_code.lon))
                                nearest_zip = zip_code

                if nearest_zip is not None:
                    break
            newmedoids.append(nearest_zip)

        medoids_str_lst = [zipp.zip for zipp in medoids]
        new_medoids_str_lst = [zipp.zip for zipp in newmedoids]

        medoids_str_lst.sort()
        new_medoids_str_lst.sort()

        # Place holder break conditions. Can be improved.
        if medoids_str_lst in past_seen_medoids or new_medoids_str_lst in past_seen_medoids:
            print("Special exit")
            break

        past_seen_medoids.append(medoids)

        if medoids_str_lst == new_medoids_str_lst:
            break

        clusters_str_lst = ((zipp.zip for zipp in cluster) for cluster in clusters)

        if prev_clusters == clusters:
            break

        prev_clusters = clusters_str_lst
        medoids = newmedoids
    return clusters


def k_means(data_points, k):
    if len(data_points) < k:
        raise Exception("K too large")
    if k == 0:
        raise Exception("K cannot be 0")

    if k == data_points:
        return data_points
    centroids = [point[1] for point in random.sample(data_points, k)]
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
    return clusters
