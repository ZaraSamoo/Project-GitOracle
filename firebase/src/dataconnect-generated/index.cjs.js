const { queryRef, executeQuery, validateArgsWithOptions, mutationRef, executeMutation, validateArgs, makeMemoryCacheProvider } = require('firebase/data-connect');

const connectorConfig = {
  connector: 'example',
  service: 'ui',
  location: 'asia-northeast1'
};
exports.connectorConfig = connectorConfig;
const dataConnectSettings = {
  cacheSettings: {
    cacheProvider: makeMemoryCacheProvider()
  }
};
exports.dataConnectSettings = dataConnectSettings;

const listAllProjectsRef = (dc) => {
  const { dc: dcInstance} = validateArgs(connectorConfig, dc, undefined);
  dcInstance._useGeneratedSdk();
  return queryRef(dcInstance, 'ListAllProjects');
}
listAllProjectsRef.operationName = 'ListAllProjects';
exports.listAllProjectsRef = listAllProjectsRef;

exports.listAllProjects = function listAllProjects(dcOrOptions, options) {
  
  const { dc: dcInstance, vars: inputVars, options: inputOpts } = validateArgsWithOptions(connectorConfig, dcOrOptions, options, undefined,false, false);
  return executeQuery(listAllProjectsRef(dcInstance, inputVars), inputOpts && inputOpts.fetchPolicy);
}
;

const createSnippetRef = (dcOrVars, vars) => {
  const { dc: dcInstance, vars: inputVars} = validateArgs(connectorConfig, dcOrVars, vars, true);
  dcInstance._useGeneratedSdk();
  return mutationRef(dcInstance, 'CreateSnippet', inputVars);
}
createSnippetRef.operationName = 'CreateSnippet';
exports.createSnippetRef = createSnippetRef;

exports.createSnippet = function createSnippet(dcOrVars, vars) {
  const { dc: dcInstance, vars: inputVars } = validateArgs(connectorConfig, dcOrVars, vars, true);
  return executeMutation(createSnippetRef(dcInstance, inputVars));
}
;

const getMySnippetsRef = (dc) => {
  const { dc: dcInstance} = validateArgs(connectorConfig, dc, undefined);
  dcInstance._useGeneratedSdk();
  return queryRef(dcInstance, 'GetMySnippets');
}
getMySnippetsRef.operationName = 'GetMySnippets';
exports.getMySnippetsRef = getMySnippetsRef;

exports.getMySnippets = function getMySnippets(dcOrOptions, options) {
  
  const { dc: dcInstance, vars: inputVars, options: inputOpts } = validateArgsWithOptions(connectorConfig, dcOrOptions, options, undefined,false, false);
  return executeQuery(getMySnippetsRef(dcInstance, inputVars), inputOpts && inputOpts.fetchPolicy);
}
;

const addReviewToSnippetRef = (dcOrVars, vars) => {
  const { dc: dcInstance, vars: inputVars} = validateArgs(connectorConfig, dcOrVars, vars, true);
  dcInstance._useGeneratedSdk();
  return mutationRef(dcInstance, 'AddReviewToSnippet', inputVars);
}
addReviewToSnippetRef.operationName = 'AddReviewToSnippet';
exports.addReviewToSnippetRef = addReviewToSnippetRef;

exports.addReviewToSnippet = function addReviewToSnippet(dcOrVars, vars) {
  const { dc: dcInstance, vars: inputVars } = validateArgs(connectorConfig, dcOrVars, vars, true);
  return executeMutation(addReviewToSnippetRef(dcInstance, inputVars));
}
;
