"""
The ``mlflow.paddle`` module provides an API for logging and loading paddle models.
This module exports paddle models with the following flavors:

Paddle (native) format
    This is the main flavor that can be loaded back into paddle.

:py:mod:`mlflow.pyfunc`
    Produced for use by generic pyfunc-based deployment tools and batch inference.
    NOTE: The `mlflow.pyfunc` flavor is only added for paddle models that define `predict()`,
    since `predict()` is required for pyfunc model inference.
"""

import os
import logging
import yaml

import mlflow
from mlflow import pyfunc
from mlflow.exceptions import MlflowException
from mlflow.models import Model
from mlflow.models.model import MLMODEL_FILE_NAME
from mlflow.models.signature import ModelSignature
from mlflow.models.utils import ModelInputExample, _save_example
from mlflow.protos.databricks_pb2 import RESOURCE_ALREADY_EXISTS
from mlflow.tracking.artifact_utils import _download_artifact_from_uri
from mlflow.utils.environment import _mlflow_conda_env, _log_pip_requirements
from mlflow.utils.model_utils import _get_flavor_configuration
from mlflow.tracking._model_registry import DEFAULT_AWAIT_MAX_SLEEP_SECONDS

FLAVOR_NAME = "paddle"

_logger = logging.getLogger(__name__)


def get_default_conda_env():
    """
    :return: The default Conda environment for MLflow Models produced by calls to
             :func:`save_model()` and :func:`log_model()`.
    """
    import paddle

    pip_deps = ["paddlepaddle=={}".format(paddle.__version__)]
    return _mlflow_conda_env(additional_pip_deps=pip_deps, additional_conda_channels=None)


def save_model(
    pd_model,
    path,
    training=False,
    conda_env=None,
    mlflow_model=None,
    signature: ModelSignature = None,
    input_example: ModelInputExample = None,
):
    """
    Save a paddle model to a path on the local file system. Produces an MLflow Model
    containing the following flavors:

        - :py:mod:`mlflow.paddle`
        - :py:mod:`mlflow.pyfunc`. NOTE: This flavor is only included for paddle models
          that define `predict()`, since `predict()` is required for pyfunc model inference.

    :param pd_model: paddle model to be saved.
    :param path: Local path where the model is to be saved.
    :param training: Only valid when saving a model trained using the PaddlePaddle high level API.
                     If set to True, the saved model supports both re-training and
                     inference. If set to False, it only supports inference.
    :param conda_env: Either a dictionary representation of a Conda environment or the path to a
                      Conda environment yaml file. If provided, this decsribes the environment
                      this model should be run in. At minimum, it should specify the dependencies
                      contained in :func:`get_default_conda_env()`. If `None`, the default
                      :func:`get_default_conda_env()` environment is added to the model.
                      The following is an *example* dictionary representation of a Conda
                      environment::

                        {
                            'name': 'mlflow-env',
                            'channels': ['defaults'],
                            'dependencies': [
                                'python=3.8.2',
                                'paddle=2.1.0'
                            ]
                        }

    :param mlflow_model: :py:mod:`mlflow.models.Model` this flavor is being added to.
    :param signature: (Experimental) :py:class:`ModelSignature <mlflow.models.ModelSignature>`
                      describes model input and output :py:class:`Schema <mlflow.types.Schema>`.
                      The model signature can be :py:func:`inferred <mlflow.models.infer_signature>`
                      from datasets with valid model input (e.g. the training dataset with target
                      column omitted) and valid model output (e.g. model predictions generated on
                      the training dataset), for example:
                      .. code-block:: python

                        from mlflow.models.signature import infer_signature
                        train = df.drop_column("target_label")
                        predictions = ... # compute model predictions
                        signature = infer_signature(train, predictions)
    :param input_example: (Experimental) Input example provides one or several instances of valid
                          model input. The example can be used as a hint of what data to feed the
                          model. The given example will be converted to a Pandas DataFrame and then
                          serialized to json using the Pandas split-oriented format. Bytes are
                          base64-encoded.

    .. code-block:: python
        :caption: Example

        import mlflow.paddle
        import paddle
        from paddle.nn import Linear
        import paddle.nn.functional as F
        import numpy as np
        import os
        import random
        from sklearn.datasets import load_boston
        from sklearn.model_selection import train_test_split
        from sklearn import preprocessing

        def load_data():
            # dataset on boston housing prediction
            X, y = load_boston(return_X_y=True)

            min_max_scaler = preprocessing.MinMaxScaler()
            X_min_max = min_max_scaler.fit_transform(X)
            X_normalized = preprocessing.scale(X_min_max, with_std=False)

            X_train, X_test, y_train, y_test = train_test_split(
                X_normalized, y, test_size=0.2, random_state=42)

            y_train = y_train.reshape(-1, 1)
            y_test = y_test.reshape(-1, 1)
            return np.concatenate(
                (X_train, y_train), axis=1),np.concatenate((X_test, y_test), axis=1
            )

        class Regressor(paddle.nn.Layer):

            def __init__(self):
                super(Regressor, self).__init__()

                self.fc = Linear(in_features=13, out_features=1)

            @paddle.jit.to_static
            def forward(self, inputs):
                x = self.fc(inputs)
                return x

        model = Regressor()
        model.train()
        training_data, test_data = load_data()
        opt = paddle.optimizer.SGD(learning_rate=0.01, parameters=model.parameters())

        EPOCH_NUM = 10
        BATCH_SIZE = 10

        for epoch_id in range(EPOCH_NUM):
            np.random.shuffle(training_data)
            mini_batches = [training_data[k : k + BATCH_SIZE]
                for k in range(0, len(training_data), BATCH_SIZE)]
            for iter_id, mini_batch in enumerate(mini_batches):
                x = np.array(mini_batch[:, :-1]).astype('float32')
                y = np.array(mini_batch[:, -1:]).astype('float32')
                house_features = paddle.to_tensor(x)
                prices = paddle.to_tensor(y)

                predicts = model(house_features)

                loss = F.square_error_cost(predicts, label=prices)
                avg_loss = paddle.mean(loss)
                if iter_id%20==0:
                    print("epoch: {}, iter: {}, loss is: {}".format(
                        epoch_id, iter_id, avg_loss.numpy()))

                avg_loss.backward()
                opt.step()
                opt.clear_grad()

        mlflow.log_param('learning_rate', 0.01)
        mlflow.paddle.log_model(model, "model")
        sk_path_dir = './test-out'
        mlflow.paddle.save_model(model, sk_path_dir)
        print("Model saved in run %s" % mlflow.active_run().info.run_uuid)
    """
    import paddle

    if os.path.exists(path):
        raise MlflowException(
            message="Path '{}' already exists".format(path), error_code=RESOURCE_ALREADY_EXISTS
        )

    os.makedirs(path)
    if mlflow_model is None:
        mlflow_model = Model()
    if signature is not None:
        mlflow_model.signature = signature
    if input_example is not None:
        _save_example(mlflow_model, input_example, path)

    model_data_subpath = "model"
    output_path = os.path.join(path, model_data_subpath)

    if isinstance(pd_model, paddle.Model):
        pd_model.save(output_path, training=training)
    else:
        paddle.jit.save(pd_model, output_path)

    conda_env_subpath = "conda.yaml"
    if conda_env is None:
        conda_env = get_default_conda_env()
    elif not isinstance(conda_env, dict):
        with open(conda_env, "r") as f:
            conda_env = yaml.safe_load(f)
    with open(os.path.join(path, conda_env_subpath), "w") as f:
        yaml.safe_dump(conda_env, stream=f, default_flow_style=False)

    _log_pip_requirements(conda_env, path)

    # `PyFuncModel` only works for paddle models that define `predict()`.
    pyfunc.add_to_model(
        mlflow_model,
        loader_module="mlflow.paddle",
        model_path=model_data_subpath,
        env=conda_env_subpath,
    )
    mlflow_model.add_flavor(
        FLAVOR_NAME, pickled_model=model_data_subpath, paddle_version=paddle.__version__,
    )
    mlflow_model.save(os.path.join(path, MLMODEL_FILE_NAME))


def load_model(model_uri, model=None, **kwargs):
    """
    Load a paddle model from a local file or a run.
    :param model_uri: The location, in URI format, of the MLflow model, for example:

            - ``/Users/me/path/to/local/model``
            - ``relative/path/to/local/model``
            - ``s3://my_bucket/path/to/model``
            - ``runs:/<mlflow_run_id>/run-relative/path/to/model``
            - ``models:/<model_name>/<model_version>``
            - ``models:/<model_name>/<stage>``

    :param model: Required when loading a `paddle.Model` model saved with `training=True`.
    :param kwargs: The keyword arguments to pass to `paddle.jit.load`
                   or `model.load`.

    For more information about supported URI schemes, see
    `Referencing Artifacts <https://www.mlflow.org/docs/latest/concepts.html#
    artifact-locations>`_.

    :return: A paddle model.

    .. code-block:: python
        :caption: Example

        import mlflow.paddle
        pd_model = mlflow.paddle.load_model("runs:/96771d893a5e46159d9f3b49bf9013e2/pd_models")
        # use Pandas DataFrame to make predictions
        np_array = ...
        predictions = pd_model(np_array)
    """
    import paddle

    local_model_path = _download_artifact_from_uri(artifact_uri=model_uri)
    flavor_conf = _get_flavor_configuration(model_path=local_model_path, flavor_name=FLAVOR_NAME)
    pd_model_artifacts_path = os.path.join(local_model_path, flavor_conf["pickled_model"])
    if model is None:
        return paddle.jit.load(pd_model_artifacts_path, **kwargs)
    elif not isinstance(model, paddle.Model):
        raise TypeError(
            "Invalid object type `{}` for `model`, must be `paddle.Model`".format(type(model))
        )
    else:
        contains_pdparams = _contains_pdparams(local_model_path)
        if not contains_pdparams:
            raise TypeError(
                "This model can't be loaded via `model.load` because a '.pdparams' file "
                "doesn't exist. Please leave `model` unspecified to load the model via "
                "`paddle.jit.load` or set `training` to True when saving a model."
            )

        model.load(
            pd_model_artifacts_path, **kwargs,
        )
        return model


def log_model(
    pd_model,
    artifact_path,
    training=False,
    conda_env=None,
    registered_model_name=None,
    signature: ModelSignature = None,
    input_example: ModelInputExample = None,
    await_registration_for=DEFAULT_AWAIT_MAX_SLEEP_SECONDS,
):

    """
    Log a paddle model as an MLflow artifact for the current run. Produces an MLflow Model
    containing the following flavors:

        - :py:mod:`mlflow.paddle`
        - :py:mod:`mlflow.pyfunc`. NOTE: This flavor is only included for paddle models
          that define `predict()`, since `predict()` is required for pyfunc model inference.

    :param pd_model: paddle model to be saved.
    :param artifact_path: Run-relative artifact path.
    :param training: Only valid when saving a model trained using the PaddlePaddle high level API.
                     If set to True, the saved model supports both re-training and
                     inference. If set to False, it only supports inference.
    :param conda_env: Either a dictionary representation of a Conda environment or the path to a
                      Conda environment yaml file. If provided, this decsribes the environment
                      this model should be run in. At minimum, it should specify the dependencies
                      contained in :func:`get_default_conda_env()`. If `None`, the default
                      :func:`get_default_conda_env()` environment is added to the model.
                      The following is an *example* dictionary representation of a Conda
                      environment::

                        {
                            'name': 'mlflow-env',
                            'channels': ['defaults'],
                            'dependencies': [
                                'python=3.8.2',
                                'paddlepaddle=2.1.0'
                            ]
                        }

    :param registered_model_name: (Experimental) If given, create a model version under
                                  ``registered_model_name``, also creating a registered model if one
                                  with the given name does not exist.
    :param signature: (Experimental) :py:class:`ModelSignature <mlflow.models.ModelSignature>`
                      describes model input and output :py:class:`Schema <mlflow.types.Schema>`.
                      The model signature can be :py:func:`inferred <mlflow.models.infer_signature>`
                      from datasets with valid model input (e.g. the training dataset with target
                      column omitted) and valid model output (e.g. model predictions generated on
                      the training dataset), for example:
                      .. code-block:: python

                        from mlflow.models.signature import infer_signature
                        train = df.drop_column("target_label")
                        predictions = ... # compute model predictions
                        signature = infer_signature(train, predictions)
    :param input_example: (Experimental) Input example provides one or several instances of valid
                          model input. The example can be used as a hint of what data to feed the
                          model. The given example will be converted to a Pandas DataFrame and then
                          serialized to json using the Pandas split-oriented format. Bytes are
                          base64-encoded.
    :param await_registration_for: Number of seconds to wait for the model version to finish
                            being created and is in ``READY`` status. By default, the function
                            waits for five minutes. Specify 0 or None to skip waiting.

    .. code-block:: python
        :caption: Example

        import mlflow.paddle
        def load_data():
            ...
        class Regressor():
            ...
        model = Regressor()
        model.train()
        training_data, test_data = load_data()
        opt = paddle.optimizer.SGD(learning_rate=0.01, parameters=model.parameters())

        EPOCH_NUM = 10
        BATCH_SIZE = 10

        for epoch_id in range(EPOCH_NUM):
            ...

        mlflow.log_param('learning_rate', 0.01)
        mlflow.paddle.log_model(model, "model")
        sk_path_dir = ...
        mlflow.paddle.save_model(model, sk_path_dir)
    """
    return Model.log(
        artifact_path=artifact_path,
        flavor=mlflow.paddle,
        pd_model=pd_model,
        conda_env=conda_env,
        registered_model_name=registered_model_name,
        signature=signature,
        input_example=input_example,
        await_registration_for=await_registration_for,
        training=training,
    )


def _load_pyfunc(path):
    """
    Load PyFunc implementation. Called by ``pyfunc.load_pyfunc``.
    :param path: Local filesystem path to the MLflow Model with the ``paddle`` flavor.
    """
    return _PaddleWrapper(load_model(path))


class _PaddleWrapper(object):
    """
    Wrapper class that creates a predict function such that
    predict(data: pd.DataFrame) -> model's output as pd.DataFrame (pandas DataFrame)
    """

    def __init__(self, pd_model):
        self.pd_model = pd_model

    def predict(self, data):
        import pandas as pd
        import numpy as np

        if isinstance(data, pd.DataFrame):
            inp_data = data.values.astype(np.float32)
        elif isinstance(data, np.ndarray):
            inp_data = data
        elif isinstance(data, (list, dict)):
            raise TypeError(
                "The paddle flavor does not support List or Dict input types. "
                "Please use a pandas.DataFrame or a numpy.ndarray"
            )
        else:
            raise TypeError("Input data should be pandas.DataFrame or numpy.ndarray")
        inp_data = np.squeeze(inp_data)

        self.pd_model.eval()

        predicted = self.pd_model(inp_data)
        return pd.DataFrame(predicted.numpy())


def _contains_pdparams(path):
    file_list = os.listdir(path)
    return any(".pdparams" in file for file in file_list)
