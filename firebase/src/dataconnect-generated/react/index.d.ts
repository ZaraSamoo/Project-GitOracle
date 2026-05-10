import { ListAllProjectsData, CreateSnippetData, CreateSnippetVariables, GetMySnippetsData, AddReviewToSnippetData, AddReviewToSnippetVariables } from '../';
import { UseDataConnectQueryResult, useDataConnectQueryOptions, UseDataConnectMutationResult, useDataConnectMutationOptions} from '@tanstack-query-firebase/react/data-connect';
import { UseQueryResult, UseMutationResult} from '@tanstack/react-query';
import { DataConnect } from 'firebase/data-connect';
import { FirebaseError } from 'firebase/app';


export function useListAllProjects(options?: useDataConnectQueryOptions<ListAllProjectsData>): UseDataConnectQueryResult<ListAllProjectsData, undefined>;
export function useListAllProjects(dc: DataConnect, options?: useDataConnectQueryOptions<ListAllProjectsData>): UseDataConnectQueryResult<ListAllProjectsData, undefined>;

export function useCreateSnippet(options?: useDataConnectMutationOptions<CreateSnippetData, FirebaseError, CreateSnippetVariables>): UseDataConnectMutationResult<CreateSnippetData, CreateSnippetVariables>;
export function useCreateSnippet(dc: DataConnect, options?: useDataConnectMutationOptions<CreateSnippetData, FirebaseError, CreateSnippetVariables>): UseDataConnectMutationResult<CreateSnippetData, CreateSnippetVariables>;

export function useGetMySnippets(options?: useDataConnectQueryOptions<GetMySnippetsData>): UseDataConnectQueryResult<GetMySnippetsData, undefined>;
export function useGetMySnippets(dc: DataConnect, options?: useDataConnectQueryOptions<GetMySnippetsData>): UseDataConnectQueryResult<GetMySnippetsData, undefined>;

export function useAddReviewToSnippet(options?: useDataConnectMutationOptions<AddReviewToSnippetData, FirebaseError, AddReviewToSnippetVariables>): UseDataConnectMutationResult<AddReviewToSnippetData, AddReviewToSnippetVariables>;
export function useAddReviewToSnippet(dc: DataConnect, options?: useDataConnectMutationOptions<AddReviewToSnippetData, FirebaseError, AddReviewToSnippetVariables>): UseDataConnectMutationResult<AddReviewToSnippetData, AddReviewToSnippetVariables>;
