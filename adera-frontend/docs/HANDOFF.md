# Moving this into the team repository

The active Adera frontend lives in `adera-frontend/`. Never push to `main` or `develop` directly.

## 1. Check everything first

In this project's folder:

```bash
npm install
npm test
npm run lint
npm run build
```

All four should finish without errors.

## 2. Get the team repository

```bash
cd ~/Projects
git clone https://github.com/Ahmedmkofficial/adera
cd adera
git checkout develop
git pull
git checkout -b feature/frontend
```

If `feature/frontend` already exists on GitHub, use `git checkout feature/frontend` instead of `-b`.

## 3. Copy your project in

Copy **everything inside** this frontend project into `adera/adera-frontend/` **except** `node_modules`, `dist`, and `.git`.

PowerShell:

```powershell
cd ~/Projects
Get-ChildItem adera-frontend -Force -Exclude node_modules,dist,.git | Copy-Item -Destination adera/adera-frontend -Recurse -Force
```

(If `adera/adera-frontend` does not exist yet, create it first.)

Make sure `.env` is **not** copied (only `.env.example`).

## 4. Check it works in its new home

```bash
cd ~/Projects/adera/adera-frontend
npm install
npm run dev
```

## 5. Save and share

```bash
cd ~/Projects/adera
git status
git add adera-frontend
git commit -m "Add Adera frontend: customer and analyst interfaces"
git push -u origin feature/frontend
```

Then on GitHub, open a **Pull Request** from `feature/frontend` into `develop` and tell the team.

## 6. Connecting to the backend later

1. Ahmed's API runs (for example on port 8000).
2. In `adera-frontend/`, copy `.env.example` to `.env` and set `VITE_USE_MOCK=false`.
3. Compare `docs/API_CONTRACT.md` with the real responses. Differences are fixed in **one** file: `src/services/api.js`.
4. Ask Tigiste to run the full flow: payment, alert, investigation, case, decision.
