# 🎓 AI University Study Planner

**CrewAI Flow app that plans your entire study abroad journey in 10 minutes**

## What it does

Takes your study preferences and generates a complete plan with:
- 🎯 **University research** - Rankings, costs, requirements  
- 🏠 **Local living guide** - Housing, transport, daily costs
- 📅 **Timeline & budget** - Month-by-month action plan

**Saves you 300+ hours** of manual research!

## How it works

Three AI agents work together using **CrewAI Flow**:

1. **University Expert** searches for programs and requirements
2. **Local Expert** finds housing and living costs  
3. **Timeline Specialist** creates your action plan with real budget calculations

## Quick Start

```bash
git clone https://github.com/jmforduk/crew-ai.git
cd crew-ai
pip install -r requirements.txt
streamlit run university_planner_app.py
```

Set `OPENAI_API_KEY` or use free Ollama models.

## Why it's better

- ✅ **Real data** - Authentic web search and scraping
- ✅ **Current info** - Live data from university websites  
- ✅ **Complete plan** - Universities + living + timeline
- ✅ **Fast results** - 10 minutes vs 300+ hours manual

## Tech Stack

- **CrewAI Flow** - Agent orchestration
- **Streamlit** - Web interface
- **Real APIs** - Search, currency, web scraping
- **OpenAI/Ollama** - LLM flexibility

## Acknowledgments

Built with **CrewAI** by João Moura and inspired by the AI agent community including [Tony Kipkemboi](https://www.tonykipkemboi.com/)'s educational content. Special thanks to the CrewAI team for creating such a powerful multi-agent framework!

---

**Star ⭐ if this helped you plan your study abroad!**
