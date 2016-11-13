import pickle
from operator import itemgetter

import KMeans


# TODO: List comprehensions.
# TODO: Weighted merge of results of split nodes.
# TODO: Add Representative points for each node to make user look up faster and incremental update possible.

class QTreeNode:
    def __init__(self, elements):
        self.next_level = []
        self.elements = elements

    def setNext(self, next_level):
        self.next_level = next_level


class QuadTree:
    def __init__(self, r_system):
        self.levels = []
        self.r_system = r_system

    def to_quad_tree(self, elements, k):
        """Convert input data to QuadTree based on their location"""
        curr_level = 0
        break_now = True
        # Initialize root
        levels = [[QTreeNode(elements)]]
        work_level = levels[curr_level]
        while True:
            new_level = []

            # Split each node at current height level
            for node in work_level:
                if len(node.elements) >= k:
                    nodes = [QTreeNode(cluster) for cluster in KMeans.k_means(node.elements, k)]
                    if self.check_split(node, nodes, k):
                        break_now = False
                        new_level.extend(nodes)
                        node.setNext(nodes)
            curr_level += 1

            # No node was split. Algorithm converges.
            if break_now:
                break
            work_level = new_level
            levels.append(new_level)
            break_now = True

        # Get rid of user location used to create tree. Only user IDs are kept.
        for level in levels:
            cleaned_nodes = []
            for node in level:
                user_list = []
                for user, location in node.elements:
                    user_list.append(user)
                cleaned_nodes.append(QTreeNode(user_list))
            self.levels.append(cleaned_nodes)

    def check_split(self, cur_node, nodes, k):
        """Check if we should split the node further more"""
        # Check if cluster splits into k-1 empty clusters and itself. If so then stop splitting. Algorithm converged.
        for node in nodes:
            node.elements.sort(key=itemgetter(0))
            if node.elements == cur_node.elements:
                return False

        # Predict users without splitting
        pred_curr_users = self.r_system.__knn__((cur_node.elements[0][0], cur_node.elements[0][1]), cur_node.elements,
                                                k)

        # Predict users after splitting
        pred_split_users = []
        for node in nodes:
            if len(node.elements) > 0:
                result = self.r_system.__knn__((node.elements[0][0], node.elements[0][1]), node.elements, int(k / 4))
                pred_split_users.extend(result)

        # Decide splitting further. Do not split if we have 75% similar prediction.
        # Calculated using Jaccard Coefficient
        return len(set(pred_curr_users).intersection(set(pred_split_users))) * 200 / (
            len(pred_curr_users) + len(pred_split_users)) < 75

    def export_tree(self, filename):
        """Pickle the tree for later use"""
        with open(filename, "wb") as outfile:
            pickle.dump(self, outfile)

    @staticmethod
    def import_tree(filename):
        """Load tree from file"""
        with open(filename, "rb") as infile:
            return pickle.load(infile)
