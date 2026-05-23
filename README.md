# AutoDash — Automatic Dashboard Generator
#### Video Demo: <https://youtu.be/p3fKThUgjhU>
#### Description:

## What is AutoDash?

AutoDash is a web application that automatically generates an
interactive dashboard from any CSV or Excel file. The user simply
uploads a file, and the application instantly produces KPI cards,
interactive charts, and a data table — with no configuration required.

The goal was to make data visualization accessible to anyone, even
people with no technical background. Instead of spending hours in
Excel or learning a BI tool, AutoDash gives you a full dashboard
in seconds.

## Files

### `app.py`
This is the main Flask application. It handles two routes:
- `GET /` renders the main HTML page.
- `POST /upload` receives the uploaded file, loads it with Pandas,
detects the data context, computes KPIs, generates Plotly charts,
and returns everything as JSON.

The file also contains the `detect_ctx()` function, which scans
the column names of the uploaded file and matches them against
keyword lists for five domains: sales, HR, finance, logistics,
and insurance claims. This is the core intelligence of AutoDash —
it allows the dashboard to automatically adapt its labels, colors,
and titles depending on what kind of data it receives.

The `load_file()` function handles both CSV and Excel formats,
and tries multiple encodings (UTF-8, Latin-1, CP1252) to avoid
errors with files that contain accented characters.

The `fmt()` function formats large numbers for display — for
example, 1,245,780 becomes 1.2M, making the KPI cards clean
and readable.

### `templates/index.html`
This is the entire frontend of the application — HTML, CSS and
JavaScript in a single file. It contains three views managed by
JavaScript: the upload page, a loading screen, and the dashboard.

The design is inspired by modern BI tools like Google Looker Studio.
It features a dark sidebar, a white topbar with the filename, four
colored KPI cards at the top, and a two-column layout with charts
on the left and a data table on the right.

The drag-and-drop functionality is implemented in vanilla JavaScript
using the HTML5 FileReader API and the Fetch API to send the file
to the Flask backend without reloading the page.

Plotly.js is loaded from a CDN and used to render the charts
returned by the server as JSON.

### `requirements.txt`
Lists the Python dependencies: Flask, Pandas, Plotly, openpyxl
and xlrd. The user can install all of them with a single command:
`python -m pip install -r requirements.txt`

## Design Choices

One important decision was to do all chart generation on the
server side using Plotly's Python library, rather than sending
raw data to the frontend and building charts in JavaScript.
This approach means the frontend only needs to call
`Plotly.newPlot()` with the JSON received from the server,
which keeps the frontend simple and the logic centralized.

Another choice was to keep the entire frontend in a single HTML
file instead of splitting it into separate CSS and JS files.
For a project of this size, this makes deployment simpler —
there is only one template to maintain.

The automatic context detection uses simple keyword matching
rather than machine learning. This was a deliberate choice:
it is fast, transparent, and works reliably for the most common
use cases without requiring any training data.

## Technologies Used

- **Python 3** — backend logic
- **Flask** — web framework
- **Pandas** — data loading and processing
- **Plotly** — interactive chart generation
- **openpyxl / xlrd** — Excel file support
- **HTML / CSS / JavaScript** — frontend (no framework)
- **Plotly.js** — chart rendering in the browser