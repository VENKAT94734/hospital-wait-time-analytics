# CareFlow Analytics — GitHub Pages Dashboard

This folder contains a static, interactive dashboard for Hospital Patient Waiting-Time Analytics. It reads the included synthetic visit dataset and runs entirely in the browser.

## Publish to GitHub Pages
1. Copy `index.html` and the `data` folder from this `github_pages` folder into the **root** of your GitHub repository (replace the current README-only landing page; keep the rest of your Python project files).
2. Commit and push the changes to the `main` branch.
3. In GitHub, open **Settings → Pages**.
4. Under **Build and deployment**, choose **Deploy from a branch**, select `main` and `/(root)`, then Save.
5. Wait for deployment. Your site should be available at `https://YOUR-USERNAME.github.io/YOUR-REPOSITORY/`.

## Features
- Date range, department, acuity, and long-wait threshold filters
- Visits, median wait, P90 wait, and long-wait KPIs
- Daily median/P90 trend
- Arrival volume by hour
- Department wait comparison and scorecard
- Wait-time distribution
- Automatically generated operational signals
- Export filtered records to CSV
- Responsive layout for desktop and mobile

## Data note
`data/visits_dashboard.csv` contains a reduced view of 12,000 synthetic visit records. No real patient data is included. This dashboard is a portfolio demo and is not suitable for clinical decisions.

Chart.js is loaded from a CDN, so internet access is required for chart rendering.
