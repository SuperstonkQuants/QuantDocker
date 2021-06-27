#!/usr/bin/env bash
set -x
# Set err=1 if any commands exit with non-zero status as described in
# https://stackoverflow.com/a/42219754
err=0
trap 'err=1' ERR
export MLFLOW_HOME=$(pwd)

# Run ML framework tests in their own Python processes to avoid OOM issues due to per-framework
# overhead
pytest tests/pytorch --large
pytest tests/h2o --large
pytest tests/onnx --large
pytest tests/pyfunc --large
pytest tests/sklearn --large
pytest tests/azureml --large
pytest tests/models --large
pytest tests/xgboost --large
pytest tests/lightgbm --large
pytest tests/catboost --large
pytest tests/statsmodels --large
pytest tests/gluon --large
pytest tests/gluon_autolog --large
pytest tests/spacy --large
pytest tests/fastai --large
pytest tests/shap --large
pytest tests/paddle --large
pytest tests/utils/test_model_utils.py --large
pytest tests/tracking/fluent/test_fluent_autolog.py --large
pytest tests/autologging --large
find tests/spark_autologging/ml -name 'test*.py' | xargs -L 1 pytest --large
pytest tests/test_mlflow_lazily_imports_ml_packages.py --lazy-import

test $err = 0
