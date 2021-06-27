import { Experiment, RunInfo } from '../../sdk/MlflowMessages';

const createExperiment = ({
  experiment_id = '0',
  name = 'Default',
  artifact_location = 'dbfs:/databricks/mlflow/0',
  lifecycle_stage = 'active',
  tags = [],
} = {}) => Experiment.fromJs({ experiment_id, name, artifact_location, lifecycle_stage, tags });

const createRunInfo = () => {
  return RunInfo.fromJs({ run_uuid: 0 });
};

export default {
  createExperiment,
  createRunInfo,
  experiments: [createExperiment(), createExperiment({ experiment_id: '1', name: 'Test' })],
};
