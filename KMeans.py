import random
import sys

import zipcode as zipcode


# TODO: put in a function to provide interface. Will take zip list as parameter. Will be called by QuadTree.
try:
    zip_list = [zipcode.isequal(code) for code in open(sys.argv[1], "r")]
except FileNotFoundError or FileExistsError as e:
    print("Could not open file")
else:
    medoids = random.sample(zip_list, 4)
    newmedoids = []
    clusters = [[], [], [], []]
    distances = [[], [], [], []]

    while True:
        clusters = [[], [], [], []]
        coords = lambda code: (code.lat, code.lon)
        getindex = lambda dists, value: dists.index(value)
        distances = [[zipcode.haversine(coords(medoids[dist]), coords(code)) for code in zip_list] for i in range(0, 4)]

        dist = 0
        for distance_tuple in zip(*distances):
            index = getindex(list(distance_tuple), min(distance_tuple))
            clusters[index].append(zip_list[dist])
            dist += 1

        lat, lon = 0, 0
        for cluster in clusters:
            for points in cluster:
                lat = points.lat
                lon = points.lon
            lat /= len(cluster)
            lon /= len(cluster)
            nearestZip = None
            # 12425 is the largest distance between any two cities on earth
            for dist in range(0, 12425):
                nearZips = zipcode.isinradius((lat, lon), dist)
                if len(nearZips) > 0:
                    minD = dist + 1
                    for zip_code in nearZips:
                        if zipcode.haversine((lat, lon), (zip_code.lat, zip_code.lon)) < minD:
                            minD = zipcode.haversine((lat, lon), (zip_code.lat, zip_code.lon)) < minD
                            nearestZip = zip_code
                    break
            newmedoids.append(nearestZip)

        if medoids == newmedoids:
            break
        medoids = newmedoids

    print(clusters)
