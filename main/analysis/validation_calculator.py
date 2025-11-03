"""
Class for validating classification results against actual role assignments.

This module provides a ValidationCalculator class that validates predicted role 
recommendations against actual assignments with flexible input (DataFrames or file paths).

Important validation logic:
- True Hit = (Recommendation in Future_Assignments) AND (Recommendation NOT in Past_Assignments)
- Calculates both Precision (Match Rate) and Recall
- Filters out roles users already had in training data
"""

import pandas as pd
import numpy as np
from typing import Union, Dict, Optional, Tuple
from pathlib import Path


def extract_role_prefix(role_full: str) -> str:
    """
    Extract the role prefix from the full role string.
    
    Args:
        role_full: Full role string (e.g., "ZD_ALMMPU0-001-07-001:0504")
    
    Returns:
        Role prefix (e.g., "ZD_ALMMPU0")
    """
    if pd.isna(role_full):
        return ""
    
    # Split by "-" and take the first part
    role_parts = str(role_full).split("-")
    return role_parts[0] if role_parts else ""


class ValidationCalculator:
    """
    A class to validate role recommendations against actual assignments.
    
    This class accepts DataFrames directly (already processed) or file paths,
    and performs validation to calculate precision, recall, and identify true hits.
    
    Attributes:
        predictions_df (pd.DataFrame): DataFrame with predictions (Usuario, Recommended_Role columns)
        past_assignments_df (pd.DataFrame): DataFrame with past assignments (Usuario, Rol columns)
        resumen_df (pd.DataFrame): DataFrame with future assignments (Usuario, Rol, Fecha columns)
        date_filter (str): Optional date filter for future assignments
        results (dict): Validation results after running compute_validation()
    """
    
    def __init__(self, 
                 predictions_data: Union[pd.DataFrame, str],
                 past_assignments_data: Union[pd.DataFrame, str],
                 resumen_data: Union[pd.DataFrame, str],
                 date_filter: Optional[str] = None):
        """
        Initialize the ValidationCalculator.
        
        Args:
            predictions_data: DataFrame or path to CSV with predictions
                            Required columns: Usuario, Recommended_Role (or Recomendation)
            past_assignments_data: DataFrame or path to CSV with past assignments
                                  Required columns: Usuario, Rol
            resumen_data: DataFrame or path to CSV with future assignments
                         Required columns: Usuario, Rol, Fecha (optional)
            date_filter: Optional date string 'YYYY-MM-DD' to filter future assignments
        
        Raises:
            ValueError: If required columns are missing
            FileNotFoundError: If file paths don't exist
            TypeError: If input types are invalid
        """
        self.date_filter = date_filter
        
        # Load data
        self.predictions_df = self._load_predictions(predictions_data)
        self.past_assignments_df = self._load_past_assignments(past_assignments_data)
        self.resumen_df = self._load_resumen(resumen_data, date_filter)
        
        # Validate required columns
        self._validate_dataframes()
        
        # Add User_Role keys
        self._add_user_role_keys()
        
        # Results will be populated after validation
        self.results = None
    
    def _load_predictions(self, data: Union[pd.DataFrame, str]) -> pd.DataFrame:
        """Load predictions data from DataFrame or CSV file."""
        if isinstance(data, pd.DataFrame):
            df = data.copy()
        elif isinstance(data, str):
            if not Path(data).exists():
                raise FileNotFoundError(f"Predictions file not found: {data}")
            df = pd.read_csv(data)
        else:
            raise TypeError(f"predictions_data must be DataFrame or str, got {type(data)}")
        
        # Standardize column names
        if 'Recomendation' in df.columns and 'Recommended_Role' not in df.columns:
            df['Recommended_Role'] = df['Recomendation']
        elif 'Recommended_Role' not in df.columns and 'Recomendation' not in df.columns:
            raise ValueError("Predictions DataFrame must have 'Recommended_Role' or 'Recomendation' column")
        
        if 'Usuario' not in df.columns:
            raise ValueError("Predictions DataFrame must have 'Usuario' column")
        
        return df
    
    def _load_past_assignments(self, data: Union[pd.DataFrame, str]) -> pd.DataFrame:
        """Load past assignments data from DataFrame or CSV file."""
        if isinstance(data, pd.DataFrame):
            df = data.copy()
        elif isinstance(data, str):
            if not Path(data).exists():
                raise FileNotFoundError(f"Past assignments file not found: {data}")
            df = pd.read_csv(data)
        else:
            raise TypeError(f"past_assignments_data must be DataFrame or str, got {type(data)}")
        
        # Validate required columns
        if 'Usuario' not in df.columns:
            raise ValueError("Past assignments DataFrame must have 'Usuario' column")
        if 'Rol' not in df.columns:
            raise ValueError("Past assignments DataFrame must have 'Rol' column")
        
        # Parse role lists and expand to individual roles
        import ast
        
        def parse_role_list(role_str):
            """Parse role string to list."""
            # Handle None, NaN, or empty values
            if role_str is None or (isinstance(role_str, float) and pd.isna(role_str)):
                return []
            
            if isinstance(role_str, list):
                return [str(r) for r in role_str if str(r) != 'NONE']
            
            if isinstance(role_str, str):
                role_str = role_str.strip()
                if not role_str or role_str.upper() == 'NONE':
                    return []
                
                try:
                    parsed = ast.literal_eval(role_str)
                    if isinstance(parsed, list):
                        return [str(r) for r in parsed if str(r) != 'NONE']
                    else:
                        return [str(parsed)] if str(parsed) != 'NONE' else []
                except (ValueError, SyntaxError):
                    return [role_str] if role_str != 'NONE' else []
            
            return []
        
        # Explode role lists into individual rows
        df['Rol_List'] = df['Rol'].apply(parse_role_list)
        df = df.explode('Rol_List').reset_index(drop=True)
        
        # Remove rows with no roles
        df = df[df['Rol_List'].notna() & (df['Rol_List'] != '')].copy()
        
        # Extract role prefix from each role
        df['Rol_Prefix'] = df['Rol_List'].apply(extract_role_prefix)
        
        # Replace Rol column with the extracted prefix
        df['Rol'] = df['Rol_Prefix']
        
        # Get unique past assignments
        past_assignments = df[['Usuario', 'Rol']].drop_duplicates()
        
        return past_assignments
    
    def _load_resumen(self, data: Union[pd.DataFrame, str], date_filter: Optional[str] = None) -> pd.DataFrame:
        """Load resumen (future assignments) data from DataFrame or CSV file."""
        if isinstance(data, pd.DataFrame):
            df = data.copy()
        elif isinstance(data, str):
            if not Path(data).exists():
                raise FileNotFoundError(f"Resumen file not found: {data}")
            df = pd.read_csv(data)
        else:
            raise TypeError(f"resumen_data must be DataFrame or str, got {type(data)}")
        
        # Validate required columns
        if 'Usuario' not in df.columns:
            raise ValueError("Resumen DataFrame must have 'Usuario' column")
        if 'Rol' not in df.columns:
            raise ValueError("Resumen DataFrame must have 'Rol' column")
        
        # Apply date filter if provided and Fecha column exists
        if date_filter and 'Fecha' in df.columns:
            df['Fecha'] = pd.to_datetime(df['Fecha'])
            filter_date = pd.to_datetime(date_filter)
            df = df[df['Fecha'] > filter_date].copy()
        
        # Extract role prefix from full role string
        df['Rol_Prefix'] = df['Rol'].apply(extract_role_prefix)
        
        return df
    
    def _validate_dataframes(self):
        """Validate that all required columns exist in DataFrames."""
        # Predictions
        if 'Usuario' not in self.predictions_df.columns:
            raise ValueError("Predictions DataFrame must have 'Usuario' column")
        if 'Recommended_Role' not in self.predictions_df.columns and 'Recomendation' not in self.predictions_df.columns:
            raise ValueError("Predictions DataFrame must have 'Recommended_Role' or 'Recomendation' column")
        
        # Past assignments
        if 'Usuario' not in self.past_assignments_df.columns or 'Rol' not in self.past_assignments_df.columns:
            raise ValueError("Past assignments DataFrame must have 'Usuario' and 'Rol' columns")
        
        # Resumen
        if 'Usuario' not in self.resumen_df.columns or 'Rol' not in self.resumen_df.columns:
            raise ValueError("Resumen DataFrame must have 'Usuario' and 'Rol' columns")
    
    def _add_user_role_keys(self):
        """Add User_Role key columns for matching."""
        # Predictions
        role_col = 'Recommended_Role' if 'Recommended_Role' in self.predictions_df.columns else 'Recomendation'
        self.predictions_df['User_Role'] = (
            self.predictions_df['Usuario'].str.upper() + "_" + self.predictions_df[role_col].astype(str)
        )
        
        # Past assignments
        self.past_assignments_df['User_Role'] = (
            self.past_assignments_df['Usuario'].str.upper() + "_" + self.past_assignments_df['Rol'].astype(str)
        )
        
        # Resumen - use Rol_Prefix instead of Rol for matching
        self.resumen_df['User_Role'] = (
            self.resumen_df['Usuario'].str.upper() + "_" + self.resumen_df['Rol_Prefix'].astype(str)
        )
    
    def compute_validation(self) -> Dict:
        """
        Compute validation metrics including precision, recall, and true hits.
        
        A TRUE HIT requires:
        1. Recommendation is in Future_Assignments (resumen_df)
        2. Recommendation was NOT in Past_Assignments
        
        Returns:
            Dictionary with validation results including:
                - total_predictions: Total number of predictions
                - unique_predicted_pairs: Unique User-Role pairs predicted
                - true_hits: Count of true hits
                - false_positives: Count of false positives
                - precision: Precision percentage
                - recall: Recall percentage
                - predictions_with_validation: DataFrame with validation flags
                - true_hit_predictions_df: DataFrame with only true hits
        """
        # Get unique users from predictions
        predicted_users = set(self.predictions_df['Usuario'].str.upper().unique())
        
        # Filter resumen and past assignments to only include users in predictions
        resumen_filtered = self.resumen_df[
            self.resumen_df['Usuario'].str.upper().isin(predicted_users)
        ].copy()
        
        past_filtered = self.past_assignments_df[
            self.past_assignments_df['Usuario'].str.upper().isin(predicted_users)
        ].copy()


        # Get unique user-role pairs
        predicted_pairs = set(self.predictions_df['User_Role'].unique())
        future_pairs = set(resumen_filtered['User_Role'].unique())
        past_pairs = set(past_filtered['User_Role'].unique())
        
        # STEP 1: Find predictions in future assignments
        matches_in_future = predicted_pairs.intersection(future_pairs)
        
        # STEP 2: Filter out false positives (already in past)
        false_positives = matches_in_future.intersection(past_pairs)
        
        # STEP 3: TRUE HITS = In Future AND NOT in Past
        true_hits = matches_in_future - false_positives
        
        # Predictions not in resumen
        not_in_resumen = predicted_pairs - future_pairs
        
        # Recommendations for roles already had
        already_had = predicted_pairs.intersection(past_pairs)
        
        # Add validation flags to predictions DataFrame
        predictions_validated = self.predictions_df.copy()
        predictions_validated['In_Future'] = predictions_validated['User_Role'].isin(future_pairs)
        predictions_validated['In_Past'] = predictions_validated['User_Role'].isin(past_pairs)
        predictions_validated['Is_True_Hit'] = predictions_validated['User_Role'].isin(true_hits)
        predictions_validated['Is_False_Positive'] = predictions_validated['User_Role'].isin(false_positives)
        
        # Calculate metrics
        precision = (len(true_hits) / len(predicted_pairs) * 100) if predicted_pairs else 0
        
        # Recall = True Hits / Truly New Future Roles
        truly_new_future_roles = future_pairs - past_pairs
        recall = (len(true_hits) / len(truly_new_future_roles) * 100) if truly_new_future_roles else 0
        
        # Get true hit predictions with dates if available
        true_hit_predictions = predictions_validated[predictions_validated['Is_True_Hit']].copy()
        if not true_hit_predictions.empty and 'Fecha' in resumen_filtered.columns:
            resumen_unique = resumen_filtered[['User_Role', 'Fecha']].drop_duplicates(
                subset=['User_Role'], keep='first'
            )
            true_hit_predictions = true_hit_predictions.merge(
                resumen_unique, on='User_Role', how='left'
            )
        
        # Store results
        self.results = {
            'total_predictions': len(self.predictions_df),
            'truly_new_future_roles': len(truly_new_future_roles),
            'matches_in_future': len(matches_in_future),
            'true_hits': len(true_hits),
            'precision': precision,
            'recall': recall,
            'old_match_rate': (len(matches_in_future) / len(predicted_pairs) * 100) if predicted_pairs else 0,
            'date_filter': self.date_filter
        }
        
        return self.results
    
    def get_statistics(self) -> Dict:
        """
        Get validation statistics.
        
        Returns:
            Dictionary with validation statistics
        
        Raises:
            RuntimeError: If compute_validation() hasn't been called yet
        """
        if self.results is None:
            raise RuntimeError("Must call compute_validation() before getting statistics")
        
        return {
            'total_predictions': self.results['total_predictions'],
            'unique_predicted_pairs': self.results['unique_predicted_pairs'],
            'true_hits': self.results['true_hits'],
            'false_positives': self.results['false_positives'],
            'precision': self.results['precision'],
            'recall': self.results['recall'],
            'truly_new_future_roles': self.results['truly_new_future_roles']
        }
    
    def get_true_hits(self) -> pd.DataFrame:
        """
        Get DataFrame with true hit predictions only.
        
        Returns:
            DataFrame with true hits
        
        Raises:
            RuntimeError: If compute_validation() hasn't been called yet
        """
        if self.results is None:
            raise RuntimeError("Must call compute_validation() before getting true hits")
        
        return self.results['true_hit_predictions_df']
    
    def get_false_positives(self) -> pd.DataFrame:
        """
        Get DataFrame with false positive predictions.
        
        Returns:
            DataFrame with false positives
        
        Raises:
            RuntimeError: If compute_validation() hasn't been called yet
        """
        if self.results is None:
            raise RuntimeError("Must call compute_validation() before getting false positives")
        
        return self.results['predictions_with_validation'][
            self.results['predictions_with_validation']['Is_False_Positive']
        ]
    
    def get_predictions_with_validation(self) -> pd.DataFrame:
        """
        Get all predictions with validation flags.
        
        Returns:
            DataFrame with all predictions and validation columns
        
        Raises:
            RuntimeError: If compute_validation() hasn't been called yet
        """
        if self.results is None:
            raise RuntimeError("Must call compute_validation() before getting predictions")
        
        return self.results['predictions_with_validation']
    
    def generate_user_statistics(self) -> pd.DataFrame:
        """
        Generate user-level statistics showing recommendations, assignments, and matches.
        
        Returns:
            DataFrame with user statistics (excluding users with no assigned roles)
        
        Raises:
            RuntimeError: If compute_validation() hasn't been called yet
        """
        if self.results is None:
            raise RuntimeError("Must call compute_validation() before generating user statistics")
        
        predictions_df = self.results['predictions_with_validation']
        
        # Count recommendations per user
        user_recommendations = predictions_df.groupby('Usuario').size().reset_index(name='Roles_Recommended')
        
        # Count TRUE HITS per user
        user_true_hits = predictions_df[predictions_df['Is_True_Hit']].groupby('Usuario').size().reset_index(name='True_Hits')
        
        # Count FALSE POSITIVES per user
        user_false_pos = predictions_df[predictions_df['Is_False_Positive']].groupby('Usuario').size().reset_index(name='False_Positives')
        
        # Count roles user already had
        user_had = predictions_df[predictions_df['In_Past']].groupby('Usuario').size().reset_index(name='Already_Had')
        
        # Merge all counts
        user_stats = user_recommendations
        user_stats = user_stats.merge(user_true_hits, on='Usuario', how='left')
        user_stats = user_stats.merge(user_false_pos, on='Usuario', how='left')
        user_stats = user_stats.merge(user_had, on='Usuario', how='left')
        
        # Fill NaN with 0
        user_stats['True_Hits'] = user_stats['True_Hits'].fillna(0).astype(int)
        user_stats['False_Positives'] = user_stats['False_Positives'].fillna(0).astype(int)
        user_stats['Already_Had'] = user_stats['Already_Had'].fillna(0).astype(int)
        
        # Get future roles from resumen - use Rol_Prefix
        resumen_filtered = self.results['resumen_filtered']
        user_future = resumen_filtered.groupby('Usuario')['Rol_Prefix'].nunique().reset_index(name='Future_Roles')
        user_stats = user_stats.merge(user_future, on='Usuario', how='left')
        user_stats['Future_Roles'] = user_stats['Future_Roles'].fillna(0).astype(int)
        
        # Get past roles
        past_filtered = self.results['past_assignments_filtered']
        user_past = past_filtered.groupby('Usuario')['Rol'].nunique().reset_index(name='Past_Roles')
        user_stats = user_stats.merge(user_past, on='Usuario', how='left')
        user_stats['Past_Roles'] = user_stats['Past_Roles'].fillna(0).astype(int)
        
        # Calculate NEW future roles
        user_stats['New_Future_Roles'] = user_stats['Future_Roles'] - user_stats['False_Positives']
        
        # Calculate Precision and Recall per user
        user_stats['Precision'] = (user_stats['True_Hits'] / user_stats['Roles_Recommended'] * 100).fillna(0).round(2)
        user_stats['Recall'] = user_stats.apply(
            lambda row: (row['True_Hits'] / row['New_Future_Roles'] * 100) if row['New_Future_Roles'] > 0 else 0,
            axis=1
        ).round(2)
        
        # Filter out users with no future roles
        user_stats = user_stats[user_stats['Future_Roles'] > 0].copy()
        
        # Reorder columns
        user_stats = user_stats[[
            'Usuario', 'Roles_Recommended', 'Past_Roles', 'Future_Roles', 'New_Future_Roles',
            'True_Hits', 'False_Positives', 'Already_Had', 'Precision', 'Recall'
        ]]
        
        # Sort by True_Hits descending, then by Precision descending
        user_stats = user_stats.sort_values(['True_Hits', 'Precision'], ascending=[False, False]).reset_index(drop=True)
        
        return user_stats
    
    def export_results(self, output_dir: str = "data/similarity/results_validation"):
        """
        Export validation results to CSV files.
        
        Args:
            output_dir: Directory to save output files
        
        Raises:
            RuntimeError: If compute_validation() hasn't been called yet
        """
        if self.results is None:
            raise RuntimeError("Must call compute_validation() before exporting results")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Export TRUE HITS
        if not self.results['true_hit_predictions_df'].empty:
            true_hits_file = output_path / "validation_true_hits.csv"
            role_col = 'Recommended_Role' if 'Recommended_Role' in self.results['true_hit_predictions_df'].columns else 'Recomendation'
            true_hits_output = self.results['true_hit_predictions_df'][['Usuario', role_col]].copy()
            true_hits_output.to_csv(true_hits_file, index=False)
        
        # Export all predictions with validation flags
        all_file = output_path / "validation_all_predictions_detailed.csv"
        role_col = 'Recommended_Role' if 'Recommended_Role' in self.results['predictions_with_validation'].columns else 'Recomendation'
        all_output = self.results['predictions_with_validation'][
            ['Usuario', role_col, 'In_Future', 'In_Past', 'Is_True_Hit', 'Is_False_Positive']
        ].copy()
        all_output.to_csv(all_file, index=False)
        
        # Export FALSE POSITIVES
        false_positives = self.get_false_positives()
        if not false_positives.empty:
            fp_file = output_path / "validation_false_positives.csv"
            fp_output = false_positives[['Usuario', role_col]].copy()
            fp_output.to_csv(fp_file, index=False)
        
        # Export user statistics
        user_stats = self.generate_user_statistics()
        user_stats_file = output_path / "validation_user_statistics.csv"
        user_stats.to_csv(user_stats_file, index=False)
        
        # Export summary
        summary_file = output_path / "validation_summary.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("VALIDATION SUMMARY - TRUE HIT ANALYSIS\n")
            f.write("="*80 + "\n\n")
            if self.results['date_filter']:
                f.write(f"Date Filter: Only assignments AFTER {self.results['date_filter']}\n\n")
            
            f.write("DATA OVERVIEW:\n")
            f.write(f"  Total predictions: {self.results['total_predictions']:,}\n")
            f.write(f"  Unique User-Role pairs predicted: {self.results['unique_predicted_pairs']:,}\n")
            f.write(f"  Future assignments (predicted users): {self.results['unique_future_pairs']:,}\n")
            f.write(f"  Past assignments (predicted users): {self.results['unique_past_pairs']:,}\n")
            f.write(f"  Truly NEW future roles: {self.results['truly_new_future_roles']:,}\n\n")
            
            f.write("PERFORMANCE METRICS:\n")
            f.write(f"  PRECISION: {self.results['precision']:.2f}%\n")
            f.write(f"  RECALL: {self.results['recall']:.2f}%\n")
            f.write(f"  TRUE HITS: {self.results['true_hits']:,}\n")
            f.write(f"  FALSE POSITIVES: {self.results['false_positives']:,}\n")
    
    def print_summary(self):
        """
        Print a formatted summary of validation results.
        
        Raises:
            RuntimeError: If compute_validation() hasn't been called yet
        """
        if self.results is None:
            raise RuntimeError("Must call compute_validation() before printing summary")
        
        print("\n" + "="*80)
        print("📊 VALIDATION RESULTS - TRUE HIT ANALYSIS")
        print("="*80)
        
        if self.results['date_filter']:
            print(f"\n📅 Date Filter: Only assignments AFTER {self.results['date_filter']}")
        
        print(f"\n📈 Data Overview:")
        print(f"   Total predictions: {self.results['total_predictions']:,}")
        print(f"   Unique User-Role pairs predicted: {self.results['unique_predicted_pairs']:,}")
        print(f"   Future assignments (predicted users): {self.results['unique_future_pairs']:,}")
        print(f"   Truly NEW future roles: {self.results['truly_new_future_roles']:,}")
        
        print(f"\n🎯 Performance Metrics:")
        print(f"   PRECISION: {self.results['precision']:.2f}%")
        print(f"   RECALL: {self.results['recall']:.2f}%")
        print(f"   TRUE HITS: {self.results['true_hits']:,}")
        print(f"   FALSE POSITIVES: {self.results['false_positives']:,}")
        
        print("\n" + "="*80)


if __name__ == "__main__":
    # Example usage with file paths
    validator = ValidationCalculator(
        predictions_data="data/similarity/recommended/classifier/filtered_recommendations_classifier_0.9.csv",
        past_assignments_data="data/processed/split_roles.csv",
        resumen_data="data/processed/resumen_2025.csv",
        date_filter="2025-06-07"
    )
    
    # Compute validation
    results = validator.compute_validation()
    
    # Print summary
    validator.print_summary()
    
    # Export results
    validator.export_results("data/similarity/results_validation/VALIDATION_TEST")
    
    # Get statistics
    stats = validator.get_statistics()
    print(f"\n📊 Statistics: {stats}")
