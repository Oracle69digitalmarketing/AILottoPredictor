import os
import csv
import json
from datetime import datetime
from flask import Flask, jsonify
from supabase import create_client, Client
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# --- Environment Variables ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")

# --- Initialize Clients ---
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Error initializing Supabase client: {e}")
    supabase = None

try:
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1")
except Exception as e:
    print(f"Error initializing OpenAI client for DeepSeek: {e}")
    client = None

# --- Main Prediction Route ---
@app.route('/api/predict', methods=['GET'])
def get_prediction():
    if not supabase or not client:
        return jsonify({"error": "Backend services not configured properly."}), 500

    try:
        with open('api/babaijeburesults.csv', 'r') as f:
            lines = f.read().splitlines()
        reader = csv.DictReader(lines)
        draws = list(reader)
        if not draws:
            return jsonify({"error": "CSV file is empty or has no data."}), 400
    except FileNotFoundError:
        return jsonify({"error": "Data file not found. Please ensure `api/babaijeburesults.csv` exists."}), 404

    formatted_draws = "\n".join([f"{i+1}. {row['Date']}: {row['Winning Numbers']}" for i, row in enumerate(draws)])
    prompt = f"""
Here is the historical data for the '{draws[-1]['Game']}' game:
{formatted_draws}
Based on the entire history, what are the 5 most likely numbers to appear in the next draw?
Return your answer as a clean JSON object with two keys: "numbers" (a list of 5 integers) and "probabilities" (a dictionary mapping each number as a string to its probability as a float).
"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        predictions_text = response.choices[0].message.content
        predictions = json.loads(predictions_text)
    except Exception as e:
        return jsonify({"error": f"Error invoking model or processing response: {str(e)}"}), 500

    try:
        game_name = draws[-1]['Game']
        prediction_date = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        probabilities_for_db = {str(k): float(v) for k, v in predictions['probabilities'].items()}
        supabase.table('LottoPredictions').insert({
            'GameName': game_name,
            'PredictionDate': prediction_date,
            'TopNumbers': predictions['numbers'],
            'Probabilities': probabilities_for_db,
            'ModelVersion': 'DeepSeek V3 (deepseek-chat)'
        }).execute()
    except Exception as e:
        print(f"Error storing prediction to Supabase: {str(e)}")

    return jsonify(predictions)

if __name__ == '__main__':
    app.run(debug=True)
