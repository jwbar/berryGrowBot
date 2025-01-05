from flask import Flask, render_template_string, request
import pandas as pd
import json
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime

app = Flask(__name__)

# Load JSON files
def load_data():
    # Load and adjust data from pws.json
    with open('pws.json', 'r') as f:
        data1 = json.load(f)
    df1 = pd.DataFrame(data1).rename(columns={'dt': 'timestamp', 'temp': 'temperature_OpenWeather', 'humidity': 'humidity_OpenWeather'})
    df1['timestamp'] = pd.to_datetime(df1['timestamp'], utc=True).dt.tz_convert(None)

    # Load and adjust data from kcontainer.json
    with open('kcontainer.json', 'r') as f:
        data2 = json.load(f)
    df2 = pd.DataFrame(data2).rename(columns={'temperature': 'temperature_kcontainer', 'humidity': 'humidity_kcontainer'})
    df2['timestamp'] = pd.to_datetime(df2['timestamp'])

    return df1, df2

# Generate comparison plot
def generate_comparison_plot(df1, df2):
    # Merge datasets on timestamp for comparison
    merged_df = pd.merge(df1, df2, on='timestamp', how='outer').sort_values('timestamp')
    fig, ax = plt.subplots(2, 1, figsize=(10, 8))

    # Plot temperature comparison
    ax[0].plot(merged_df['timestamp'], merged_df['temperature_OpenWeather'], label='OpenWeather Temperature', color='blue')
    ax[0].plot(merged_df['timestamp'], merged_df['temperature_kcontainer'], label='kcontainer Temperature', color='green')
    ax[0].set_ylabel('Temperature (°C)')
    ax[0].legend()

    # Plot humidity comparison
    ax[1].plot(merged_df['timestamp'], merged_df['humidity_OpenWeather'], label='OpenWeather Humidity', color='red')
    ax[1].plot(merged_df['timestamp'], merged_df['humidity_kcontainer'], label='kcontainer Humidity', color='purple')
    ax[1].set_ylabel('Humidity (%)')
    ax[1].set_xlabel('Timestamp')
    ax[1].legend()

    plt.tight_layout()

    # Save plot to a BytesIO object and encode as base64
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    plot_data = base64.b64encode(buf.read()).decode('utf-8')  # Convert to base64
    return plot_data

@app.route('/', methods=['GET', 'POST'])
def index():
    # Load and process data
    df1, df2 = load_data()

    # Handle form submission
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')

    # Filter data based on selected dates
    if start_date and end_date:
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        df1 = df1[(df1['timestamp'] >= start_date) & (df1['timestamp'] <= end_date)]
        df2 = df2[(df2['timestamp'] >= start_date) & (df2['timestamp'] <= end_date)]

    # Generate plot with filtered data
    plot_data = generate_comparison_plot(df1, df2)

    style = """
    <style>
    body {
        background-color: #1a1a1a;
        color: #f1f1f1;
        font-family: 'Courier New', Courier, monospace;
        text-align: center;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        justify-content: center;
        height: 100vh;
    }
    h1 {
        color: #27ae60;
        margin-bottom: 20px;
    }
    input {
        padding: 5px;
        margin: 5px;
    }
    </style>
    """

    # HTML template as a string
    html_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Temperature and Humidity Comparison</title>
        ''' + style + '''
    </head>
    <body>
        <h1>Temperature and Humidity Comparison</h1>
        <form method="post">
            <label for="start_date">Start Date:</label>
            <input type="date" id="start_date" name="start_date" required>
            <label for="end_date">End Date:</label>
            <input type="date" id="end_date" name="end_date" required>
            <input type="submit" value="Submit">
        </form>
        <img src="data:image/png;base64,{{ plot_data }}" alt="Temperature and Humidity Comparison">
    </body>
    </html>
    '''

    return render_template_string(html_template, plot_data=plot_data)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5003)
