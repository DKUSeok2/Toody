from flask import Flask
from flask_cors import CORS, cross_origin
from app.api.summary_api import summary_bp
from app.api.upload_api import upload_bp
from app.api.sidebar_api import sidebar_bp
from app.api.download_api import download_bp
from app.api.url_api import url_bp
from app.api.todo_api import todo_bp
from app.api.security_api import security_bp
from dotenv import load_dotenv
from datetime import timedelta
import secrets

load_dotenv()

app = Flask(__name__, template_folder="templates")
app.secret_key = secrets.token_hex(32)

# 세션 영구화 설정
app.permanent_session_lifetime = timedelta(days=30)  # 30일간 세션 유지

# CORS 설정 - 세션 사용을 위해 credentials 지원
CORS(app, 
     origins=['http://localhost:3000'], 
     supports_credentials=True,
     allow_headers=['Content-Type', 'Authorization'],
     expose_headers=['Content-Disposition'],  # Content-Disposition 헤더 노출 허용
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

# 추가 헤더 설정
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Expose-Headers', 'Content-Disposition')  # 추가
    return response

app.register_blueprint(summary_bp)
app.register_blueprint(upload_bp)
app.register_blueprint(sidebar_bp)
app.register_blueprint(download_bp)
app.register_blueprint(url_bp)
app.register_blueprint(todo_bp)
app.register_blueprint(security_bp)

if __name__ == "__main__":
    app.run(debug=True, port=8000, host='0.0.0.0')