from ast import main
import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    make_scorer,
    precision_score,
    recall_score,
    roc_auc_score,
    average_precision_score
)
from catboost import CatBoostClassifier

def load_data(file_path):
    data = pd.read_csv(file_path)
    return data

def train_test_split_data(data, target_column, test_size=0.2, random_state=42):
    X = data.drop(columns=[target_column])
    y = data[target_column]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)

    return X_train, X_test, y_train, y_test


def create_catboost_pipeline():
    """
    Create CatBoost pipeline.
    
    Returns:
        Pipeline: Sklearn pipeline with CatBoost model
    """
    features = ['DEPARTAMETNO', 'FUNCION', 'ROL']
    
    # Use high iterations with early stopping
    catboost_model = CatBoostClassifier(
        iterations=1000,  # High number with early stopping
        cat_features=features,
        verbose=False,
        random_state=42,
        early_stopping_rounds=50,
        task_type='GPU'
    )

    catboost_pipe = Pipeline([
        ('model', catboost_model)
    ])

    return catboost_pipe


def get_catboost_param_grid():
    """
    Get a small, fast hyperparameter grid for CatBoost.
    Focuses only on learning_rate and depth.
    """
    param_grid = {
        'model__learning_rate': [0.05, 0.1],
        'model__depth': [4, 6, 8],
    }
    return param_grid


def catboost_grid_search(param_grid=None, cv=3, scoring='roc_auc', n_jobs=1):
    """
    Perform GridSearchCV for CatBoost with early stopping.
    
    Args:
        param_grid: Parameter grid (if None, uses default)
        cv: Number of cross-validation folds
        scoring: Scoring metric for GridSearchCV
        n_jobs: Number of parallel jobs
    
    Returns:
        tuple: (best_pipeline, results_df, cv_results)
    """
    # Load data
    df = load_data("data/modulo_recomendacion_roles/training_pairs_uniform_with_negatives.csv")
    df = df.dropna()
    X_train, X_test, y_train, y_test = train_test_split_data(df, target_column='ASIGNADO')

    # Create pipeline
    pipeline = create_catboost_pipeline()
    
    # Get param grid
    if param_grid is None:
        param_grid = get_catboost_param_grid()
    
    # Define multiple scorers
    # Note: For probability-based metrics, use response_method='predict_proba'
    scoring_dict = {
        'roc_auc': 'roc_auc',  # Built-in scorer handles probabilities automatically
        'pr_auc': make_scorer(average_precision_score, response_method='predict_proba'),
        'precision': make_scorer(precision_score),
        'recall': make_scorer(recall_score)
    }
    
    # Create GridSearchCV
    grid_search = GridSearchCV(
        pipeline,
        param_grid,
        cv=cv,
        scoring=scoring_dict,
        refit=scoring,  # Refit on the main scoring metric
        n_jobs=n_jobs,
        verbose=2,
        return_train_score=True
    )
    
    # Fit with validation set for early stopping

    
    print(f"Starting GridSearchCV with {len(param_grid)} parameters and {cv} folds...")
    grid_search.fit(X_train, y_train)
    
    print(f"\nBest parameters: {grid_search.best_params_}")
    print(f"Best {scoring} score: {grid_search.best_score_:.4f}")
    
    # Get best pipeline
    best_pipeline = grid_search.best_estimator_
    
    # Test set evaluation
    y_pred = best_pipeline.predict(X_test)
    y_pred_proba = best_pipeline.predict_proba(X_test)[:, 1]
    
    test_results = {
        'precision': precision_score(y_test, y_pred),
        'recall': recall_score(y_test, y_pred),
        'roc_auc': roc_auc_score(y_test, y_pred_proba),
        'pr_auc': average_precision_score(y_test, y_pred_proba)
    }
    
    print(f"\nTest set results:")
    for metric, value in test_results.items():
        print(f"  {metric}: {value:.4f}")
    
    # Extract CV results
    cv_results_df = pd.DataFrame(grid_search.cv_results_)
    
    return best_pipeline, test_results, cv_results_df, grid_search


if __name__ == "__main__":
    results = catboost_grid_search()