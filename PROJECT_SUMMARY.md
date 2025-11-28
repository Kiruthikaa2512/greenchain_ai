# **GreenChain AI — Sustainable Supply Chain Intelligence**
**Author:** Kiruthikaa Natarajan Srinivasan  
**Date:** November 24, 2025  

## **Overview**

GreenChain-AI is an integrated sustainability intelligence system designed to help organizations measure, understand, and reduce environmental impact across their supply chain. Modern supply chains generate the majority of a company’s emissions and waste, yet most companies lack accessible tools to track transportation emissions, inventory waste, supplier sustainability, or warehouse energy consumption. Even when data exists, it is scattered across spreadsheets and departments, making sustainability analysis inefficient and unreliable.

GreenChain-AI solves this by unifying transportation routes, demand forecasting, supplier ESG performance, and warehouse energy use into a single, intuitive web application. The system computes a real-time sustainability index and provides immediate feedback on how operational decisions influence carbon emissions, waste production, energy consumption, and overall environmental performance. The interface is designed for users without technical or supply-chain backgrounds, allowing any organization—large or small—to adopt data-driven sustainability practices.



# **What the Project Does**

GreenChain-AI contains four major modules, each reflecting a core supply chain function. All modules accept either user-uploaded CSV data or automatically generated sample data. Each module updates the system’s scores and contributes to the unified sustainability index.

Below is a detailed explanation of every module, including every action the user can perform, how the system responds, and why each function matters.


# **1. Transportation & Routing Module**

### **Purpose for non-experts**

Transportation is one of the largest contributors to supply chain emissions. Route inefficiencies, low load utilization, and fuel type choices significantly influence carbon output. This module quantifies these impacts and makes the trade-offs visible.

### **User Actions and Effects**

1. **Upload Route CSV (location, latitude, longitude, drop_kg)**

   * If valid, the system uses the real data.
   * If invalid or absent, a sample route dataset is generated.
   * CSV template is provided so any user understands the required structure.

2. **Set number of delivery stops**

   * Used only if no CSV is provided.
   * Generates realistic synthetic lat/long and demand quantities.

3. **Select vehicle type**

   * Options: Diesel, Gasoline, Hybrid, Electric.
   * Each vehicle has a defined emissions factor.
   * The system recalculates emissions instantly when vehicle type changes.

4. **Adjust load utilization percentage**

   * Represents how full the vehicle is.
   * Higher utilization reduces emissions per kilogram delivered.
   * Directly affects the sustainability score.

### **Internal Logic**

* Routes are optimized using a nearest-neighbor method.
* Distances between consecutive stops are calculated.
* Emissions are computed as:
  `total_distance × emission_factor × load_factor_adjustment`

### **Outputs**

* Total route distance
* Emissions for selected vehicle
* Baseline emissions (Diesel scenario)
* Emissions saved
* A bar chart comparing both scenarios
* A transport sustainability score contributing to the overall index

### **Why this matters**

This allows businesses to quantify the real impact of switching to hybrid or electric fleets and optimizing delivery routes. Managers gain a clear, numeric understanding of how each transportation choice affects emissions.



# **2. Demand & Waste Forecasting Module**

### **Purpose for non-experts**

A significant source of supply chain waste is overproduction and excess inventory. This module forecasts demand and detects overstock risks, enabling companies to make more accurate production or procurement decisions.

### **User Actions and Effects**

1. **Upload demand CSV (date, demand)**

   * If valid, data is used directly.
   * If invalid or absent, synthetic historical data is generated.
   * Template included to guarantee correct formatting.

2. **Select historical duration and forecast horizon**

   * Users can simulate short-term or long-term planning.
   * Forecast adjusts dynamically.

3. **Adjust safety stock percentage**

   * Safety stock represents production or purchasing buffer.
   * Increasing this buffer increases projected overstock.
   * System immediately recalculates overstock quantity and waste score.

### **Internal Logic**

* Linear regression model predicts future demand.
* Forecast is computed for the selected duration.
* Overstock is calculated as:
  `max(planned_quantity - forecast, 0)`
* Overstock ratio generates the waste sustainability score.

### **Outputs**

* Historical demand chart
* Forecast vs planned quantity chart
* Total forecasted demand
* Total planned quantity
* Estimated overstock
* Waste & Forecasting sustainability score

### **Why this matters**

Organizations can visually see whether they are producing too much, wasting materials, or storing excess stock. This reduces waste, storage energy, perishables spoilage, and cost.



# **3. Supplier Sustainability Module**

### **Purpose for non-experts**

Suppliers heavily influence emissions (Scope 3), product quality, and ethical outcomes. This module quantifies supplier performance across four dimensions: on-time delivery, ESG maturity, product quality, and emission transparency.

### **User Actions and Effects**

1. **Upload Supplier CSV**

   * If valid: direct supplier scoring.
   * If missing columns: system falls back to sample supplier dataset.
   * Template available.

2. **Adjust weights for four parameters**

   * Users define what matters most to their organization.
   * Weights are normalized (sum = 1).
   * Supplier scores update instantly.

3. **Select a supplier for deeper analysis**

   * Radar chart visualizes performance across all four axes.

### **Internal Logic**

* Weighted score computed for each supplier:
  `(A × W1) + (B × W2) + (C × W3) + (D × W4)`
* Average supplier score becomes the Supplier Sustainability score.

### **Outputs**

* Scored supplier table
* Radar visualization
* Supplier sustainability score feeding into overall index

### **Why this matters**

Organizations gain quantifiable justification for choosing ethical, transparent, and high-performing suppliers. This directly influences long-term sustainability and reputational compliance.



# **4. Warehouse Energy & Ops Module**

### **Purpose for non-experts**

Warehouses consume large amounts of energy, especially refrigeration and material-handling equipment. This module approximates daily energy usage based on warehouse characteristics.

### **User Actions and Effects**

1. **Upload warehouse configuration CSV**
2. **Set warehouse area**
3. **Daily operating hours**
4. **Percentage of refrigerated area**
5. **Number of electric forklifts**

These parameters collectively determine the warehouse’s energy intensity.

### **Internal Logic**

Energy consumption is estimated using a simplified but realistic model:

`kWh = area × hours × base_factor × refrigeration_multiplier × forklift_factor`

An alternative scenario is auto-generated with reduced hours and lower refrigeration to compare potential optimizations.

### **Outputs**

* Estimated daily energy usage
* Sustainability score based on energy efficiency
* Bar chart comparing current vs optimized scenarios
* Potential energy savings

### **Why this matters**

Companies understand how operating hours, refrigeration load, and equipment choices affect energy usage and emissions, enabling targeted improvements.



# **Unified Sustainability Index**

GreenChain-AI combines all module scores into a single 0–100 index using weighted contributions:

* Transportation: 30%
* Waste & Forecasting: 25%
* Supplier Sustainability: 25%
* Warehouse Energy: 20%

This gives organizations a simplified, holistic metric suitable for reporting, ESG dashboards, and operational decision-making.



# **Auto-Generated Reports**

The system generates a downloadable PDF and text summary that includes:

* Overall Sustainability Index
* Module-wise scores
* Emissions metrics
* Waste and supplier analysis
* Warehouse energy results

This is essential for internal reporting, sustainability reviews, or hackathon submissions.



# **Impact**

GreenChain-AI makes sustainability accessible:

1. It equips non-technical business users with clear, data-driven insights.
2. It reduces waste, emissions, energy use, and supplier risk.
3. It consolidates fragmented datasets into a unified intelligence layer.
4. It provides an affordable alternative to enterprise-grade sustainability tools.
5. It encourages environmentally responsible decision-making through measurable improvements rather than guesswork.

**How I Built It (Tools and Development Process)**

GreenChain-AI was developed using Streamlit as the primary frontend framework because it allows rapid development of interactive data apps with clean UI components. The backend logic is implemented entirely in Python, using Pandas for data processing, NumPy for numerical computations, and Scikit-learn for the demand-forecasting model. Plotly is used for all charts and visualizations, and ReportLab is used to generate downloadable PDF sustainability summaries.

During development, the first step was to define the four sustainability pillars and create a consistent scoring methodology for each. Once the scoring system was clear, CSV templates were created to ensure any user could upload structured data without previous supply-chain knowledge. Each module was built independently and later unified under a central sustainability index calculation. The UI was refined iteratively to ensure clarity, simplicity, and accessibility for non-technical users.

**What Surprised Me**

I was surprised by how much clarity simple visualizations can bring to complex sustainability metrics. Even small changes—such as switching vehicle type or adjusting safety stock—created visible improvements in emissions or waste reduction that users could immediately understand. It was also surprising how sensitive sustainability scores are to even minor inefficiencies in transportation or inventory planning, which validated the importance of tools like this.

**What Was Hard**

The most challenging aspect was designing the system so that each module works independently while still contributing to a unified sustainability index. Handling inconsistent CSV formats, filling missing columns, and making the app fail-safe for non-technical users required significant effort. Balancing accuracy with simplicity—especially in emissions modeling, forecasting, and warehouse energy estimation—was also difficult. Ensuring that every input triggers instant recalculations without slowing down the interface required careful structuring of the code.
