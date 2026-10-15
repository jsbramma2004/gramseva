# 🌾 GramSeva Backend

**Rural Infrastructure Issue Reporting Portal — Python + FastAPI + MongoDB + Cloudinary**

---

## 📁 Project Structure

```
gramseva-backend/
├── app/
│   ├── main.py                    # FastAPI app entry point
│   ├── database.py                # MongoDB (Motor) connection
│   ├── routers/
│   │   └── reports.py             # All report API endpoints
│   ├── models/
│   │   └── report.py              # Pydantic schemas & enums
│   ├── services/
│   │   ├── cloudinary_service.py  # Image upload / delete
│   │   └── email_service.py       # Department email alerts
│   └── utils/
│       └── ticket.py              # Ticket ID generator
├── .env.example                   # Environment variable template
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup Instructions

### 1. Clone & create virtual environment
```bash
git clone <your-repo>
cd gramseva-backend

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables
```bash
cp .env.example .env
# Open .env and fill in your real values (see below)
```

### 4. Run the server
```bash
uvicorn app.main:app --reload --port 8000
```

Visit → **http://localhost:8000/docs** for the interactive Swagger UI.

---

## 🔑 Environment Variables

| Variable | Description |
|---|---|
| `MONGO_URI` | MongoDB Atlas connection string |
| `DB_NAME` | Database name (default: `gramseva`) |
| `CLOUDINARY_CLOUD_NAME` | Your Cloudinary cloud name |
| `CLOUDINARY_API_KEY` | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret |
| `SMTP_HOST` | SMTP server (e.g. `smtp.gmail.com`) |
| `SMTP_PORT` | SMTP port (usually `587`) |
| `SMTP_USER` | Your Gmail address |
| `SMTP_PASS` | Gmail App Password (not your login password!) |
| `EMAIL_WATER_SUPPLY` | Dept email for water issues |
| `EMAIL_ROADS` | Dept email for road issues |
| `EMAIL_WATER_MANAGEMENT` | Dept email for water management |
| `EMAIL_STREET_LIGHTS` | Dept email for street light issues |
| `EMAIL_DRAINAGE` | Dept email for drainage issues |
| `EMAIL_OTHER` | Gram Panchayat fallback email |

### How to get a Gmail App Password:
1. Go to your Google Account → Security
2. Enable 2-Step Verification
3. Search "App passwords" → Create one for "Mail"
4. Paste that 16-char password in `SMTP_PASS`

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/reports/` | Submit new report (multipart/form-data) |
| `GET` | `/api/v1/reports/` | List reports (paginated + filtered) |
| `GET` | `/api/v1/reports/{ticket_id}` | Get single report |
| `PATCH` | `/api/v1/reports/{ticket_id}` | Update report status |
| `DELETE` | `/api/v1/reports/{ticket_id}` | Delete report |
| `GET` | `/api/v1/reports/stats/summary` | Dashboard statistics |
| `GET` | `/health` | Health check |

### Query Parameters (GET /reports/)
- `category` — Filter by issue category
- `status` — `pending` / `in_progress` / `resolved` / `rejected`
- `district` — Search by district name
- `urgency` — `low` / `medium` / `high`
- `page` — Page number (default: 1)
- `limit` — Items per page (default: 20, max: 100)

---

## 🔌 Connecting the Frontend

In your HTML file, replace the `submitReport()` function with a `fetch` call:

```javascript
async function submitReport() {
  const formData = new FormData();
  formData.append("name",        document.getElementById("f-name").value);
  formData.append("phone",       document.getElementById("f-phone").value);
  formData.append("village",     document.getElementById("f-village").value);
  formData.append("district",    document.getElementById("f-district").value);
  formData.append("category",    document.getElementById("f-category").value);
  formData.append("description", document.getElementById("f-desc").value);
  formData.append("urgency",     selectedUrgency || "medium");

  const photoFile = document.getElementById("f-photo").files[0];
  if (photoFile) formData.append("photo", photoFile);

  const res = await fetch("http://localhost:8000/api/v1/reports/", {
    method: "POST",
    body: formData,   // Do NOT set Content-Type header — browser does it automatically
  });

  const data = await res.json();
  if (res.ok) {
    document.getElementById("ticket-num").textContent = "Ticket #" + data.ticket_id;
    document.getElementById("modal").classList.add("active");
  } else {
    alert("Error: " + data.detail);
  }
}
```

---

## 🗄️ MongoDB Atlas Setup (Free Tier)

1. Go to **https://cloud.mongodb.com** → Create free account
2. Create a free **M0 cluster**
3. Under **Database Access** → Add a DB user (username + password)
4. Under **Network Access** → Add IP `0.0.0.0/0` (allow all) for development
5. Click **Connect → Connect your application** → Copy the connection string
6. Replace `<username>`, `<password>` in the string and paste into `.env`

---

## ☁️ Cloudinary Setup (Free Tier)

1. Go to **https://cloudinary.com** → Sign up free
2. From your Dashboard, copy: Cloud Name, API Key, API Secret
3. Paste into `.env`

---

## 🚀 Deploy to Production

**Render (free):**
```bash
# Set environment variables in Render dashboard
# Start command:
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Railway / Fly.io / DigitalOcean App Platform** also work great.

---

## 📊 MongoDB Collections

### `reports` collection schema:
```json
{
  "ticket_id":       "GS-2026-12345",
  "name":            "Ramesh Kumar",
  "phone":           "9876543210",
  "village":         "Ramnagar",
  "district":        "Varanasi",
  "state":           "Uttar Pradesh",
  "category":        "Water Supply / Pipe Leakage",
  "description":     "Main pipeline burst near temple...",
  "urgency":         "high",
  "status":          "pending",
  "image_url":       "https://res.cloudinary.com/...",
  "image_public_id": "gramseva/reports/abc123",
  "department":      "Public Health Engineering Dept",
  "email_sent":      true,
  "latitude":        25.3176,
  "longitude":       82.9739,
  "created_at":      "2026-03-23T10:30:00Z",
  "updated_at":      "2026-03-23T10:30:00Z"
}
```
