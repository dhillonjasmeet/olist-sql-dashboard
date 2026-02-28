# Deploy the dashboard so recruiters can open it with one link

One path only. The deployed app will show a **subset of your real data** (same as local, smaller). Recruiters get a URL—no code to run.

---

## What you need

- The **full Olist dataset** in `data/` on your machine (same CSVs you use when you run the app locally).
- A **GitHub** account and a repo for this project.
- A **Streamlit Community Cloud** account (free, sign in with GitHub).

---

## Step 1: Build the sample from your real data (on your machine)

1. Put all Olist CSVs in **`data/`** (e.g. `olist_orders_dataset.csv`, `olist_customers_dataset.csv`, etc.).
2. In the project folder, run:
   ```bash
   python scripts/create_sample_data.py
   ```
3. You should see:
   - Lines like `olist_orders_dataset.csv: … rows` for each file.
   - **Verified: Retention & Loyalty has … rows.**
   - **Next: git add data_sample/ …**
4. If you see **ERROR** or **Verification failed**, fix the issue (usually: use the full dataset in `data/`) and run the script again. Do **not** push until the script finishes successfully.

This creates **`data_sample/`** = a subset of your real data, with correct links between tables and enough repeat customers so Retention & Loyalty works.

---

## Step 2: Commit and push the sample

1. Add and commit the sample (and any app/script changes):
   ```bash
   git add data_sample/ app.py scripts/ requirements.txt
   git status
   git commit -m "Add data_sample for Streamlit Cloud"
   git push
   ```
2. On GitHub, open your repo and confirm the **`data_sample`** folder is there and contains **9 CSV files**. The **`data/`** folder will not be in the repo (it’s gitignored)—that’s correct.

---

## Step 3: Deploy on Streamlit Community Cloud

1. Go to **https://share.streamlit.io** and sign in with GitHub.
2. Click **New app**.
3. Set:
   - **Repository:** `YourUsername/your-repo-name`
   - **Branch:** `main` (or your default branch)
   - **Main file path:** `app.py`
   - **App URL:** e.g. `olist-sql-dashboard`
4. Click **Deploy**.
5. Wait a few minutes. When it’s ready, copy the app URL (e.g. `https://olist-sql-dashboard.streamlit.app`).

---

## Step 4: Share the link

1. In your **README.md**, add near the top:
   ```markdown
   **Live dashboard:** [Open the app](https://your-app-url.streamlit.app)
   ```
2. Commit and push:
   ```bash
   git add README.md
   git commit -m "Add live dashboard link"
   git push
   ```

Recruiters can open the repo, see the link, and view the dashboard with no setup.

---

## If something goes wrong

| Problem | What to do |
|--------|------------|
| **“No data loaded”** on the live app | Ensure **`data_sample/`** (with 9 CSVs) is in the repo and pushed. Then: Streamlit Cloud → your app → **Manage app** → **Reboot app**. |
| **Retention & Loyalty shows “No retention data available”** | Regenerate the sample: run `python scripts/create_sample_data.py` again (with full data in `data/`). Make sure the script prints **Verified: Retention & Loyalty has … rows.** Then `git add data_sample/`, commit, push, and reboot the app. |
| **Deployed report looks wrong / not like local** | The repo must use a sample **from your real data**. Do not use any other sample or fake data. Put the full Olist CSVs in `data/`, run `python scripts/create_sample_data.py`, then commit and push `data_sample/` and reboot. |
| **Build error / app won’t start** | In Streamlit Cloud, open **Manage app** → **Logs**. Fix the error (often a missing dependency: add it to **requirements.txt**, commit, push). |

---

## Summary

| Step | Action |
|------|--------|
| 1 | Full Olist CSVs in `data/` → run `python scripts/create_sample_data.py` until it shows **Verified**. |
| 2 | `git add data_sample/ …` → commit → push. |
| 3 | share.streamlit.io → New app → repo, branch, `app.py` → Deploy. |
| 4 | Add the app URL to README, commit, push. |

After that, your live report is a subset of your real data, and recruiters can open it with one link.
