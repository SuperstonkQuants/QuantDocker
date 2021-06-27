.. _tracking:

===============
MLflow Tracking
===============

The MLflow Tracking component is an API and UI for logging parameters, code versions, metrics, and output files
when running your machine learning code and for later visualizing the results.
MLflow Tracking lets you log and query experiments using :ref:`Python <python-api>`, :ref:`REST <rest-api>`, :ref:`R-api`, and :ref:`java_api` APIs.

.. contents:: Table of Contents
  :local:
  :depth: 2

Concepts
========

MLflow Tracking is organized around the concept of *runs*, which are executions of some piece of
data science code. Each run records the following information:

Code Version
    Git commit hash used for the run, if it was run from an :ref:`MLflow Project <projects>`.

Start & End Time
    Start and end time of the run

Source
    Name of the file to launch the run, or the project name and entry point for the run
    if run from an :ref:`MLflow Project <projects>`.

Parameters
    Key-value input parameters of your choice. Both keys and values are strings.

Metrics
    Key-value metrics, where the value is numeric. Each metric can be updated throughout the
    course of the run (for example, to track how your model's loss function is converging), and
    MLflow records and lets you visualize the metric's full history.

Artifacts
    Output files in any format. For example, you can record images (for example, PNGs), models
    (for example, a pickled scikit-learn model), and data files (for example, a
    `Parquet <https://parquet.apache.org/>`_ file) as artifacts.

You can record runs using MLflow Python, R, Java, and REST APIs from anywhere you run your code. For
example, you can record them in a standalone program, on a remote cloud machine, or in an
interactive notebook. If you record runs in an :ref:`MLflow Project <projects>`, MLflow
remembers the project URI and source version.

You can optionally organize runs into *experiments*, which group together runs for a
specific task. You can create an experiment using the ``mlflow experiments`` CLI, with
:py:func:`mlflow.create_experiment`, or using the corresponding REST parameters. The MLflow API and
UI let you create and search for experiments.

Once your runs have been recorded, you can query them using the :ref:`tracking_ui` or the MLflow
API.

.. _where_runs_are_recorded:

Where Runs Are Recorded
=======================

MLflow runs can be recorded to local files, to a SQLAlchemy compatible database, or remotely
to a tracking server. By default, the MLflow Python API logs runs locally to files in an ``mlruns`` directory wherever you
ran your program. You can then run ``mlflow ui`` to see the logged runs.

To log runs remotely, set the ``MLFLOW_TRACKING_URI`` environment variable to a tracking server's URI or
call :py:func:`mlflow.set_tracking_uri`.

There are different kinds of remote tracking URIs:

- Local file path (specified as ``file:/my/local/dir``), where data is just directly stored locally.
- Database encoded as ``<dialect>+<driver>://<username>:<password>@<host>:<port>/<database>``. MLflow supports the dialects ``mysql``, ``mssql``, ``sqlite``, and ``postgresql``. For more details, see `SQLAlchemy database uri <https://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls>`_.
- HTTP server (specified as ``https://my-server:5000``), which is a server hosting an :ref:`MLflow tracking server <tracking_server>`.
- Databricks workspace (specified as ``databricks`` or as ``databricks://<profileName>``, a `Databricks CLI profile <https://github.com/databricks/databricks-cli#installation>`_.
  Refer to Access the MLflow tracking server from outside Databricks `[AWS] <http://docs.databricks.com/applications/mlflow/access-hosted-tracking-server.html>`_
  `[Azure] <http://docs.microsoft.com/azure/databricks/applications/mlflow/access-hosted-tracking-server>`_, or :ref:`the quickstart <quickstart_logging_to_remote_server>` to
  easily get started with hosted MLflow on Databricks Community Edition.

How Runs and Artifacts are Recorded
===================================
As mentioned above, MLflow runs can be recorded to local files, to a SQLAlchemy compatible database, or remotely to a tracking server. MLflow artifacts can be persisted to local files
and a variety of remote file storage solutions. For storing runs and artifacts, MLflow uses two components for `storage <https://mlflow.org/docs/latest/tracking.html#storage>`_: backend store and artifact store. While the backend store persists
MLflow entities (runs, parameters, metrics, tags, notes, metadata, etc), the artifact store persists artifacts
(files, models, images, in-memory objects, or model summary, etc).

The MLflow client can interface with a variety of `backend <https://mlflow.org/docs/latest/tracking.html#backend-stores>`_ and `artifact <https://mlflow.org/docs/latest/tracking.html#artifact-stores>`_ storage configurations.
Here are four common configuration scenarios:

Scenario 1: MLflow on localhost
-------------------------------

Many developers run MLflow on their local machine, where both the backend and artifact store share a directory
on the local filesystem—``./mlruns``—as shown in the diagram. The MLflow client directly interfaces with an
instance of a `FileStore` and `LocalArtifactRepository`.

.. figure:: _static/images/scenario_1.png

In this simple scenario, the MLflow client uses the following interfaces to record MLflow entities and artifacts:

 * An instance of a `LocalArtifactRepository` (to store artifacts)
 * An instance of a `FileStore` (to save MLflow entities)

Scenario 2: MLflow on localhost with SQLite
-------------------------------------------

Many users also run MLflow on their local machines with a `SQLAlchemy-compatible <https://docs.sqlalchemy.org/en/14/core/engines.html#database-urls>`_ database: `SQLite <https://sqlite.org/docs.html>`_. In this case, artifacts
are stored under the local ``./mlruns`` directory, and MLflow entities are inserted in a SQLite database file ``mlruns.db``.

.. figure:: _static/images/scenario_2.png

In this scenario, the MLflow client uses the following interfaces to record MLflow entities and artifacts:

 * An instance of a `LocalArtifactRepository` (to save artifacts)
 * An instance of an `SQLAlchemyStore` (to store MLflow entities to a SQLite file ``mlruns.db``)

Scenario 3: MLflow on localhost with Tracking Server
----------------------------------------------------

Similar to scenario 1 but a tracking server is launched, listening for REST request calls at the default port 5000.
The arguments supplied to the ``mlflow server <args>`` dictate what backend and artifact stores are used.
The default is local `FileStore`. For example, if a user launched a tracking server as
``mlflow server --backend-store-uri sqlite:///mydb.sqlite``, then SQLite would be used for backend storage instead.

As in scenario 1, MLflow uses a local `mlruns` filesystem directory as a backend store and artifact store. With a tracking
server running, the MLflow client interacts with the tracking server via REST requests, as shown in the diagram.

.. figure:: _static/images/scenario_3.png

To store all runs' MLflow entities, the MLflow client interacts with the tracking server via a series of REST requests:

 * **Part 1a and b**:

  * The MLflow client creates an instance of a `RestStore` and sends REST API requests to log MLflow entities
  * The Tracking Server creates an instance of a `FileStore` to save MLflow entities and writes directly to the local `mlruns` directory

For the artifacts, the MLflow client interacts with the tracking server via a REST request:

 * **Part 2a, b, and c**:

   * The MLflow client uses `RestStore` to send a REST request to fetch the artifact store URI location
   * The Tracking Server responds with an artifact store URI location
   * The MLflow client creates an instance of a `LocalArtifactRepository` and saves artifacts to the local filesystem location specified by the artifact store URI (a subdirectory of `mlruns`)

Scenario 4: MLflow with remote Tracking Server, backend and artifact stores
---------------------------------------------------------------------------

MLflow also supports distributed architectures, where the tracking server, backend store, and artifact store
reside on remote hosts. This example scenario depicts an architecture with a remote MLflow Tracking Server,
a Postgres database for backend entity storage, and an S3 bucket for artifact storage.

.. figure:: _static/images/scenario_4.png

To record all runs' MLflow entities, the MLflow client interacts with the tracking server via a series of REST requests:

 * **Part 1a and b**:

  * The MLflow client creates an instance of a `RestStore` and sends REST API requests to log MLflow entities
  * The Tracking Server creates an instance of an `SQLAlchemyStore` and connects to the remote host to
    insert MLflow entities in the database

For artifact logging, the MLflow client interacts with the remote Tracking Server and artifact storage host:

 * **Part 2a, b, and c**:

  * The MLflow client uses `RestStore` to send a REST request to fetch the artifact store URI location from the Tracking Server
  * The Tracking Server responds with an artifact store URI location (an S3 storage URI in this case)
  * The MLflow client creates an instance of an `S3ArtifactRepository`, connects to the remote AWS host using the
    `boto client <https://boto3.amazonaws.com/v1/documentation/api/latest/index.html>`_ libraries, and uploads the artifacts to the S3 bucket URI location

.. note::

    In all scenarios, the MLflow client directly logs artifacts to the remote artifact store. It does not proxy these through the
    tracking server.

The `FileStore <https://github.com/mlflow/mlflow/blob/master/mlflow/store/tracking/file_store.py#L115>`_,
`RestoreStore <https://github.com/mlflow/mlflow/blob/master/mlflow/store/tracking/rest_store.py#L39>`_,
and `SQLAlchemyStore <https://github.com/mlflow/mlflow/blob/master/mlflow/store/tracking/sqlalchemy_store.py#L61>`_ are
concrete implementations of the abstract class `AbstractStore <https://github.com/mlflow/mlflow/blob/master/mlflow/store/tracking/abstract_store.py>`_,
and the `LocalArtifactRepository <https://github.com/mlflow/mlflow/blob/master/mlflow/store/artifact/local_artifact_repo.py#L15>`_ and
`S3ArtifactRepository <https://github.com/mlflow/mlflow/blob/master/mlflow/store/artifact/s3_artifact_repo.py#L14>`_ are
concrete implementations of the abstract class `ArtifactRepository <https://github.com/mlflow/mlflow/blob/master/mlflow/store/artifact/artifact_repo.py#L13>`_.

Logging Data to Runs
====================

You can log data to runs using the MLflow Python, R, Java, or REST API. This section
shows the Python API.

.. contents:: In this section:
  :depth: 1
  :local:


Logging Functions
------------------

:py:func:`mlflow.set_tracking_uri` connects to a tracking URI. You can also set the
``MLFLOW_TRACKING_URI`` environment variable to have MLflow find a URI from there. In both cases,
the URI can either be a HTTP/HTTPS URI for a remote server, a database connection string, or a
local path to log data to a directory. The URI defaults to ``mlruns``.

:py:func:`mlflow.tracking.get_tracking_uri` returns the current tracking URI.

:py:func:`mlflow.create_experiment` creates a new experiment and returns its ID. Runs can be
launched under the experiment by passing the experiment ID to ``mlflow.start_run``.

:py:func:`mlflow.set_experiment` sets an experiment as active. If the experiment does not exist,
creates a new experiment. If you do not specify an experiment in :py:func:`mlflow.start_run`, new
runs are launched under this experiment.

:py:func:`mlflow.start_run` returns the currently active run (if one exists), or starts a new run
and returns a :py:class:`mlflow.ActiveRun` object usable as a context manager for the
current run. You do not need to call ``start_run`` explicitly: calling one of the logging functions
with no active run automatically starts a new one.

:py:func:`mlflow.end_run` ends the currently active run, if any, taking an optional run status.

:py:func:`mlflow.active_run` returns a :py:class:`mlflow.entities.Run` object corresponding to the
currently active run, if any.
**Note**: You cannot access currently-active run attributes
(parameters, metrics, etc.) through the run returned by ``mlflow.active_run``. In order to access
such attributes, use the :py:class:`mlflow.tracking.MlflowClient` as follows:

.. code-block:: py

    client = mlflow.tracking.MlflowClient()
    data = client.get_run(mlflow.active_run().info.run_id).data


:py:func:`mlflow.log_param` logs a single key-value param in the currently active run. The key and
value are both strings. Use :py:func:`mlflow.log_params` to log multiple params at once.

:py:func:`mlflow.log_metric` logs a single key-value metric. The value must always be a number.
MLflow remembers the history of values for each metric. Use :py:func:`mlflow.log_metrics` to log
multiple metrics at once.

:py:func:`mlflow.set_tag` sets a single key-value tag in the currently active run. The key and
value are both strings. Use :py:func:`mlflow.set_tags` to set multiple tags at once.

:py:func:`mlflow.log_artifact` logs a local file or directory as an artifact, optionally taking an
``artifact_path`` to place it in within the run's artifact URI. Run artifacts can be organized into
directories, so you can place the artifact in a directory this way.

:py:func:`mlflow.log_artifacts` logs all the files in a given directory as artifacts, again taking
an optional ``artifact_path``.

:py:func:`mlflow.get_artifact_uri` returns the URI that artifacts from the current run should be
logged to.


Launching Multiple Runs in One Program
--------------------------------------

Sometimes you want to launch multiple MLflow runs in the same program: for example, maybe you are
performing a hyperparameter search locally or your experiments are just very fast to run. This is
easy to do because the ``ActiveRun`` object returned by :py:func:`mlflow.start_run` is a Python
`context manager <https://docs.python.org/2.5/whatsnew/pep-343.html>`_. You can "scope" each run to
just one block of code as follows:

.. code-block:: py

   with mlflow.start_run():
       mlflow.log_param("x", 1)
       mlflow.log_metric("y", 2)
       ...

The run remains open throughout the ``with`` statement, and is automatically closed when the
statement exits, even if it exits due to an exception.


Performance Tracking with Metrics
---------------------------------

You log MLflow metrics with ``log`` methods in the Tracking API. The ``log`` methods support two alternative methods for distinguishing metric values on the x-axis: ``timestamp`` and ``step``.

``timestamp`` is an optional long value that represents the time that the metric was logged. ``timestamp`` defaults to the current time. ``step`` is an optional integer that represents any measurement of training progress (number of training iterations, number of epochs, and so on). ``step`` defaults to 0 and has the following requirements and properties:

- Must be a valid 64-bit integer value.
- Can be negative.
- Can be out of order in successive write calls. For example, (1, 3, 2) is a valid sequence.
- Can have "gaps" in the sequence of values specified in successive write calls. For example, (1, 5, 75, -20) is a valid sequence.

If you specify both a timestamp and a step, metrics are recorded against both axes independently.

Examples
~~~~~~~~

Python
  .. code-block:: py

    with mlflow.start_run():
        for epoch in range(0, 3):
            mlflow.log_metric(key="quality", value=2*epoch, step=epoch)

Java and Scala
  .. code-block:: java

    MlflowClient client = new MlflowClient();
    RunInfo run = client.createRun();
    for (int epoch = 0; epoch < 3; epoch ++) {
        client.logMetric(run.getRunId(), "quality", 2 * epoch, System.currentTimeMillis(), epoch);
    }


Visualizing Metrics
-------------------

Here is an example plot of the :ref:`quick start tutorial <quickstart>` with the step x-axis and two timestamp axes:

.. figure:: _static/images/metrics-step.png

  X-axis step

.. figure:: _static/images/metrics-time-wall.png

  X-axis wall time - graphs the absolute time each metric was logged

.. figure:: _static/images/metrics-time-relative.png

  X-axis relative time - graphs the time relative to the first metric logged, for each run


.. _automatic-logging:

Automatic Logging
=================

Automatic logging allows you to log metrics, parameters, and models without the need for explicit log statements. 

There are two ways to use autologging:

#. Call :py:func:`mlflow.autolog` before your training code. This will enable autologging for each supported library you have installed as soon as you import it.
#. Use library-specific autolog calls for each library you use in your code. See below for examples.

The following libraries support autologging:

.. contents::
  :local:
  :depth: 1

For flavors that automatically save models as an artifact, `additional files <https://mlflow.org/docs/latest/models.html#storage-format>`_ for dependency management are logged.


Scikit-learn (experimental)
---------------------------

Call :py:func:`mlflow.sklearn.autolog` before your training code to enable automatic logging of sklearn metrics, params, and models.
See example usage `here <https://github.com/mlflow/mlflow/tree/master/examples/sklearn_autolog>`_.

Autologging for estimators (e.g. `LinearRegression`_) and meta estimators (e.g. `Pipeline`_) creates a single run and logs:

+-------------------------+--------------------------+------------------------------+------------------+
| Metrics                 | Parameters               | Tags                         | Artifacts        |
+-------------------------+--------------------------+------------------------------+------------------+
| Training score obtained | Parameters obtained by   | - Class name                 | Fitted estimator |
| by ``estimator.score``  | ``estimator.get_params`` | - Fully qualified class name |                  |
+-------------------------+--------------------------+------------------------------+------------------+


.. _LinearRegression:
    https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LinearRegression.html

.. _Pipeline:
    https://scikit-learn.org/stable/modules/generated/sklearn.pipeline.Pipeline.html


Autologging for parameter search estimators (e.g. `GridSearchCV`_) creates a single parent run and nested child runs

.. code-block::

  - Parent run
    - Child run 1
    - Child run 2
    - ...

containing the following data:

+------------------+----------------------------+-------------------------------------------+------------------------------+-------------------------------------+
| Run type         | Metrics                    | Parameters                                | Tags                         | Artifacts                           |
+------------------+----------------------------+-------------------------------------------+------------------------------+-------------------------------------+
| Parent           | Training score             | - Parameter search estimator's parameters | - Class name                 | - Fitted parameter search estimator |
|                  |                            | - Best parameter combination              | - Fully qualified class name | - Fitted best estimator             |
|                  |                            |                                           |                              | - Search results csv file           |
+------------------+----------------------------+-------------------------------------------+------------------------------+-------------------------------------+
| Child            | CV test score for          | Each parameter combination                | - Class name                 | --                                  |
|                  | each parameter combination |                                           | - Fully qualified class name |                                     |
+------------------+----------------------------+-------------------------------------------+------------------------------+-------------------------------------+

.. _GridSearchCV:
    https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GridSearchCV.html

.. note::
  This feature is experimental - the API and format of the logged data are subject to change.  

TensorFlow and Keras (experimental)
-----------------------------------
Call :py:func:`mlflow.tensorflow.autolog` or :py:func:`mlflow.keras.autolog` before your training code to enable automatic logging of metrics and parameters. See example usages with `Keras <https://github.com/mlflow/mlflow/tree/master/examples/keras>`_ and
`TensorFlow <https://github.com/mlflow/mlflow/tree/master/examples/tensorflow>`_.

Note that autologging for ``tf.keras`` is handled by :py:func:`mlflow.tensorflow.autolog`, not :py:func:`mlflow.keras.autolog`.
Whether you are using TensorFlow 1.x or 2.x, the respective metrics associated with ``tf.estimator`` and ``EarlyStopping`` are automatically logged.
As an example, try running the `MLflow TensorFlow examples <https://github.com/mlflow/mlflow/tree/master/examples/tensorflow>`_.

Autologging captures the following information:

+------------------------------------------+------------------------------------------------------------+-------------------------------------------------------------------------------------+---------------+-----------------------------------------------------------------------------------------------------------------------------------------------+
| Framework/module                         | Metrics                                                    | Parameters                                                                          | Tags          | Artifacts                                                                                                                                     |
+------------------------------------------+------------------------------------------------------------+-------------------------------------------------------------------------------------+---------------+-----------------------------------------------------------------------------------------------------------------------------------------------+
| ``keras``                                | Training loss; validation loss; user-specified metrics.    | ``fit()`` or ``fit_generator()`` parameters; optimizer name; learning rate; epsilon.| --            | Model summary on training start; `MLflow Model <https://mlflow.org/docs/latest/models.html>`_ (Keras model) on training end                   |
|                                          |                                                            |                                                                                     |               |                                                                                                                                               |
|                                          | Metrics from the ``EarlyStopping`` callbacks.              | Parameters associated with ``EarlyStopping``.                                       |               |                                                                                                                                               |
|                                          | For example, ``stopped_epoch``, ``restored_epoch``,        | For example, ``min_delta``, ``patience``, ``baseline``,                             |               |                                                                                                                                               |
|                                          | ``restore_best_weight``, etc.                              | ``restore_best_weights``, etc                                                       |               |                                                                                                                                               |
+------------------------------------------+------------------------------------------------------------+-------------------------------------------------------------------------------------+---------------+-----------------------------------------------------------------------------------------------------------------------------------------------+
| ``tf.keras``                             | Training loss; validation loss; user-specified metrics     | ``fit()`` or ``fit_generator()`` parameters; optimizer name; learning rate; epsilon | --            | Model summary on training start; `MLflow Model <https://mlflow.org/docs/latest/models.html>`_ (Keras model); TensorBoard logs on training end |
+------------------------------------------+------------------------------------------------------------+-------------------------------------------------------------------------------------+---------------+-----------------------------------------------------------------------------------------------------------------------------------------------+
| ``tf.keras.callbacks.EarlyStopping``     | Metrics from the ``EarlyStopping`` callbacks. For example, | ``fit()`` or ``fit_generator()`` parameters from ``EarlyStopping``.                 | --            | --                                                                                                                                            |
|                                          | ``stopped_epoch``, ``restored_epoch``,                     | For example, ``min_delta``, ``patience``, ``baseline``,                             |               |                                                                                                                                               |
|                                          | ``restore_best_weight``, etc                               | ``restore_best_weights``, etc                                                       |               |                                                                                                                                               |
+------------------------------------------+------------------------------------------------------------+-------------------------------------------------------------------------------------+---------------+-----------------------------------------------------------------------------------------------------------------------------------------------+
| ``tf.estimator``                         | TensorBoard metrics. For example, ``average_loss``,        | ``steps``, ``max_steps``                                                            | --            | `MLflow Model <https://mlflow.org/docs/latest/models.html>`_ (TF saved model) on call to ``tf.estimator.export_saved_model``                  |
|                                          | ``loss`` etc.                                              |                                                                                     |               |                                                                                                                                               |
+------------------------------------------+------------------------------------------------------------+-------------------------------------------------------------------------------------+---------------+-----------------------------------------------------------------------------------------------------------------------------------------------+
| TensorFlow Core                          | All ``tf.summary.scalar`` calls                            | --                                                                                  | --            | --                                                                                                                                            |
+------------------------------------------+------------------------------------------------------------+-------------------------------------------------------------------------------------+---------------+-----------------------------------------------------------------------------------------------------------------------------------------------+

If no active run exists when ``autolog()`` captures data, MLflow will automatically create a run to log information to.
Also, MLflow will then automatically end the run once training ends via calls to ``tf.estimator.train()``, ``tf.keras.fit()``, ``tf.keras.fit_generator()``, ``keras.fit()`` or ``keras.fit_generator()``,
or once ``tf.estimator`` models are exported via ``tf.estimator.export_saved_model()``.

If a run already exists when ``autolog()`` captures data, MLflow will log to that run but not automatically end that run after training.

.. note::
  - Parameters not explicitly passed by users (parameters that use default values) while using ``keras.Model.fit_generator()`` are not currently automatically logged.
  - This feature is experimental - the API and format of the logged data are subject to change.

Gluon (experimental)
--------------------
Call :py:func:`mlflow.gluon.autolog` before your training code to enable automatic logging of metrics and parameters.
See example usages with `Gluon <https://github.com/mlflow/mlflow/tree/master/examples/gluon>`_ .

Autologging captures the following information:

+------------------+--------------------------------------------------------+----------------------------------------------------------+---------------+-------------------------------------------------------------------------------------------------------------------------------+
| Framework        | Metrics                                                | Parameters                                               | Tags          | Artifacts                                                                                                                     |
+------------------+--------------------------------------------------------+----------------------------------------------------------+---------------+-------------------------------------------------------------------------------------------------------------------------------+
| Gluon            | Training loss; validation loss; user-specified metrics | Number of layers; optimizer name; learning rate; epsilon | --            | `MLflow Model <https://mlflow.org/docs/latest/models.html>`_ (Gluon model); on training end                                   |
+------------------+--------------------------------------------------------+----------------------------------------------------------+---------------+-------------------------------------------------------------------------------------------------------------------------------+

.. note::
  This feature is experimental - the API and format of the logged data are subject to change.

XGBoost (experimental)
----------------------
Call :py:func:`mlflow.xgboost.autolog` before your training code to enable automatic logging of metrics and parameters.

Autologging captures the following information:

+-----------+------------------------+-----------------------------+---------------+---------------------------------------------------------------------------------------------------------+
| Framework | Metrics                | Parameters                  | Tags          | Artifacts                                                                                               |
+-----------+------------------------+-----------------------------+---------------+---------------------------------------------------------------------------------------------------------+
| XGBoost   | user-specified metrics | `xgboost.train`_ parameters | --            | `MLflow Model`_ (XGBoost model) with model signature on training end; feature importance; input example |
+-----------+------------------------+-----------------------------+---------------+---------------------------------------------------------------------------------------------------------+

If early stopping is activated, metrics at the best iteration will be logged as an extra step/iteration.

.. note::
  - This feature is experimental - the API and format of the logged data are subject to change.
  - The `scikit-learn API <https://xgboost.readthedocs.io/en/latest/python/python_api.html#module-xgboost.sklearn>`__ is not supported.

.. _xgboost.train: https://xgboost.readthedocs.io/en/latest/python/python_api.html#xgboost.train
.. _MLflow Model: https://mlflow.org/docs/latest/models.html


LightGBM (experimental)
-----------------------
Call :py:func:`mlflow.lightgbm.autolog` before your training code to enable automatic logging of metrics and parameters.

Autologging captures the following information:

+-----------+------------------------+------------------------------+---------------+-----------------------------------------------------------------------------------------------------------+
| Framework | Metrics                | Parameters                   | Tags          | Artifacts                                                                                                 |
+-----------+------------------------+------------------------------+---------------+-----------------------------------------------------------------------------------------------------------+
| LightGBM  | user-specified metrics | `lightgbm.train`_ parameters | --            | `MLflow Model`_ (LightGBM model) with model signature on training end; feature importance; input example  |
+-----------+------------------------+------------------------------+---------------+-----------------------------------------------------------------------------------------------------------+

If early stopping is activated, metrics at the best iteration will be logged as an extra step/iteration.

.. note::
  - This feature is experimental - the API and format of the logged data are subject to change.
  - The `scikit-learn API <https://lightgbm.readthedocs.io/en/latest/Python-API.html#scikit-learn-api>`__ is not supported.

.. _lightgbm.train: https://lightgbm.readthedocs.io/en/latest/pythonapi/lightgbm.train.html#lightgbm-train

Statsmodels (experimental)
--------------------------
Call :py:func:`mlflow.statsmodels.autolog` before your training code to enable automatic logging of metrics and parameters.

Autologging captures the following information:

+--------------+------------------------+------------------------------------------------+---------------+-----------------------------------------------------------------------------+
| Framework    | Metrics                | Parameters                                     | Tags          | Artifacts                                                                   |
+--------------+------------------------+------------------------------------------------+---------------+-----------------------------------------------------------------------------+
| Statsmodels  | user-specified metrics | `statsmodels.base.model.Model.fit`_ parameters | --            | `MLflow Model`_ (`statsmodels.base.wrapper.ResultsWrapper`) on training end |
+--------------+------------------------+------------------------------------------------+---------------+-----------------------------------------------------------------------------+

.. note::
  - This feature is experimental - the API and format of the logged data are subject to change.
  - Each model subclass that overrides `fit` expects and logs its own parameters.

.. _statsmodels.base.model.Model.fit: https://www.statsmodels.org/dev/dev/generated/statsmodels.base.model.Model.html

Spark (experimental)
--------------------

Initialize a SparkSession with the mlflow-spark JAR attached (e.g.
``SparkSession.builder.config("spark.jars.packages", "org.mlflow.mlflow-spark")``) and then
call :py:func:`mlflow.spark.autolog` to enable automatic logging of Spark datasource
information at read-time, without the need for explicit
log statements. Note that autologging of Spark ML (MLlib) models is not yet supported.

Autologging captures the following information:

+------------------+---------+------------+----------------------------------------------------------------------------------------------+-----------+
| Framework        | Metrics | Parameters |  Tags                                                                                        | Artifacts |
+------------------+---------+------------+----------------------------------------------------------------------------------------------+-----------+
| Spark            | --      | --         | Single tag containing source path, version, format. The tag contains one line per datasource | --        |
+------------------+---------+------------+----------------------------------------------------------------------------------------------+-----------+

.. note::
  - This feature is experimental - the API and format of the logged data are subject to change.
  - Moreover, Spark datasource autologging occurs asynchronously - as such, it's possible (though unlikely) to see race conditions when launching short-lived MLflow runs that result in datasource information not being logged.

Fastai (experimental)
---------------------

Call :py:func:`mlflow.fastai.autolog` before your training code to enable automatic logging of metrics and parameters.
See an example usage with `Fastai <https://github.com/mlflow/mlflow/tree/master/examples/fastai>`_.

Autologging captures the following information:

.. _EarlyStoppingCallback: https://docs.fast.ai/callbacks.html#EarlyStoppingCallback
.. _OneCycleScheduler: https://docs.fast.ai/callbacks.html#OneCycleScheduler

+-----------+------------------------+----------------------------------------------------------+---------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Framework | Metrics                | Parameters                                               | Tags          | Artifacts                                                                                                                                                             |
+-----------+------------------------+----------------------------------------------------------+---------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| fastai    | user-specified metrics | Logs optimizer data as parameters. For example,          |  --           | Model checkpoints are logged to a ‘models’ directory; `MLflow Model`_ (fastai Learner model) on training end; Model summary text is logged                            |
|           |                        | ``epochs``, ``lr``, ``opt_func``, etc;                   |               |                                                                                                                                                                       |
|           |                        | Logs the parameters of the `EarlyStoppingCallback`_ and  |               |                                                                                                                                                                       |
|           |                        | `OneCycleScheduler`_ callbacks                           |               |                                                                                                                                                                       |
+-----------+------------------------+----------------------------------------------------------+---------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Pytorch (experimental)
--------------------------

Call :py:func:`mlflow.pytorch.autolog` before your Pytorch Lightning training code to enable automatic logging of metrics, parameters, and models. See example usages `here <https://github.com/chauhang/mlflow/tree/master/examples/pytorch/MNIST>`__. Note
that currently, Pytorch autologging supports only models trained using Pytorch Lightning. 

Autologging is triggered on calls to ``pytorch_lightning.trainer.Trainer.fit`` and captures the following information:

+------------------------------------------------+-------------------------------------------------------------+--------------------------------------------------------------------------------------+---------------+-----------------------------------------------------------------------------------------------------------------------------------------------+
| Framework/module                               | Metrics                                                     | Parameters                                                                           | Tags          | Artifacts                                                                                                                                     |
+------------------------------------------------+-------------------------------------------------------------+--------------------------------------------------------------------------------------+---------------+-----------------------------------------------------------------------------------------------------------------------------------------------+
| ``pytorch_lightning.trainer.Trainer``          | Training loss; validation loss; average_test_accuracy;      | ``fit()`` parameters; optimizer name; learning rate; epsilon.                        | --            | Model summary on training start, `MLflow Model <https://mlflow.org/docs/latest/models.html>`_ (Pytorch model) on training end;                |
|                                                | user-defined-metrics.                                       |                                                                                      |               |                                                                                                                                               |
|                                                |                                                             |                                                                                      |               |                                                                                                                                               |
|                                                |                                                             |                                                                                      |               |                                                                                                                                               |
|                                                |                                                             |                                                                                      |               |                                                                                                                                               |
+------------------------------------------------+-------------------------------------------------------------+--------------------------------------------------------------------------------------+---------------+-----------------------------------------------------------------------------------------------------------------------------------------------+
| ``pytorch_lightning.callbacks.earlystopping``  | Training loss; validation loss; average_test_accuracy;      | ``fit()`` parameters; optimizer name; learning rate; epsilon                         | --            | Model summary on training start; `MLflow Model <https://mlflow.org/docs/latest/models.html>`_ (Pytorch model) on training end;                |
|                                                | user-defined-metrics.                                       | Parameters from the ``EarlyStopping`` callbacks.                                     |               | Best Pytorch model checkpoint, if training stops due to early stopping callback.                                                              |
|                                                | Metrics from the ``EarlyStopping`` callbacks.               | For example, ``min_delta``, ``patience``, ``baseline``,``restore_best_weights``, etc |               |                                                                                                                                               |
|                                                | For example, ``stopped_epoch``, ``restored_epoch``,         |                                                                                      |               |                                                                                                                                               |
|                                                | ``restore_best_weight``, etc.                               |                                                                                      |               |                                                                                                                                               |
|                                                |                                                             |                                                                                      |               |                                                                                                                                               |
|                                                |                                                             |                                                                                      |               |                                                                                                                                               |
|                                                |                                                             |                                                                                      |               |                                                                                                                                               |
+------------------------------------------------+-------------------------------------------------------------+--------------------------------------------------------------------------------------+---------------+-----------------------------------------------------------------------------------------------------------------------------------------------+

If no active run exists when ``autolog()`` captures data, MLflow will automatically create a run to log information, ending the run once
the call to ``pytorch_lightning.trainer.Trainer.fit()`` completes.

If a run already exists when ``autolog()`` captures data, MLflow will log to that run but not automatically end that run after training.

.. note::
  - Parameters not explicitly passed by users (parameters that use default values) while using ``pytorch_lightning.trainer.Trainer.fit()`` are not currently automatically logged
  - In case of a multi-optimizer scenario (such as usage of autoencoder), only the parameters for the first optimizer are logged
  - This feature is experimental - the API and format of the logged data are subject to change


.. _organizing_runs_in_experiments:

Organizing Runs in Experiments
==============================

MLflow allows you to group runs under experiments, which can be useful for comparing runs intended
to tackle a particular task. You can create experiments using the :ref:`cli` (``mlflow experiments``) or
the :py:func:`mlflow.create_experiment` Python API. You can pass the experiment name for a individual run
using the CLI (for example, ``mlflow run ... --experiment-name [name]``) or the ``MLFLOW_EXPERIMENT_NAME``
environment variable. Alternatively, you can use the experiment ID instead, via the
``--experiment-id`` CLI flag or the ``MLFLOW_EXPERIMENT_ID`` environment variable.

.. code-block:: bash

    # Set the experiment via environment variables
    export MLFLOW_EXPERIMENT_NAME=fraud-detection

    mlflow experiments create --experiment-name fraud-detection

.. code-block:: py

    # Launch a run. The experiment is inferred from the MLFLOW_EXPERIMENT_NAME environment
    # variable, or from the --experiment-name parameter passed to the MLflow CLI (the latter
    # taking precedence)
    with mlflow.start_run():
        mlflow.log_param("a", 1)
        mlflow.log_metric("b", 2)

Managing Experiments and Runs with the Tracking Service API
-----------------------------------------------------------

MLflow provides a more detailed Tracking Service API for managing experiments and runs directly,
which is available through client SDK in the :py:mod:`mlflow.tracking` module.
This makes it possible to query data about past runs, log additional information about them, create experiments,
add tags to a run, and more.

.. rubric:: Example

.. code-block:: py

    from  mlflow.tracking import MlflowClient
    client = MlflowClient()
    experiments = client.list_experiments() # returns a list of mlflow.entities.Experiment
    run = client.create_run(experiments[0].experiment_id) # returns mlflow.entities.Run
    client.log_param(run.info.run_id, "hello", "world")
    client.set_terminated(run.info.run_id)

Adding Tags to Runs
~~~~~~~~~~~~~~~~~~~

The :py:func:`mlflow.tracking.MlflowClient.set_tag` function lets you add custom tags to runs. A tag can only have a single unique value mapped to it at a time. For example:

.. code-block:: py

  client.set_tag(run.info.run_id, "tag_key", "tag_value")

.. important:: Do not use the prefix ``mlflow`` for a tag.  This prefix is reserved for use by MLflow.

.. _tracking_ui:

Tracking UI
===========

The Tracking UI lets you visualize, search and compare runs, as well as download run artifacts or
metadata for analysis in other tools. If you log runs to a local ``mlruns`` directory,
run ``mlflow ui`` in the directory above it, and it loads the corresponding runs.
Alternatively, the :ref:`MLflow tracking server <tracking_server>` serves the same UI and enables remote storage of run artifacts.
In that case, you can view the UI using URL ``http://<ip address of your MLflow tracking server>:5000`` in your browser from any
machine, including any remote machine that can connect to your tracking server.

The UI contains the following key features:

* Experiment-based run listing and comparison
* Searching for runs by parameter or metric value
* Visualizing run metrics
* Downloading run results

.. _tracking_query_api:

Querying Runs Programmatically
==============================

You can access all of the functions in the Tracking UI programmatically. This makes it easy to do several common tasks:

* Query and compare runs using any data analysis tool of your choice, for example, **pandas**.
* Determine the artifact URI for a run to feed some of its artifacts into a new run when executing a workflow. For an example of querying runs and constructing a multistep workflow, see the MLflow `Multistep Workflow Example project <https://github.com/mlflow/mlflow/blob/15cc05ce2217b7c7af4133977b07542934a9a19f/examples/multistep_workflow/main.py#L63>`_.
* Load artifacts from past runs as :ref:`models`. For an example of training, exporting, and loading a model, and predicting using the model, see the MLflow `TensorFlow example <https://github.com/mlflow/mlflow/tree/master/examples/tensorflow>`_.
* Run automated parameter search algorithms, where you query the metrics from various runs to submit new ones. For an example of running automated parameter search algorithms, see the MLflow `Hyperparameter Tuning Example project <https://github.com/mlflow/mlflow/blob/master/examples/hyperparam/README.rst>`_.


.. _tracking_server:

MLflow Tracking Servers
=======================

.. contents:: In this section:
  :local:
  :depth: 2

You run an MLflow tracking server using ``mlflow server``.  An example configuration for a server is:

.. code-block:: bash

    mlflow server \
        --backend-store-uri /mnt/persistent-disk \
        --default-artifact-root s3://my-mlflow-bucket/ \
        --host 0.0.0.0

Storage
-------

An MLflow tracking server has two components for storage: a *backend store* and an *artifact store*.

Backend Stores
~~~~~~~~~~~~~~
The backend store is where MLflow Tracking Server stores experiment and run metadata as well as
params, metrics, and tags for runs. MLflow supports two types of backend stores: *file store* and
*database-backed store*.

.. note::
    In order to use model registry functionality, you must run your server using a database-backed store.


Use ``--backend-store-uri`` to configure the type of backend store. You specify:

- A file store backend as ``./path_to_store`` or ``file:/path_to_store``
- A database-backed store as `SQLAlchemy database URI <https://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls>`_.
  The database URI typically takes the format ``<dialect>+<driver>://<username>:<password>@<host>:<port>/<database>``.
  MLflow supports the database dialects ``mysql``, ``mssql``, ``sqlite``, and ``postgresql``.
  Drivers are optional. If you do not specify a driver, SQLAlchemy uses a dialect's default driver. For example, ``--backend-store-uri sqlite:///mlflow.db`` would use a local SQLite database.


.. important::

    ``mlflow server`` will fail against a database-backed store with an out-of-date database schema.
    To prevent this, upgrade your database schema to the latest supported version using
    ``mlflow db upgrade [db_uri]``. Schema migrations can result in database downtime, may
    take longer on larger databases, and are not guaranteed to be transactional. You should always
    take a backup of your database prior to running ``mlflow db upgrade`` - consult your database's
    documentation for instructions on taking a backup.


By default ``--backend-store-uri`` is set to the local ``./mlruns`` directory (the same as when
running ``mlflow run`` locally), but when running a server, make sure that this points to a
persistent (that is, non-ephemeral) file system location.

.. _artifact-stores:

Artifact Stores
~~~~~~~~~~~~~~~~

.. contents:: In this section:
  :local:
  :depth: 1

The artifact store is a location suitable for large data (such as an S3 bucket or shared NFS
file system) and is where clients log their artifact output (for example, models).
``artifact_location`` is a property recorded on :py:class:`mlflow.entities.Experiment` for
default location to store artifacts for all runs in this experiment. Additional, ``artifact_uri``
is a property on :py:class:`mlflow.entities.RunInfo` to indicate location where all artifacts for
this run are stored.

The MLflow client caches artifact location information on a per-run basis.
It is therefore not recommended to alter a run's artifact location before it has terminated.

In addition to local file paths, MLflow supports the following storage systems as artifact
stores: Amazon S3, Azure Blob Storage, Google Cloud Storage, SFTP server, and NFS.

Use ``--default-artifact-root`` (defaults to local ``./mlruns`` directory) to configure default
location to server's artifact store. This will be used as artifact location for newly-created
experiments that do not specify one. Once you create an experiment, ``--default-artifact-root``
is no longer relevant to that experiment.

To allow the server and clients to access the artifact location, you should configure your cloud
provider credentials as normal. For example, for S3, you can set the ``AWS_ACCESS_KEY_ID``
and ``AWS_SECRET_ACCESS_KEY`` environment variables, use an IAM role, or configure a default
profile in ``~/.aws/credentials``.
See `Set up AWS Credentials and Region for Development <https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/setup-credentials.html>`_ for more info.

.. important::

  If you do not specify a ``--default-artifact-root`` or an artifact URI when creating the experiment
  (for example, ``mlflow experiments create --artifact-location s3://<my-bucket>``), the artifact root
  is a path inside the file store. Typically this is not an appropriate location, as the client and
  server probably refer to different physical locations (that is, the same path on different disks).


Amazon S3 and S3-compatible storage
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To store artifacts in S3 (whether on Amazon S3 or on an S3-compatible alternative, such as 
`MinIO <https://min.io/>`_), specify a URI of the form ``s3://<bucket>/<path>``. MLflow obtains
credentials to access S3 from your machine's IAM role, a profile in ``~/.aws/credentials``, or
the environment variables ``AWS_ACCESS_KEY_ID`` and ``AWS_SECRET_ACCESS_KEY`` depending on which of
these are available. For more information on how to set credentials, see
`Set up AWS Credentials and Region for Development <https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/setup-credentials.html>`_.

To add S3 file upload extra arguments, set ``MLFLOW_S3_UPLOAD_EXTRA_ARGS`` to a JSON object of key/value pairs.
For example, if you want to upload to a KMS Encrypted bucket using the KMS Key 1234:

.. code-block:: bash

  export MLFLOW_S3_UPLOAD_EXTRA_ARGS='{"ServerSideEncryption": "aws:kms", "SSEKMSKeyId": "1234"}'

For a list of available extra args see `Boto3 ExtraArgs Documentation <https://github.com/boto/boto3/blob/develop/docs/source/guide/s3-uploading-files.rst#the-extraargs-parameter>`_.

To store artifacts in a custom endpoint, set the ``MLFLOW_S3_ENDPOINT_URL`` to your endpoint's URL.
For example, if you have a MinIO server at 1.2.3.4 on port 9000:

.. code-block:: bash

  export MLFLOW_S3_ENDPOINT_URL=http://1.2.3.4:9000

If the MinIO server is configured with using SSL self-signed or signed using some internal-only CA certificate, you could set ``MLFLOW_S3_IGNORE_TLS`` or ``AWS_CA_BUNDLE`` variables (not both at the same time!) to disable certificate signature check, or add a custom CA bundle to perform this check, respectively:

.. code-block:: bash

  export MLFLOW_S3_IGNORE_TLS=true
  #or
  export AWS_CA_BUNDLE=/some/ca/bundle.pem

Additionally, if MinIO server is configured with non-default region, you should set ``AWS_DEFAULT_REGION`` variable:

.. code-block:: bash

  export AWS_DEFAULT_REGION=my_region


Complete list of configurable values for an S3 client is available in `boto3 documentation <https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#configuration>`_.

Azure Blob Storage
^^^^^^^^^^^^^^^^^^

To store artifacts in Azure Blob Storage, specify a URI of the form
``wasbs://<container>@<storage-account>.blob.core.windows.net/<path>``.
MLflow expects Azure Storage access credentials in the
``AZURE_STORAGE_CONNECTION_STRING`` or ``AZURE_STORAGE_ACCESS_KEY`` environment variables (preferring
a connection string if one is set), so you must set one of these variables on both your client
application and your MLflow tracking server. Finally, you must run ``pip install azure-storage-blob``
separately (on both your client and the server) to access Azure Blob Storage; MLflow does not declare
a dependency on this package by default.

Google Cloud Storage
^^^^^^^^^^^^^^^^^^^^

To store artifacts in Google Cloud Storage, specify a URI of the form ``gs://<bucket>/<path>``.
You should configure credentials for accessing the GCS container on the client and server as described
in the `GCS documentation <https://google-cloud.readthedocs.io/en/latest/core/auth.html>`_.
Finally, you must run ``pip install google-cloud-storage`` (on both your client and the server)
to access Google Cloud Storage; MLflow does not declare a dependency on this package by default.

FTP server
^^^^^^^^^^^

To store artifacts in a FTP server, specify a URI of the form ftp://user@host/path/to/directory .
The URI may optionally include a password for logging into the server, e.g. ``ftp://user:pass@host/path/to/directory``

SFTP Server
^^^^^^^^^^^

To store artifacts in an SFTP server, specify a URI of the form ``sftp://user@host/path/to/directory``.
You should configure the client to be able to log in to the SFTP server without a password over SSH (e.g. public key, identity file in ssh_config, etc.).

The format ``sftp://user:pass@host/`` is supported for logging in. However, for safety reasons this is not recommended.

When using this store, ``pysftp`` must be installed on both the server and the client. Run ``pip install pysftp`` to install the required package.

NFS
^^^

To store artifacts in an NFS mount, specify a URI as a normal file system path, e.g., ``/mnt/nfs``.
This path must be the same on both the server and the client -- you may need to use symlinks or remount
the client in order to enforce this property.


HDFS
^^^^

To store artifacts in HDFS, specify a ``hdfs:`` URI. It can contain host and port: ``hdfs://<host>:<port>/<path>`` or just the path: ``hdfs://<path>``.

There are also two ways to authenticate to HDFS:

- Use current UNIX account authorization
- Kerberos credentials using following environment variables:

.. code-block:: bash

  export MLFLOW_KERBEROS_TICKET_CACHE=/tmp/krb5cc_22222222
  export MLFLOW_KERBEROS_USER=user_name_to_use

Most of the cluster contest settings are read from ``hdfs-site.xml`` accessed by the HDFS native
driver using the ``CLASSPATH`` environment variable.

The used HDFS driver is ``libhdfs``.


File store performance
~~~~~~~~~~~~~~~~~~~~~~

MLflow will automatically try to use `LibYAML <https://pyyaml.org/wiki/LibYAML>`_ bindings if they are already installed.
However if you notice any performance issues when using *file store* backend, it could mean LibYAML is not installed on your system.
On Linux or Mac you can easily install it using your system package manager:

.. code-block:: sh

    # On Ubuntu/Debian
    apt-get install libyaml-cpp-dev libyaml-dev

    # On macOS using Homebrew
    brew install yaml-cpp libyaml

After installing LibYAML, you need to reinstall PyYAML:

.. code-block:: sh

    # Reinstall PyYAML
    pip --no-cache-dir install --force-reinstall -I pyyaml


Deletion Behavior
~~~~~~~~~~~~~~~~~
In order to allow MLflow Runs to be restored, Run metadata and artifacts are not automatically removed
from the backend store or artifact store when a Run is deleted. The :ref:`mlflow gc <cli>` CLI is provided
for permanently removing Run metadata and artifacts for deleted runs.

SQLAlchemy Options
~~~~~~~~~~~~~~~~~~

You can inject some `SQLAlchemy connection pooling options <https://docs.sqlalchemy.org/en/latest/core/pooling.html>`_ using environment variables.

+-----------------------------------------+-----------------------------+
| MLflow Environment Variable             | SQLAlchemy QueuePool Option |
+-----------------------------------------+-----------------------------+
| ``MLFLOW_SQLALCHEMYSTORE_POOL_SIZE``    | ``pool_size``               |
+-----------------------------------------+-----------------------------+
| ``MLFLOW_SQLALCHEMYSTORE_MAX_OVERFLOW`` | ``max_overflow``            |
+-----------------------------------------+-----------------------------+

Networking
----------

The ``--host`` option exposes the service on all interfaces. If running a server in production, we
would recommend not exposing the built-in server broadly (as it is unauthenticated and unencrypted),
and instead putting it behind a reverse proxy like NGINX or Apache httpd, or connecting over VPN.
You can then pass authentication headers to MLflow using these :ref:`environment variables <tracking_auth>`.

Additionally, you should ensure that the ``--backend-store-uri`` (which defaults to the
``./mlruns`` directory) points to a persistent (non-ephemeral) disk or database connection.

.. _logging_to_a_tracking_server:

Logging to a Tracking Server
----------------------------

To log to a tracking server, set the ``MLFLOW_TRACKING_URI`` environment variable to the server's URI,
along with its scheme and port (for example, ``http://10.0.0.1:5000``) or call :py:func:`mlflow.set_tracking_uri`.

The :py:func:`mlflow.start_run`, :py:func:`mlflow.log_param`, and :py:func:`mlflow.log_metric` calls
then make API requests to your remote tracking server.

  .. code-section::

    .. code-block:: python

        import mlflow
        remote_server_uri = "..." # set to your server URI
        mlflow.set_tracking_uri(remote_server_uri)
        # Note: on Databricks, the experiment name passed to mlflow_set_experiment must be a
        # valid path in the workspace
        mlflow.set_experiment("/my-experiment")
        with mlflow.start_run():
            mlflow.log_param("a", 1)
            mlflow.log_metric("b", 2)

    .. code-block:: R

        library(mlflow)
        install_mlflow()
        remote_server_uri = "..." # set to your server URI
        mlflow_set_tracking_uri(remote_server_uri)
        # Note: on Databricks, the experiment name passed to mlflow_set_experiment must be a
        # valid path in the workspace
        mlflow_set_experiment("/my-experiment")
        mlflow_log_param("a", "1")


.. _tracking_auth:

In addition to the ``MLFLOW_TRACKING_URI`` environment variable, the following environment variables
allow passing HTTP authentication to the tracking server:

- ``MLFLOW_TRACKING_USERNAME`` and ``MLFLOW_TRACKING_PASSWORD`` - username and password to use with HTTP
  Basic authentication. To use Basic authentication, you must set `both` environment variables .
- ``MLFLOW_TRACKING_TOKEN`` - token to use with HTTP Bearer authentication. Basic authentication takes precedence if set.
- ``MLFLOW_TRACKING_INSECURE_TLS`` - If set to the literal ``true``, MLflow does not verify the TLS connection,
  meaning it does not validate certificates or hostnames for ``https://`` tracking URIs. This flag is not recommended for
  production environments. If this is set to ``true`` then ``MLFLOW_TRACKING_SERVER_CERT_PATH`` must not be set.
- ``MLFLOW_TRACKING_SERVER_CERT_PATH`` - Path to a CA bundle to use. Sets the ``verify`` param of the
  ``requests.request`` function
  (see `requests main interface <https://requests.readthedocs.io/en/master/api/>`_).
  When you use a self-signed server certificate you can use this to verify it on client side.
  If this is set ``MLFLOW_TRACKING_INSECURE_TLS`` must not be set (false).
- ``MLFLOW_TRACKING_CLIENT_CERT_PATH`` - Path to ssl client cert file (.pem). Sets the ``cert`` param
  of the ``requests.request`` function
  (see `requests main interface <https://requests.readthedocs.io/en/master/api/>`_).
  This can be used to use a (self-signed) client certificate.


.. note::
    The client directly pushes artifacts to the artifact store. It does not proxy these through the tracking server.

    For this reason, the client needs direct access to the artifact store. For instructions on setting up these credentials,
    see :ref:`Artifact Stores <artifact-stores>`.


.. _system_tags:

System Tags
===========

You can annotate runs with arbitrary tags. Tag keys that start with ``mlflow.`` are reserved for
internal use. The following tags are set automatically by MLflow, when appropriate:

+-------------------------------+----------------------------------------------------------------------------------------+
| Key                           | Description                                                                            |
+===============================+========================================================================================+
| ``mlflow.runName``            | Human readable name that identifies this run.                                          |
+-------------------------------+----------------------------------------------------------------------------------------+
| ``mlflow.note.content``       | A descriptive note about this run. This reserved tag is not set automatically and can  |
|                               | be overridden by the user to include additional information about the run. The content |
|                               | is displayed on the run's page under the Notes section.                                |
+-------------------------------+----------------------------------------------------------------------------------------+
| ``mlflow.parentRunId``        | The ID of the parent run, if this is a nested run.                                     |
+-------------------------------+----------------------------------------------------------------------------------------+
| ``mlflow.user``               | Identifier of the user who created the run.                                            |
+-------------------------------+----------------------------------------------------------------------------------------+
| ``mlflow.source.type``        | Source type. Possible values: ``"NOTEBOOK"``, ``"JOB"``, ``"PROJECT"``,                |
|                               | ``"LOCAL"``, and ``"UNKNOWN"``                                                         |
+-------------------------------+----------------------------------------------------------------------------------------+
| ``mlflow.source.name``        | Source identifier (e.g., GitHub URL, local Python filename, name of notebook)          |
+-------------------------------+----------------------------------------------------------------------------------------+
| ``mlflow.source.git.commit``  | Commit hash of the executed code, if in a git repository.                              |
+-------------------------------+----------------------------------------------------------------------------------------+
| ``mlflow.source.git.branch``  | Name of the branch of the executed code, if in a git repository.                       |
+-------------------------------+----------------------------------------------------------------------------------------+
| ``mlflow.source.git.repoURL`` | URL that the executed code was cloned from.                                            |
+-------------------------------+----------------------------------------------------------------------------------------+
| ``mlflow.project.env``        | The runtime context used by the MLflow project.                                        |
|                               | Possible values: ``"docker"`` and ``"conda"``.                                         |
+-------------------------------+----------------------------------------------------------------------------------------+
| ``mlflow.project.entryPoint`` | Name of the project entry point associated with the current run, if any.               |
+-------------------------------+----------------------------------------------------------------------------------------+
| ``mlflow.docker.image.name``  | Name of the Docker image used to execute this run.                                     |
+-------------------------------+----------------------------------------------------------------------------------------+
| ``mlflow.docker.image.id``    | ID of the Docker image used to execute this run.                                       |
+-------------------------------+----------------------------------------------------------------------------------------+
| ``mlflow.log-model.history``  | (Experimental) Model metadata collected by log-model calls. Includes the serialized    |
|                               | form of the MLModel model files logged to a run, although the exact format and         |
|                               | information captured is subject to change.                                             |
+-------------------------------+----------------------------------------------------------------------------------------+
