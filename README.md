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

It then creates a ready-to-use script plus platform-appropriate captions and hashtags. After generating the script, the app asks for your confirmation to create a video; upon confirmation it calls a separate video API module.

After a video is generated, the app asks: "Do you want to upload this video?" If you confirm, you can provide a caption and hashtags and upload to selected platforms (TikTok, YouTube, LinkedIn, Facebook, Twitter/X).

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
* **Reel History Page**: Dedicated page under the sidebar (Reel History) to browse, preview, and save reels. Supports saving remote URLs or downloading a local copy to `reels/…` and storing a lightweight record in MongoDB.
* **Explicit Confirmation Flow**: After script generation, the app asks: "Can I proceed to create the video?" You can confirm to generate the video or regenerate the script.
* **Post-Video Upload Flow**: After video creation, the app asks: "Do you want to upload this video?" Provide caption and hashtags, choose platforms, and upload.
* **Pluggable Video API Module**: All video logic lives in `src/video_api.py` so you can swap providers without touching the main app.
* **Modular Uploaders**: Each platform has its own module under `src/uploaders/`. Credentials are read from `.env`.

---

## 🏗️ Project Structure

```
AutoReel AI/
├── app.py                   # Main Streamlit application (UI + confirmation loop)
├── README.md                # Project documentation
├── requirements.txt         # Python dependencies
├── src/
│   ├── workflow.py          # Script & captions generation via LangGraph + Groq
│   ├── groq_client.py       # Groq chat API wrapper
│   ├── prompts.py           # Prompt builders
│   └── video_api.py         # Isolated video generation API wrapper
│   └── uploaders/
│       ├── __init__.py              # Exports upload router and supported platforms
│       ├── router.py                # Dispatch upload to selected platforms
│       ├── utils.py                 # Helpers and UploadResult type
│       ├── tiktok_upload.py         # TikTok uploader (stub)
│       ├── youtube_upload.py        # YouTube uploader (stub)
│       ├── linkedin_upload.py       # LinkedIn uploader (stub)
│       ├── facebook_upload.py       # Facebook uploader (stub)
│       └── twitter_upload.py        # Twitter/X uploader (stub)
└── tests/
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

Required for script generation:

```
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.1-8b-instant
GROQ_API_URL=https://api.groq.com/openai/v1/chat/completions
GROQ_TIMEOUT=60
```

Optional for video generation (if omitted, a mock URL is returned for dev):

```
VIDEO_API_BASE_URL=https://your-video-provider.example.com
VIDEO_API_KEY=your_video_api_key
VIDEO_API_TIMEOUT=60

# Platform upload credentials (fill as needed)
# TikTok
TIKTOK_ACCESS_TOKEN=

# YouTube
YOUTUBE_API_KEY=
YOUTUBE_OAUTH_TOKEN=

# LinkedIn
LINKEDIN_ACCESS_TOKEN=

# Facebook
FACEBOOK_PAGE_ACCESS_TOKEN=
FACEBOOK_PAGE_ID=

# Twitter/X
TWITTER_API_KEY=
TWITTER_API_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_SECRET=
```

---

## ▶️ Usage

Run the Streamlit app:

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501` to access the UI.

In the sidebar, click "Reel History" to open the history page.

---

## 💡 How It Works

1. **User Input**: Product details, benefits, tone, language, duration, platforms, aspect ratios.
2. **Script Generation**: LLM prompts craft an outline, final script, and per-platform captions/hashtags.
3. **Output Display**: Script and hashtags are shown in a clean Streamlit interface.
4. **Confirmation Prompt**: The app asks: "Can I proceed to create the video?" with two buttons:
  - Yes → Calls `video_api.generate_video(...)` using only the Final Script section.
  - No  → Regenerates the script and repeats the confirmation step.

5. **Upload Confirmation**: If a direct `video_url` is returned:
  - The app asks: "Do you want to upload this video?"
  - Choose platforms (TikTok, YouTube, LinkedIn, Facebook, Twitter/X), enter a caption and comma-separated hashtags.
  - The app uploads via `src/uploaders/router.py` which delegates to per-platform modules.

---

## � Swapping the Video Provider

Update `src/video_api.py` to integrate your preferred provider. Keep the function signature for `generate_video(...)` the same to avoid touching the app. The module currently posts to `VIDEO_API_BASE_URL + "/generate"` with the script and metadata and normalizes the response to:

```
{
  "status": "success" | "error",
  "video_url": "https://...",   # if available
  "job_id": "abc123",           # if asynchronous
  "message": "human-readable details"
}
```

---

## 🛠️ Tech Stack

* **Python 3.9+**
* **Streamlit**: Front-end UI
* **Groq API**: LLM completions
* **Video API**: Pluggable; defined in `src/video_api.py`
* **Uploaders**: Modular per-platform, in `src/uploaders/` (stubs return simulated success until real APIs are wired).

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

