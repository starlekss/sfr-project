from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import aiofiles
import os
import uuid
from datetime import datetime
from pathlib import Path

app = FastAPI(title="СФР File Upload Service", description="Сервис для загрузки документов")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Создание директорий для загрузки
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Поддиректории для разных типов документов
DOC_TYPES = {
    'passport': UPLOAD_DIR / 'passports',
    'snils': UPLOAD_DIR / 'snils',
    'additional': UPLOAD_DIR / 'additional'
}

for dir_path in DOC_TYPES.values():
    dir_path.mkdir(exist_ok=True, parents=True)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Главная страница FastAPI сервиса"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>СФР - File Upload Service</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                background: rgba(255,255,255,0.9);
                padding: 30px;
                border-radius: 15px;
                color: #333;
            }
            h1 { color: #667eea; }
            .status { color: green; font-weight: bold; }
            .endpoint {
                background: #f0f0f0;
                padding: 10px;
                margin: 10px 0;
                border-radius: 5px;
                font-family: monospace;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 СФР File Upload Service</h1>
            <p>Статус: <span class="status">✅ Работает</span></p>

            <h2>Доступные эндпоинты:</h2>

            <div class="endpoint">
                <strong>POST /upload/{doc_type}</strong><br>
                Загрузить файл (doc_type: passport, snils, additional)
            </div>

            <div class="endpoint">
                <strong>GET /files/{doc_type}/{filename}</strong><br>
                Скачать файл
            </div>

            <div class="endpoint">
                <strong>GET /health</strong><br>
                Проверка здоровья сервиса
            </div>

            <hr>

            <h3>📤 Тест загрузки файла:</h3>
            <form id="uploadForm" enctype="multipart/form-data">
                <select id="docType" style="padding: 10px; margin-right: 10px;">
                    <option value="passport">Паспорт</option>
                    <option value="snils">СНИЛС</option>
                    <option value="additional">Доп. документы</option>
                </select>
                <input type="file" id="fileInput" style="padding: 10px;">
                <button type="submit" style="padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 5px;">Загрузить</button>
            </form>
            <div id="result" style="margin-top: 20px;"></div>
        </div>

        <script>
            document.getElementById('uploadForm').onsubmit = async (e) => {
                e.preventDefault();
                const docType = document.getElementById('docType').value;
                const file = document.getElementById('fileInput').files[0];

                if (!file) {
                    alert('Выберите файл');
                    return;
                }

                const formData = new FormData();
                formData.append('file', file);

                const response = await fetch(`/upload/${docType}`, {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();
                document.getElementById('result').innerHTML = `
                    <div style="background: #e0f2fe; padding: 15px; border-radius: 10px; margin-top: 10px;">
                        <strong>✅ Файл загружен!</strong><br>
                        Имя: ${result.filename}<br>
                        Размер: ${result.size} bytes
                    </div>
                `;
            };
        </script>
    </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "upload_dirs": {
            "base": str(UPLOAD_DIR),
            "passport": str(DOC_TYPES['passport']),
            "snils": str(DOC_TYPES['snils']),
            "additional": str(DOC_TYPES['additional'])
        }
    }


@app.post("/upload/{doc_type}")
async def upload_file(doc_type: str, file: UploadFile = File(...)):
    """Загрузка скана документа"""

    # Проверка типа документа
    if doc_type not in DOC_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid document type. Allowed: {list(DOC_TYPES.keys())}")

    # Проверка размера файла (максимум 10MB)
    file_size = 0
    content = await file.read()
    file_size = len(content)

    if file_size > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(status_code=400, detail="File too large. Max size: 10MB")

    # Проверка расширения файла
    allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
    file_extension = Path(file.filename).suffix.lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {allowed_extensions}")

    # Генерация уникального имени файла
    unique_filename = f"{doc_type}_{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_extension}"
    file_path = DOC_TYPES[doc_type] / unique_filename

    # Сохранение файла
    async with aiofiles.open(file_path, 'wb') as out_file:
        await out_file.write(content)

    return JSONResponse({
        "status": "success",
        "doc_type": doc_type,
        "filename": unique_filename,
        "original_name": file.filename,
        "path": str(file_path),
        "size": file_size,
        "url": f"/files/{doc_type}/{unique_filename}"
    })


@app.get("/files/{doc_type}/{filename}")
async def get_file(doc_type: str, filename: str):
    """Скачивание файла"""

    if doc_type not in DOC_TYPES:
        raise HTTPException(status_code=400, detail="Invalid document type")

    file_path = DOC_TYPES[doc_type] / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )


@app.get("/files/list")
async def list_files():
    """Список всех загруженных файлов"""
    files = {}

    for doc_type, dir_path in DOC_TYPES.items():
        files[doc_type] = []
        if dir_path.exists():
            for file_path in dir_path.iterdir():
                if file_path.is_file():
                    files[doc_type].append({
                        "filename": file_path.name,
                        "size": file_path.stat().st_size,
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                        "url": f"/files/{doc_type}/{file_path.name}"
                    })

    return JSONResponse(files)


@app.delete("/files/{doc_type}/{filename}")
async def delete_file(doc_type: str, filename: str):
    """Удаление файла"""

    if doc_type not in DOC_TYPES:
        raise HTTPException(status_code=400, detail="Invalid document type")

    file_path = DOC_TYPES[doc_type] / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    file_path.unlink()

    return JSONResponse({
        "status": "success",
        "message": f"File {filename} deleted"
    })


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)