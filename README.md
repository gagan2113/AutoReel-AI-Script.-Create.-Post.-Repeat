# 📜 AI Product Script Generator

A **Streamlit + LangGraph (Groq API)** application to quickly generate engaging, product-focused social media scripts. The app lets you specify:

- product_name (str)
- product_description (str)
- product_benefits (list[str])
- product_image_analysis (str, optional)
- tone (str)
- primary_language (str)
- duration_seconds (int)
- platforms (list[str])
- aspect_ratios_alts (list[str])

It then creates a ready-to-use script plus platform-appropriate captions and hashtags.

---

## 🚀 Features

* **Social Media Script Generator**: Enter product details, tone, duration, platforms, language, and optional image analysis to create:

  * Final script (ready to record or post)
  * Suggested caption
  * Relevant hashtags

* **Groq LangGraph Integration**: Automatically saves generated content into a knowledge graph as nodes (topic, script) and edges (relationships).

* **Structured Output**:

  * Outline: Hook, value points, objection handling, CTA
  * Final Script: Platform-aware, tone-aligned, language-specific
  * Captions & Hashtags: Per-platform, 8–10 relevant tags

* **Streamlit UI**: User-friendly interface to input content details and view generated output.

---

## 🏗️ Project Structure

```
Geni/
├── app.py                            # Main Streamlit application
├── README.md                         # Project documentation
├── requirements.txt                   # Python dependencies
└── ... (optional config files)
```

---

## ⚙️ Installation

1️⃣ **Clone the repository**

```bash
git clone https://github.com/yourusername/Content_Generator_Bot.git
cd Content_Generator_Bot
```

2️⃣ **Create a virtual environment (recommended)**

```bash
python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows
```

3️⃣ **Install dependencies**

```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Variables

Create a `.env` file in the root directory and add:

```
GROQ_API_KEY=your_groq_api_key
GROQ_PROJECT=your_groq_project_id
LLM_API_KEY=your_preferred_llm_key   # Optional if using external LLMs
```

---

## ▶️ Usage

Run the Streamlit app:

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501` to access the UI.

---

## 💡 How It Works

1. **User Input**: Product details, benefits, tone, language, duration, platforms, aspect ratios.
2. **Script Generation**: LLM prompts craft an outline, final script, and per-platform captions/hashtags.
3. **LangGraph Storage**: If enabled, the app calls the Groq API to create nodes and edges linking the topic to the generated script.
4. **Output Display**: Script and hashtags are shown in a clean Streamlit interface.

---

## 🔄 Modes of Operation

Always generates both outline and final script, plus per-platform captions and hashtags.

Toggle modes by changing the prompt variable in `LangGraph_Groq_Streamlit_App.py`.

---

## 🛠️ Tech Stack

* **Python 3.9+**
* **Streamlit**: Front-end UI
* **Groq API**: LangGraph storage of nodes and edges
* **Optional LLM**: Replace the deterministic script builder with your favorite LLM (e.g., OpenAI, Anthropic) for more creativity.

---

## 📌 Example Prompt for Simple Script

Example fields: product_name="Acme Smart Bottle", tone="Humorous", duration_seconds=45, platforms=["TikTok", "Instagram"], aspect_ratios_alts=["9:16 (vertical)"]

---

## 🧩 Customization

* **Replace pseudo-functions** `groq_create_node` and `groq_create_edge` with real API calls to the Groq LangGraph endpoint.
* Integrate your own **LLM provider** to enhance creativity.
* Adjust the **speaking rate** or **word count** estimation in `build_script()`.

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

