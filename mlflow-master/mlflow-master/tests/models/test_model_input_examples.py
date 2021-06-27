import json
import math
import numpy as np
import pandas as pd
import pytest

from mlflow.models.signature import infer_signature
from mlflow.models.utils import _Example, _read_tensor_input_from_json
from mlflow.types.utils import TensorsNotSupportedException
from mlflow.utils.file_utils import TempDir
from mlflow.utils.proto_json_utils import _dataframe_from_json


@pytest.fixture
def pandas_df_with_all_types():
    df = pd.DataFrame(
        {
            "boolean": [True, False, True],
            "integer": np.array([1, 2, 3], np.int32),
            "long": np.array([1, 2, 3], np.int64),
            "float": np.array([math.pi, 2 * math.pi, 3 * math.pi], np.float32),
            "double": [math.pi, 2 * math.pi, 3 * math.pi],
            "binary": [bytes([1, 2, 3]), bytes([4, 5, 6]), bytes([7, 8, 9])],
            "string": ["a", "b", "c"],
            "boolean_ext": [True, False, True],
            "integer_ext": [1, 2, 3],
            "string_ext": ["a", "b", "c"],
        }
    )
    df["boolean_ext"] = df["boolean_ext"].astype("boolean")
    df["integer_ext"] = df["integer_ext"].astype("Int64")
    df["string_ext"] = df["string_ext"].astype("string")
    return df


@pytest.fixture
def dict_of_ndarrays():
    return {
        "1D": np.arange(0, 12, 0.5),
        "2D": np.arange(0, 12, 0.5).reshape(3, 8),
        "3D": np.arange(0, 12, 0.5).reshape(2, 3, 4),
        "4D": np.arange(0, 12, 0.5).reshape(3, 2, 2, 2),
    }


def test_input_examples(pandas_df_with_all_types, dict_of_ndarrays):
    sig = infer_signature(pandas_df_with_all_types)
    # test setting example with data frame with all supported data types
    with TempDir() as tmp:
        example = _Example(pandas_df_with_all_types)
        example.save(tmp.path())
        filename = example.info["artifact_path"]
        with open(tmp.path(filename), "r") as f:
            data = json.load(f)
            assert set(data.keys()) == set(("columns", "data"))
        parsed_df = _dataframe_from_json(tmp.path(filename), schema=sig.inputs)
        assert (pandas_df_with_all_types == parsed_df).all().all()
        # the frame read without schema should match except for the binary values
        assert (
            (
                parsed_df.drop(columns=["binary"])
                == _dataframe_from_json(tmp.path(filename)).drop(columns=["binary"])
            )
            .all()
            .all()
        )

    # NB: Drop columns that cannot be encoded by proto_json_utils.pyNumpyEncoder
    new_df = pandas_df_with_all_types.drop(columns=["boolean_ext", "integer_ext", "string_ext"])

    # pass the input as dictionary instead
    with TempDir() as tmp:
        d = {name: new_df[name].values for name in new_df.columns}
        example = _Example(d)
        example.save(tmp.path())
        filename = example.info["artifact_path"]
        parsed_dict = _read_tensor_input_from_json(tmp.path(filename))
        assert d.keys() == parsed_dict.keys()
        # Asserting binary will fail since it is converted to base64 encoded strings.
        # The check above suffices that the binary input is stored.
        del d["binary"]
        for key in d:
            assert np.array_equal(d[key], parsed_dict[key])

    # input passed as numpy array
    new_df = pandas_df_with_all_types.drop(columns=["binary"])
    for col in new_df:
        input_example = new_df[col].to_numpy()
        with TempDir() as tmp:
            example = _Example(input_example)
            example.save(tmp.path())
            filename = example.info["artifact_path"]
            parsed_ary = _read_tensor_input_from_json(tmp.path(filename))
            assert np.array_equal(parsed_ary, input_example)

    # pass multidimensional array
    for col in dict_of_ndarrays:
        input_example = dict_of_ndarrays[col]
        with TempDir() as tmp:
            example = _Example(input_example)
            example.save(tmp.path())
            filename = example.info["artifact_path"]
            parsed_ary = _read_tensor_input_from_json(tmp.path(filename))
            assert np.array_equal(parsed_ary, input_example)

    # pass multidimensional array as a list
    example = np.array([[1, 2, 3]])
    with pytest.raises(TensorsNotSupportedException):
        _Example([example, example])

    # pass dict with scalars
    with TempDir() as tmp:
        example = {"a": 1, "b": "abc"}
        x = _Example(example)
        x.save(tmp.path())
        filename = x.info["artifact_path"]
        parsed_df = _dataframe_from_json(tmp.path(filename))
        assert example == parsed_df.to_dict(orient="records")[0]
