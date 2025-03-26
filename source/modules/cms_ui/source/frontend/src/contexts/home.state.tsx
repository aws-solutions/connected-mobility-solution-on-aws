// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

export interface HomeInitialState {
  selectedDeployment: any;
  deploymentsData: any;
  runtimeConfig?: any;
  reloadData?: boolean;
  numUseCases: number;
  currentPageIndex: number;
  searchFilter: string;
  submittedSearchFilter: string;
}

export const initialState: HomeInitialState = {
  selectedDeployment: {},
  deploymentsData: [],
  reloadData: false,
  numUseCases: 0,
  currentPageIndex: 1,
  searchFilter: "",
  submittedSearchFilter: "",
};

export const insertRuntimeConfig = (
  state: Partial<HomeInitialState>,
  runtimeConfig: any,
) => {
  return {
    ...state,
    runtimeConfig,
  };
};
