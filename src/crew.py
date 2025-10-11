from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.flow.flow import Flow, start, listen
from typing import Dict, Any, Optional, List
from crewai import LLM
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import os

# Import your existing tools
from search_tools import SearchTools
from browser_tools import BrowserTools
from calculator_tools import CalculatorTools

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

@CrewBase
class UniversityPlannerCrew():
    """University Planner crew for comprehensive study abroad planning"""
    
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self):
        self.llm = self._get_llm_config()
        self.search_tool = SearchTool()
        self.browser_tool = BrowserTool()
        self.calculator_tool = CalculatorTool()

    def _get_llm_config(self) -> Optional[LLM]:
        """Get LLM configuration with fallbacks"""
        # OpenAI
        openai_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_APIKEY") or os.getenv("OPENAI")
        if openai_key:
            try:
                return LLM(model="openai/gpt-4o-mini", api_key=openai_key)
            except Exception:
                pass
        
        # Ollama fallback
        ollama_models = ["llama3.2:3b", "llama3.1:8b", "mistral:7b"]
        for model in ollama_models:
            try:
                return LLM(model=f"ollama/{model}", base_url="http://localhost:11434")
            except Exception:
                continue
        
        return None

    @agent
    def university_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['university_researcher'],
            verbose=True,
            tools=[self.search_tool, self.browser_tool],
            llm=self.llm
        )

    @agent
    def local_expert(self) -> Agent:
        return Agent(
            config=self.agents_config['local_expert'],
            verbose=True,
            tools=[self.search_tool, self.browser_tool],
            llm=self.llm
        )

    @agent
    def timeline_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config['timeline_specialist'],
            verbose=True,
            tools=[self.search_tool, self.browser_tool, self.calculator_tool],
            llm=self.llm
        )

    @task
    def research_universities(self) -> Task:
        return Task(
            config=self.tasks_config['research_universities'],
            agent=self.university_researcher
        )

    @task
    def local_living_guide(self) -> Task:
        return Task(
            config=self.tasks_config['local_living_guide'],
            agent=self.local_expert
        )

    @task
    def create_timeline(self) -> Task:
        return Task(
            config=self.tasks_config['create_timeline'],
            agent=self.timeline_specialist,
            output_file='output/study_plan.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the university planner crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )

# Flow class for Streamlit integration
class StudyPlannerFlow(Flow):
    def __init__(self, llm: Optional[LLM] = None):
        super().__init__()
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

    @start()
    def collect_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
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
            import datetime
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
        """Research universities"""
        agent = self.make_university_agent()
        task_description = f"""
        CRITICAL: Provide an 800+ word university research report for subject '{ctx['subject']}' 
        and study level '{ctx['study_level']}'. Cities to analyze: {', '.join(ctx['cities']) or 'N/A'}. 
        Origin: {ctx['origin']}. Period: {ctx['daterange']}.
        Include: program rankings, admission requirements with exact thresholds, tuition by year, 
        deadlines, scholarships, and employment outcomes.
        """
        
        task = Task(
            description=task_description.strip(),
            agent=agent,
            expected_output="Comprehensive 800+ word university research report"
        )
        
        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        result = crew.kickoff()
        
        return {
            "inputs": ctx,
            "university_report": str(result)
        }

    @listen("university_research")
    def local_living_guide(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        """Create local living guide"""
        inputs = ctx["inputs"]
        uni = ctx["university_report"]
        
        agent = self.make_local_agent()
        task_description = f"""
        Using the selected universities and insights below, write a 700+ word local living guide.
        Subject: {inputs['subject']}, Level: {inputs['study_level']}, Origin: {inputs['origin']}.
        Period: {inputs['daterange']}. Cities: {', '.join(inputs['cities']) or 'N/A'}.
        SOURCE REPORT: {uni}
        Include: housing options with exact costs, neighborhood tips, transport passes and monthly costs, 
        food costs, utilities, mobile/internet, textbooks, entertainment.
        """
        
        task = Task(
            description=task_description.strip(),
            agent=agent,
            expected_output="Comprehensive 700+ word local living guide"
        )
        
        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        result = crew.kickoff()
        
        return {
            "inputs": inputs,
            "university_report": uni,
            "local_guide": str(result)
        }

    @listen("local_living_guide")
    def timeline_and_budget(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        """Create timeline and budget"""
        inputs = ctx["inputs"]
        uni = ctx["university_report"]
        local = ctx["local_guide"]
        
        agent = self.make_timeline_agent()
        task_description = f"""
        Create a 1000+ word month-by-month timeline and budget for {inputs['daterange']}, 
        subject '{inputs['subject']}', level '{inputs['study_level']}'.
        SOURCE REPORTS: - University research: {uni} - Local living guide: {local}
        Include: standardized test dates, application deadlines, deposit timings, visa steps with dates, 
        flight booking windows, arrival setup, semester milestones.
        """
        
        task = Task(
            description=task_description.strip(),
            agent=agent,
            expected_output="Comprehensive 1000+ word timeline and budget plan"
        )
        
        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        result = crew.kickoff()
        
        return {
            "university_report": uni,
            "local_guide": local,
            "timeline_plan": str(result)
        }