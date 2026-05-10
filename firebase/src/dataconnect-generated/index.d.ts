import { ConnectorConfig, DataConnect, QueryRef, QueryPromise, ExecuteQueryOptions, MutationRef, MutationPromise, DataConnectSettings } from 'firebase/data-connect';

export const connectorConfig: ConnectorConfig;
export const dataConnectSettings: DataConnectSettings;

export type TimestampString = string;
export type UUIDString = string;
export type Int64String = string;
export type DateString = string;




export interface AddReviewToSnippetData {
  review_insert: Review_Key;
}

export interface AddReviewToSnippetVariables {
  snippetId: UUIDString;
  rating: number;
  comment?: string | null;
}

export interface CreateSnippetData {
  snippet_insert: Snippet_Key;
}

export interface CreateSnippetVariables {
  title: string;
  codeContent: string;
  language: string;
  description?: string | null;
  tags?: string[] | null;
}

export interface GetMySnippetsData {
  snippets: ({
    id: UUIDString;
    title: string;
    language: string;
    createdAt: TimestampString;
    updatedAt: TimestampString;
  } & Snippet_Key)[];
}

export interface ListAllProjectsData {
  projects: ({
    id: UUIDString;
    name: string;
    description?: string | null;
    createdAt: TimestampString;
    owner?: {
      id: UUIDString;
      username: string;
      displayName?: string | null;
    } & User_Key;
  } & Project_Key)[];
}

export interface ProjectSnippet_Key {
  projectId: UUIDString;
  snippetId: UUIDString;
  __typename?: 'ProjectSnippet_Key';
}

export interface Project_Key {
  id: UUIDString;
  __typename?: 'Project_Key';
}

export interface Review_Key {
  id: UUIDString;
  __typename?: 'Review_Key';
}

export interface Snippet_Key {
  id: UUIDString;
  __typename?: 'Snippet_Key';
}

export interface User_Key {
  id: UUIDString;
  __typename?: 'User_Key';
}

interface ListAllProjectsRef {
  /* Allow users to create refs without passing in DataConnect */
  (): QueryRef<ListAllProjectsData, undefined>;
  /* Allow users to pass in custom DataConnect instances */
  (dc: DataConnect): QueryRef<ListAllProjectsData, undefined>;
  operationName: string;
}
export const listAllProjectsRef: ListAllProjectsRef;

export function listAllProjects(options?: ExecuteQueryOptions): QueryPromise<ListAllProjectsData, undefined>;
export function listAllProjects(dc: DataConnect, options?: ExecuteQueryOptions): QueryPromise<ListAllProjectsData, undefined>;

interface CreateSnippetRef {
  /* Allow users to create refs without passing in DataConnect */
  (vars: CreateSnippetVariables): MutationRef<CreateSnippetData, CreateSnippetVariables>;
  /* Allow users to pass in custom DataConnect instances */
  (dc: DataConnect, vars: CreateSnippetVariables): MutationRef<CreateSnippetData, CreateSnippetVariables>;
  operationName: string;
}
export const createSnippetRef: CreateSnippetRef;

export function createSnippet(vars: CreateSnippetVariables): MutationPromise<CreateSnippetData, CreateSnippetVariables>;
export function createSnippet(dc: DataConnect, vars: CreateSnippetVariables): MutationPromise<CreateSnippetData, CreateSnippetVariables>;

interface GetMySnippetsRef {
  /* Allow users to create refs without passing in DataConnect */
  (): QueryRef<GetMySnippetsData, undefined>;
  /* Allow users to pass in custom DataConnect instances */
  (dc: DataConnect): QueryRef<GetMySnippetsData, undefined>;
  operationName: string;
}
export const getMySnippetsRef: GetMySnippetsRef;

export function getMySnippets(options?: ExecuteQueryOptions): QueryPromise<GetMySnippetsData, undefined>;
export function getMySnippets(dc: DataConnect, options?: ExecuteQueryOptions): QueryPromise<GetMySnippetsData, undefined>;

interface AddReviewToSnippetRef {
  /* Allow users to create refs without passing in DataConnect */
  (vars: AddReviewToSnippetVariables): MutationRef<AddReviewToSnippetData, AddReviewToSnippetVariables>;
  /* Allow users to pass in custom DataConnect instances */
  (dc: DataConnect, vars: AddReviewToSnippetVariables): MutationRef<AddReviewToSnippetData, AddReviewToSnippetVariables>;
  operationName: string;
}
export const addReviewToSnippetRef: AddReviewToSnippetRef;

export function addReviewToSnippet(vars: AddReviewToSnippetVariables): MutationPromise<AddReviewToSnippetData, AddReviewToSnippetVariables>;
export function addReviewToSnippet(dc: DataConnect, vars: AddReviewToSnippetVariables): MutationPromise<AddReviewToSnippetData, AddReviewToSnippetVariables>;

