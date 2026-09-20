# Gem City Data Model Lab

This interactive case asks students to redesign a fragile order-to-cash export for the fictional Gem City Office Supply. The app guides students through grain, anomalies, normalization, E-R relationships, and REA modeling. It does not require a login and does not collect names or other identifying information.

## Run locally

```bash
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

## Run the checks

```bash
python -m unittest discover -s tests -v
python -m py_compile streamlit_app.py gem_city_data_model_lab/*.py
```

Student progress is stored in a compact validated `progress` parameter in the page URL. It preserves the current step, submitted work, unfinished selections, and the student's randomized question order. Students can refresh or bookmark the current URL and resume, while **Start over** replaces the saved state with a fresh activity. Navigation to a new step also resets the Streamlit content area to the top.

The visual theme uses the University of Dayton's public red, navy, and turquoise color system. No university logo or protected mark is included.
