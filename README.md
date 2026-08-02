# Fitness and Nutrition Expert System

> Academic Project | Artificial Intelligence | Expert Systems

## Description

An Expert System developed in Python that provides **personalized advice** on nutrition and physical training. The system utilizes production rules (IF-THEN), a forward-chaining inference engine, and an explanation module to justify every recommendation it generates.

---

## System Architecture

```text
examen/
├── main.py              ← Entry point and main orchestrator
├── knowledge_base.py    ← Knowledge base (IF-THEN rules)
├── inference_engine.py  ← Inference engine (forward chaining)
├── calculations.py      ← Core calculations: BMI, BMR, TDEE, macros
├── nutrition.py         ← Dietary plans categorized by goal
├── training.py          ← Workout routines (home/gym)
├── user_profile.py      ← User data model
├── database.py          ← Local JSON persistence
├── ui.py                ← Console interface (CLI)
├── gui.py               ← Web interface (Streamlit)
└── app_desktop.pyw      ← Native desktop interface (CustomTkinter)
