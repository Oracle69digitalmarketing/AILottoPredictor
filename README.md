# AI Lotto Predictor

This project is a mobile application that uses an AI-powered backend to predict lottery numbers.

## Architecture

The project is divided into two main components:

1.  **Frontend**: A React Native application located in the `AILottoPredictorApp` directory. This app is responsible for displaying the lottery predictions to the user.
2.  **Backend**: An AWS Lambda function in the `prediction-engine-lambda` directory. This serverless function fetches historical lottery data from an S3 bucket, uses Amazon Bedrock to generate predictions with the Claude 3 Sonnet model, and stores the results in a DynamoDB table.

### Backend Details

-   **Trigger**: The Lambda function is intended to be triggered by an API Gateway endpoint.
-   **Data Source**: It reads lottery results from a CSV file (`babaijeburesults.csv`) in an S3 bucket.
-   **AI Model**: It uses the `anthropic.claude-3-sonnet-20240229-v1:0` model from Amazon Bedrock.
-   **Data Storage**: Predictions are stored in a DynamoDB table named `LottoPredictions`.

## Getting Started

### Prerequisites

-   Node.js and npm (for the React Native app)
-   React Native development environment (see the [official guide](https://reactnative.dev/docs/set-up-your-environment))
-   AWS account and configured AWS CLI (for deploying the backend)

### Frontend Setup

1.  Navigate to the `AILottoPredictorApp` directory:
    ```sh
    cd AILottoPredictorApp
    ```
2.  Install the dependencies:
    ```sh
    npm install
    ```
3.  Run the application:
    -   For Android: `npm run android`
    -   For iOS: `npm run ios`

### Backend Deployment

1.  **Create AWS Resources**:
    -   An S3 bucket to store the lottery data CSV.
    -   A DynamoDB table named `LottoPredictions`.
    -   An IAM role for the Lambda function with permissions for S3, Bedrock, and DynamoDB.
2.  **Deploy the Lambda Function**:
    -   Package the `lambda_function.py` file and its dependencies into a zip file.
    -   Create a new Lambda function in the AWS console and upload the zip file.
3.  **Configure API Gateway**:
    -   Create a new REST API in API Gateway.
    -   Create a new resource and a `GET` method.
    -   Configure the `GET` method to integrate with the Lambda function.
    -   Deploy the API to a stage.
4.  **Update Frontend**:
    -   Replace the placeholder `API_URL` in `AILottoPredictorApp/src/PredictionView.tsx` with the deployed API Gateway endpoint URL.
