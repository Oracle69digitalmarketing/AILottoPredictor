import os
import csv
import json
from datetime import datetime
from flask import Flask, jsonify
from supabase import create_client, Client
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# --- Environment Variables ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# --- Initialize Clients ---
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Error initializing Supabase client: {e}")
    supabase = None

try:
    anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)
except Exception as e:
    print(f"Error initializing Anthropic client: {e}")
    anthropic = None

# --- Main Prediction Route ---
@app.route('/api/predict', methods=['GET'])
def get_prediction():
    if not supabase or not anthropic:
        return jsonify({"error": "Backend services not configured properly."}), 500

    # 1. Read local CSV data
    try:
        with open('api/babaijeburesults.csv', 'r') as f:
            lines = f.read().splitlines()
        reader = csv.DictReader(lines)
        draws = list(reader)[-10:]
        if not draws:
            return jsonify({"error": "CSV file is empty or has no data."}), 400
    except FileNotFoundError:
        return jsonify({"error": "Data file not found."}), 404

    # 2. Format data and create a prompt for the AI model
    formatted_draws = "\n".join([
        f"{i+1}. {row['Date']}: {row['Winning Numbers']}"
        for i, row in enumerate(draws)
    ])
    prompt = f"""
Here are the last 10 draws of the '{draws[-1]['Game']}' game:
{formatted_draws}
Based on this data, what are the 5 most likely numbers to appear in the next draw?
Return your answer as a clean JSON object with two keys: "numbers" (a list of 5 integers) and "probabilities" (a dictionary mapping each number as a string to its probability as a float).
"""

    # 3. Invoke the Anthropic AI model
    try:
        message = anthropic.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=500,
            temperature=0.7,
            messages=[
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}]
                }
            ]
        )
        predictions_text = message.content[0].text
        # Clean the response to ensure it's valid JSON
        predictions_json = predictions_text[predictions_text.find('{'):predictions_text.rfind('}')+1]
        predictions = json.loads(predictions_json)

    except Exception as e:
        return jsonify({"error": f"Error invoking model or processing response: {str(e)}"}), 500

    # 4. Store predictions to Supabase
    try:
        game_name = draws[-1]['Game']
        prediction_date = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

        # Ensure probabilities are stored in a format Supabase can handle (e.g., JSONB)
        probabilities_for_db = {str(k): float(v) for k, v in predictions['probabilities'].items()}

        data, count = supabase.table('LottoPredictions').insert({
            'GameName': game_name,
            'PredictionDate': prediction_date,
            'TopNumbers': predictions['numbers'],
            'Probabilities': probabilities_for_db,
            'ModelVersion': 'Claude 3 Sonnet (Anthropic API)'
        }).execute()

    except Exception as e:
        # Log the error but don't fail the request if the DB insert fails
        print(f"Error storing prediction to Supabase: {str(e)}")

    return jsonify(predictions)

if __name__ == '__main__':
    app.run(debug=True)
