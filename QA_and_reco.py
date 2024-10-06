import pyodbc
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

# Database connection
conn = pyodbc.connect(    f"DRIVER={config['connection_string']['DRIVER']};"
    f"SERVER={config['connection_string']['SERVER']};"
    f"DATABASE={config['connection_string']['DATABASE']};"
    f"UID={config['connection_string']['UID']};"
    f"PWD={config['connection_string']['PWD']};")

# Query to retrieve only non-null main_accords
query = """
SELECT perfume_name, main_accords
FROM dbo.perfumes
WHERE main_accords IS NOT NULL AND main_accords <> '';
"""
df = pd.read_sql(query, conn)

# Close connection
conn.close()
print(df)
# Convert main_accords from a string to a list of accords
df['main_accords'] = df['main_accords'].apply(lambda x: x.split(', '))

# Create a list of all unique accords
unique_accords = set([accord for sublist in df['main_accords'] for accord in sublist])

# Create a mapping of accord to index
accord_to_index = {accord: idx for idx, accord in enumerate(unique_accords)}

# Convert accords to feature vectors
def accords_to_vector(accords, accord_to_index):
    vector = [0] * len(accord_to_index)
    for accord in accords:
        if accord in accord_to_index:
            vector[accord_to_index[accord]] = 1
    return vector

df['vector'] = df['main_accords'].apply(lambda x: accords_to_vector(x, accord_to_index))

# Create a DataFrame of vectors
X = pd.DataFrame(df['vector'].to_list(), index=df.index)

# Number of clusters
n_clusters = 5

# Apply K-Means clustering
kmeans = KMeans(n_clusters=n_clusters, random_state=42)
df['cluster'] = kmeans.fit_predict(X)

# Perform PCA for 2D visualization
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X)

# Plotting the clusters
plt.figure(figsize=(10, 7))
scatter = plt.scatter(X_pca[:, 0], X_pca[:, 1], c=df['cluster'], s=50, cmap='viridis')
plt.colorbar(scatter, label='Cluster ID')
plt.xlabel('PCA Feature 1')
plt.ylabel('PCA Feature 2')
plt.title('K-Means Clustering of Perfumes')
plt.show()
