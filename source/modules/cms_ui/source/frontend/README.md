## CMS UI - Frontend

This project is the web interface (UI Application) that provides the front-end experience. The application is
based on [Reactjs](https://react.dev/) framework and uses components from the [AWS Cloudscape Design System](https://cloudscape.design/)

### Local Configuration Setup

To build and run the application locally, the setup requires

- [Nodejs 18.x](https://nodejs.org/en) or higher installed

Follow the below steps before building the web app for local execution

- The backend infrastructure stacks from `source/infrastructure` are deployed in your AWS account
- Create a file `source/ui-deployment/public/runtimeConfig.json` (if one does not exist) by executing

```bash
mkdir -p source/frontend/public
touch source/frontend/public/runtimeConfig.json
```

- From the AWS CloudFormation console, navigate to the `Outputs` tab
  of the main/ parent stack deployed and copy the `Value` of the `Key`
  named `WebConfigKey`.
- Navigate to AWS Systems Manager Parameter Store in the AWS web
  console, search for the `Key` in the previous step and copy the
  contents into the file created in the previous (step #2)
  steps (`source/frontend/public/runtimeConfig.json`)

For reference, the string in the Parameter Store should look something like the below:

```json
{
    "ApiEndpoint": "https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/",
    "UserPoolClientId": "xxxxxxxxx",
    "UserPoolId": "us-east-1_xxxxxxxxx",
    "IsInternalUser": "false",
    "AwsRegion": "us-east-1"
}
```

After completing the above steps, you can run the web application locally.

### Build and Run the App Locally

1. From the project root directory, change directory to `source/frontend`

```bash
    cd source/frontend
```

1. Install the library modules if building the project for the first time

```bash
    yarn install
```

1. Building the project with the below command will generate a `build` folder which contains
   the compiled components and minified JavaScript files.

```bash
    yarn run build
```

1. Executing the following command will run a local server on port 3000 <http://localhost:3000>

```bash
    yarn start
```

You should now be able to log in with the User Id and Password
for which you should have received an email during deployment.
You can also create additional users in the Amazon Cognito
User Pool from the AWS web console.
