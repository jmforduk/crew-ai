# university_planner_app.py
# Complete CrewAI Flow version with sidebar inputs and right flyout notifications
# UI: Streamlit with selectors in left sidebar, flyout notifications on right
# Orchestration: CrewAI Flow (not Crew/Task)
# Tools: Your existing search_tools.py, browser_tools.py, calculator_tools.py

import streamlit as st
st.set_page_config(page_icon="🎓", layout="wide")  # Must be first Streamlit call

import os
import sys
import re
import datetime
from textwrap import dedent
from typing import Dict, Any, Optional

# CrewAI core
from crewai import Agent, LLM, Task, Crew
from crewai.flow.flow import Flow, start, listen
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# Use your existing tools
TOOLS_OK = True
try:
    from search_tools import SearchTools
    from browser_tools import BrowserTools  
    from calculator_tools import CalculatorTools
except Exception as e:
    TOOLS_OK = False
    TOOLS_IMPORT_ERROR = str(e)

# ----------------------------
# Right flyout notifications
# ----------------------------
FLYOUT_CSS = """
<style>
#flyout-container {
  position: fixed;
  top: 80px;
  right: 20px;
  width: 360px;
  max-width: 88vw;
  z-index: 1000;
}
.flyout-card {
  background: #111827;
  color: #f9fafb;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.35);
  padding: 12px 14px;
  margin-bottom: 10px;
  border: 1px solid rgba(255,255,255,0.08);
  font-size: 0.92rem;
  animation: flyInRight 0.3s ease-out;
}
.flyout-card.success { border-left: 6px solid #10b981; }
.flyout-card.info    { border-left: 6px solid #3b82f6; }
.flyout-card.warn    { border-left: 6px solid #f59e0b; }
.flyout-card.error   { border-left: 6px solid #ef4444; }
.flyout-title { font-weight: 700; margin-bottom: 4px; }
.flyout-body { opacity: 0.95; line-height: 1.35; }
@keyframes flyInRight {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}
.main-header { 
    padding: 1rem 0; 
    text-align: center; 
    background: linear-gradient(90deg,#667eea,#764ba2); 
    color: white; 
    border-radius: 10px; 
    margin-bottom: 1.2rem; 
}
</style>
<div id="flyout-container"></div>
<script>
function addFlyout(message, level){
  const c = document.getElementById('flyout-container');
  if(!c) return;
  const card = document.createElement('div');
  card.className = 'flyout-card ' + (level || 'info');
  const title = document.createElement('div');
  title.className = 'flyout-title';
  title.textContent = (level || 'Info').toUpperCase();
  const body = document.createElement('div');
  body.className = 'flyout-body';
  body.textContent = message;
  card.appendChild(title);
  card.appendChild(body);
  c.appendChild(card);
  setTimeout(()=>{ card.style.transition = 'opacity 0.5s ease'; card.style.opacity = 0; }, 4500);
  setTimeout(()=>{ if(card.parentNode){ card.parentNode.removeChild(card); } }, 5200);
}
window.addEventListener('message', (ev)=>{
  if(ev.data && ev.data.type === 'flyout'){
    addFlyout(ev.data.message, ev.data.level);
  }
});
</script>
"""

st.markdown(FLYOUT_CSS, unsafe_allow_html=True)

def flyout(message: str, level: str = 'info'):
    st.markdown(
        f"""
        <script>
        window.postMessage({{ type: 'flyout', message: {message!r}, level: {level!r} }}, '*');
        </script>
        """,
        unsafe_allow_html=True,
    )

# ----------------------------
# Encoding helpers
# ----------------------------
def safe_decode(data, fallback_encoding='cp1252'):
    if data is None:
        return ""
    if isinstance(data, str):
        return data
    if isinstance(data, bytes):
        for encoding in ('utf-8', fallback_encoding, 'latin1'):
            try:
                return data.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                continue
        return data.decode('utf-8', errors='ignore')
    return str(data)

# ----------------------------
# LLM configuration
# ----------------------------
def get_llm_config() -> Optional[LLM]:
    # OpenAI
    openai_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_APIKEY") or os.getenv("OPENAI")
    if openai_key:
        try:
            flyout("OpenAI API key detected - using gpt-4o-mini", "success")
            return LLM(model="openai/gpt-4o-mini", api_key=openai_key)
        except Exception:
            pass

    # Ollama fallback: try common local models
    ollama_models = [
        "llama3.2:3b",
        "llama3.1:8b", 
        "mistral:7b",
        "deepseek-r1:latest",
        "qwen2.5:7b"
    ]
    base_url = "http://localhost:11434"
    for model in ollama_models:
        try:
            llm = LLM(model=f"ollama/{model}", base_url=base_url)
            flyout(f"Using Ollama model: {model}", "success")
            return llm
        except Exception:
            continue

    flyout("No LLM configured - using CrewAI default", "warn")
    return None

SYSTEM_LLM = get_llm_config()

# ----------------------------
# Create Proper Tool Instances
# ----------------------------
class SearchInput(BaseModel):
    query: str = Field(..., description="Search query")

class SearchTool(BaseTool):
    name: str = "search_internet"
    description: str = "Search the internet for information"
    args_schema: type[BaseModel] = SearchInput

    def _run(self, query: str) -> str:
        try:
            return SearchTools.search_internet(query)
        except Exception as e:
            return f"Search failed: {str(e)}"

class BrowserInput(BaseModel):
    url: str = Field(..., description="URL to scrape")

class BrowserTool(BaseTool):
    name: str = "scrape_website"
    description: str = "Scrape and summarize a website"
    args_schema: type[BaseModel] = BrowserInput

    def _run(self, url: str) -> str:
        try:
            return BrowserTools.scrape_and_summarize_website(url)
        except Exception as e:
            return f"Website scraping failed: {str(e)}"

class CalculatorInput(BaseModel):
    expression: str = Field(..., description="Mathematical expression to calculate")

class CalculatorTool(BaseTool):
    name: str = "calculate"
    description: str = "Perform calculations"
    args_schema: type[BaseModel] = CalculatorInput

    def _run(self, expression: str) -> str:
        try:
            return CalculatorTools.calculate_expression(expression)
        except Exception as e:
            return f"Calculation failed: {str(e)}"

# Create tool instances
search_tool = SearchTool()
browser_tool = BrowserTool()
calculator_tool = CalculatorTool()

# ----------------------------
# Agents
# ----------------------------
def make_university_selection_agent(system_llm: Optional[LLM]) -> Agent:
    return Agent(
        role="University Selection Research Expert",
        goal="Research rankings, costs, admission requirements, deadlines, and program specifics.",
        backstory=(
            "Senior education consultant with 15 years of experience helping international students. "
            "Expert in program rankings, admissions, international requirements, and scholarships."
        ),
        tools=[search_tool, browser_tool],
        verbose=True,
        allow_delegation=False,
        llm=system_llm
    )

def make_local_expert_agent(system_llm: Optional[LLM]) -> Agent:
    return Agent(
        role="Local City Student Life Expert", 
        goal="Provide cost of living, housing, transport, and cultural integration with specific prices and places.",
        backstory=(
            "Local expert with insider knowledge of major university cities. Provides exact prices and practical tips."
        ),
        tools=[search_tool, browser_tool],
        verbose=True,
        allow_delegation=False,
        llm=system_llm
    )

def make_travel_timeline_agent(system_llm: Optional[LLM]) -> Agent:
    return Agent(
        role="Study Abroad Travel Timeline Specialist",
        goal="Create a month-by-month plan with dates, visa steps, budget totals, and logistics.",
        backstory=(
            "Specialist in international study timelines and logistics, visas, flights, and budget planning."
        ),
        tools=[search_tool, browser_tool, calculator_tool],
        verbose=True,
        allow_delegation=False,
        llm=system_llm
    )

# ----------------------------
# Flow Orchestration
# ----------------------------
class StudyPlannerFlow(Flow):
    def __init__(self, llm: Optional[LLM] = None):
        super().__init__()
        self.llm = llm

    @start()
    def collect_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        flyout("Processing inputs and preparing flow...", "info")
        
        # Normalize UI inputs to a consistent context
        cities_val = inputs.get("cities", "")
        if isinstance(cities_val, str):
            city_list = [c.strip() for c in cities_val.split(";") if c.strip()]
        elif isinstance(cities_val, list):
            city_list = [str(c).strip() for c in cities_val if str(c).strip()]
        else:
            city_list = []

        daterange = inputs.get("daterange")
        if isinstance(daterange, (list, tuple)) and len(daterange) == 2:
            time_range = (str(daterange[0]), str(daterange[1]))
        else:
            time_range = (str(datetime.date.today()), str(datetime.date.today()))

        return {
            "origin": inputs.get("origin", "").strip(),
            "cities": city_list,
            "daterange": time_range,
            "interests": inputs.get("interests", "").strip(),
            "subject": inputs.get("subject", "").strip(),
            "study_level": inputs.get("study_level", "").strip(),
            "budget_range": inputs.get("budget_range", "").strip(),
            "advanced": inputs.get("advanced", {})
        }

    @listen("collect_inputs")
    def university_research(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        flyout("University research agent is analyzing programs...", "info")
        
        # Create agent and task
        agent = make_university_selection_agent(self.llm)
        
        task_description = f"""
        CRITICAL: Provide an 800+ word university research report for subject '{ctx['subject']}' and study level '{ctx['study_level']}'.
        Cities to analyze: {', '.join(ctx['cities']) or 'N/A'}. Origin: {ctx['origin']}. Period: {ctx['daterange']}.
        Include: program rankings, admission requirements with exact thresholds, tuition by year, deadlines,
        scholarships, and employment outcomes. Use search_internet tool to find current information.

        Student interests: {ctx.get('interests') or 'none provided'}.
        Budget range: {ctx.get('budget_range') or 'not specified'}.
        """
        
        task = Task(
            description=dedent(task_description).strip(),
            agent=agent,
            expected_output="Comprehensive 800+ word university research report"
        )
        
        # Execute task using a single-agent crew
        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        result = crew.kickoff()
        
        flyout("University research completed successfully", "success")
        
        return {
            "inputs": ctx,
            "university_report": str(result)
        }

    @listen("university_research") 
    def local_living_guide(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        flyout("Local expert is compiling living guide...", "info")
        
        inputs = ctx["inputs"]
        uni = ctx["university_report"]
        
        # Create agent and task
        agent = make_local_expert_agent(self.llm)
        
        task_description = f"""
        Using the selected universities and insights below, write a 700+ word local living guide.
        Subject: {inputs['subject']}, Level: {inputs['study_level']}, Origin: {inputs['origin']}.
        Period: {inputs['daterange']}. Cities: {', '.join(inputs['cities']) or 'N/A'}.

        SOURCE REPORT:
        {uni}

        Include: housing options with exact costs, neighborhood tips, transport passes and monthly costs,
        food costs, utilities, mobile/internet, textbooks, entertainment, seasonal prep, student clubs,
        cultural integration resources, safety and healthcare access, local job options.
        Use search_internet and scrape_website tools for current local information.
        """
        
        task = Task(
            description=dedent(task_description).strip(),
            agent=agent,
            expected_output="Comprehensive 700+ word local living guide"
        )
        
        # Execute task using a single-agent crew
        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        result = crew.kickoff()
        
        flyout("Local living guide completed", "success")
        
        return {
            "inputs": inputs,
            "university_report": uni,
            "local_guide": str(result)
        }

    @listen("local_living_guide")
    def timeline_and_budget(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        flyout("Timeline specialist is building your plan...", "warn")
        
        inputs = ctx["inputs"]
        uni = ctx["university_report"]
        local = ctx["local_guide"]
        
        # Create agent and task
        agent = make_travel_timeline_agent(self.llm)
        
        task_description = f"""
        Create a 1000+ word month-by-month timeline and budget for {inputs['daterange']}, 
        subject '{inputs['subject']}', level '{inputs['study_level']}'.

        SOURCE REPORTS:
        - University research:
        {uni}

        - Local living guide:
        {local}

        Include: standardized test dates, application deadlines, deposit timings, visa steps with dates,
        flight booking windows, arrival setup, semester milestones. Provide cost totals (pre-departure, setup,
        monthly, emergency fund) and a program-length projection (2-year Masters or 4-year Bachelors).
        Use calculate tool for budget calculations and search_internet for timeline information.
        """
        
        task = Task(
            description=dedent(task_description).strip(),
            agent=agent,
            expected_output="Comprehensive 1000+ word timeline and budget plan"
        )
        
        # Execute task using a single-agent crew
        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        result = crew.kickoff()
        
        flyout("Timeline and budget plan completed!", "success")
        
        return {
            "university_report": uni,
            "local_guide": local,
            "timeline_plan": str(result)
        }

# ----------------------------
# Tool availability check
# ----------------------------
if not TOOLS_OK:
    st.error(f"Cannot import tools: {TOOLS_IMPORT_ERROR}")
    st.info("Make sure search_tools.py, browser_tools.py, and calculator_tools.py are in the same folder.")
    flyout(f"Tool import failed: {TOOLS_IMPORT_ERROR}", "error")
    st.stop()
else:
    flyout("Tools successfully wrapped as CrewAI BaseTool instances", "success")

# ----------------------------
# Header
# ----------------------------
st.markdown('<div class="main-header"><h1>🎓 AI University Study Planner — CrewAI Flow</h1><p>Comprehensive planning with CrewAI Flow orchestration and flyout notifications</p></div>', unsafe_allow_html=True)

# ----------------------------
# Sidebar Form (moved back to left pane)
# ----------------------------
today = datetime.date.today()
default_end = today + datetime.timedelta(days=365)

with st.sidebar:
    st.header("Plan Your Study Abroad")

    location = st.text_input("Current Location", placeholder="Mumbai, India / London, UK / San Francisco, USA")
    cities = st.text_input("Target Study Destinations (separate by ;)", placeholder="London, UK; Toronto, Canada; Sydney, Australia")

    major_category = st.selectbox(
        "Major Category",
        [
            "STEM (Science, Tech, Engineering, Math)",
            "Business & Economics",
            "Arts & Humanities",
            "Social Sciences",
            "Health & Medicine",
            "Law & Legal Studies",
            "Education & Teaching",
            "Creative Arts & Design",
        ],
    )

    field_map = {
        "STEM (Science, Tech, Engineering, Math)": [
            "Computer Science / Software Engineering",
            "Data Science / AI",
            "Mechanical Engineering",
            "Electrical & Electronics",
            "Civil / Environmental Engineering",
            "Biotechnology / Bioengineering",
            "Chemistry / Chemical Engineering",
            "Physics / Materials Science",
            "Mathematics / Statistics",
            "Cybersecurity / Information Systems",
        ],
        "Business & Economics": [
            "Business Administration (MBA)",
            "Finance / Investment Banking",
            "Marketing / Digital Marketing",
            "International Business",
            "Economics / Econometrics",
            "Supply Chain & Operations",
            "Entrepreneurship & Innovation",
            "Accounting / Financial Management",
        ],
        "Arts & Humanities": [
            "English Literature / Creative Writing",
            "History / Archaeology",
            "Philosophy / Ethics",
            "Languages / Linguistics",
            "Media Studies / Communications",
            "Art History / Criticism",
            "Religious Studies",
            "Cultural Studies",
        ],
        "Social Sciences": [
            "Psychology / Behavioral Sciences",
            "International Relations / Diplomacy",
            "Sociology / Anthropology",
            "Political Science / Public Policy",
            "Criminal Justice / Criminology",
            "Social Work / Community Development",
            "Geography / Urban Planning",
        ],
        "Health & Medicine": [
            "Medicine (MBBS/MD)",
            "Nursing / Healthcare",
            "Dentistry",
            "Pharmacy / Pharmaceutical Sciences",
            "Public Health / Epidemiology",
            "Physical Therapy / Rehabilitation",
            "Veterinary Medicine",
            "Biomedical Sciences",
        ],
        "Law & Legal Studies": [
            "Law (LLB/JD)",
            "International Law",
            "Corporate / Commercial Law",
            "Human Rights Law",
            "Environmental Law",
            "Intellectual Property Law",
        ],
        "Education & Teaching": [
            "Education / Teaching",
            "Educational Psychology",
            "Curriculum & Instruction",
            "Special Education",
            "Educational Leadership / Administration",
        ],
        "Creative Arts & Design": [
            "Graphic Design / Visual Arts",
            "Architecture / Urban Design",
            "Film / Media Production",
            "Music / Performing Arts",
            "Fashion Design",
            "Industrial / Product Design",
        ],
    }

    specific_field = st.selectbox("Specific Field", field_map.get(major_category, ["General"]))
    study_level = st.selectbox("Study Level", ["Bachelor's", "Master's", "PhD / Doctoral", "Exchange Program", "Certificate / Diploma"])
    daterange = st.date_input("Intended Study Period", value=(today, default_end), min_value=today, help="Select start and end dates")
    budget_range = st.selectbox("Annual Budget Range (USD)", ["Under 25,000", "25,000–50,000", "50,000–75,000", "75,000–100,000", "100,000+", "Need scholarship/financial aid"])
    interests = st.text_area("Additional Profile Preferences", placeholder="Language preferences, climate, career goals, accommodation preferences, target companies, etc.", height=100)

    with st.expander("Advanced Preferences"):
        advanced_prefs = {
            "work_opportunities": st.checkbox("Interested in part-time work opportunities"),
            "research_focus": st.checkbox("Prefer research-oriented programs"),
            "exchange_programs": st.checkbox("Interested in exchange/study abroad options"),
            "postgrad_work": st.checkbox("Post-graduation work visa important"),
        }

    submitted = st.button("Create Comprehensive Study Plan", use_container_width=True)

st.divider()

# ----------------------------
# Flow Execution
# ----------------------------
def run_flow_pipeline():
    # Prepare flow inputs
    comprehensive_subject = f"{specific_field} — {study_level}"
    flow_inputs = {
        "origin": location,
        "cities": cities,
        "daterange": daterange,
        "interests": interests,
        "subject": comprehensive_subject,
        "study_level": study_level,
        "budget_range": budget_range,
        "advanced": advanced_prefs
    }

    status = st.status("CrewAI Flow running...", state="running", expanded=True)
    progress = st.progress(0)

    try:
        flow = StudyPlannerFlow(llm=SYSTEM_LLM)

        # Stage 1: Collect inputs
        progress.progress(10)
        status.update(label="Preparing inputs...", state="running")
        ctx_inputs = flow.collect_inputs(flow_inputs)

        # Stage 2: University research
        progress.progress(35)
        status.update(label="University research in progress...", state="running")
        ctx_uni = flow.university_research(ctx_inputs)

        # Stage 3: Local living guide
        progress.progress(65)
        status.update(label="Compiling local living guide...", state="running")
        ctx_local = flow.local_living_guide(ctx_uni)

        # Stage 4: Timeline and budget
        progress.progress(85)
        status.update(label="Building timeline and budget...", state="running")
        final_ctx = flow.timeline_and_budget(ctx_local)

        # Assemble result
        result_text = (
            "## University Research\n\n" + safe_decode(final_ctx["university_report"]) +
            "\n\n---\n\n## Local Living Guide\n\n" + safe_decode(final_ctx["local_guide"]) +
            "\n\n---\n\n## Timeline & Budget Plan\n\n" + safe_decode(final_ctx["timeline_plan"])
        )

        progress.progress(100)
        status.update(label="Flow complete ✅", state="complete", expanded=False)
        flyout("Complete study plan generated successfully!", "success")
        return result_text

    except Exception as e:
        progress.progress(100)
        status.update(label="Flow error ❌", state="error", expanded=True)
        flyout(f"Flow execution failed: {str(e)}", "error")
        return f"Error: {e}"

# ----------------------------
# Main execution trigger
# ----------------------------
if submitted:
    if not all([location, cities, interests]):
        st.error("Please fill in Current Location, Target Destinations, and Additional Profile Preferences.")
        flyout("Please complete all required fields", "error")
    else:
        st.info(f"Planning Summary — Field: {specific_field} ({study_level}) | Destinations: {cities} | Budget: {budget_range} | Period: {daterange[0]} to {daterange[1]}")
        flyout(f"Starting plan for {specific_field} ({study_level})", "info")
        
        result_md = run_flow_pipeline()

        st.markdown("---")
        st.subheader(f"Your Comprehensive {specific_field} Study Plan", anchor=False)
        
        if result_md and "Error:" not in result_md:
            st.markdown(result_md)
            
            # Download button
            try:
                result_bytes = result_md.encode("utf-8")
                st.download_button(
                    "📥 Download Study Plan",
                    data=result_bytes,
                    file_name=f"{specific_field.lower().replace(' ', '-')}_study-plan_{datetime.date.today().strftime('%Y-%m-%d')}.md",
                    mime="text/markdown"
                )
                flyout("Study plan ready for download", "success")
            except Exception:
                st.info("Download not available.")
                
            # Regenerate button
            if st.button("🔄 Regenerate Plan"):
                flyout("Regenerating study plan...", "info")
                st.rerun()
        else:
            st.error("Unable to generate plan. Check configuration (LLM/tools) and try again.")
            flyout("Plan generation failed - check configuration", "error")
else:
    st.info("Configure your study abroad preferences in the left sidebar and click the button to generate your comprehensive plan.")
    flyout("Welcome! Fill out the form on the left to get started", "info")