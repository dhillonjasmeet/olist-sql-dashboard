# Deploy the dashboard so recruiters can open it with one link

Follow these steps once. After that, you’ll have a public URL (e.g. `https://your-app.streamlit.app`) that recruiters can open without running any code.

---

## Step 1: Create sample data (on your machine)

You need a small copy of the dataset in the repo so the app can run on Streamlit’s servers (they don’t have your full `data/` folder).

**Option A – You have the full Olist dataset in `data/`**  
Run:
```bash
python scripts/create_sample_data.py
```
This keeps referential integrity and ensures enough repeat customers so **Retention & Loyalty** has data.

**Option B – You don’t have full data, or Retention & Loyalty is still empty**  
Run:
```bash
python scripts/create_seed_data.py
```
This generates a minimal referentially consistent sample (including repeat customers) so all three sections—Sales, Logistics, and **Retention & Loyalty**—have data.

3. Check that the **`data_sample`** folder exists and contains 9 CSV files.

---

## Step 2: Commit and push the sample data and app

1. In the project folder, run:
   ```bash
   git add data_sample/ app.py scripts/
   git status
   ```
   You should see `data_sample/` with the new CSVs and any changed files.

2. Commit and push:
   ```bash
   git commit -m "Add data_sample for Streamlit Cloud demo"
   git push
   ```
3. On GitHub, confirm that the **`data_sample`** folder and the CSVs inside it are in the repo (and that `data/` is still empty there, which is correct).

---

## Step 3: Deploy on Streamlit Community Cloud

1. Go to **https://share.streamlit.io** in your browser.
2. Sign in with **GitHub** (authorize Streamlit if asked).
3. Click **“New app”**.
4. Fill in:
   - **Repository:** `YourUsername/olist-sql-dashboard` (your GitHub repo).
   - **Branch:** `main`.
   - **Main file path:** `app.py`.
   - **App URL:** pick a short name (e.g. `olist-sql-dashboard`). You’ll get `https://olist-sql-dashboard.streamlit.app` (or similar).
5. Click **“Deploy!”**.
6. Wait a few minutes. The first run can take 2–5 minutes while it installs dependencies and loads the sample data.
7. When it’s done, you’ll see the dashboard. Copy the **URL** from the browser (e.g. `https://your-app-name.streamlit.app`).

---

## Step 4: Put the link in your README

1. Open **README.md** in your project.
2. Near the top (e.g. right under the title or the first paragraph), add a line like:
   ```markdown
   **Live dashboard:** [Open the app](https://your-app-name.streamlit.app)
   ```
   Replace `https://your-app-name.streamlit.app` with the URL you copied.
3. Save, then commit and push:
   ```bash
   git add README.md
   git commit -m "Add live dashboard link to README"
   git push
   ```

Recruiters can then open your repo, see the link, and click it to view the dashboard without running any code.

---

## If something goes wrong

- **“No data loaded” on the live app**  
  Make sure **Step 1 and Step 2** are done and that **`data_sample`** (and the CSVs inside it) are in the repo and pushed. Then in Streamlit Cloud, open your app, click **“Manage app”** (bottom right), and **“Reboot app”**.

- **App won’t start / build error**  
  In Streamlit Cloud, click **“Manage app”** and check the **Logs** for the exact error. Often it’s a missing dependency: add it to **requirements.txt**, commit, push, and the app will rebuild.

- **Charts are empty or look odd**  
  The live app uses the **sample** data (subset). For full data, run the app locally with your full `data/` folder.

- **Retention & Loyalty shows “No retention data available”**  
  The sample in the repo has no repeat customers (or broken links between orders and payments). Regenerate the sample: run `python scripts/create_seed_data.py` (no full dataset needed), then `git add data_sample/`, commit, push, and reboot the app on Streamlit Cloud.

---

## Summary

| Step | What you do |
|------|-------------|
| 1 | Run `python scripts/create_sample_data.py` (full data in `data/`) or `python scripts/create_seed_data.py` (no full data) to create `data_sample/`. |
| 2 | `git add data_sample/ app.py scripts/`, commit, push. |
| 3 | On share.streamlit.io, New app → pick repo, branch, `app.py` → Deploy. |
| 4 | Copy the app URL, add it to the README, commit and push. |

After that, recruiters can use the link in your README to open the dashboard in one click.
