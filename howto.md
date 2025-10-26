# How to Build the AI Lotto Predictor

This document provides a step-by-step guide to building and deploying the AI Lotto Predictor, based on the provided developer documentation.

## Phase 1: Backend Setup (AWS Infrastructure)

This phase focuses on setting up the necessary AWS resources.

### Step 1.1: Set up AWS S3 Bucket
- Create an S3 bucket to store the historical lotto data.
- **Bucket Name**: `ai-lotto-predictor-data`

### Step 1.2: Set up AWS DynamoDB Table
- Create a DynamoDB table to store the predictions.
- **Table Name**: `LottoPredictions`
- **Primary Key**: `GameName` (String)
- **Sort Key**: `PredictionDate` (String)

### Step 1.3: Set up IAM Roles
- Create an IAM role for the Data Scraper Lambda function with `s3:PutObject` permissions for the `ai-lotto-predictor-data` bucket.
- Create an IAM role for the Prediction Engine Lambda function with `s3:GetObject`, `dynamodb:PutItem`, and `bedrock:InvokeModel` permissions.

### Step 1.4: Set up API Gateway
- Create a REST API in API Gateway.
- Create a `/predict` resource with a `GET` method. This will be integrated with the Prediction Engine Lambda in a later step.

## Phase 2: Backend Development (Lambda Functions)

This phase focuses on creating and deploying the AWS Lambda functions.

### Step 2.1: Create the Data Scraper Lambda Function
- Create a new Lambda function in the AWS console.
- **Runtime**: Python 3.x
- **Function Name**: `ai-lotto-predictor-scraper`
- Use the IAM role created in Step 1.3.
- Use the Python code for the data scraper from the documentation.
- **Note**: You will need to create a deployment package with the required libraries (`BeautifulSoup`, `requests`).
- Set up a CloudWatch Event to trigger this Lambda function on a schedule (e.g., daily).

### Step 2.2: Create the Prediction Engine Lambda Function
- Create a new Lambda function.
- **Runtime**: Python 3.x
- **Function Name**: `ai-lotto-predictor-predictor`
- Use the IAM role created in Step 1.3.
- Use the Python code for the prediction engine from the documentation.
- **IMPORTANT**: The prediction engine uses Amazon Bedrock to interact with the Claude 3 Sonnet model. Ensure the IAM role for the `ai-lotto-predictor-predictor` Lambda function has the necessary `bedrock:InvokeModel` permissions for the `anthropic.claude-3-sonnet-20240229-v1:0` model.
- Connect this Lambda function to the API Gateway endpoint created in Step 1.4.

## Phase 3: Frontend Setup (React Native Project)

This phase focuses on setting up the React Native project.

### Step 3.1: Set up your Development Environment
- Ensure you have Node.js, npm, and the React Native CLI installed.
- Install the AWS Amplify CLI: `npm install -g @aws-amplify/cli`

### Step 3.2: Create a new React Native Project
- Create a new React Native project: `npx react-native init AILottoPredictorApp`
- `cd AILottoPredictorApp`

### Step 3.3: Initialize Amplify
- Configure the Amplify CLI with your AWS account: `amplify configure`
- Initialize Amplify in your project: `amplify init`

### Step 3.4: Add API and Auth
- Add the API category: `amplify add api` (Choose `REST` and connect to your API Gateway)
- Add authentication: `amplify add auth`
- Push the changes: `amplify push`

### Step 3.5: Install Dependencies
- `npm install @react-native-picker/picker aws-amplify axios react-native-paper`

## Phase 4: Frontend Development (UI and Logic)

This phase focuses on building the user interface and application logic.

### Step 4.1: Create the HomeScreen Component
- Create a new file `src/screens/HomeScreen.js`.
- Use the `HomeScreen.js` code from the second part of the documentation.
- **IMPORTANT**: Replace `<your-api-id>` in the `axios.get` URL with your actual API Gateway ID.

### Step 4.2: Set up Navigation
- Install React Navigation: `npm install @react-navigation/native @react-navigation/stack react-native-screens react-native-safe-area-context`
- Set up a root navigator to display the `HomeScreen`.

## Phase 5: Integration and Deployment

This phase focuses on connecting all the pieces and deploying the app.

### Step 5.1: Test the Backend
- Manually invoke the scraper Lambda to populate the S3 bucket.
- Test the predictor Lambda via the API Gateway endpoint.

### Step 5.2: Test the Frontend
- Run the app: `npx react-native run-ios` or `npx react-native run-android`
- Verify that the app fetches and displays predictions.

### Step 5.3: Deploy the App
- The backend is already deployed on AWS.
- For the frontend, follow the React Native/Expo documentation to build and publish your app.

## Phase 6: Future Enhancements

This phase outlines future improvements based on the documentation.

- **Model Accuracy**: Integrate feature weighting.
- **Performance**: Use AWS Step Functions.
- **User Experience**: Add push notifications with AWS SNS.
- **Monetization**: Add subscriptions with Stripe.
- **Analytics**: Build a Prediction Analytics Dashboard.
- **AI Integration**: Explore AWS Bedrock, Sonnet 5, Gemini 2.0.
- **Authentication**: Implement user login with Cognito.