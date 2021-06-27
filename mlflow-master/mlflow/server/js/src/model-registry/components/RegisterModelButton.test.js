import React from 'react';
import { mountWithIntl, shallowWithInjectIntl, mockAjax } from '../../common/utils/TestUtils';
import configureStore from 'redux-mock-store';
import promiseMiddleware from 'redux-promise-middleware';
import thunk from 'redux-thunk';
import { RegisterModelButtonWithIntl } from './RegisterModelButton';
import { getProtoField } from '../utils';

describe('RegisterModelButton', () => {
  let wrapper;
  let minimalProps;
  let minimalStore;
  const mockStore = configureStore([thunk, promiseMiddleware()]);

  beforeEach(() => {
    mockAjax();
    minimalProps = {
      disabled: false,
      runUuid: 'runUuid',
      modelPath: 'modelPath',
      // connected props
      modelByName: {},
      createRegisteredModelApi: jest.fn(() => Promise.resolve({})),
      createModelVersionApi: jest.fn(() => Promise.resolve({})),
      listRegisteredModelsApi: jest.fn(() => Promise.resolve({})),
      searchModelVersionsApi: jest.fn(() => Promise.resolve({})),
      searchRegisteredModelsApi: jest.fn(() => Promise.resolve({})),
    };
    minimalStore = mockStore({
      entities: {
        modelByName: {},
      },
    });
  });

  test('should render with minimal props and store without exploding', () => {
    wrapper = mountWithIntl(<RegisterModelButtonWithIntl {...minimalProps} store={minimalStore} />);
    expect(wrapper.find('button').length).toBe(1);
  });

  test('handleSearchRegisteredModel should invoke api', () => {
    const response = { value: {} };
    response.value[getProtoField('registered_models')] = [
      {
        name: 'Model A',
      },
    ];

    const searchRegisteredModelsApi = jest.fn(() => Promise.resolve(response));
    const props = {
      ...minimalProps,
      searchRegisteredModelsApi,
    };
    wrapper = shallowWithInjectIntl(
      <RegisterModelButtonWithIntl {...props} store={minimalStore} />,
    );
    const instance = wrapper.instance();
    instance.handleSearchRegisteredModels('A');
    expect(props.searchRegisteredModelsApi.mock.calls.length).toBe(1);
  });
});
