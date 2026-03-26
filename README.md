КАК ЗАПУСКАТЬ: 
### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Интерфейс: `http://localhost:3000`

### Docker
```bash
docker-compose up
```
