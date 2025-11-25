#  **GreenChain AI**

### *Sustainable Supply Chain Intelligence for a Greener World*

## *Built for Aethra Global Vibeathon 2025* ##

---

## **Overview**

Supply chains power the world — but they also generate **over 60% of global emissions**, according to McKinsey.
While large enterprises invest millions into sustainability analytics, **most teams still rely on spreadsheets**, manual estimates, and fragmented tools.

**GreenChain AI** changes that.

This project is a unified, intelligent sustainability assistant that turns **transportation routes**, **demand patterns**, **supplier ESG maturity**, and **warehouse energy usage** into a single, interpretable **Sustainability Index (0–100)**.

It gives organizations — even small ones — the analytics superpowers normally reserved for Fortune 500 logistics teams.

---

# **Why We Built This (The Problem)**

Today, the supply chain sustainability landscape is fragmented:

### ❌ Routing tools calculate distance — not emissions

### ❌ Forecasting tools predict demand — not waste

### ❌ Supplier scorecards measure performance — not ESG transparency

### ❌ Warehouse dashboards show operations — not sustainability impact

Organizations are forced to stitch together multiple tools and manually guess sustainability metrics.
This leads to:

* Inefficient route planning
* Unnecessary emissions
* Overstock & waste
* Poor supplier environmental accountability
* Energy-inefficient warehouse operations
* Lack of a *unified sustainability score*

Meanwhile, governments and corporations are pushing towards **net-zero commitments**, yet small and mid-sized businesses have no accessible tools to participate.

---

# **What GreenChain AI Does (The Solution)**

GreenChain AI integrates **4 critical pillars of sustainable logistics** into a single platform:

---

## 1️ **Transportation & Routing Intelligence**

✔ Route optimization (nearest-neighbor heuristic)
✔ Emissions modeling by vehicle type (diesel, gas, hybrid, EV)
✔ Load factor impact
✔ CSV upload + interactive dashboards
✔ Transport Sustainability Score

---

## 2️ **Demand Forecasting & Waste Reduction**

✔ Linear regression forecasting
✔ Safety stock simulation
✔ Overstock waste estimation
✔ CSV upload for real historical demand
✔ Waste & Forecasting Score

---

## 3️ **Supplier Sustainability Evaluation**

✔ ESG-aware supplier scoring
✔ Weighted evaluation (delivery, ESG, quality, transparency)
✔ Upload your own supplier data
✔ Radar ESG visualization
✔ Supplier Sustainability Score

---

## 4️ **Warehouse Energy & Operations**

✔ Energy consumption estimation
✔ Refrigerated storage modeling
✔ Forklift electrification impact
✔ Current vs optimized scenarios
✔ Warehouse Sustainability Score

---

#  **Unified Sustainability Index (0–100)**

The platform aggregates all modules into a single **Sustainability Index**, helping organizations:

* Benchmark operations
* Report sustainability performance
* Prioritize areas of improvement
* Share sustainability proof in audits or grants
* Add evidence in submissions (like this hackathon!)

---

#  **Why This Matters**

GreenChain AI democratizes sustainability intelligence:

### **Accessible**

Runs in a browser. No enterprise software required.

### **Actionable**

Shows exactly *where* emissions and waste originate.

### **Transparent**

Gives organizations control over their sustainability decisions.

### **High-Impact**

Addresses climate, logistics optimization, energy efficiency, and ESG transparency at once.

What previously required four independent enterprise systems now fits inside one cohesive application — simplifying sustainability for millions of businesses.

---

# **How the App Works**

### **1. Upload CSV or Use Sample Data**

Each module allows CSV uploads with downloadable templates:

* Route data
* Demand history
* Supplier ratings
* Warehouse configuration

### **2. View Analytics & Scores**

Each module shows:

* Metrics
* Charts
* Optimizations
* Sustainability scores

### **3. Download Reports**

A complete sustainability report is generated as:

* PDF
* Plain text (for Devpost submission)

---

# Technology Stack

| Component          | Used For                   |
| ------------------ | -------------------------- |
| **Python**         | Core logic                 |
| **Streamlit**      | UI & application framework |
| **Pandas / NumPy** | Data processing            |
| **Plotly**         | Visualizations             |
| **scikit-learn**   | Linear regression          |
| **ReportLab**      | PDF generation             |
| **CSS**            | Custom UI theme            |

---

# Installation

```
pip install -r requirements.txt
streamlit run app.py
```

---

# requirements.txt

```
streamlit
pandas
numpy
plotly
scikit-learn
reportlab
networkx
```

---

# CSV Template Formats

### **1️ Route Template (route_template.csv)**

```
location,latitude,longitude,drop_kg
Stop 1,12.90,77.50,10
Stop 2,12.95,77.60,15
Stop 3,12.88,77.72,8
```

### **2️ Demand Template (demand_template.csv)**

```
date,demand
2024-01-01,200
2024-01-02,220
2024-01-03,210
```

### **3️ Supplier Template (supplier_template.csv)**

```
supplier,on_time_delivery,esg_score,quality_score,emission_transparency
Supplier A,0.96,0.82,0.9,0.85
Supplier B,0.88,0.78,0.86,0.65
```

### **4️ Warehouse Template (warehouse_template.csv)**

```
area_m2,operating_hours,refrigerated_pct,forklifts
8000,16,30,10
```

---

# Key Innovations

###  Unified multi-dimensional sustainability scoring

No other open-source tool merges transport, demand, suppliers, and warehouse energy.

###  CSV-first design

Real organizations can plug in their raw data instantly.

### Completely local & privacy-safe

Everything runs in your browser — zero cloud dependencies.

### Hackathon-ready evidence generation

Built-in PDF and summary exports to strengthen your submission.

---

# Final Thoughts

GreenChain AI is built with one purpose:

## **Make sustainability measurable, actionable, and accessible for everyone.**

Whether you're a small business or a global enterprise, sustainability shouldn’t require enterprise software or million-dollar platforms.

GreenChain AI proves that powerful sustainability intelligence can be:

* simple
* intuitive
* transparent
* open
* and impactful


