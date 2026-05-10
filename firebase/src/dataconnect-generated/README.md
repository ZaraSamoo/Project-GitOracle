# Generated TypeScript README
This README will guide you through the process of using the generated JavaScript SDK package for the connector `example`. It will also provide examples on how to use your generated SDK to call your Data Connect queries and mutations.

**If you're looking for the `React README`, you can find it at [`dataconnect-generated/react/README.md`](./react/README.md)**

***NOTE:** This README is generated alongside the generated SDK. If you make changes to this file, they will be overwritten when the SDK is regenerated.*

# Table of Contents
- [**Overview**](#generated-javascript-readme)
- [**Accessing the connector**](#accessing-the-connector)
  - [*Connecting to the local Emulator*](#connecting-to-the-local-emulator)
- [**Queries**](#queries)
  - [*ListAllProjects*](#listallprojects)
  - [*GetMySnippets*](#getmysnippets)
- [**Mutations**](#mutations)
  - [*CreateSnippet*](#createsnippet)
  - [*AddReviewToSnippet*](#addreviewtosnippet)

# Accessing the connector
A connector is a collection of Queries and Mutations. One SDK is generated for each connector - this SDK is generated for the connector `example`. You can find more information about connectors in the [Data Connect documentation](https://firebase.google.com/docs/data-connect#how-does).

You can use this generated SDK by importing from the package `@dataconnect/generated` as shown below. Both CommonJS and ESM imports are supported.

You can also follow the instructions from the [Data Connect documentation](https://firebase.google.com/docs/data-connect/web-sdk#set-client).

```typescript
import { getDataConnect } from 'firebase/data-connect';
import { connectorConfig } from '@dataconnect/generated';

const dataConnect = getDataConnect(connectorConfig);
```

## Connecting to the local Emulator
By default, the connector will connect to the production service.

To connect to the emulator, you can use the following code.
You can also follow the emulator instructions from the [Data Connect documentation](https://firebase.google.com/docs/data-connect/web-sdk#instrument-clients).

```typescript
import { connectDataConnectEmulator, getDataConnect } from 'firebase/data-connect';
import { connectorConfig } from '@dataconnect/generated';

const dataConnect = getDataConnect(connectorConfig);
connectDataConnectEmulator(dataConnect, 'localhost', 9399);
```

After it's initialized, you can call your Data Connect [queries](#queries) and [mutations](#mutations) from your generated SDK.

# Queries

There are two ways to execute a Data Connect Query using the generated Web SDK:
- Using a Query Reference function, which returns a `QueryRef`
  - The `QueryRef` can be used as an argument to `executeQuery()`, which will execute the Query and return a `QueryPromise`
- Using an action shortcut function, which returns a `QueryPromise`
  - Calling the action shortcut function will execute the Query and return a `QueryPromise`

The following is true for both the action shortcut function and the `QueryRef` function:
- The `QueryPromise` returned will resolve to the result of the Query once it has finished executing
- If the Query accepts arguments, both the action shortcut function and the `QueryRef` function accept a single argument: an object that contains all the required variables (and the optional variables) for the Query
- Both functions can be called with or without passing in a `DataConnect` instance as an argument. If no `DataConnect` argument is passed in, then the generated SDK will call `getDataConnect(connectorConfig)` behind the scenes for you.

Below are examples of how to use the `example` connector's generated functions to execute each query. You can also follow the examples from the [Data Connect documentation](https://firebase.google.com/docs/data-connect/web-sdk#using-queries).

## ListAllProjects
You can execute the `ListAllProjects` query using the following action shortcut function, or by calling `executeQuery()` after calling the following `QueryRef` function, both of which are defined in [dataconnect-generated/index.d.ts](./index.d.ts):
```typescript
listAllProjects(options?: ExecuteQueryOptions): QueryPromise<ListAllProjectsData, undefined>;

interface ListAllProjectsRef {
  ...
  /* Allow users to create refs without passing in DataConnect */
  (): QueryRef<ListAllProjectsData, undefined>;
}
export const listAllProjectsRef: ListAllProjectsRef;
```
You can also pass in a `DataConnect` instance to the action shortcut function or `QueryRef` function.
```typescript
listAllProjects(dc: DataConnect, options?: ExecuteQueryOptions): QueryPromise<ListAllProjectsData, undefined>;

interface ListAllProjectsRef {
  ...
  (dc: DataConnect): QueryRef<ListAllProjectsData, undefined>;
}
export const listAllProjectsRef: ListAllProjectsRef;
```

If you need the name of the operation without creating a ref, you can retrieve the operation name by calling the `operationName` property on the listAllProjectsRef:
```typescript
const name = listAllProjectsRef.operationName;
console.log(name);
```

### Variables
The `ListAllProjects` query has no variables.
### Return Type
Recall that executing the `ListAllProjects` query returns a `QueryPromise` that resolves to an object with a `data` property.

The `data` property is an object of type `ListAllProjectsData`, which is defined in [dataconnect-generated/index.d.ts](./index.d.ts). It has the following fields:
```typescript
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
```
### Using `ListAllProjects`'s action shortcut function

```typescript
import { getDataConnect } from 'firebase/data-connect';
import { connectorConfig, listAllProjects } from '@dataconnect/generated';


// Call the `listAllProjects()` function to execute the query.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await listAllProjects();

// You can also pass in a `DataConnect` instance to the action shortcut function.
const dataConnect = getDataConnect(connectorConfig);
const { data } = await listAllProjects(dataConnect);

console.log(data.projects);

// Or, you can use the `Promise` API.
listAllProjects().then((response) => {
  const data = response.data;
  console.log(data.projects);
});
```

### Using `ListAllProjects`'s `QueryRef` function

```typescript
import { getDataConnect, executeQuery } from 'firebase/data-connect';
import { connectorConfig, listAllProjectsRef } from '@dataconnect/generated';


// Call the `listAllProjectsRef()` function to get a reference to the query.
const ref = listAllProjectsRef();

// You can also pass in a `DataConnect` instance to the `QueryRef` function.
const dataConnect = getDataConnect(connectorConfig);
const ref = listAllProjectsRef(dataConnect);

// Call `executeQuery()` on the reference to execute the query.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await executeQuery(ref);

console.log(data.projects);

// Or, you can use the `Promise` API.
executeQuery(ref).then((response) => {
  const data = response.data;
  console.log(data.projects);
});
```

## GetMySnippets
You can execute the `GetMySnippets` query using the following action shortcut function, or by calling `executeQuery()` after calling the following `QueryRef` function, both of which are defined in [dataconnect-generated/index.d.ts](./index.d.ts):
```typescript
getMySnippets(options?: ExecuteQueryOptions): QueryPromise<GetMySnippetsData, undefined>;

interface GetMySnippetsRef {
  ...
  /* Allow users to create refs without passing in DataConnect */
  (): QueryRef<GetMySnippetsData, undefined>;
}
export const getMySnippetsRef: GetMySnippetsRef;
```
You can also pass in a `DataConnect` instance to the action shortcut function or `QueryRef` function.
```typescript
getMySnippets(dc: DataConnect, options?: ExecuteQueryOptions): QueryPromise<GetMySnippetsData, undefined>;

interface GetMySnippetsRef {
  ...
  (dc: DataConnect): QueryRef<GetMySnippetsData, undefined>;
}
export const getMySnippetsRef: GetMySnippetsRef;
```

If you need the name of the operation without creating a ref, you can retrieve the operation name by calling the `operationName` property on the getMySnippetsRef:
```typescript
const name = getMySnippetsRef.operationName;
console.log(name);
```

### Variables
The `GetMySnippets` query has no variables.
### Return Type
Recall that executing the `GetMySnippets` query returns a `QueryPromise` that resolves to an object with a `data` property.

The `data` property is an object of type `GetMySnippetsData`, which is defined in [dataconnect-generated/index.d.ts](./index.d.ts). It has the following fields:
```typescript
export interface GetMySnippetsData {
  snippets: ({
    id: UUIDString;
    title: string;
    language: string;
    createdAt: TimestampString;
    updatedAt: TimestampString;
  } & Snippet_Key)[];
}
```
### Using `GetMySnippets`'s action shortcut function

```typescript
import { getDataConnect } from 'firebase/data-connect';
import { connectorConfig, getMySnippets } from '@dataconnect/generated';


// Call the `getMySnippets()` function to execute the query.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await getMySnippets();

// You can also pass in a `DataConnect` instance to the action shortcut function.
const dataConnect = getDataConnect(connectorConfig);
const { data } = await getMySnippets(dataConnect);

console.log(data.snippets);

// Or, you can use the `Promise` API.
getMySnippets().then((response) => {
  const data = response.data;
  console.log(data.snippets);
});
```

### Using `GetMySnippets`'s `QueryRef` function

```typescript
import { getDataConnect, executeQuery } from 'firebase/data-connect';
import { connectorConfig, getMySnippetsRef } from '@dataconnect/generated';


// Call the `getMySnippetsRef()` function to get a reference to the query.
const ref = getMySnippetsRef();

// You can also pass in a `DataConnect` instance to the `QueryRef` function.
const dataConnect = getDataConnect(connectorConfig);
const ref = getMySnippetsRef(dataConnect);

// Call `executeQuery()` on the reference to execute the query.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await executeQuery(ref);

console.log(data.snippets);

// Or, you can use the `Promise` API.
executeQuery(ref).then((response) => {
  const data = response.data;
  console.log(data.snippets);
});
```

# Mutations

There are two ways to execute a Data Connect Mutation using the generated Web SDK:
- Using a Mutation Reference function, which returns a `MutationRef`
  - The `MutationRef` can be used as an argument to `executeMutation()`, which will execute the Mutation and return a `MutationPromise`
- Using an action shortcut function, which returns a `MutationPromise`
  - Calling the action shortcut function will execute the Mutation and return a `MutationPromise`

The following is true for both the action shortcut function and the `MutationRef` function:
- The `MutationPromise` returned will resolve to the result of the Mutation once it has finished executing
- If the Mutation accepts arguments, both the action shortcut function and the `MutationRef` function accept a single argument: an object that contains all the required variables (and the optional variables) for the Mutation
- Both functions can be called with or without passing in a `DataConnect` instance as an argument. If no `DataConnect` argument is passed in, then the generated SDK will call `getDataConnect(connectorConfig)` behind the scenes for you.

Below are examples of how to use the `example` connector's generated functions to execute each mutation. You can also follow the examples from the [Data Connect documentation](https://firebase.google.com/docs/data-connect/web-sdk#using-mutations).

## CreateSnippet
You can execute the `CreateSnippet` mutation using the following action shortcut function, or by calling `executeMutation()` after calling the following `MutationRef` function, both of which are defined in [dataconnect-generated/index.d.ts](./index.d.ts):
```typescript
createSnippet(vars: CreateSnippetVariables): MutationPromise<CreateSnippetData, CreateSnippetVariables>;

interface CreateSnippetRef {
  ...
  /* Allow users to create refs without passing in DataConnect */
  (vars: CreateSnippetVariables): MutationRef<CreateSnippetData, CreateSnippetVariables>;
}
export const createSnippetRef: CreateSnippetRef;
```
You can also pass in a `DataConnect` instance to the action shortcut function or `MutationRef` function.
```typescript
createSnippet(dc: DataConnect, vars: CreateSnippetVariables): MutationPromise<CreateSnippetData, CreateSnippetVariables>;

interface CreateSnippetRef {
  ...
  (dc: DataConnect, vars: CreateSnippetVariables): MutationRef<CreateSnippetData, CreateSnippetVariables>;
}
export const createSnippetRef: CreateSnippetRef;
```

If you need the name of the operation without creating a ref, you can retrieve the operation name by calling the `operationName` property on the createSnippetRef:
```typescript
const name = createSnippetRef.operationName;
console.log(name);
```

### Variables
The `CreateSnippet` mutation requires an argument of type `CreateSnippetVariables`, which is defined in [dataconnect-generated/index.d.ts](./index.d.ts). It has the following fields:

```typescript
export interface CreateSnippetVariables {
  title: string;
  codeContent: string;
  language: string;
  description?: string | null;
  tags?: string[] | null;
}
```
### Return Type
Recall that executing the `CreateSnippet` mutation returns a `MutationPromise` that resolves to an object with a `data` property.

The `data` property is an object of type `CreateSnippetData`, which is defined in [dataconnect-generated/index.d.ts](./index.d.ts). It has the following fields:
```typescript
export interface CreateSnippetData {
  snippet_insert: Snippet_Key;
}
```
### Using `CreateSnippet`'s action shortcut function

```typescript
import { getDataConnect } from 'firebase/data-connect';
import { connectorConfig, createSnippet, CreateSnippetVariables } from '@dataconnect/generated';

// The `CreateSnippet` mutation requires an argument of type `CreateSnippetVariables`:
const createSnippetVars: CreateSnippetVariables = {
  title: ..., 
  codeContent: ..., 
  language: ..., 
  description: ..., // optional
  tags: ..., // optional
};

// Call the `createSnippet()` function to execute the mutation.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await createSnippet(createSnippetVars);
// Variables can be defined inline as well.
const { data } = await createSnippet({ title: ..., codeContent: ..., language: ..., description: ..., tags: ..., });

// You can also pass in a `DataConnect` instance to the action shortcut function.
const dataConnect = getDataConnect(connectorConfig);
const { data } = await createSnippet(dataConnect, createSnippetVars);

console.log(data.snippet_insert);

// Or, you can use the `Promise` API.
createSnippet(createSnippetVars).then((response) => {
  const data = response.data;
  console.log(data.snippet_insert);
});
```

### Using `CreateSnippet`'s `MutationRef` function

```typescript
import { getDataConnect, executeMutation } from 'firebase/data-connect';
import { connectorConfig, createSnippetRef, CreateSnippetVariables } from '@dataconnect/generated';

// The `CreateSnippet` mutation requires an argument of type `CreateSnippetVariables`:
const createSnippetVars: CreateSnippetVariables = {
  title: ..., 
  codeContent: ..., 
  language: ..., 
  description: ..., // optional
  tags: ..., // optional
};

// Call the `createSnippetRef()` function to get a reference to the mutation.
const ref = createSnippetRef(createSnippetVars);
// Variables can be defined inline as well.
const ref = createSnippetRef({ title: ..., codeContent: ..., language: ..., description: ..., tags: ..., });

// You can also pass in a `DataConnect` instance to the `MutationRef` function.
const dataConnect = getDataConnect(connectorConfig);
const ref = createSnippetRef(dataConnect, createSnippetVars);

// Call `executeMutation()` on the reference to execute the mutation.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await executeMutation(ref);

console.log(data.snippet_insert);

// Or, you can use the `Promise` API.
executeMutation(ref).then((response) => {
  const data = response.data;
  console.log(data.snippet_insert);
});
```

## AddReviewToSnippet
You can execute the `AddReviewToSnippet` mutation using the following action shortcut function, or by calling `executeMutation()` after calling the following `MutationRef` function, both of which are defined in [dataconnect-generated/index.d.ts](./index.d.ts):
```typescript
addReviewToSnippet(vars: AddReviewToSnippetVariables): MutationPromise<AddReviewToSnippetData, AddReviewToSnippetVariables>;

interface AddReviewToSnippetRef {
  ...
  /* Allow users to create refs without passing in DataConnect */
  (vars: AddReviewToSnippetVariables): MutationRef<AddReviewToSnippetData, AddReviewToSnippetVariables>;
}
export const addReviewToSnippetRef: AddReviewToSnippetRef;
```
You can also pass in a `DataConnect` instance to the action shortcut function or `MutationRef` function.
```typescript
addReviewToSnippet(dc: DataConnect, vars: AddReviewToSnippetVariables): MutationPromise<AddReviewToSnippetData, AddReviewToSnippetVariables>;

interface AddReviewToSnippetRef {
  ...
  (dc: DataConnect, vars: AddReviewToSnippetVariables): MutationRef<AddReviewToSnippetData, AddReviewToSnippetVariables>;
}
export const addReviewToSnippetRef: AddReviewToSnippetRef;
```

If you need the name of the operation without creating a ref, you can retrieve the operation name by calling the `operationName` property on the addReviewToSnippetRef:
```typescript
const name = addReviewToSnippetRef.operationName;
console.log(name);
```

### Variables
The `AddReviewToSnippet` mutation requires an argument of type `AddReviewToSnippetVariables`, which is defined in [dataconnect-generated/index.d.ts](./index.d.ts). It has the following fields:

```typescript
export interface AddReviewToSnippetVariables {
  snippetId: UUIDString;
  rating: number;
  comment?: string | null;
}
```
### Return Type
Recall that executing the `AddReviewToSnippet` mutation returns a `MutationPromise` that resolves to an object with a `data` property.

The `data` property is an object of type `AddReviewToSnippetData`, which is defined in [dataconnect-generated/index.d.ts](./index.d.ts). It has the following fields:
```typescript
export interface AddReviewToSnippetData {
  review_insert: Review_Key;
}
```
### Using `AddReviewToSnippet`'s action shortcut function

```typescript
import { getDataConnect } from 'firebase/data-connect';
import { connectorConfig, addReviewToSnippet, AddReviewToSnippetVariables } from '@dataconnect/generated';

// The `AddReviewToSnippet` mutation requires an argument of type `AddReviewToSnippetVariables`:
const addReviewToSnippetVars: AddReviewToSnippetVariables = {
  snippetId: ..., 
  rating: ..., 
  comment: ..., // optional
};

// Call the `addReviewToSnippet()` function to execute the mutation.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await addReviewToSnippet(addReviewToSnippetVars);
// Variables can be defined inline as well.
const { data } = await addReviewToSnippet({ snippetId: ..., rating: ..., comment: ..., });

// You can also pass in a `DataConnect` instance to the action shortcut function.
const dataConnect = getDataConnect(connectorConfig);
const { data } = await addReviewToSnippet(dataConnect, addReviewToSnippetVars);

console.log(data.review_insert);

// Or, you can use the `Promise` API.
addReviewToSnippet(addReviewToSnippetVars).then((response) => {
  const data = response.data;
  console.log(data.review_insert);
});
```

### Using `AddReviewToSnippet`'s `MutationRef` function

```typescript
import { getDataConnect, executeMutation } from 'firebase/data-connect';
import { connectorConfig, addReviewToSnippetRef, AddReviewToSnippetVariables } from '@dataconnect/generated';

// The `AddReviewToSnippet` mutation requires an argument of type `AddReviewToSnippetVariables`:
const addReviewToSnippetVars: AddReviewToSnippetVariables = {
  snippetId: ..., 
  rating: ..., 
  comment: ..., // optional
};

// Call the `addReviewToSnippetRef()` function to get a reference to the mutation.
const ref = addReviewToSnippetRef(addReviewToSnippetVars);
// Variables can be defined inline as well.
const ref = addReviewToSnippetRef({ snippetId: ..., rating: ..., comment: ..., });

// You can also pass in a `DataConnect` instance to the `MutationRef` function.
const dataConnect = getDataConnect(connectorConfig);
const ref = addReviewToSnippetRef(dataConnect, addReviewToSnippetVars);

// Call `executeMutation()` on the reference to execute the mutation.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await executeMutation(ref);

console.log(data.review_insert);

// Or, you can use the `Promise` API.
executeMutation(ref).then((response) => {
  const data = response.data;
  console.log(data.review_insert);
});
```

