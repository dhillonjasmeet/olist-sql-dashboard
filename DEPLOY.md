# Deploy the dashboard so recruiters can open it with one link

**Goal:** The live app shows the **same data** as your local app. No sampling, no separate folder—the app reads from **`data/`** on both your machine and on Streamlit Cloud.

---

## How it works

- **Local:** You run the app with your Olist CSVs in **`data/`**. The app loads from `data/`.
- **Cloud:** You put those same CSVs in **`data/`** and **commit** that folder to your GitHub repo. Streamlit Cloud runs the app from the repo, so it loads the same **`data/`** folder. Same files = same report.

The project is set up so **`data/`** is no longer ignored. When you add and push **`data/`**, the CSV files go to GitHub and the live app uses them.

---

## What you need

- Your Olist CSVs in **`data/`** (the same ones you use locally).
- A GitHub repo for this project.
- A Streamlit Community Cloud account (free; sign in with GitHub).

---

## Step 1: Commit your data folder

1. Put all your Olist CSVs in **`data/`** (same as when you run the app locally).
2. In the project folder, run:
   ```bash
   git add data/
   git status
   ```
   You should see the CSV files under `data/` listed.
3. Commit and push:
   ```bash
   git commit -m "Add data for Streamlit Cloud so live app matches local"
   git push
   ```
4. On GitHub, open your repo and confirm the **`data`** folder is there and contains your CSV files.

**Note:** The Olist dataset is typically tens of megabytes. GitHub allows it; if you hit size limits, see the troubleshooting section below.

---

## Step 2: Deploy on Streamlit Community Cloud

1. Go to **https://share.streamlit.io** and sign in with GitHub.
2. Click **New app**.
3. Set:
   - **Repository:** your GitHub repo (e.g. `YourUsername/sql_portfolio`)
   - **Branch:** `main` (or your default branch)
   - **Main file path:** `app.py`
   - **App URL:** e.g. `olist-dashboard`
4. Click **Deploy**.
5. Wait a few minutes. When it’s ready, copy the app URL.

The app will load **`data/`** from the repo, so the report will match what you see locally.

---

## Step 3: Share the link

1. In **README.md**, add near the top:
   ```markdown
   **Live dashboard:** [Open the app](https://olist-sql-dashboard.streamlit.app)
   ```
2. Commit and push:
   ```bash
   git add README.md
   git commit -m "Add live dashboard link"
   git push
   ```

Recruiters can open the repo and click the link—no code to run.

---

## If something goes wrong

| Problem | What to do |
|--------|------------|
| **“No data loaded”** on the live app | Make sure **`data/`** (with your CSVs) is in the repo and pushed. Then: Streamlit Cloud → your app → **Manage app** → **Reboot app**. |
| **Repo or file too large** | GitHub warns on files over 50MB and blocks over 100MB. If your CSVs are very large, use [Git LFS](https://git-lfs.github.com/) for the data files, or reduce the dataset (e.g. keep one year of orders) and commit that. |
| **Build error / app won’t start** | In Streamlit Cloud, open **Manage app** → **Logs**. Fix the error (e.g. add missing dependencies to **requirements.txt**, commit, push). |

---

## Summary

| Step | Action |
|------|--------|
| 1 | Put Olist CSVs in `data/` → `git add data/` → commit → push. |
| 2 | share.streamlit.io → New app → your repo, `app.py` → Deploy. |
| 3 | Add the app URL to README, commit, push. |

After that, the live app uses the same **`data/`** as your local app, so the data matches exactly.
