# Lambda Handlers

See [API Handlers](./api/README.md) and [Simulate Handler](./simulate/README.md) for more details on the API handlers.

## CDK Custom Resources

The following is the list of custom resources created for this project and are used in
[infrastructure](../infrastructure/README.md) as a part of the Cloudformation deployment.

### Create UUID

Generate a unique UUID for use in deployment IDs.

### Copy S3 Assets

Read the manifest file and copy the necessary resources.

### Create Console Config

Generate the typescript config for use in the frontend on load. The config is saved in S3.

### Fetch IoT Endpoint URL

Dynamically fetch the IoT endpoint URL.

### Detach IoT Policies

When attempting to delete the cloudformation stack, it is not able to detach the IoT policies. This resource is
designed to detach those policies so the stack is able to be deleted.

### Create Admin User

During the deployment, this creates the user who is able to login into the frontend.
