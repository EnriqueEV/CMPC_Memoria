import pandas as pd
from pathlib import Path
from main.modulo_similaridad.similarity import SimilarityCalculator
from main.analysis.validation_calculator import ValidationCalculator
from main.modulo_recomendacion_roles.predictor import RoleRecommendationPredictor

MODEL_PATH = "models/modulo_recomendacion_roles/20251012_173859_TargetEnc_m20_s15_LGBM_set6_BEST.joblib"
OUTPUT_PATH = "data/outputs/test_full/filtered_recommendations_classifier.csv"
mkdir = Path(OUTPUT_PATH).parent
mkdir.mkdir(parents=True, exist_ok=True)


class CmpcRoleRecommender:
    def __init__(self, similarity_metric, resumen_data_path, n_top = 10, data_folder = "data", threshold=0.7, data_type = ".csv"):
        self.similarity_calculator = SimilarityCalculator(similarity_metric, n_top, data_folder, threshold, data_type)

        self.resumen_data = pd.read_csv(resumen_data_path)
        self.split_roles = self.similarity_calculator.get_split_df()
        self.predictions_df = None
        self.recommendations = None

    def run_recommendations(self):
        self.recommendations = self.similarity_calculator.run_recommendation(n_component=10, pca_kernel='rbf', pca_gamma='scale')
        return self.recommendations
    

    def validate_results(self):
        validator = ValidationCalculator(self.recommendations, self.split_roles, self.resumen_data,date_filter = "2025-06-07")
        results = validator.compute_validation()
        #validator.print_summary()
        return results
    
    def classify_recommendations(self, model_path=MODEL_PATH,threshold=0.5):
        self.predictor = RoleRecommendationPredictor(model_path,classification_threshold=threshold)
        
        features_df = self.predictor.prepare_features(self.recommendations, self.split_roles)
        self.predictor.load_model()
        self.predictions_df_full = self.predictor.predict(features_df)   
        self.predictions_df = self.predictor.filter_recommendations(self.predictions_df_full)



    def validate_classification_results(self):
        validator = ValidationCalculator(self.predictions_df, self.split_roles, self.resumen_data,date_filter = "2025-06-07")
        results = validator.compute_validation()
        #validator.print_summary()
        return results

    def prediction_stats(self):
        
        stats = self.predictor.get_statistics(self.predictions_df)
        
        print("\n" + "="*80)
        print("PREDICTION STATISTICS")
        print("="*80)
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"{key}: {value:.2f}")
            else:
                print(f"{key}: {value}")

    def export_data(self, recommendations_path, resumen_path, split_roles_path):
        
        if self.predictions_df is not None:
            self.predictor.export_predictions(
            self.predictions_df,
            output_path=OUTPUT_PATH,
            include_all=False
            )
        
        if self.recommendations is not None:
            self.recommendations.to_csv(recommendations_path, index=False)
        if self.resumen_data is not None:
            self.resumen_data.to_csv(resumen_path, index=False)
        if self.split_roles is not None:
            self.split_roles.to_csv(split_roles_path, index=False)


    def get_split_roles(self):
        return self.split_roles
    def get_recomendation(self):
        return self.predictions_df

if __name__ == "__main__":

    model_path = "models/modulo_recomendacion_roles/grid_search/catboost_best_model_20251102_183656.joblib"
    model_path_lightgbm = "models/modulo_recomendacion_roles/grid_search/lightgbm_best_model_20251102_183656.joblib"
    similarity_thresholds= [ 0.8, 0.9]
    for s_threshold in similarity_thresholds:
        print(f"\n--- SIMILARITY THRESHOLD: {s_threshold} ---")
        recommender = CmpcRoleRecommender(
            similarity_metric='cosine',
            resumen_data_path='data/processed/resumen_2025.csv',
            threshold=s_threshold,
        )
        recommendations = recommender.run_recommendations()
        thresholds= [0.5, 0.6, 0.7, 0.8, 0.9]
        validation_results = recommender.validate_results()
        print("VALIDATION RESULTS BEFORE CLASSIFICATION:")
        print(validation_results)
        for threshold in thresholds:
            print(f"\n--- CLASSIFICATION WITH THRESHOLD: {threshold} ---")
            recommender.classify_recommendations(model_path=model_path_lightgbm, threshold=threshold)
            validate_classification_results = recommender.validate_classification_results()
        
            print("VALIDATION RESULTS AFTER CLASSIFICATION:")
            print(validate_classification_results)
        
        base_path = 'data/outputs/'
        output_path = Path(base_path)
        output_path.mkdir(parents=True, exist_ok=True)

    # recommender.export_data(
    #     recommendations_path=output_path / 'role_recommendations.csv',
    #     resumen_path=output_path / 'resumen_data.csv',
    #     split_roles_path=output_path / 'split_roles_data.csv'
    # )