"""
Simple prediction module for role recommendations using pre-trained models.

This module loads pre-trained classifier models and makes predictions on 
similarity-based recommendations to filter high-quality recommendations.
"""

import pandas as pd
import joblib
from pathlib import Path
from typing import Optional, Dict, Any


class RoleRecommendationPredictor:
    """
    Predictor for filtering role recommendations using pre-trained models.
    
    This class loads a trained model and makes predictions on new recommendations
    to determine which ones should be accepted.
    """
    
    def __init__(
        self,
        model_path: str,
        classification_threshold: float = 0.5
    ):
        """
        Initialize the predictor.
        
        Args:
            model_path: Path to the trained model (.joblib file)
            classification_threshold: Threshold for binary classification (default: 0.5)
        """
        self.model_path = Path(model_path)
        self.classification_threshold = classification_threshold
        self.model = None
        self.pipeline = None
        
        # Validate inputs
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        if not 0 <= classification_threshold <= 1:
            raise ValueError("Classification threshold must be between 0 and 1")
    
    def load_model(self) -> None:
        """
        Load the trained model from disk.
        """
        self.pipeline = joblib.load(self.model_path)
    
    def load_recommendations(
        self,
        recommendations_path: str
    ) -> pd.DataFrame:
        """
        Load recommendations from CSV file.
        
        Args:
            recommendations_path: Path to recommendations CSV file
            
        Returns:
            DataFrame with recommendations
        """
        df = pd.read_csv(recommendations_path)
        return df
    
    def prepare_features(
        self,
        recommendations_df: pd.DataFrame,
        user_metadata_df: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Prepare features for prediction.
        
        Args:
            recommendations_df: DataFrame with recommendations
            user_metadata_df: Optional DataFrame with user metadata (Departamento, Función)
            
        Returns:
            DataFrame ready for prediction
        """
        # Make a copy to avoid modifying original
        df = recommendations_df.copy()
        
        # If user metadata is provided, merge it
        if user_metadata_df is not None:
            if 'Usuario' in df.columns:
                # user_metadata_df should have 'Usuario', 'Departamento', 'Función' columns
                required_meta_cols = ['Usuario', 'Departamento', 'Función']
                missing_meta_cols = [col for col in required_meta_cols if col not in user_metadata_df.columns]
                
                if not missing_meta_cols:
                    # Merge on Usuario column
                    df = df.merge(
                        user_metadata_df[['Usuario', 'Departamento', 'Función']],
                        on='Usuario',
                        how='left'
                    )
                    
                    # Rename to expected format for model (DEPARTAMETNO, FUNCION)
                    df = df.rename(columns={
                        'Departamento': 'DEPARTAMETNO',
                        'Función': 'FUNCION'
                    })
        
        # Ensure required columns exist
        required_cols = ['DEPARTAMETNO', 'FUNCION', 'ROL']
        
        # Check if we have the required columns or can create them
        # recommendations_df has 'Recommended_Role' column
        if 'ROL' not in df.columns:
            if 'Recommended_Role' in df.columns:
                df['ROL'] = df['Recommended_Role']
            elif 'Recomendation' in df.columns:
                df['ROL'] = df['Recomendation']
        
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            # Fill with unknown values
            for col in missing_cols:
                df[col] = 'UNKNOWN'
        
        df = df.dropna()
        return df
    
    def predict(
        self,
        features_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Make predictions on prepared features.
        
        Args:
            features_df: DataFrame with features ready for prediction
            
        Returns:
            DataFrame with predictions and confidence scores
        """
        if self.pipeline is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        # Get required columns for the model
        required_cols = ['DEPARTAMETNO', 'FUNCION', 'ROL']
        X = features_df[required_cols].copy()
        
        # Make predictions
        predictions = self.pipeline.predict(X)
        probabilities = self.pipeline.predict_proba(X)
        
        # Add predictions to DataFrame
        # Use correct column name: 'Recommended_Role'
        output_cols = ['Usuario']
        if 'Recommended_Role' in features_df.columns:
            output_cols.append('Recommended_Role')
        elif 'Recomendation' in features_df.columns:
            output_cols.append('Recomendation')
        
        result_df = features_df[output_cols].copy()
        result_df['Prediction'] = predictions
        result_df['Confidence'] = probabilities[:, 1]  # Probability of positive class
        
        return result_df
    
    def filter_recommendations(
        self,
        predictions_df: pd.DataFrame,
        threshold: Optional[float] = None
    ) -> pd.DataFrame:
        """
        Filter recommendations based on confidence threshold.
        
        Args:
            predictions_df: DataFrame with predictions
            threshold: Optional custom threshold (uses instance threshold if None)
            
        Returns:
            Filtered DataFrame with only accepted recommendations
        """
        if threshold is None:
            threshold = self.classification_threshold
        
        # Filter by confidence threshold
        filtered_df = predictions_df[predictions_df['Confidence'] >= threshold].copy()
        
        return filtered_df
    
    def export_predictions(
        self,
        predictions_df: pd.DataFrame,
        output_path: str,
        include_all: bool = False
    ) -> None:
        """
        Export predictions to CSV file.
        
        Args:
            predictions_df: DataFrame with predictions
            output_path: Path to save CSV file
            include_all: If True, include all predictions; if False, only filtered ones
        """
        if not include_all:
            predictions_df = self.filter_recommendations(predictions_df)
        
        # Sort by confidence descending
        predictions_df = predictions_df.sort_values('Confidence', ascending=False)
        
        predictions_df.to_csv(output_path, index=False)
    
    def get_statistics(
        self,
        predictions_df: pd.DataFrame,
        filtered_df: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Calculate statistics about predictions.
        
        Args:
            predictions_df: DataFrame with all predictions
            filtered_df: Optional DataFrame with filtered recommendations
            
        Returns:
            Dictionary with statistics
        """
        if filtered_df is None:
            filtered_df = self.filter_recommendations(predictions_df)
        
        stats = {
            'total_recommendations': len(predictions_df),
            'filtered_recommendations': len(filtered_df),
            'filtering_rate': (1 - len(filtered_df)/len(predictions_df)) * 100,
            'avg_confidence_all': predictions_df['Confidence'].mean(),
            'avg_confidence_filtered': filtered_df['Confidence'].mean() if len(filtered_df) > 0 else 0,
            'min_confidence': predictions_df['Confidence'].min(),
            'max_confidence': predictions_df['Confidence'].max(),
            'positive_predictions': int((predictions_df['Prediction'] == 1).sum()),
            'positive_rate': (predictions_df['Prediction'] == 1).mean() * 100
        }
        
        # User-level statistics if user column exists
        user_cols = [col for col in predictions_df.columns if col.upper() in ['USUARIO', 'USER', 'USUARIO_ID']]
        if user_cols:
            user_col = user_cols[0]
            stats['unique_users_all'] = predictions_df[user_col].nunique()
            stats['unique_users_filtered'] = filtered_df[user_col].nunique() if len(filtered_df) > 0 else 0
            stats['avg_recs_per_user'] = len(predictions_df) / predictions_df[user_col].nunique()
            stats['avg_filtered_per_user'] = len(filtered_df) / filtered_df[user_col].nunique() if len(filtered_df) > 0 else 0
        
        return stats


def main():
    """
    Example usage of the predictor.
    """
    # Example configuration
    MODEL_PATH = "models/modulo_recomendacion_roles/20251012_173859_TargetEnc_m20_s15_LGBM_set6_BEST.joblib"
    RECOMMENDATIONS_PATH = "data/similarity/role_recommendations_0_9.csv"
    USER_METADATA_PATH = "data/processed/split_roles.csv"
    OUTPUT_PATH = "data/processed/filtered_recommendations_classifier.csv"
    THRESHOLD = 0.5
    
    # Initialize predictor
    predictor = RoleRecommendationPredictor(
        model_path=MODEL_PATH,
        classification_threshold=THRESHOLD
    )
    
    # Load model
    predictor.load_model()
    
    # Load recommendations
    recommendations_df = predictor.load_recommendations(RECOMMENDATIONS_PATH)
    
    # Load user metadata (optional but recommended)
    try:
        user_metadata_df = pd.read_csv(USER_METADATA_PATH)
    except Exception as e:
        user_metadata_df = None
    
    # Prepare features
    features_df = predictor.prepare_features(recommendations_df, user_metadata_df)
    
    # Make predictions
    predictions_df = predictor.predict(features_df)
    
    # Get statistics
    stats = predictor.get_statistics(predictions_df)
    
    print("\n" + "="*80)
    print("PREDICTION STATISTICS")
    print("="*80)
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"{key}: {value:.2f}")
        else:
            print(f"{key}: {value}")
    
    # Export filtered recommendations
    predictor.export_predictions(
        predictions_df,
        output_path=OUTPUT_PATH,
        include_all=False
    )
    
    print("\n" + "="*80)
    print(f"Filtered recommendations saved to: {OUTPUT_PATH}")
    print("="*80)


if __name__ == "__main__":
    main()
