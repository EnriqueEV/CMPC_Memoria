

# Step 1: Initial User Embeddings - Technical Summary

## **Overview**

Convert raw user data into numerical feature vectors (initial embeddings) that serve as input to the Graph Neural Network.

***

## **Data Structure**

- **Users**: 1,041 total users
- **Departments**: 201 unique categories
- **Functions**: 452 unique categories
- **Permissions**: 4,090 unique permission codes
- **Contexts**: 10 different contexts where permissions operate

***

## **Hybrid Encoding Strategy**

### **Feature Components:**

1. **Department**: One-hot encoding → 201 dimensions
2. **Function**: One-hot encoding → 452 dimensions
3. **Permissions (Generic)**: Multi-hot encoding → 4,090 dimensions
    - Binary indicator: does user have permission X (regardless of context)?
4. **Permission-Context Pairs**: Multi-hot encoding → 40,900 dimensions (4,090 × 10)
    - Binary indicator: does user have permission X in specific context Y?

### **Total Vector Dimensionality**: ~45,643 dimensions per user

### **Vector Characteristics:**

- **Sparse representation**: Most dimensions are 0, only relevant features are 1
- **Hierarchical similarity**: Users can be similar at permission level OR permission+context level
- **Granular security modeling**: Captures both "what" and "where" for access control

***

## **Encoding Process**

```python
# Pseudo-structure of final vector per user:
user_vector = [
    department_onehot,           # 201 dims: [0,0,1,0,0,...]
    function_onehot,             # 452 dims: [0,1,0,0,0,...]
    permissions_multihot,        # 4090 dims: [1,0,1,1,0,...]
    perm_context_pairs_multihot  # 40900 dims: [0,1,0,0,1,...]
]
```


***

## **Pros of This Implementation**

✅ **Comprehensive Representation**: Captures all relevant user attributes and their contexts

✅ **Hierarchical Similarity**: Users can match on:

- Same department/function
- Same permission (any context)
- Exact permission+context match

✅ **Security Granularity**: Distinguishes between having permission X in different systems/contexts

✅ **GNN Compatible**: High-dimensional sparse vectors work well as GNN input features

✅ **Interpretable**: Easy to understand what each dimension represents

✅ **Flexible**: Can weight or modify individual feature groups as needed

***

## **Cons of This Implementation**

❌ **High Dimensionality**: 45,643 dimensions creates very sparse, memory-intensive vectors

❌ **Computational Cost**: Large similarity matrix calculations (1,041 × 1,041 × 45,643)

❌ **Storage Requirements**: Sparse matrix storage needed to handle efficiently

❌ **Potential Overfitting**: High dimensionality vs. sample size ratio (45K dims, 1K users)

❌ **Feature Explosion**: Adding new contexts/permissions increases dimensionality rapidly

❌ **Noise Sensitivity**: Many irrelevant dimensions might confuse similarity calculations

***

## **Mitigation Strategies**

### **Memory \& Performance:**

- Use **sparse matrix representations** (CSR/CSC format)
- Apply **dimensionality reduction** (PCA, SVD) before similarity computation
- Implement **feature selection** to remove rare or uninformative dimensions


### **Model Architecture:**

- Add **learnable embedding layers** in GNN to compress high-dimensional input
- Use **attention mechanisms** to focus on relevant feature subsets
- Apply **regularization** (dropout, L2) to prevent overfitting


### **Data Preprocessing:**

- **Group rare permissions** into buckets to reduce dimensionality
- **Weight features** by importance (e.g., TF-IDF-like weighting)
- **Normalize vectors** to unit length for consistent similarity computation

***

## **Expected Workflow**

1. **Encode**: Transform raw user data → 45,643-dim sparse vectors
2. **Similarity**: Compute cosine similarity between user vectors
3. **Graph**: Build initial similarity graph (threshold or k-NN based)
4. **Input**: Feed vectors + graph structure to GNN for training

***

This hybrid encoding provides rich, contextual user representations suitable for advanced similarity learning while requiring careful handling of the high-dimensional sparse feature space.

