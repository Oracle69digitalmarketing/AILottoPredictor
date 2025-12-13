import os
import csv
import json
from datetime import datetime
from flask import Flask, jsonify
from supabase import create_client, Client
from openai import OpenAI
from dotenv import load_dotenv
import logging
from pathlib import Path

# --- Basic Logging Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
logger.info("Environment variables loaded.")

app = Flask(__name__)

# --- Environment Variables ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")

# --- Initialize Clients ---
supabase = None
client = None

try:
    logger.info("Initializing Supabase client...")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("Supabase client initialized successfully.")
except Exception as e:
    logger.error(f"FATAL: Error initializing Supabase client: {e}", exc_info=True)

try:
    logger.info("Initializing OpenAI client for Deepseek...")
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
    logger.info("OpenAI client initialized successfully.")
except Exception as e:
    logger.error(f"FATAL: Error initializing OpenAI client: {e}", exc_info=True)

# --- Main Prediction Route ---
@app.route('/api/predict', methods=['GET'])
def get_prediction():
    logger.info("'/api/predict' route handler started.")
    if not supabase or not client:
        logger.error("FATAL: Backend services not configured properly. Supabase or OpenAI client is missing.")
        return jsonify({"error": "Backend services not configured properly."}), 500

    # 1. Read local CSV data using a robust path
    try:
        # Construct an absolute path to the CSV file
        base_path = Path(__file__).parent
        csv_path = base_path / 'babaijeburesults.csv'
        logger.info(f"Attempting to read CSV file from: {csv_path}")

        with open(csv_path, 'r') as f:
            lines = f.read().splitlines()

        reader = csv.DictReader(lines)
        draws = list(reader)[-10:]

        if not draws:
            logger.warning("CSV file is empty or has no data.")
            return jsonify({"error": "CSV file is empty or has no data."}), 400
        logger.info(f"Successfully read {len(draws)} draws from CSV.")

    except FileNotFoundError:
        logger.error(f"CRITICAL: Data file not found at {csv_path}", exc_info=True)
        return jsonify({"error": "Data file not found."}), 404
    except Exception as e:
        logger.error(f"CRITICAL: An unexpected error occurred while reading the CSV file: {e}", exc_info=True)
        return jsonify({"error": "Could not read data file."}), 500

    # 2. Format data and create a prompt for the AI model
    try:
        formatted_draws = "\n".join([
            f"{i+1}. {row['Date']}: {row['Winning Numbers']}"
            for i, row in enumerate(draws)
        ])
        game_name_from_csv = draws[-1].get('Game', 'Unknown Game')
        prompt = (
            f"Here are the last 10 draws of the '{game_name_from_csv}' game:\n"
            f"{formatted_draws}\n"
            "Based on this data, what are the 5 most likely numbers to appear in the next draw?\n"
            'Return your answer as a clean JSON object with two keys: "numbers" (a list of 5 integers) '
            'and "probabilities" (a dictionary mapping each number as a string to its probability as a float).'
        )
        logger.info("Successfully created prompt for AI model.")
    except Exception as e:
        logger.error(f"CRITICAL: Error formatting the prompt: {e}", exc_info=True)
        return jsonify({"error": "Failed to format data for prediction."}), 500

    # 3. Invoke the Deepseek AI model
    try:
        logger.info("Invoking Deepseek AI model...")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides answers in JSON format."},
                {"role": "user", "content": prompt},
            ],
            stream=False
        )
        predictions_text = response.choices[0].message.content
        logger.info("Successfully received response from Deepseek.")

        # Clean the response to ensure it's valid JSON
        json_start = predictions_text.find('{')
        json_end = predictions_text.rfind('}') + 1

        if json_start == -1 or json_end == 0:
            logger.error(f"Could not find a JSON object in the model's response. Raw response: {predictions_text}")
            raise ValueError("No JSON object found in response")

        predictions_json = predictions_text[json_start:json_end]
        predictions = json.loads(predictions_json)
        logger.info("Successfully parsed JSON from model response.")

    except Exception as e:
        logger.error(f"CRITICAL: Error invoking model or processing response: {e}", exc_info=True)
        return jsonify({"error": f"Error invoking model or processing response: {str(e)}"}), 500

    # 4. Store predictions to Supabase
    try:
        game_name = draws[-1]['Game']
        prediction_date = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

        probabilities_for_db = {str(k): float(v) for k, v in predictions['probabilities'].items()}

        logger.info("Storing predictions to Supabase...")
        data, count = supabase.table('LottoPredictions').insert({
            'GameName': game_name,
            'PredictionDate': prediction_date,
            'TopNumbers': predictions['numbers'],
            'Probabilities': probabilities_for_db,
            'ModelVersion': 'Deepseek Chat (Deepseek API)'
        }).execute()
        logger.info("Successfully stored predictions to Supabase.")

    except Exception as e:
        logger.warning(f"NON-CRITICAL: Error storing prediction to Supabase: {str(e)}", exc_info=True)

    logger.info("'/api/predict' route handler finished successfully.")
    return jsonify(predictions)

if __name__ == '__main__':
    app.run(debug=True)
