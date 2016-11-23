""" test shit in here"""
from recommender import RecommendationSystem

r_system = RecommendationSystem()
recommendations = r_system.getRecommendation()
print("Movies recommended for you:")
print("\n".join(recommendations))
