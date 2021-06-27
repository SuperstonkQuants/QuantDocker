import os

import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.ensemble import RandomForestClassifier
import shap

import mlflow
from utils import to_pandas_Xy


# prepare training data
X, y = to_pandas_Xy(load_breast_cancer())
X = X.iloc[:50, :8]
y = y.iloc[:50]

# train a model
model = RandomForestClassifier()
model.fit(X, y)

# log an explanation
with mlflow.start_run() as run:
    mlflow.shap.log_explanation(lambda X: model.predict_proba(X)[:, 1], X)

# list artifacts
client = mlflow.tracking.MlflowClient()
artifact_path = "model_explanations_shap"
artifacts = [x.path for x in client.list_artifacts(run.info.run_id, artifact_path)]
print("# artifacts:")
print(artifacts)

# load back the logged explanation
dst_path = client.download_artifacts(run.info.run_id, artifact_path)
base_values = np.load(os.path.join(dst_path, "base_values.npy"))
shap_values = np.load(os.path.join(dst_path, "shap_values.npy"))

# show a force plot
shap.force_plot(float(base_values), shap_values[0, :], X.iloc[0, :], matplotlib=True)
