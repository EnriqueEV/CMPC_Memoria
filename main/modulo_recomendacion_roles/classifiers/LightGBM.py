from lightgbm import LGBMClassifier, early_stopping
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    make_scorer,
    precision_score, 
    recall_score, 
    roc_auc_score,
    average_precision_score
)
from sklearn.preprocessing import OrdinalEncoder
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import GridSearchCV

from Catboost import load_data, train_test_split_data
import time


def create_lgbm_pipeline():
    """
    Create LightGBM pipeline with preprocessing.
    
    Returns:
        Pipeline: Sklearn pipeline with preprocessing and LightGBM model
    """
    features = ['DEPARTAMETNO', 'FUNCION', 'ROL']
    categorical_features = features

    preprocessor = ColumnTransformer(
        transformers=[
            ('cat_encoder', OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1), categorical_features)
        ],
        remainder='passthrough',
        verbose_feature_names_out=False
    )
    preprocessor.set_output(transform="pandas")

    # Use high n_estimators with early stopping
    # Note: OrdinalEncoder already converts categoricals to integers
    # LightGBM can work with these directly without specifying categorical_feature
    model_lgbm = LGBMClassifier(
        n_estimators=1000,  # High number with early stopping
        verbose=-1,
        random_state=42,
        callbacks=[early_stopping(stopping_rounds=50, verbose=False)]
    )

    lgbm_pipe = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('model', model_lgbm)
    ])

    return lgbm_pipe


def get_lgbm_param_grid():
    """
    Get a small, fast hyperparameter grid for LightGBM.
    Focuses only on learning_rate and num_leaves.
    """
    param_grid = {
        'model__learning_rate': [0.05, 0.1],
        'model__num_leaves': [31, 50, 70],
    }
    return param_grid

def lgbm_grid_search(param_grid=None, cv=3, scoring='roc_auc', n_jobs=1):
    
    """
    Perform GridSearchCV for LightGBM with early stopping.
    
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
    pipeline = create_lgbm_pipeline()
    
    # Get param grid
    if param_grid is None:
        param_grid = get_lgbm_param_grid()
    
    # Define multiple scorers
    # Note: For probability-based metrics, use response_method='predict_proba'
    print(param_grid)
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
    
    # Fit with early stopping

    
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
    print("LightGBM Classifier")
    start_time = time.time()

    results = lgbm_grid_search()

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time:.2f} seconds")