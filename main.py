# 🎓 AI University Study Planner — CrewAI Agents
# Comprehensive planning with CrewAI agents orchestration

import streamlit as st
st.set_page_config(page_icon="🎓", layout="wide")

import os
import sys
import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Add current directory to path for tool imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# CrewAI imports
from crewai import LLM, Agent, Crew, Task
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# Import tools first (they should be in the same directory as main.py)
TOOLS_OK = True
TOOLS_IMPORT_ERROR = ""
try:
    from search_tools import SearchTools
    from browser_tools import BrowserTools
    from calculator_tools import CalculatorTools
    st.success("✅ All tool modules loaded successfully")
except Exception as e:
    TOOLS_OK = False
    TOOLS_IMPORT_ERROR = str(e)
    st.error(f"❌ Cannot import tools: {TOOLS_IMPORT_ERROR}")

# Tool wrapper classes
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

# Planning class - Simplified approach without Flow
class StudyPlannerCrew:
    def __init__(self, llm: Optional[LLM] = None):
        self.llm = llm
        self.search_tool = SearchTool()
        self.browser_tool = BrowserTool()
        self.calculator_tool = CalculatorTool()

    def make_university_agent(self) -> Agent:
        return Agent(
            role="University Selection Research Expert",
            goal="Research rankings, costs, admission requirements, deadlines, and program specifics.",
            backstory=(
                "Senior education consultant with 15 years of experience helping international students. "
                "Expert in program rankings, admissions, international requirements, and scholarships."
            ),
            tools=[self.search_tool, self.browser_tool],
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

    def make_local_agent(self) -> Agent:
        return Agent(
            role="Local City Student Life Expert",
            goal="Provide cost of living, housing, transport, and cultural integration with specific prices and places.",
            backstory=(
                "Local expert with insider knowledge of major university cities. Provides exact prices and practical tips."
            ),
            tools=[self.search_tool, self.browser_tool],
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

    def make_timeline_agent(self) -> Agent:
        return Agent(
            role="Study Abroad Travel Timeline Specialist",
            goal="Create a month-by-month plan with dates, visa steps, budget totals, and logistics.",
            backstory=(
                "Specialist in international study timelines and logistics, visas, flights, and budget planning."
            ),
            tools=[self.search_tool, self.browser_tool, self.calculator_tool],
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

    def process_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process and normalize inputs"""
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

    def university_research(self, ctx: Dict[str, Any]) -> str:
        """Research universities"""
        agent = self.make_university_agent()
        cities_str = ', '.join(ctx['cities']) if ctx['cities'] else 'N/A'
        
        task_description = f"""
        CRITICAL: Provide an 800+ word university research report for subject '{ctx['subject']}' 
        and study level '{ctx['study_level']}'. Cities to analyze: {cities_str}. 
        Origin: {ctx['origin']}. Study period: {ctx['daterange']}.
        Budget range: {ctx['budget_range']}.
        
        Include: program rankings, admission requirements with exact thresholds, tuition by year, 
        deadlines, scholarships, and employment outcomes. Use current 2025 information.
        """
        
        task = Task(
            description=task_description.strip(),
            agent=agent,
            expected_output="Comprehensive 800+ word university research report"
        )
        
        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        result = crew.kickoff()
        return str(result)

    def local_living_guide(self, ctx: Dict[str, Any], uni_report: str) -> str:
        """Create local living guide"""
        agent = self.make_local_agent()
        cities_str = ', '.join(ctx['cities']) if ctx['cities'] else 'N/A'
        
        task_description = f"""
        Using the university research below, write a 700+ word local living guide.
        Subject: {ctx['subject']}, Level: {ctx['study_level']}, Origin: {ctx['origin']}.
        Period: {ctx['daterange']}. Cities: {cities_str}.
        Budget range: {ctx['budget_range']}.
        
        UNIVERSITY RESEARCH: {uni_report}
        
        Include: housing options with exact costs, neighborhood tips, transport passes and monthly costs, 
        food costs, utilities, mobile/internet, textbooks, entertainment, cultural tips.
        """
        
        task = Task(
            description=task_description.strip(),
            agent=agent,
            expected_output="Comprehensive 700+ word local living guide"
        )
        
        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        result = crew.kickoff()
        return str(result)

    def timeline_and_budget(self, ctx: Dict[str, Any], uni_report: str, local_guide: str) -> str:
        """Create timeline and budget"""
        agent = self.make_timeline_agent()
        
        task_description = f"""
        Create a 1000+ word month-by-month timeline and budget for {ctx['daterange']}, 
        subject '{ctx['subject']}', level '{ctx['study_level']}', budget range '{ctx['budget_range']}'.
        
        UNIVERSITY RESEARCH: {uni_report}
        LOCAL LIVING GUIDE: {local_guide}
        
        Include: standardized test dates, application deadlines, deposit timings, visa steps with dates, 
        flight booking windows, arrival setup, semester milestones, complete budget breakdown.
        """
        
        task = Task(
            description=task_description.strip(),
            agent=agent,
            expected_output="Comprehensive 1000+ word timeline and budget plan"
        )
        
        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        result = crew.kickoff()
        return str(result)

    def generate_plan(self, inputs: Dict[str, Any]) -> Dict[str, str]:
        """Generate complete study plan"""
        # Process inputs
        ctx = self.process_inputs(inputs)
        
        # Step 1: University Research
        university_report = self.university_research(ctx)
        
        # Step 2: Local Living Guide
        local_guide = self.local_living_guide(ctx, university_report)
        
        # Step 3: Timeline and Budget
        timeline_plan = self.timeline_and_budget(ctx, university_report, local_guide)
        
        return {
            "university_report": university_report,
            "local_guide": local_guide,
            "timeline_plan": timeline_plan
        }

# ----------------------------
# LLM configuration
# ----------------------------
def get_llm_config() -> Optional[LLM]:
    """Get LLM configuration with status feedback"""
    # OpenAI
    openai_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_APIKEY") or os.getenv("OPENAI")
    if openai_key:
        try:
            st.success("✅ OpenAI API key detected - using gpt-4o-mini")
            return LLM(model="openai/gpt-4o-mini", api_key=openai_key)
        except Exception:
            pass
    
    # Ollama fallback
    ollama_models = ["llama3.2:3b", "llama3.1:8b", "mistral:7b", "deepseek-r1:latest"]
    for model in ollama_models:
        try:
            llm = LLM(model=f"ollama/{model}", base_url="http://localhost:11434")
            st.info(f"🦙 Using Ollama model: {model}")
            return llm
        except Exception:
            continue
    
    st.warning("⚠️ No LLM configured - using CrewAI default")
    return None

# System check
if not TOOLS_OK:
    st.error("❌ Cannot proceed without tools")
    st.info("Make sure search_tools.py, browser_tools.py, and calculator_tools.py are in the same directory as main.py")
    st.stop()

st.success("✅ CrewAI system ready")

# ----------------------------
# Header
# ----------------------------
st.markdown('''
# 🎓 AI University Study Planner
**Comprehensive planning with CrewAI agent orchestration**

Plan your entire study abroad journey in minutes with AI-powered research and timeline generation.
''')

# ----------------------------
# Input Form
# ----------------------------
with st.form("study_planner_form"):
    st.subheader("📝 Study Abroad Planning Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        origin = st.text_input(
            "🏠 Your current location/country",
            placeholder="e.g., Mumbai, India",
            help="Where are you currently located?"
        )
        
        subject = st.text_input(
            "📚 Subject/Field of study",
            placeholder="e.g., Computer Science, Business Administration",
            help="What subject do you want to study?"
        )
        
        study_level = st.selectbox(
            "🎓 Study level",
            ["Bachelor's", "Master's", "PhD", "Certificate/Diploma"],
            help="What level of study are you planning?"
        )
        
        budget_range = st.selectbox(
            "💰 Budget range (total program)",
            ["Under $20,000", "$20,000-$50,000", "$50,000-$100,000", "$100,000-$200,000", "Above $200,000", "Not sure"],
            help="What's your approximate budget for the entire program?"
        )
    
    with col2:
        cities = st.text_area(
            "🌍 Target cities/countries (separate with ;)",
            placeholder="e.g., London, UK; Toronto, Canada; Melbourne, Australia",
            help="List your preferred study destinations"
        )
        
        interests = st.text_area(
            "🎯 Specific interests or requirements",
            placeholder="e.g., AI/ML focus, internship opportunities, scholarship eligibility",
            help="Any specific program features or requirements you're looking for?"
        )
        
        # Date range
        st.write("📅 **Study timeline**")
        start_date = st.date_input(
            "Planned start date",
            datetime.date.today() + datetime.timedelta(days=365),
            help="When do you plan to start your studies?"
        )
        
        duration_months = st.number_input(
            "Program duration (months)",
            min_value=6, max_value=60, value=24,
            help="How long is your intended program?"
        )
        
        end_date = start_date + datetime.timedelta(days=duration_months * 30)
        st.write(f"Estimated end date: {end_date}")
    
    submit_button = st.form_submit_button("🚀 Generate Study Plan", type="primary")

# ----------------------------
# Plan Generation
# ----------------------------
if submit_button:
    # Validate inputs
    if not all([origin.strip(), subject.strip(), cities.strip()]):
        st.error("❌ Please fill in all required fields (origin, subject, cities)")
        st.stop()
    
    # Prepare inputs
    inputs = {
        "origin": origin,
        "subject": subject,
        "study_level": study_level,
        "cities": cities,
        "interests": interests,
        "budget_range": budget_range,
        "daterange": (start_date, end_date)
    }
    
    # Initialize LLM and Planning System
    system_llm = get_llm_config()
    
    with st.spinner("🔄 Initializing AI planning system..."):
        try:
            planner = StudyPlannerCrew(llm=system_llm)
            st.success("✅ Planning system initialized")
        except Exception as e:
            st.error(f"❌ Failed to initialize planner: {str(e)}")
            st.stop()
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: University Research
        status_text.text("🔍 Phase 1/3: Researching universities and programs...")
        progress_bar.progress(10)
        
        # Process all steps
        result = planner.generate_plan(inputs)
        
        if result.get('university_report'):
            progress_bar.progress(40)
            status_text.text("✅ University research completed")
            
            # Step 2: Local Living Guide  
            status_text.text("🏠 Phase 2/3: Analyzing local living conditions...")
            progress_bar.progress(70)
            
            if result.get('local_guide'):
                status_text.text("✅ Local living guide completed")
                
                # Step 3: Timeline & Budget
                status_text.text("📅 Phase 3/3: Creating timeline and budget plan...")
                progress_bar.progress(90)
                
                if result.get('timeline_plan'):
                    progress_bar.progress(100)
                    status_text.text("🎉 Complete study plan generated!")
                    
                    # Display Results
                    st.success("✅ Your comprehensive study abroad plan is ready!")
                    
                    # Create tabs for organized display
                    tab1, tab2, tab3 = st.tabs(["🎓 University Research", "🏠 Living Guide", "📅 Timeline & Budget"])
                    
                    with tab1:
                        st.markdown("## 🎓 University Research Report")
                        st.markdown(result['university_report'])
                    
                    with tab2:
                        st.markdown("## 🏠 Local Living Guide")
                        st.markdown(result['local_guide'])
                    
                    with tab3:
                        st.markdown("## 📅 Timeline & Budget Plan")
                        st.markdown(result['timeline_plan'])
                    
                    # Download option
                    st.markdown("---")
                    full_report = f"""
# 🎓 Study Abroad Plan for {subject}

## 🎓 University Research
{result['university_report']}

## 🏠 Living Guide
{result['local_guide']}

## 📅 Timeline & Budget
{result['timeline_plan']}

---
Generated by AI University Study Planner
"""
                    st.download_button(
                        label="📄 Download Complete Report",
                        data=full_report,
                        file_name=f"study_plan_{subject.replace(' ', '_')}_{datetime.date.today()}.md",
                        mime="text/markdown"
                    )
                else:
                    st.error("❌ Failed to generate timeline and budget plan")
            else:
                st.error("❌ Failed to generate local living guide")
        else:
            st.error("❌ Failed to generate university research report")
            
    except Exception as e:
        st.error(f"❌ An error occurred during planning: {str(e)}")
        st.info("💡 Try checking your API keys or internet connection")
        progress_bar.progress(0)
        status_text.text("❌ Planning failed")

# ----------------------------
# Sidebar Info
# ----------------------------
with st.sidebar:
    st.markdown("## 💡 How it works")
    st.markdown("""
    **Three AI agents work together:**
    
    1. 🎓 **University Expert** - Researches programs, rankings, costs, requirements
    
    2. 🏠 **Local Expert** - Finds housing, transport, living costs, cultural tips
    
    3. 📅 **Timeline Specialist** - Creates month-by-month plan with budget calculations
    """)
    
    st.markdown("## ⚙️ Setup")
    
    # LLM Status
    if os.getenv("OPENAI_API_KEY"):
        st.success("✅ OpenAI API configured")
    else:
        st.warning("⚠️ Set OPENAI_API_KEY for best results")
        st.info("💡 Or run local Ollama models")
    
    # Tool Status
    if TOOLS_OK:
        st.success("✅ All tools loaded successfully")
    else:
        st.error("❌ Tool loading failed")
    
    st.success("✅ CrewAI agents ready")
    
    st.markdown("## 🔧 Features")
    st.markdown("""
    - ✅ Real-time web research
    - ✅ Current program information
    - ✅ Local cost analysis  
    - ✅ Timeline with deadlines
    - ✅ Budget calculations
    - ✅ Export to markdown
    """)

def main():
    """Main function for script entry point"""
    pass

if __name__ == "__main__":
    main()