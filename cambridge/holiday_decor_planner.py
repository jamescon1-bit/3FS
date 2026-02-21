"""
Cambridge NY Holiday Decor Planner
Comprehensive project manager for commercial holiday installations across NYC.

Features:
- Full project lifecycle management from intake to takedown
- Design themes and material tracking
- Installation scheduling and crew management
- Budget tracking and P&L per project
- Multi-project dashboard for concurrent installations
- Timeline management for holiday season workflow
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union
import json
import uuid


class ProjectStatus(Enum):
    INTAKE = "intake"
    DESIGN = "design"
    APPROVED = "approved"
    SOURCING = "sourcing"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    INSTALLED = "installed"
    MAINTAINED = "maintained"
    TAKEDOWN_SCHEDULED = "takedown_scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DecorTheme(Enum):
    CLASSIC_CHRISTMAS = "classic_christmas"
    WINTER_WONDERLAND = "winter_wonderland"
    MODERN_MINIMALIST = "modern_minimalist"
    FESTIVE_CORPORATE = "festive_corporate"
    LUXURY_GOLD = "luxury_gold"
    NYC_LIGHTS = "nyc_lights"
    HANUKKAH = "hanukkah"
    MULTI_FAITH = "multi_faith"
    CUSTOM = "custom"


class MaterialCategory(Enum):
    LIGHTS = "lights"
    ORNAMENTS = "ornaments"
    GARLAND = "garland"
    WREATHS = "wreaths"
    TREES = "trees"
    RIBBON = "ribbon"
    BOWS = "bows"
    INSTALLATIONS = "installations"
    ELECTRICAL = "electrical"
    HARDWARE = "hardware"


class ProjectSize(Enum):
    SMALL = "small"      # <2000 sq ft
    MEDIUM = "medium"    # 2000-5000 sq ft
    LARGE = "large"      # 5000-10000 sq ft
    ENTERPRISE = "enterprise"  # >10000 sq ft


class CrewRole(Enum):
    PROJECT_MANAGER = "project_manager"
    LEAD_INSTALLER = "lead_installer"
    INSTALLER = "installer"
    ELECTRICIAN = "electrician"
    DECORATOR = "decorator"
    DRIVER = "driver"


@dataclass
class MaterialItem:
    """Individual material item with costs and quantities"""
    item_id: str
    name: str
    category: MaterialCategory
    unit_cost: Decimal
    quantity_needed: int
    quantity_ordered: int = 0
    quantity_received: int = 0
    supplier: Optional[str] = None
    supplier_sku: Optional[str] = None
    notes: Optional[str] = None
    
    def total_cost(self) -> Decimal:
        return self.unit_cost * self.quantity_needed
    
    def is_fully_stocked(self) -> bool:
        return self.quantity_received >= self.quantity_needed


@dataclass
class CrewMember:
    """Crew member with skills and availability"""
    member_id: str
    name: str
    role: CrewRole
    hourly_rate: Decimal
    skills: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    phone: Optional[str] = None
    email: Optional[str] = None


@dataclass
class InstallSchedule:
    """Installation scheduling with crew assignments"""
    schedule_id: str
    project_id: str
    install_date: date
    start_time: datetime
    estimated_hours: float
    crew_members: List[str] = field(default_factory=list)  # member_ids
    equipment_needed: List[str] = field(default_factory=list)
    special_requirements: Optional[str] = None
    weather_contingency: bool = True
    
    def estimated_end_time(self) -> datetime:
        return self.start_time + timedelta(hours=self.estimated_hours)


@dataclass
class MaintenanceSchedule:
    """Maintenance visit scheduling"""
    maintenance_id: str
    project_id: str
    visit_date: date
    visit_type: str  # "check", "repair", "adjustment"
    assigned_crew: List[str] = field(default_factory=list)
    estimated_hours: float = 1.0
    completed: bool = False
    notes: Optional[str] = None


@dataclass
class BudgetLineItem:
    """Budget line item for P&L tracking"""
    description: str
    category: str
    budgeted_amount: Decimal
    actual_amount: Decimal = Decimal('0')
    notes: Optional[str] = None


@dataclass
class HolidayProject:
    """Complete holiday decoration project"""
    project_id: str
    client_name: str
    project_name: str
    location_address: str
    contact_name: str
    contact_phone: str
    contact_email: str
    
    # Project details
    project_size: ProjectSize
    square_footage: int
    theme: DecorTheme
    custom_requirements: Optional[str] = None
    status: ProjectStatus = ProjectStatus.INTAKE
    
    # Timeline
    created_date: datetime = field(default_factory=datetime.now)
    design_deadline: Optional[date] = None
    install_start_date: Optional[date] = None
    install_end_date: Optional[date] = None
    takedown_date: Optional[date] = None
    
    # Materials and crew
    materials: List[MaterialItem] = field(default_factory=list)
    install_schedule: Optional[InstallSchedule] = None
    maintenance_visits: List[MaintenanceSchedule] = field(default_factory=list)
    
    # Budget tracking
    budget_items: List[BudgetLineItem] = field(default_factory=list)
    total_budget: Decimal = Decimal('0')
    
    # Project notes
    design_notes: Optional[str] = None
    install_notes: Optional[str] = None
    client_feedback: Optional[str] = None
    
    def calculate_material_cost(self) -> Decimal:
        """Calculate total material costs"""
        return sum(item.total_cost() for item in self.materials)
    
    def calculate_budget_variance(self) -> Decimal:
        """Calculate budget variance (actual vs budgeted)"""
        budgeted = sum(item.budgeted_amount for item in self.budget_items)
        actual = sum(item.actual_amount for item in self.budget_items)
        return actual - budgeted
    
    def is_materials_ready(self) -> bool:
        """Check if all materials are fully stocked"""
        return all(item.is_fully_stocked() for item in self.materials)
    
    def get_project_timeline_days(self) -> int:
        """Calculate project timeline in days"""
        if self.install_start_date and self.takedown_date:
            return (self.takedown_date - self.install_start_date).days
        return 0


class HolidayDecorPlanner:
    """Comprehensive holiday decor project management system"""
    
    def __init__(self, data_directory: str = "./holiday_projects"):
        import os
        self.data_directory = data_directory
        os.makedirs(data_directory, exist_ok=True)
        
        self.projects: Dict[str, HolidayProject] = {}
        self.crew_members: Dict[str, CrewMember] = {}
        self.theme_templates: Dict[DecorTheme, Dict] = self._initialize_theme_templates()
        self.material_catalog: Dict[str, Dict] = self._initialize_material_catalog()
        
        # Load existing data
        self._load_data()
    
    def _initialize_theme_templates(self) -> Dict[DecorTheme, Dict]:
        """Initialize design theme templates with typical materials"""
        return {
            DecorTheme.CLASSIC_CHRISTMAS: {
                "description": "Traditional red, gold, and green with warm white lights",
                "typical_materials": [
                    {"name": "Warm White LED String Lights", "category": "lights", "unit_cost": 25.00},
                    {"name": "Red Velvet Ribbon", "category": "ribbon", "unit_cost": 8.50},
                    {"name": "Gold Ball Ornaments", "category": "ornaments", "unit_cost": 12.00},
                    {"name": "Fresh Pine Garland", "category": "garland", "unit_cost": 15.00},
                    {"name": "Traditional Wreath 24\"", "category": "wreaths", "unit_cost": 45.00},
                ],
                "color_scheme": ["red", "gold", "green", "white"]
            },
            DecorTheme.WINTER_WONDERLAND: {
                "description": "Silver, blue, and white with cool white lights and snowflakes",
                "typical_materials": [
                    {"name": "Cool White LED Lights", "category": "lights", "unit_cost": 28.00},
                    {"name": "Silver Ribbon", "category": "ribbon", "unit_cost": 9.00},
                    {"name": "Blue Glass Ornaments", "category": "ornaments", "unit_cost": 14.00},
                    {"name": "Artificial Snow Garland", "category": "garland", "unit_cost": 18.00},
                    {"name": "Snowflake Decorations", "category": "ornaments", "unit_cost": 22.00},
                ],
                "color_scheme": ["silver", "blue", "white", "ice blue"]
            },
            DecorTheme.MODERN_MINIMALIST: {
                "description": "Clean lines, monochromatic colors, geometric shapes",
                "typical_materials": [
                    {"name": "White LED Strip Lights", "category": "lights", "unit_cost": 35.00},
                    {"name": "Black Ribbon", "category": "ribbon", "unit_cost": 7.00},
                    {"name": "Geometric Ornaments", "category": "ornaments", "unit_cost": 18.00},
                    {"name": "Simple Line Garland", "category": "garland", "unit_cost": 12.00},
                ],
                "color_scheme": ["white", "black", "silver", "gray"]
            },
            DecorTheme.FESTIVE_CORPORATE: {
                "description": "Professional yet festive, brand-appropriate colors",
                "typical_materials": [
                    {"name": "Neutral LED Lights", "category": "lights", "unit_cost": 30.00},
                    {"name": "Company Color Ribbon", "category": "ribbon", "unit_cost": 10.00},
                    {"name": "Corporate Branded Ornaments", "category": "ornaments", "unit_cost": 25.00},
                    {"name": "Elegant Garland", "category": "garland", "unit_cost": 20.00},
                ],
                "color_scheme": ["custom", "gold", "silver", "white"]
            },
            DecorTheme.LUXURY_GOLD: {
                "description": "Opulent gold and burgundy with premium materials",
                "typical_materials": [
                    {"name": "Warm Gold LED Lights", "category": "lights", "unit_cost": 45.00},
                    {"name": "Burgundy Velvet Ribbon", "category": "ribbon", "unit_cost": 15.00},
                    {"name": "Gold Glass Ornaments", "category": "ornaments", "unit_cost": 28.00},
                    {"name": "Premium Gold Garland", "category": "garland", "unit_cost": 35.00},
                    {"name": "Luxury Bow Arrangements", "category": "bows", "unit_cost": 65.00},
                ],
                "color_scheme": ["gold", "burgundy", "cream", "bronze"]
            },
            DecorTheme.NYC_LIGHTS: {
                "description": "Metropolitan style with multicolor lights and urban elements",
                "typical_materials": [
                    {"name": "Multicolor LED Lights", "category": "lights", "unit_cost": 32.00},
                    {"name": "Metallic Ribbon", "category": "ribbon", "unit_cost": 11.00},
                    {"name": "NYC-themed Ornaments", "category": "ornaments", "unit_cost": 20.00},
                    {"name": "Urban Style Garland", "category": "garland", "unit_cost": 22.00},
                ],
                "color_scheme": ["red", "blue", "gold", "white", "green"]
            },
            DecorTheme.HANUKKAH: {
                "description": "Traditional blue and white with Jewish holiday elements",
                "typical_materials": [
                    {"name": "Blue and White LED Lights", "category": "lights", "unit_cost": 30.00},
                    {"name": "Blue Ribbon", "category": "ribbon", "unit_cost": 9.00},
                    {"name": "Star of David Ornaments", "category": "ornaments", "unit_cost": 16.00},
                    {"name": "Hanukkah Garland", "category": "garland", "unit_cost": 18.00},
                    {"name": "Menorah Display", "category": "installations", "unit_cost": 85.00},
                ],
                "color_scheme": ["blue", "white", "silver"]
            },
            DecorTheme.MULTI_FAITH: {
                "description": "Inclusive winter celebration without religious symbols",
                "typical_materials": [
                    {"name": "Warm White LED Lights", "category": "lights", "unit_cost": 25.00},
                    {"name": "Gold Ribbon", "category": "ribbon", "unit_cost": 8.00},
                    {"name": "Winter Scene Ornaments", "category": "ornaments", "unit_cost": 15.00},
                    {"name": "Seasonal Garland", "category": "garland", "unit_cost": 16.00},
                ],
                "color_scheme": ["gold", "white", "green", "burgundy"]
            }
        }
    
    def _initialize_material_catalog(self) -> Dict[str, Dict]:
        """Initialize comprehensive material catalog"""
        return {
            # Lights
            "led_string_warm": {"name": "Warm White LED String Lights", "category": "lights", "unit_cost": 25.00, "unit": "50ft strand"},
            "led_string_cool": {"name": "Cool White LED String Lights", "category": "lights", "unit_cost": 28.00, "unit": "50ft strand"},
            "led_icicle": {"name": "LED Icicle Lights", "category": "lights", "unit_cost": 35.00, "unit": "25ft strand"},
            "led_net": {"name": "LED Net Lights", "category": "lights", "unit_cost": 40.00, "unit": "4x6ft net"},
            
            # Trees
            "fraser_fir_6ft": {"name": "Fraser Fir Christmas Tree 6ft", "category": "trees", "unit_cost": 150.00, "unit": "each"},
            "fraser_fir_8ft": {"name": "Fraser Fir Christmas Tree 8ft", "category": "trees", "unit_cost": 225.00, "unit": "each"},
            "noble_fir_10ft": {"name": "Noble Fir Christmas Tree 10ft", "category": "trees", "unit_cost": 350.00, "unit": "each"},
            "artificial_tree_6ft": {"name": "Premium Artificial Tree 6ft", "category": "trees", "unit_cost": 280.00, "unit": "each"},
            
            # Garland
            "fresh_pine_garland": {"name": "Fresh Pine Garland", "category": "garland", "unit_cost": 15.00, "unit": "per foot"},
            "artificial_garland": {"name": "Artificial Pine Garland", "category": "garland", "unit_cost": 12.00, "unit": "per foot"},
            "magnolia_garland": {"name": "Magnolia Leaf Garland", "category": "garland", "unit_cost": 18.00, "unit": "per foot"},
            
            # Wreaths
            "wreath_18": {"name": "Fresh Wreath 18 inch", "category": "wreaths", "unit_cost": 35.00, "unit": "each"},
            "wreath_24": {"name": "Fresh Wreath 24 inch", "category": "wreaths", "unit_cost": 45.00, "unit": "each"},
            "wreath_30": {"name": "Fresh Wreath 30 inch", "category": "wreaths", "unit_cost": 65.00, "unit": "each"},
        }
    
    def _load_data(self):
        """Load existing project and crew data"""
        # Implementation would load from JSON files
        pass
    
    def _save_data(self):
        """Save project and crew data to JSON files"""
        # Implementation would save to JSON files
        pass
    
    def create_project(self,
                      client_name: str,
                      project_name: str,
                      location_address: str,
                      contact_name: str,
                      contact_phone: str,
                      contact_email: str,
                      project_size: ProjectSize,
                      square_footage: int,
                      theme: DecorTheme = DecorTheme.CLASSIC_CHRISTMAS,
                      custom_requirements: str = None) -> str:
        """Create a new holiday decoration project"""
        
        project_id = str(uuid.uuid4())[:8].upper()
        
        # Set typical deadlines based on current date
        today = date.today()
        design_deadline = date(today.year, 11, 15)  # Mid-November
        install_start = date(today.year, 11, 25)    # Week of Thanksgiving
        takedown = date(today.year + 1, 1, 15)      # Mid-January
        
        project = HolidayProject(
            project_id=project_id,
            client_name=client_name,
            project_name=project_name,
            location_address=location_address,
            contact_name=contact_name,
            contact_phone=contact_phone,
            contact_email=contact_email,
            project_size=project_size,
            square_footage=square_footage,
            theme=theme,
            custom_requirements=custom_requirements,
            design_deadline=design_deadline,
            install_start_date=install_start,
            takedown_date=takedown
        )
        
        # Add initial budget estimates based on project size
        self._generate_initial_budget(project)
        
        self.projects[project_id] = project
        self._save_data()
        
        return project_id
    
    def _generate_initial_budget(self, project: HolidayProject):
        """Generate initial budget estimates based on project size"""
        size_multipliers = {
            ProjectSize.SMALL: Decimal('1.0'),
            ProjectSize.MEDIUM: Decimal('2.5'),
            ProjectSize.LARGE: Decimal('5.0'),
            ProjectSize.ENTERPRISE: Decimal('10.0')
        }
        
        multiplier = size_multipliers.get(project.project_size, Decimal('1.0'))
        
        # Base budget items
        base_materials = Decimal('2500') * multiplier
        base_labor = Decimal('1800') * multiplier
        base_equipment = Decimal('400') * multiplier
        
        project.budget_items = [
            BudgetLineItem("Materials & Supplies", "materials", base_materials),
            BudgetLineItem("Installation Labor", "labor", base_labor),
            BudgetLineItem("Equipment Rental", "equipment", base_equipment),
            BudgetLineItem("Travel & Transportation", "travel", Decimal('300')),
            BudgetLineItem("Maintenance Visits", "maintenance", Decimal('500')),
            BudgetLineItem("Takedown Labor", "takedown", base_labor * Decimal('0.6')),
        ]
        
        project.total_budget = sum(item.budgeted_amount for item in project.budget_items)
    
    def add_materials_from_theme(self, project_id: str) -> bool:
        """Add typical materials based on selected theme"""
        if project_id not in self.projects:
            return False
        
        project = self.projects[project_id]
        theme_template = self.theme_templates.get(project.theme)
        
        if not theme_template:
            return False
        
        # Calculate quantities based on square footage
        sqft_factor = project.square_footage / 1000  # Base factor per 1000 sq ft
        
        for material_template in theme_template["typical_materials"]:
            # Estimate quantity based on material type and space
            if material_template["category"] == "lights":
                quantity = max(1, int(sqft_factor * 4))  # 4 strands per 1000 sq ft
            elif material_template["category"] == "garland":
                quantity = max(10, int(sqft_factor * 50))  # 50 feet per 1000 sq ft
            elif material_template["category"] == "wreaths":
                quantity = max(1, int(sqft_factor * 2))  # 2 wreaths per 1000 sq ft
            else:
                quantity = max(1, int(sqft_factor * 3))  # 3 units per 1000 sq ft
            
            material = MaterialItem(
                item_id=str(uuid.uuid4())[:8],
                name=material_template["name"],
                category=MaterialCategory(material_template["category"]),
                unit_cost=Decimal(str(material_template["unit_cost"])),
                quantity_needed=quantity
            )
            
            project.materials.append(material)
        
        project.status = ProjectStatus.DESIGN
        self._save_data()
        return True
    
    def schedule_installation(self,
                            project_id: str,
                            install_date: date,
                            start_time: datetime,
                            crew_member_ids: List[str],
                            estimated_hours: float,
                            equipment_needed: List[str] = None) -> bool:
        """Schedule installation for a project"""
        if project_id not in self.projects:
            return False
        
        project = self.projects[project_id]
        
        schedule = InstallSchedule(
            schedule_id=str(uuid.uuid4())[:8],
            project_id=project_id,
            install_date=install_date,
            start_time=start_time,
            estimated_hours=estimated_hours,
            crew_members=crew_member_ids,
            equipment_needed=equipment_needed or []
        )
        
        project.install_schedule = schedule
        project.install_start_date = install_date
        project.status = ProjectStatus.SCHEDULED
        
        self._save_data()
        return True
    
    def add_maintenance_visit(self,
                            project_id: str,
                            visit_date: date,
                            visit_type: str = "check",
                            assigned_crew: List[str] = None,
                            estimated_hours: float = 2.0) -> str:
        """Schedule a maintenance visit"""
        if project_id not in self.projects:
            return ""
        
        maintenance_id = str(uuid.uuid4())[:8]
        
        maintenance = MaintenanceSchedule(
            maintenance_id=maintenance_id,
            project_id=project_id,
            visit_date=visit_date,
            visit_type=visit_type,
            assigned_crew=assigned_crew or [],
            estimated_hours=estimated_hours
        )
        
        self.projects[project_id].maintenance_visits.append(maintenance)
        self._save_data()
        
        return maintenance_id
    
    def get_project_dashboard(self, status_filter: ProjectStatus = None) -> Dict:
        """Generate multi-project dashboard view"""
        projects = list(self.projects.values())
        
        if status_filter:
            projects = [p for p in projects if p.status == status_filter]
        
        # Group by status
        status_groups = {}
        for status in ProjectStatus:
            status_groups[status] = [p for p in projects if p.status == status]
        
        # Calculate totals
        total_budget = sum(p.total_budget for p in projects)
        total_sqft = sum(p.square_footage for p in projects)
        
        return {
            "total_projects": len(projects),
            "projects_by_status": {status.value: len(group) for status, group in status_groups.items()},
            "total_budget": total_budget,
            "total_square_footage": total_sqft,
            "upcoming_installations": self._get_upcoming_installations(),
            "maintenance_due": self._get_maintenance_due(),
            "materials_needed": self._get_materials_summary()
        }
    
    def _get_upcoming_installations(self) -> List[Dict]:
        """Get installations scheduled for next 14 days"""
        cutoff = date.today() + timedelta(days=14)
        upcoming = []
        
        for project in self.projects.values():
            if (project.install_schedule and 
                project.install_schedule.install_date <= cutoff and
                project.status in [ProjectStatus.SCHEDULED, ProjectStatus.IN_PROGRESS]):
                
                upcoming.append({
                    "project_id": project.project_id,
                    "client_name": project.client_name,
                    "install_date": project.install_schedule.install_date,
                    "estimated_hours": project.install_schedule.estimated_hours,
                    "crew_size": len(project.install_schedule.crew_members)
                })
        
        return sorted(upcoming, key=lambda x: x["install_date"])
    
    def _get_maintenance_due(self) -> List[Dict]:
        """Get maintenance visits due in next 7 days"""
        cutoff = date.today() + timedelta(days=7)
        due = []
        
        for project in self.projects.values():
            for visit in project.maintenance_visits:
                if not visit.completed and visit.visit_date <= cutoff:
                    due.append({
                        "project_id": project.project_id,
                        "client_name": project.client_name,
                        "visit_date": visit.visit_date,
                        "visit_type": visit.visit_type,
                        "estimated_hours": visit.estimated_hours
                    })
        
        return sorted(due, key=lambda x: x["visit_date"])
    
    def _get_materials_summary(self) -> Dict:
        """Get summary of materials needed across all active projects"""
        materials_summary = {}
        
        for project in self.projects.values():
            if project.status in [ProjectStatus.SOURCING, ProjectStatus.SCHEDULED]:
                for material in project.materials:
                    if not material.is_fully_stocked():
                        key = material.name
                        if key not in materials_summary:
                            materials_summary[key] = {
                                "total_needed": 0,
                                "total_cost": Decimal('0'),
                                "projects": []
                            }
                        
                        needed = material.quantity_needed - material.quantity_received
                        materials_summary[key]["total_needed"] += needed
                        materials_summary[key]["total_cost"] += material.unit_cost * needed
                        materials_summary[key]["projects"].append(project.project_id)
        
        return materials_summary
    
    def generate_timeline_report(self) -> str:
        """Generate holiday season timeline report"""
        output = []
        output.append("CAMBRIDGE NY HOLIDAY DECOR - SEASON TIMELINE")
        output.append("=" * 55)
        output.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        output.append("")
        
        # Group projects by key dates
        design_phase = []
        sourcing_phase = []
        installation_phase = []
        maintenance_phase = []
        takedown_phase = []
        
        for project in self.projects.values():
            if project.status == ProjectStatus.DESIGN:
                design_phase.append(project)
            elif project.status == ProjectStatus.SOURCING:
                sourcing_phase.append(project)
            elif project.status in [ProjectStatus.SCHEDULED, ProjectStatus.IN_PROGRESS]:
                installation_phase.append(project)
            elif project.status == ProjectStatus.INSTALLED:
                maintenance_phase.append(project)
            elif project.status == ProjectStatus.TAKEDOWN_SCHEDULED:
                takedown_phase.append(project)
        
        # Design Phase (Mid November)
        output.append("🎨 DESIGN PHASE (Target: Nov 15)")
        output.append("-" * 35)
        if design_phase:
            for project in design_phase:
                output.append(f"  • {project.client_name} - {project.project_name}")
                output.append(f"    Size: {project.project_size.value} ({project.square_footage:,} sq ft)")
                output.append(f"    Theme: {project.theme.value.replace('_', ' ').title()}")
        else:
            output.append("  No projects in design phase")
        output.append("")
        
        # Installation Phase (Thanksgiving Week)
        output.append("🔧 INSTALLATION PHASE (Target: Nov 25 - Dec 15)")
        output.append("-" * 50)
        if installation_phase:
            for project in installation_phase:
                install_date = project.install_start_date or "TBD"
                output.append(f"  • {project.client_name} - Install: {install_date}")
                if project.install_schedule:
                    output.append(f"    Crew: {len(project.install_schedule.crew_members)} members, {project.install_schedule.estimated_hours}h")
        else:
            output.append("  No installations scheduled")
        output.append("")
        
        # Maintenance Phase (December - January)
        output.append("🔍 MAINTENANCE PHASE (Dec - Jan)")
        output.append("-" * 35)
        if maintenance_phase:
            for project in maintenance_phase:
                visits = len([v for v in project.maintenance_visits if not v.completed])
                output.append(f"  • {project.client_name} - {visits} visits remaining")
        else:
            output.append("  No projects in maintenance")
        output.append("")
        
        # Takedown Phase (Mid January)
        output.append("📦 TAKEDOWN PHASE (Target: Jan 15)")
        output.append("-" * 35)
        if takedown_phase:
            for project in takedown_phase:
                output.append(f"  • {project.client_name} - Takedown: {project.takedown_date}")
        else:
            output.append("  No takedowns scheduled")
        
        return "\n".join(output)


# Example Usage
if __name__ == "__main__":
    planner = HolidayDecorPlanner()
    
    print("=== Cambridge NY Holiday Decor Planner Examples ===\n")
    
    # Example 1: Create a large commercial project
    print("1. CREATING LARGE COMMERCIAL PROJECT")
    print("-" * 40)
    
    project_id = planner.create_project(
        client_name="One World Trade Center",
        project_name="Main Lobby Holiday Display",
        location_address="285 Fulton St, New York, NY 10007",
        contact_name="Sarah Johnson",
        contact_phone="212-555-0199",
        contact_email="s.johnson@1wtc.com",
        project_size=ProjectSize.ENTERPRISE,
        square_footage=15000,
        theme=DecorTheme.LUXURY_GOLD,
        custom_requirements="Must incorporate building's architectural elements, 30ft Christmas tree centerpiece"
    )
    
    print(f"Created project: {project_id}")
    
    # Add theme-based materials
    planner.add_materials_from_theme(project_id)
    print("Added materials based on Luxury Gold theme")
    
    # Example 2: Create medium corporate project
    print("\n2. CREATING MEDIUM CORPORATE PROJECT")
    print("-" * 40)
    
    corp_project_id = planner.create_project(
        client_name="Goldman Sachs",
        project_name="Executive Floor Holiday Decor",
        location_address="200 West St, New York, NY 10282",
        contact_name="Michael Chen",
        contact_phone="212-555-0288",
        contact_email="m.chen@gs.com",
        project_size=ProjectSize.MEDIUM,
        square_footage=4500,
        theme=DecorTheme.FESTIVE_CORPORATE
    )
    
    planner.add_materials_from_theme(corp_project_id)
    print(f"Created corporate project: {corp_project_id}")
    
    # Example 3: Schedule installation
    print("\n3. SCHEDULING INSTALLATION")
    print("-" * 40)
    
    install_date = date(2024, 11, 28)  # Day after Thanksgiving
    start_time = datetime(2024, 11, 28, 7, 0)  # 7 AM start
    
    planner.schedule_installation(
        project_id=project_id,
        install_date=install_date,
        start_time=start_time,
        crew_member_ids=["CREW001", "CREW002", "CREW003", "CREW004"],
        estimated_hours=12.0,
        equipment_needed=["lift_30ft", "van_large", "power_tools"]
    )
    
    print(f"Scheduled installation for {install_date} at {start_time.strftime('%H:%M')}")
    
    # Example 4: Add maintenance visits
    print("\n4. SCHEDULING MAINTENANCE")
    print("-" * 40)
    
    # Christmas week check
    visit1 = planner.add_maintenance_visit(
        project_id=project_id,
        visit_date=date(2024, 12, 23),
        visit_type="check",
        assigned_crew=["CREW001"],
        estimated_hours=2.0
    )
    
    # New Year's check
    visit2 = planner.add_maintenance_visit(
        project_id=project_id,
        visit_date=date(2025, 1, 2),
        visit_type="adjustment",
        assigned_crew=["CREW001", "CREW002"],
        estimated_hours=3.0
    )
    
    print(f"Scheduled maintenance visits: {visit1}, {visit2}")
    
    # Example 5: Generate dashboard
    print("\n5. PROJECT DASHBOARD")
    print("-" * 40)
    
    dashboard = planner.get_project_dashboard()
    
    print(f"Total Projects: {dashboard['total_projects']}")
    print(f"Total Budget: ${dashboard['total_budget']:,.2f}")
    print(f"Total Square Footage: {dashboard['total_square_footage']:,}")
    print(f"\nProjects by Status:")
    for status, count in dashboard['projects_by_status'].items():
        if count > 0:
            print(f"  • {status.replace('_', ' ').title()}: {count}")
    
    print(f"\nUpcoming Installations ({len(dashboard['upcoming_installations'])}):")
    for install in dashboard['upcoming_installations']:
        print(f"  • {install['client_name']} - {install['install_date']}")
    
    # Example 6: Generate timeline report
    print("\n6. SEASON TIMELINE REPORT")
    print("-" * 40)
    
    timeline_report = planner.generate_timeline_report()
    print(timeline_report)