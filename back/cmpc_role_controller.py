import sys
from pathlib import Path

# Añadir el directorio raíz del proyecto al path para permitir imports absolutos
# Esto permite que el archivo funcione tanto con python -m como ejecutándolo directamente
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd
from main.cmpc_role_recomender import CmpcRoleRecommender

class CmpcRoleController:
    """
    Controlador para gestionar las recomendaciones de roles utilizando CmpcRoleRecommender.
    Para cambiar los datos base, modificar data_folder (carpeta donde se encuentran USER_ADDR_IDAD3 y AGR_USERS) y data_type (formato de los archivos: .csv o .xlsx).
    """

    def __init__(self, similarity_metric, resumen_data_path, n_top = 10, data_folder = "data", threshold=0.7, data_type = ".csv"):
        self.recommender = CmpcRoleRecommender(similarity_metric, resumen_data_path, n_top, data_folder, threshold, data_type)

    def generate_recommendations(self, model_path=None, threshold=0.5):

        """Genera recomendaciones de roles y las clasifica utilizando un modelo preentrenado."""

        _ = self.recommender.run_recommendations()

        if model_path:
            self.recommender.classify_recommendations(model_path, threshold)
        else:
            self.recommender.classify_recommendations(threshold=threshold)

        return self.recommender.predictions_df

    def export_recommendations(self, recommendations_path, resumen_path, split_roles_path):
        """
        Exporta las recomendaciones y datos relacionados a archivos CSV.
        
        Args:
            recommendations_path (str): Ruta para guardar las recomendaciones.
            resumen_path (str): Ruta para guardar el resumen (importante solo para la validacion).
            split_roles_path (str): Ruta para guardar la informacion de los usuarios.
        """
        self.recommender.export_data(recommendations_path, resumen_path, split_roles_path)

    # Metodos para obtener informacion de usuarios y recomendaciones
    def get_base_user(self):
        """
        Obtiene información base de usuarios (Función y Departamento) 
        que tienen recomendaciones disponibles.
        
        Returns:
            list: Lista de diccionarios con formato:
                  [{"Usuario": "XX", "Departamento": "YY", "Función": "ZZ"}, ...]
        """
        base_info = self.recommender.get_split_roles()
        recomendation_info = self.recommender.get_recomendation()
        
        if base_info is None or recomendation_info is None:
            return []
        
        users_with_recommendations = recomendation_info['Usuario'].unique()
        

        filtered_users = base_info[base_info['Usuario'].isin(users_with_recommendations)]
        
        user_base_data = filtered_users[['Usuario', 'Departamento', 'Función']].drop_duplicates()
        
        return user_base_data.to_dict(orient='records')

    def get_user_recomendations(self, user_id):
        """
        Obtiene las recomendaciones de roles para un usuario específico.
        
        Args:
            user_id (str): Identificador del usuario.
        
        Returns:
            pd.DataFrame: DataFrame con las recomendaciones del usuario. La columna que tiene los roles es "Recommended_Role".
        """
        recommendations = self.recommender.get_recomendation()
        
        if recommendations is None:
            return pd.DataFrame()
        
        user_recommendations = recommendations[recommendations['Usuario'] == user_id]
        
        return user_recommendations
    
    def get_data_by(self,data_type = "Usuario"):
        """
        Obtiene una lista de valores únicos para un tipo de dato específico (Usuario, Departamento, Función).
        Args:
            data_type (str): Tipo de dato a obtener. Puede ser "Usuario", "Departamento" o "Función".
        Returns:
            list: Lista de valores únicos para el tipo de dato especificado.
        """

        if data_type not in ["Usuario","Departamento","Función"]:
            return []
        base_info = self.recommender.get_split_roles()
        if base_info is None:
            return []
        return base_info[data_type].unique().tolist()

    

if __name__ == "__main__":
    controller = CmpcRoleController(
        similarity_metric='cosine',
        resumen_data_path='data/processed/resumen_2025.csv',
        threshold=0.8
    )
    recommendations_df = controller.generate_recommendations(
        model_path="models/modulo_recomendacion_roles/grid_search/lightgbm_best_model_20251102_183656.joblib",
        threshold=0.7
    )
    print(recommendations_df.head())
    # Obtener información base de usuarios con recomendaciones
    base_user_info = controller.get_base_user()
    print("Base User Information with Recommendations:")
    for user_info in base_user_info:
        print(user_info)
    # Obtener recomendaciones para un usuario específico
    user_id = 'WNPEREIRA'  # Reemplazar con un ID de usuario válido
    user_recommendations = controller.get_user_recomendations(user_id)
    print(f"\nRecommendations for User {user_id}:")
    print(user_recommendations)
    # Obtener lista de departamentos únicos
    departamentos = controller.get_data_by(data_type="Departamento")
    print("\nUnique Departments:")
    print(departamentos)
    