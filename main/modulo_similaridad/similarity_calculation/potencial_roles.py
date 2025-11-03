"""
Module for recommending potential roles to users based on similarity analysis.

This module provides functionality to:
1. Load user roles and similarity data
2. Filter similar users based on a similarity threshold
3. Identify potential new roles for users
4. Export recommendations to CSV
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Set, Tuple
import ast
from pathlib import Path


class RoleRecommender:
    """
    A class to recommend potential roles based on user similarity.
    
    Attributes:
        roles_df (pd.DataFrame): DataFrame containing user roles
        similarity_df (pd.DataFrame): DataFrame containing user similarity matrix
        similarity_threshold (float): Minimum similarity threshold for recommendations
    """
    
    def __init__(self, roles_data, similarity_data, similarity_threshold: float = 0.7):
        """
        Initialize the RoleRecommender.
        
        Args:
            roles_data (str or pd.DataFrame): Path to CSV file or DataFrame containing user roles
            similarity_data (str or pd.DataFrame): Path to CSV file or DataFrame containing similarity matrix
            similarity_threshold (float): Minimum similarity threshold (0-1)
        
        Raises:
            ValueError: If similarity_threshold is not between 0 and 1
            FileNotFoundError: If input files don't exist
            TypeError: If input data types are invalid
        """
        if not 0 <= similarity_threshold <= 1:
            raise ValueError("similarity_threshold must be between 0 and 1")
        
        self.similarity_threshold = similarity_threshold
        self.roles_df = self._load_roles(roles_data)
        self.similarity_df = self._load_similarity_matrix(similarity_data)
        self.user_roles_dict = self._create_user_roles_dict()
    
    def _load_roles(self, data) -> pd.DataFrame:
        """
        Load user roles from CSV file or DataFrame.
        
        Args:
            data (str or pd.DataFrame): Path to roles CSV file or DataFrame
            
        Returns:
            pd.DataFrame: DataFrame with user roles
            
        Raises:
            FileNotFoundError: If file path doesn't exist
            TypeError: If data is neither str nor DataFrame
        """
        if isinstance(data, pd.DataFrame):
            return data.copy()
        elif isinstance(data, str):
            if not Path(data).exists():
                raise FileNotFoundError(f"Roles file not found: {data}")
            df = pd.read_csv(data)
            return df
        else:
            raise TypeError(f"roles_data must be a string path or pandas DataFrame, got {type(data)}")
    
    def _load_similarity_matrix(self, data) -> pd.DataFrame:
        """
        Load user similarity matrix from CSV file or DataFrame.
        
        Args:
            data (str or pd.DataFrame): Path to similarity matrix CSV file or DataFrame
            
        Returns:
            pd.DataFrame: Similarity matrix with users as index and columns
            
        Raises:
            FileNotFoundError: If file path doesn't exist
            TypeError: If data is neither str nor DataFrame
        """
        if isinstance(data, pd.DataFrame):
            # Ensure it's a copy to avoid modifying the original
            df = data.copy()
            # If index is not set and first column looks like user IDs, set it as index
            if df.index.name is None and len(df.columns) > 0:
                if not df.index.equals(pd.RangeIndex(len(df))):
                    # Index is already set
                    pass
                else:
                    # Try to set first column as index if it looks like IDs
                    df = df.set_index(df.columns[0])
            return df
        elif isinstance(data, str):
            if not Path(data).exists():
                raise FileNotFoundError(f"Similarity file not found: {data}")
            df = pd.read_csv(data, index_col=0)
            return df
        else:
            raise TypeError(f"similarity_data must be a string path or pandas DataFrame, got {type(data)}")
    
    def _create_user_roles_dict(self) -> Dict[str, Set[str]]:
        """
        Create a dictionary mapping users to their sets of roles.
        
        Returns:
            Dict[str, Set[str]]: Dictionary with user as key and set of roles as value
        """
        user_roles = {}
        
        for _, row in self.roles_df.iterrows():
            usuario = row['Usuario']
            roles = row['Rol']
            
            # Parse the string representation of the list
            if isinstance(roles, str):
                try:
                    roles_list = ast.literal_eval(roles)
                except (ValueError, SyntaxError):
                    roles_list = []
            elif isinstance(roles, list):
                roles_list = roles
            else:
                roles_list = []
            
            # Store as set for efficient operations
            user_roles[usuario] = set(roles_list)
        
        return user_roles
    
    def get_similar_users(self, user: str, exclude_self: bool = True) -> List[Tuple[str, float]]:
        """
        Get users similar to the given user based on the similarity threshold.
        
        Args:
            user (str): Username to find similar users for
            exclude_self (bool): Whether to exclude the user themselves
            
        Returns:
            List[Tuple[str, float]]: List of (username, similarity_score) tuples
        """
        if user not in self.similarity_df.index:
            return []
        
        # Get similarity scores for the user
        similarities = self.similarity_df.loc[user]
        
        # Filter by threshold
        similar_users = similarities[similarities >= self.similarity_threshold]
        
        # Exclude self if requested
        if exclude_self and user in similar_users.index:
            similar_users = similar_users.drop(user)
        
        # Sort by similarity (descending)
        similar_users = similar_users.sort_values(ascending=False)
        
        return list(zip(similar_users.index, similar_users.values))
    
    def get_potential_roles(self, user: str) -> Dict[str, Dict]:
        """
        Get potential new roles for a user based on similar users' roles.
        
        Args:
            user (str): Username to get recommendations for
            
        Returns:
            Dict[str, Dict]: Dictionary with potential roles and their details
                            Format: {role: {'count': int, 'similar_users': List[str], 
                                           'avg_similarity': float}}
        """
        if user not in self.user_roles_dict:
            return {}
        
        # Get user's current roles
        current_roles = self.user_roles_dict[user]
        
        # Get similar users
        similar_users = self.get_similar_users(user)
        
        if not similar_users:
            return {}
        
        # Collect roles from similar users
        potential_roles = {}
        
        for similar_user, similarity_score in similar_users:
            if similar_user not in self.user_roles_dict:
                continue
            
            similar_user_roles = self.user_roles_dict[similar_user]
            
            # Find roles the user doesn't have
            new_roles = similar_user_roles - current_roles
            
            for role in new_roles:
                if role not in potential_roles:
                    potential_roles[role] = {
                        'count': 0,
                        'similar_users': [],
                        'similarities': []
                    }
                
                potential_roles[role]['count'] += 1
                potential_roles[role]['similar_users'].append(similar_user)
                potential_roles[role]['similarities'].append(similarity_score)
        
        # Calculate average similarity for each role
        for role in potential_roles:
            similarities = potential_roles[role]['similarities']
            potential_roles[role]['avg_similarity'] = np.mean(similarities)
            # Remove the raw similarities list from final output
            del potential_roles[role]['similarities']
        
        return potential_roles
    
    def recommend_roles_for_all_users(self) -> pd.DataFrame:
        """
        Generate role recommendations for all users in the dataset.
        
        Returns:
            pd.DataFrame: DataFrame with recommendations
                         Columns: Usuario, Recommended_Role, Count, Avg_Similarity, Similar_Users
        """
        recommendations = []
        
        for user in self.user_roles_dict.keys():
            potential_roles = self.get_potential_roles(user)
            
            for role, details in potential_roles.items():
                recommendations.append({
                    'Usuario': user,
                    'Recommended_Role': role,
                    'Count': details['count'],
                    'Avg_Similarity': round(details['avg_similarity'], 4),
                    'Similar_Users': ', '.join(details['similar_users'])
                })
        
        recommendations_df = pd.DataFrame(recommendations)
        
        if not recommendations_df.empty:
            # Sort by user and then by count/similarity
            recommendations_df = recommendations_df.sort_values(
                by=['Usuario', 'Count', 'Avg_Similarity'],
                ascending=[True, False, False]
            )
        
        return recommendations_df
    
    def get_top_recommendations(self, user: str, top_n: int = 10) -> pd.DataFrame:
        """
        Get top N role recommendations for a specific user.
        
        Args:
            user (str): Username to get recommendations for
            top_n (int): Number of top recommendations to return
            
        Returns:
            pd.DataFrame: DataFrame with top recommendations
        """
        potential_roles = self.get_potential_roles(user)
        
        if not potential_roles:
            return pd.DataFrame()
        
        # Convert to DataFrame and sort
        recommendations = []
        for role, details in potential_roles.items():
            recommendations.append({
                'Role': role,
                'Count': details['count'],
                'Avg_Similarity': round(details['avg_similarity'], 4),
                'Similar_Users': ', '.join(details['similar_users'])
            })
        
        df = pd.DataFrame(recommendations)
        df = df.sort_values(by=['Count', 'Avg_Similarity'], ascending=[False, False])
        
        return df.head(top_n)
    
    def export_recommendations(self, output_path: str, top_n_per_user: int = None):
        """
        Export role recommendations to a CSV file.
        
        Args:
            output_path (str): Path where to save the recommendations CSV
            top_n_per_user (int, optional): Limit recommendations per user. None means all.
        """
        recommendations_df = self.recommend_roles_for_all_users()
        
        if recommendations_df.empty:
            return
        
        # Limit recommendations per user if specified
        if top_n_per_user is not None:
            recommendations_df = recommendations_df.groupby('Usuario').head(top_n_per_user)
        
        # Create output directory if it doesn't exist
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Export to CSV
        recommendations_df.to_csv(output_path, index=False)
    
    def get_statistics(self) -> Dict:
        """
        Get statistics about the recommendations.
        
        Returns:
            Dict: Dictionary with various statistics
        """
        recommendations_df = self.recommend_roles_for_all_users()
        
        if recommendations_df.empty:
            return {
                'total_users': len(self.user_roles_dict),
                'total_recommendations': 0,
                'users_with_recommendations': 0,
                'avg_recommendations_per_user': 0
            }
        
        stats = {
            'total_users': len(self.user_roles_dict),
            'total_recommendations': len(recommendations_df),
            'users_with_recommendations': recommendations_df['Usuario'].nunique(),
            'avg_recommendations_per_user': round(
                len(recommendations_df) / recommendations_df['Usuario'].nunique(), 2
            ),
            'most_recommended_role': recommendations_df.groupby('Recommended_Role').size().idxmax(),
            'max_recommendations_for_single_user': recommendations_df.groupby('Usuario').size().max()
        }
        
        return stats


def main():
    """
    Main function to demonstrate usage of the RoleRecommender class.
    """
    # Define file paths
    ROLES_PATH = "data/processed/split_roles.csv"
    SIMILARITY_PATH = "data/similarity/user_similarity_cosine.csv"
    OUTPUT_PATH = "data/processed/role_recommendations.csv"
    
    # Set similarity threshold
    SIMILARITY_THRESHOLD = 0.7
    
    try:
        # Initialize recommender
        recommender = RoleRecommender(
            roles_path=ROLES_PATH,
            similarity_path=SIMILARITY_PATH,
            similarity_threshold=SIMILARITY_THRESHOLD
        )
        
        # Export all recommendations
        recommender.export_recommendations(
            output_path=OUTPUT_PATH,
            top_n_per_user=10  # Limit to top 10 recommendations per user
        )
        
        # Print statistics
        stats = recommender.get_statistics()
        print("\n=== Recommendation Statistics ===")
        for key, value in stats.items():
            print(f"{key}: {value}")
        
        # Example: Get recommendations for a specific user
        example_user = "AABATTI"
        print(f"\n=== Top 5 Recommendations for {example_user} ===")
        top_recommendations = recommender.get_top_recommendations(example_user, top_n=5)
        print(top_recommendations.to_string(index=False))
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        raise


if __name__ == "__main__":
    main()
