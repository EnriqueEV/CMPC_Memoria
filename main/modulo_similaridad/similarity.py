
import utils.utils as ut
import pandas as pd
from pathlib import Path

from main.modulo_similaridad.embeadding.features import build_user_features
from main.modulo_similaridad.embeadding.embeddings import compute_kpca
from sklearn.metrics.pairwise import cosine_similarity
from main.modulo_similaridad.similarity_calculation.potencial_roles import RoleRecommender

class SimilarityCalculator:

    def __init__(self, similarity_metric, n_top, data_folder = "data", threshold=0.7, data_type = ".csv"):
        
        self.similarity_metric = similarity_metric
        self.n_top = n_top
        self.threshold = threshold
        # Load and prepare data
        user_addr_df, agr_users_df, agr_1251_df = ut.load_data(Path(data_folder),data_type)
        if user_addr_df is None or agr_users_df is None or agr_1251_df is None:
            print("Error loading data.")
            return

        merged_df = ut.merge_df(user_addr_df, agr_users_df)
        self.split_df = ut.split_merge_df(merged_df)



    def compute_embeddings(self, department_weight = 1, function_weight = 1, roles_weight = 1, n_components=10, kernel='rbf', gamma='scale'):
        # Build multi-hot user feature matrix
        X = build_user_features(
            self.split_df,
            department_weight=department_weight,
            function_weight=function_weight,
            roles_weight=roles_weight,
        )

        # Compute KPCA embeddings
        emb_df, model = compute_kpca(
            X,
            n_components=n_components,
            kernel=kernel,
            gamma=gamma,
            random_state=42,
        )

        self.emb_df = emb_df
        self.model = model

    def compute_similarity(self):
        #TODO: Add other similarity metrics
        sim_matrix = cosine_similarity(self.emb_df.values)
        sim_df = pd.DataFrame(
            sim_matrix,
            index=self.emb_df.index,
            columns=self.emb_df.index
        )
        self.sim_df = sim_df

    def compute_role_recommendation(self):
        # For each user, find top N similar users above the threshold
        # TODO: Implement different type of similarity metrics to find new roles (now only cosine is implemented)
        recommender = RoleRecommender(
            roles_data=self.split_df,
            similarity_data=self.sim_df,
            similarity_threshold=self.threshold
        )
        self.recommendations = recommender.recommend_roles_for_all_users()


    def run_recommendation(self,n_component,pca_kernel,pca_gamma):
        self.compute_embeddings(n_components=n_component, kernel=pca_kernel, gamma=pca_gamma)
        self.compute_similarity()
        self.compute_role_recommendation()
        return self.get_recommendations()

    def get_embeddings(self):
        return self.emb_df
    
    def get_model(self):
        return self.model
    
    def get_split_df(self):
        return self.split_df

    def get_similarity_df(self):
        return self.sim_df
    
    def get_recommendations(self):
        return self.recommendations
    

if __name__ == "__main__":
    sim_calc = SimilarityCalculator(similarity_metric='cosine', n_top=5, threshold=0.7)
    recomendation = sim_calc.run_recommendation(n_component=10, pca_kernel='rbf', pca_gamma='scale')
    print(recomendation)
    print(recomendation.head())