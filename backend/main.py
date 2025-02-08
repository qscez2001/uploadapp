import io
import os
from PIL import Image
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import gridfs
from bson import ObjectId

allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/images_db")

# Create sync client for GridFS
sync_client = MongoClient(MONGO_URI)
sync_db = sync_client['images_db']  # Changed to dictionary-style access
fs = gridfs.GridFS(sync_db)

# Create async client for other operations
async_client = AsyncIOMotorClient(MONGO_URI)
async_db = async_client['images_db']

@app.on_event("shutdown")
async def shutdown_event():
    sync_client.close()
    async_client.close()

def validate_image(image_file):
    """Validate image format and resolution (2048x2048)."""
    try:
        image = Image.open(image_file)
        width, height = image.size
        if width >= 2048 or height >= 2048:
            raise HTTPException(status_code=400, detail=f"影像必須為 2048x2048 像素，目前大小: {width}x{height}")
        image_file.seek(0)  # Reset file pointer after reading
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"無效的影像格式: {str(e)}")
    
@app.post("/upload")
async def upload_images(files: list[UploadFile] = File(...)):
    """Upload images to MongoDB GridFS."""
    if len(files) > 100:
        raise HTTPException(status_code=400, detail="最多只能上傳 100 張影像")

    uploaded_ids = []
    for file in files:
        validate_image(file.file)
        file_id = fs.put(file.file, filename=file.filename, content_type=file.content_type)
        uploaded_ids.append(str(file_id))

    return {"uploaded_ids": uploaded_ids}


@app.get("/images")
async def list_images():
    """Retrieve a list of uploaded images."""
    images = [{"id": str(file._id), "filename": file.filename} for file in fs.find()]
    return {"images": images}

@app.get("/image/{image_id}")
async def get_image(image_id: str):
    """Retrieve a specific image by ID."""
    try:
        file = fs.get(ObjectId(image_id))
        return StreamingResponse(io.BytesIO(file.read()), media_type=file.content_type)
    except Exception:
        raise HTTPException(status_code=404, detail="影像不存在")
