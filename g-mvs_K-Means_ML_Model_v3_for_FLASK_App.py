#!/usr/bin/env python
# coding: utf-8

# ## Part 0: Import Dependencies and Set-Up

# Import Dependencies
import numpy as np
import os
import pandas as pd
import random
from scipy.spatial import distance
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler, MultiLabelBinarizer, StandardScaler
import time


start_time = time.time()


# Path to file directory and variables for input files.
file_dir = os.path.join("Data")

# imdb Titles metadata (Extracted from title.basics.tsv)
titles_metadata_file = f'{file_dir}/title_basics_non-adult_movies.tsv'

# imdb US Titles only ids (Extracted from title.akas.tsv)
titles_us_ids_only_file = f'{file_dir}/US_title_ids.csv'

# imdb Ratings data (Derived from title.ratings.tsv)
ratings_data_file = f'{file_dir}/title_ratings.csv'


# Set Viewer Title for Testing
#viewerTitle = "Apocalypse Now"
viewerTitle = "The Maltese Falcon (1941)"
#viewerTitle = "Toy Story"
#viewerTitle = "Witness (1985)"


# ## Part 1: Import Data, Clean and Transform Data

# Import imdb Titles metadata, imdb US Title IDs, imdb Ratings data

titles_metadata = pd.read_csv(titles_metadata_file, sep='\t')
titles_us_ids_only = pd.read_csv(titles_us_ids_only_file)
ratings_data = pd.read_csv(ratings_data_file)


# Drop all Titles where primaryTitle differs from originalTitle
# (Since language of titles is not often available, this is an attempt
# to filter out obscure non-English language films)

titles_metadata = titles_metadata.loc[titles_metadata['primaryTitle'] == titles_metadata['originalTitle']]


# Look for Films with the same primaryTitle
# and set primaryTitle to primaryTitle + (startYear)

duplicate_titles_df = pd.concat(g for _, g in titles_metadata.groupby('primaryTitle') if len(g) > 1)

duplicate_titles_df['primaryTitle'] = duplicate_titles_df.apply(lambda row: "".join([row['primaryTitle'], " (", str(row['startYear']), ")"]), axis=1)
duplicate_titles_df['originalTitle'] = duplicate_titles_df['primaryTitle']


# Merge duplicate_titles_df back with titles_metadata

cols = list(titles_metadata.columns)
titles_metadata.loc[titles_metadata['tconst'].isin(duplicate_titles_df['tconst']), cols] = duplicate_titles_df[cols]


# Drop all Titles from titles_metadata that are not in titles_us_ids_only

titles_metadata = pd.merge(titles_metadata, titles_us_ids_only, on='tconst', how='inner')
titles_metadata = titles_metadata.drop_duplicates()


# Drop titles_metadata Rows with "\N" for genres and startYear
# Drop titleType isAdult and endYear Columns

titles_metadata = titles_metadata.loc[~(titles_metadata['genres'] == "\\N") & ~(titles_metadata['startYear'] == "\\N")]
titles_metadata.drop(['titleType'], axis=1, inplace=True)
titles_metadata.drop(['isAdult'], axis=1, inplace=True)
titles_metadata.drop(['endYear'], axis=1, inplace=True)


# Convert startYear Column to int

titles_metadata['startYear'] = pd.to_numeric(titles_metadata['startYear'])


# Drop titles_metadata Rows with 'startYear' less than 1920

titles_metadata = titles_metadata.loc[titles_metadata['startYear'] >= 1920]


# Merge titles_metadata and ratings_data on tconst

movies_df = pd.merge(titles_metadata, ratings_data, on="tconst")


# Add url column to movies_df
movies_df['url'] = movies_df.apply(lambda row: "".join(["https://www.imdb.com/title/", row['tconst'], "/"]), axis=1)

# Convert 'genres' entries into lists

movies_df['genres_list'] = movies_df.apply(lambda row: row['genres'].split(","), axis=1)


# Transform (get_dummies via Multi Label Bin Encoding) movies_df by 'genres'

genres = movies_df['genres_list']

mlb = MultiLabelBinarizer()

X = pd.DataFrame(mlb.fit_transform(genres), columns=mlb.classes_, index=movies_df.index)

# Merge X back with movies_df

movies_df = pd.merge(movies_df, X, how='inner', left_index=True, right_index=True)


# Integrate 'averageRating' into X DataFrame with 'primaryTitle' as new Index
Z = pd.merge(movies_df[['primaryTitle', 'averageRating']], X, how='outer', left_index=True, right_index=True)
Z.set_index('primaryTitle', inplace=True)


# Standardize the data with StandardScaler()

Z = StandardScaler().fit_transform(Z)


# ## Part 2: Principal Component Analysis


# Use PCA to reduce dimensions to three principal components
pca = PCA(n_components=3)

movies_pca = pca.fit_transform(Z)


# Create a DataFrame with the three principal components
col_names = ["PC 1", "PC 2", "PC 3"]
movies_pca_df = pd.DataFrame(movies_pca, columns=col_names, index=movies_df.index)


# ## Part 3: Clustering Using K-Means


# Initialize the K-Means model using k=4

model = KMeans(n_clusters=4, random_state=0)


# Fit the model

model.fit(movies_pca_df)



# Predict clusters
predictions = model.predict(movies_pca_df)


# Create a new DataFrame including predicted clusters and movies metadata.
# Concatenate the movies_df and movies_pca_df on the same columns.

clustered_df = pd.concat([movies_df, movies_pca_df], axis=1, sort=False)


# Add a new column, "Class" to the clustered_df DataFrame that holds the predictions.
clustered_df['Class'] = model.labels_


# ## Part 4: Generate Recommendation for User

# Find tconst for viewerTitle

viewer_tconst = clustered_df.loc[(clustered_df['primaryTitle'] == viewerTitle)]['tconst']


# #### Take viewerTitle and find Closest Neighbor


# Find Class of viewerTitle

viewerTitleClass = clustered_df.loc[clustered_df['primaryTitle'] == viewerTitle]['Class'].values[0]


# Create a Distance Matrix by 'tconst'

# First, create a DataFrame of only the three Principal Components
# of Titles in the same Class as viewerTitle

clustered_df = clustered_df.loc[clustered_df['Class'] == viewerTitleClass]

distance_inputs_df = clustered_df[['tconst', 'PC 1', 'PC 2', 'PC 3']]
distance_inputs_df.set_index('tconst', inplace=True)


# Find Principal Component Coordinates
# for viewer_tconst

viewer_input_df = distance_inputs_df.loc[viewer_tconst]


# Convert distance_inputs_df to Numpy Array

distance_inputs = distance_inputs_df.to_numpy()

viewer_input = viewer_input_df.to_numpy()


# Calculate Euclidean Distances

distance_results = distance.cdist(viewer_input, distance_inputs, 'euclidean')


# For each distance in distance_results, add a small random number
# to help guarantee uniqueness of distances
# (If distance is 0, leave it unchanged)

distance_results_rand = []

for distance in distance_results[0]:
    if distance == 0:
        continue
    else:
        distance = distance + random.randrange(1, 9, 1)/10e15
        
    distance_results_rand.append(distance)

distance_results_rand = np.asarray(distance_results_rand)


# #### Output Recommendations

# Find the k Smallest Non-Zero Distance and their Positions
# Change k to change the number of Recommendations output

k = 5
k_min_non_zero = np.partition(distance_results_rand[np.nonzero(distance_results_rand)], k)[:k]

time_elapsed = round(time.time() - start_time, 1)

print(f'\nInput Movie: {viewerTitle}\n')

print(f'Model Execution Time: {time_elapsed} seconds\n')

print(f'{k} Recommendations:\n')

# Loop through k_min_non_zero

for entry in k_min_non_zero:
    recommendation_index = list(distance_results_rand).index(entry)
    print(clustered_df.iloc[recommendation_index]['primaryTitle'])
    print(clustered_df.iloc[recommendation_index]['url'] + '\n')

# END
