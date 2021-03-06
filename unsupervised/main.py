from sklearn.metrics import classification_report
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.datasets import load_digits
from sklearn.metrics import accuracy_score
from sklearn.decomposition import PCA
from sklearn.externals import joblib
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from scipy.stats import mode
import numpy as np
import pickle
import csv

#************************** Pre-processing ******************************
# Running PCA and Whitening
def load_data():
    # import csv and separate training data from test data
    csvr = csv.reader(open('fer2013.csv'))
    header = next(csvr)
    rows = [row for row in csvr]

    trn  = [row[1:-1] for row in rows if row[-1] == 'Training']
    tst  = [row[1:-1] for row in rows if row[-1] == 'PublicTest']
    tst2 = [row[1:-1] for row in rows if row[-1] == 'PrivateTest']

    trn_targets  = [row[0] for row in rows if row[-1] == 'Training']
    tst_targets  = [row[0] for row in rows if row[-1] == 'PublicTest']
    tst2_targets = [row[0] for row in rows if row[-1] == 'PrivateTest']

    return trn, tst, tst2, trn_targets, tst_targets, tst2_targets

def vector_to_2d_array(data):
    imgs = []

    for i in data:
        # print (emotions[int(i[0])])
        im = np.fromstring(i[0], dtype=int, sep=" ").reshape((48, 48))

        imgs.append(im)
        # plt.imshow(im, cmap = 'gray', interpolation = 'bicubic')
        # plt.xticks([]), plt.yticks([])
        # plt.show()

    imgs = np.array(imgs)
    nsamples, nx, ny = imgs.shape
    d2_imgs = imgs.reshape(nsamples, nx*ny)

    return d2_imgs, imgs

# emotion indices are the labels in kmeans prediction
emotions = ["Angry", "Disgust", "Fear", "Joy", "Sad", "Surprise", "Neutral"]
n = len(emotions)

t1, t2, t3, trn_targets, tst_targets, tst2_targets = load_data()
test = t2 + t3
test_targets = list(tst_targets) + list(tst2_targets)
# reshape to image dimensions 48 x 48
d2_imgs, imgs       = vector_to_2d_array(t1)
d2_t2_imgs, t2_imgs = vector_to_2d_array(test)

# change integers to strings for MLP labels
trn_targets = np.array(trn_targets, str)
test_targets= np.array(test_targets, str)

print("Learning Emotions")
# assign training set and test sets
X_train, X_test, y_train, y_test = d2_imgs, d2_t2_imgs, trn_targets, test_targets

scaler = StandardScaler()
# standardize training data for classifier
scaler.fit(X_train)
X_train = scaler.transform(X_train)
# apply same transformation to test data
X_test = scaler.transform(X_test)

# Compute a PCA
# reduce dimensionality to n_components
n_components = 48
pca = PCA(n_components=48, whiten= True, svd_solver='randomized').fit(X_train)

# print ("PCA variance retained", np.cumsum(pca.explained_variance_ratio_))
# apply PCA transformation
X_train_pca = pca.transform(X_train)
X_test_pca = pca.transform(X_test)

X_inv_proj = pca.inverse_transform(X_train_pca)
X_proj_img = np.reshape(X_inv_proj,(len(X_train),48,48))

# ORIGINAL IMAGES
#Setup a figure 8 inches by 8 inches
fig = plt.figure(figsize=(6,6))
fig.subplots_adjust(left=0, right=1, bottom=0, top=1, hspace=0.05, wspace=0.05)
# plot the faces, each image is 64 by 64 dimension but 8x8 pixels
for i in range(64):
    ax = fig.add_subplot(8, 8, i+1, xticks=[], yticks=[])
    ax.imshow(imgs[i], cmap=plt.cm.bone, interpolation='nearest')

# IAMGES AFTER PCA AND WHITENING
#Setup a figure 8 inches by 8 inches
fig = plt.figure(figsize=(6,6))
fig.subplots_adjust(left=0, right=1, bottom=0, top=1, hspace=0.05, wspace=0.05)
# plot the faces, each image is 64 by 64 dimension but 8x8 pixels
for i in range(64):
    ax = fig.add_subplot(8, 8, i+1, xticks=[], yticks=[])
    ax.imshow(X_proj_img[i], cmap=plt.cm.bone, interpolation='nearest')

#************************** K-Means Clustering ******************************
# reshape reduced dataset for kmeans
nsamples, nx, ny = X_proj_img.shape
d2_X_proj = X_proj_img.reshape(nsamples, nx*ny)

kmeans = KMeans(n_clusters=n, random_state=0)
clusters = kmeans.fit_predict(d2_X_proj)

# print("Cluster faces post-PCA")
fig, ax = plt.subplots(1, n, figsize=(8, 3))
centers = kmeans.cluster_centers_.reshape(n, 48, 48)
for axi, center in zip(ax.flat, centers):
    axi.set(xticks=[], yticks=[])
    axi.imshow(center, interpolation='nearest', cmap=plt.cm.binary)

# print("K-means cluster plot")
#
# from sklearn.datasets.samples_generator import make_blobs
# trn, trn_targets = make_blobs(n_samples=len(t1), centers=7,
#                            cluster_std=0.60, random_state=0)
# X = trn[:, ::-1] # flip axes for better plotting
# # Plot the data with K Means Labels
# from sklearn.cluster import KMeans
# kmeans = KMeans(7, random_state=0)
# labels = kmeans.fit(X).predict(X)
# plt.scatter(X[:, 0], X[:, 1], c=labels, s=40, cmap='viridis');

labels = np.zeros_like(clusters)
mask = (clusters == 0 )
labels[mask] = mode(y_train[mask])[0]

for i in range(n):
    mask = (clusters == i)
    labels[mask] = mode(y_train[mask])[0]
labels = np.array(labels, str)
results=accuracy_score(y_train, labels)
print(results)

#*********************** Neural Network Classifier ***************************
print("Fitting the classifier to the training set")
clf = MLPClassifier(hidden_layer_sizes=(1024,), alpha=1e-05, batch_size=256, verbose=True, early_stopping=True, ).fit(X_train_pca, y_train)

y_pred = clf.predict(X_test_pca)
target_names = list(map(str, range(7)))
# print(classification_report(y_test, y_pred, target_names=target_names))

results= accuracy_score(y_test, y_pred, normalize=True)
print("MLP Results", results)

tuple_objects = (clf, X_train, y_train, results)
# Save tuple to disk
pickle.dump(tuple_objects, open("finalized_tuple_model.pkl", 'wb'))
