"""
YUI Web UI - ブラウザからYUIと対話

Flask使ってシンプルなWebインターフェースを提供
"""

from flask import Flask, render_template, request, jsonify
import json
import sys
from pathlib import Path

# YUIのパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from yui.agent.loop import run_agent_safe


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # セーフモードでYUIを実行
        response = run_agent_safe(user_message)
        
        return jsonify({
            'response': response,
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)