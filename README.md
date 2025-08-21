# Schwarz IT Interview Exercise – Sales Dashboard

This project provides a simple **Sales Dashboard** with a **FastAPI backend** and a **Dash/Plotly frontend**.  
It demonstrates the use of an API layer for data processing and a separate dashboard for visualization.

---

## ⚡ Features

- **FastAPI backend** (`/api`):
  - Serves sales data from CSV  
  - Provides metrics (sales by category, store, article, time)  
  - Includes predicted sales over time  
  - Includes actual vs predicted sales comparison  

- **Dash frontend** (`/dashboard`):
  - Interactive filtering by date and Top-N  
  - KPIs (total sales, average per day, dataset count, number of articles)  
  - Multiple charts:
    - Bar & Pie: Sales by Category  
    - Bar & Pie: Sales by Store  
    - Bar & Pie: Sales by Article  
    - Line: Sales over Time  
    - Line: Predicted Sales over Time  
    - Line: Actual vs Predicted Sales over Time  

---

## 🚀 Usage

### Run with Docker Compose (recommended)

Make sure **Docker** and **Docker Compose** are installed on your system.  
From the project root, run:

```bash
docker-compose up --build
```

This will build and start two services:

- API → http://localhost:8000
- Dashboard → http://localhost:8050

You can now open the dashboard in your browser and explore the sales data interactively.