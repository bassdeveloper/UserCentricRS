""" A non standard Quad Tree Module"""
from copy import deepcopy
from operator import itemgetter
from pickle import dump, load
from random import sample
from sys import getsizeof
from typing import List, Tuple

from haversine import haversine

from k_means import k_means
from recommender import RecommendationSystem


class QTreeNode:
    """
        Quad Tree node class.
        Stores data associated with the node in variable 'elements', child nodes in a list 'children', representative
        point as a Tuple(float, float), parent and dirty_size as int
    """

    def __init__(self, elements: List[Tuple[int, Tuple[float, float]]], rep_point: Tuple[float, float]):
        """
        Initializes node of QuadTree.
        :param elements: List of users and their location that exist in a node.
        :param rep_point: Representative/centroid point of the node.
        """
        self.elements = elements
        self.rep_point = rep_point
        self.parent = None  # type: QTreeNode
        self.children = []  # type: List[QTreeNode]
        self.dirty_size = 0

    def addChildren(self, children: List['QTreeNode']):
        """
        Adds a list of QTreeNode(s) as children of the calling node.
        :param children: List of children nodes.
        """
        for child in children:
            child.parent = self
        self.children.clear()
        self.children.extend(children)

    def dirty(self):
        """
        Returns what part of elements in the node were added and are not reflected in parent and children nodes.
        :returns: Ratio of dirty elements to all elements
        :rtype: bool
        """
        return self.dirty_size >= 0.1 * len(self.elements)


class QuadTree:
    """
        QuadTree divides given set of (user, user_location) tuples into a pyramid.
        Used for Location Aided Recommendation System.
        Uses another recommendation system for pyramid maintenance.
    """

    def __init__(self, r_system: RecommendationSystem, M=0.7):
        """
        Initializes the QuadTree
        :param M: Weight for LARS merge/split
        :param r_system: The recommendation system to use for pyramid maintenance.
        """
        self.root = None  # type: QTreeNode
        self.r_system = r_system
        self.M = M

    def to_quad_tree(self, elements: List[Tuple[int, Tuple[float, float]]]):
        """
        Convert given data to a QuadTree
        :param elements: List of user id and user location coordinate tuple
        """
        break_now = True
        # Initialize root
        rep_lat = 0
        rep_lon = 0
        for element in elements:
            rep_lat = element[1][0]
            rep_lon = element[1][1]
        rep_lat = rep_lat / max(len(elements), 1)
        rep_lon = rep_lon / max(len(elements), 1)
        self.root = QTreeNode(elements, (rep_lat, rep_lon))
        work_level = [self.root]

        level_no = 1
        while True:
            print("Building level", level_no)
            level_no += 1
            new_level = []
            # Split each node at current height level
            level_built_pct = 0

            for node in work_level:
                if len(node.elements) >= 4:
                    clusters, centroids = k_means(node.elements, 4)
                    nodes = [QTreeNode(cluster, centroid) for cluster, centroid in zip(clusters, centroids)]
                    if self.check_split(node, nodes):
                        break_now = False
                        new_level.extend(nodes)
                        node.addChildren(nodes)
                level_built_pct += 100 / len(work_level)
                print("Level built {0}%".format(level_built_pct))
            # No node was split. Algorithm converges.
            if break_now:
                break
            work_level = new_level
            break_now = True

    # noinspection PyMethodMayBeStatic
    def __scalability_change__(self, un_split_node: QTreeNode, split_nodes: List[QTreeNode]):
        """
        Calculates scalability change when a node is merge/split.
        :param un_split_node: Node that is split or formed by merging the split nodes.
        :param split_nodes: Nodes formed by splitting a given node or that will be merged into a single node.
        :returns: scalability change
        :rtype: float
        """
        sum_size_split_nodes = 0
        for node in split_nodes:
            for element in node.elements:
                sum_size_split_nodes += getsizeof(element)
            sum_size_split_nodes += getsizeof(node.rep_point)

        sum_size_un_split_node = 0
        for element in un_split_node.elements:
            sum_size_un_split_node += getsizeof(element)
        sum_size_un_split_node += getsizeof(un_split_node.rep_point)
        return sum_size_split_nodes * 100 / (sum_size_split_nodes + sum_size_split_nodes)

    # noinspection PyMethodMayBeStatic
    def __scalability_change__actual__(self, un_split_node: QTreeNode, split_nodes: List[QTreeNode]):
        """
        Calculates scalability change when a node is merge/split.
        :param un_split_node: Node that is split or formed by merging the split nodes.
        :param split_nodes: Nodes formed by splitting a given node or that will be merged into a single node.
        :returns: scalability change
        :rtype: float
        """
        return getsizeof(un_split_node) * 100 / (getsizeof(un_split_node) + getsizeof(split_nodes))

    def __locality_change__(self, un_split_node: QTreeNode, split_nodes: List[QTreeNode], is_checking_split):
        """
        Check if we should split/merge into the node further more.
        :param un_split_node: The un-split node is under consideration for splitting.
        :param split_nodes: List of nodes created by splitting the un-split node.
        :returns: Locality change
        :rtype: float
        """
        un_split_node.elements.sort(key=itemgetter(0))
        # Check if cluster splits into k-1 empty clusters and itself. If so then stop splitting. Algorithm converged.
        for node in split_nodes:
            node.elements.sort(key=itemgetter(0))
            if node.elements == un_split_node.elements:
                return 0

        # Predict users without splitting
        k = int(pow(len(un_split_node.elements), 1))
        # Overridden value for testing purposes.
        k = 4
        locality_change = 0
        random_user_sample = sample(un_split_node.elements, k)
        for user in random_user_sample:
            # Predict before splitting
            closest_users_un_split_data = self.r_system.__knn__(user, un_split_node.elements, e=4, k=k)
            recommended_for_un_split_data = self.r_system.knn(user, e=4, k=k, seed_set=closest_users_un_split_data,
                                                              n=10)

            # Predict users after splitting
            for node in split_nodes:
                closest_users_split_data = self.r_system.__knn__(user, node.elements, e=4, k=k)
                recommended_for_split_data = self.r_system.knn(user, e=4, k=k, seed_set=closest_users_split_data, n=10)

                movies_recommended_split_data = set([movie_id for movie_id, movie_score in recommended_for_split_data])
                movies_recommended_un_split_data = set(
                    [movie_id for movie_id, movie_score in recommended_for_un_split_data])

                total_set_length = len(movies_recommended_split_data) + len(movies_recommended_un_split_data)
                if total_set_length > 0:
                    # Jaccard Coefficient
                    if is_checking_split:
                        locality_change += len(
                            movies_recommended_split_data - movies_recommended_un_split_data) * 2 / total_set_length
                    else:
                        locality_change += len(
                            movies_recommended_un_split_data - movies_recommended_split_data) * 2 / total_set_length
        return locality_change * 100 / (k * k)

    def check_merge(self, node: QTreeNode, children: List[QTreeNode]):
        """
        Check if we should merge the node.
        :param node: Existing node we have i.e. the node formed after merge.
        :param children: List of nodes we are considering for a merge.
        :returns: Locality loss
        :rtype: bool
        """
        n_non_empty_child = 0
        for child in children:
            if child.elements:
                n_non_empty_child += 1
        if n_non_empty_child != len(children):
            return True

        scalability_change = (1 - self.M) * self.__scalability_change__actual__(node, children)
        locality_change = self.M * self.__locality_change__(node, children, False)
        return scalability_change > locality_change

    def check_split(self, node: QTreeNode, children: List[QTreeNode]):
        """
        Check if we should split the node further more.
        :param node: The un-split node is under consideration for splitting.
        :param children: List of nodes created by splitting the un-split node.
        :returns: Locality gain
        :rtype: bool
        """
        scalability_change = (1 - self.M) * self.__scalability_change__actual__(node, children)
        locality_change = self.M * self.__locality_change__(node, children, True)
        return scalability_change < locality_change

    def nearest_cell(self, user_loc: Tuple[float, float], level: int = None):
        """
        Find the cell which the given input location will fall into.
        :param level: Optional limitation on lars depth.
        :param user_loc: User location coordinate tuple.
        :returns: Lowest maintained cell.
        :rtype: List[Tuple[int, Tuple[float, float]]]
        """
        closest_node = self.root
        min_dist = haversine(closest_node.rep_point, user_loc)
        break_now = True
        cur_level = 1
        while True:
            if level and cur_level == level:
                break
            cur_level += 1
            for child_node in closest_node.children:
                n_dist = haversine(child_node.rep_point, user_loc)
                if n_dist < min_dist:
                    closest_node = child_node
                    min_dist = n_dist
                    break_now = False
            if break_now:
                break
            break_now = True

        return closest_node.elements

    def maintenance(self, node: QTreeNode):
        """
        Maintain Quad Tree. Look up LARS maintenance for details.
        :param node: Node to be updated.
        """
        if node.dirty():
            # Have to use bool() because straight forward comparison would need another None check in else part because
            # of incorrect type hinting. Get your shit together python.
            if bool(node.children):
                if self.check_merge(node, node.children):
                    node.elements = [element for child in node.children for element in child.elements]
                    node.children.clear()
                    node.dirty_size = 0
            else:
                clusters, centroids = k_means(node.elements, 4)
                nodes = [QTreeNode(cluster, centroid) for cluster, centroid in zip(clusters, centroids)]
                if self.check_split(node, nodes):
                    node.addChildren(nodes)
                    for child in node.children:
                        self.maintenance(child)
                    node.dirty_size = 0

        if not bool(node.children):
            clusters, centroids = k_means(node.elements, 4)
            nodes = [QTreeNode(cluster, centroid) for cluster, centroid in zip(clusters, centroids)]
            if self.check_split(node, nodes):
                node.addChildren(nodes)
                for child in node.children:
                    self.maintenance(child)
                node.dirty_size = 0

    def add_user(self, user_info: Tuple[int, Tuple[float, float]]):
        """
        Adds new user to QuadTree and calls maintenance.
        :param user_info: User id, user location coordinate tuple
        """
        root = self.root
        root.elements.append(user_info)
        closest_node = root
        path = [root]
        root.dirty_size += 1
        user_loc = user_info[1]
        min_dist = haversine(closest_node.rep_point, user_loc)
        break_now = True
        while True:
            for child_node in closest_node.children:
                n_dist = haversine(child_node.rep_point, user_loc)
                if n_dist < min_dist:
                    path.append(child_node)
                    closest_node = child_node
                    min_dist = n_dist
                    closest_node.elements.append(user_info)
                    child_node.dirty_size += 1
                    break_now = False
            if break_now:
                break
            break_now = True
        # Check split.
        path.reverse()
        for node in path:
            self.maintenance(node)

    def remove_user(self, user_info: Tuple[int, Tuple[float, float]]):
        """
        Adds new user to QuadTree and calls maintenance.
        :param user_info: User id, user location coordinate tuple
        """
        root = self.root
        root.elements.remove(user_info)
        closest_node = root
        path = [root]
        root.dirty_size += 1
        user_loc = user_info[1]
        min_dist = haversine(closest_node.rep_point, user_loc)
        break_now = True
        while True:
            for child_node in closest_node.children:
                n_dist = haversine(child_node.rep_point, user_loc)
                if n_dist < min_dist:
                    path.append(child_node)
                    closest_node = child_node
                    min_dist = n_dist
                    closest_node.elements.remove(user_info)
                    child_node.dirty_size = max(child_node.dirty_size - 1, 0)
                    break_now = False
            if break_now:
                break
            break_now = True
        # Check split.
        path.reverse()
        for node in path:
            self.maintenance(node)

    def bf_traverse(self):
        """
        Breadth wise traversal of the tree
        """
        next_nodes = [self.root]
        while True:
            nodes = deepcopy(next_nodes)  # type: List[QTreeNode]
            next_nodes.clear()
            if not nodes:
                break
            for node in nodes:
                next_nodes.extend(node.children)
                print(node, "->", node.children)

    def export_tree(self, filename: str):
        """Pickle the tree for later use
        :param filename: File path to store this QuadTree at.
        """
        with open(filename, "wb") as outfile:
            dump(self, outfile)

    @staticmethod
    def import_tree(filename: str):
        """Load tree from file
        :param filename: Input file path to the pickled QuadTree object.
        :returns: QuadTree stored in file.
        :rtype: QuadTree
        """
        with open(filename, "rb") as infile:
            return load(infile)
