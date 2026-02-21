#!/usr/bin/env python3
"""
Holiday Decor Planner - Complete commercial holiday decoration project manager
Cambridge NY commercial AI module for managing holiday decor installations in NYC
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging
from decimal import Decimal, ROUND_HALF_UP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProjectPhase(Enum):
    """Project lifecycle phases"""
    REQUIREMENTS = "requirements"
    DESIGN = "design"
    SOURCING = "sourcing"
    SCHEDULING = "scheduling"
    INSTALLATION = "installation"
    MAINTENANCE = "maintenance"
    TAKEDOWN = "takedown"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class DesignTheme(Enum):
    """Available design themes"""
    CLASSIC_CHRISTMAS = "classic_christmas"
    WINTER_WONDERLAND = "winter_wonderland"
    MODERN_MINIMALIST = "modern_minimalist"
    FESTIVE_CORPORATE = "festive_corporate"
    LUXURY_GOLD = "luxury_gold"
    NATURAL_RUSTIC = "natural_rustic"
    LED_MODERN = "led_modern"

class MaterialType(Enum):
    """Types of decoration materials"""
    LIGHTS = "lights"
    ORNAMENTS = "ornaments"
    GARLANDS = "garlands"
    WREATHS = "wreaths"
    TREES_REAL = "trees_real"
    TREES_ARTIFICIAL = "trees_artificial"
    RIBBON = "ribbon"
    SPECIALTY = "specialty"

class CrewSize(Enum):
    """Standard crew sizes"""
    SMALL = 2  # 2-person crew
    MEDIUM = 3  # 3-person crew
    LARGE = 4   # 4-person crew

class InstallDuration(Enum):
    """Installation duration estimates"""
    SHORT = 4    # 4 hours
    MEDIUM = 6   # 6 hours
    LONG = 8     # 8 hours

@dataclass
class Material:
    """Material item specification"""
    id: str
    name: str
    material_type: MaterialType
    quantity: int
    unit_cost: Decimal
    supplier: str = ""
    notes: str = ""
    in_stock: bool = True
    
    @property
    def total_cost(self) -> Decimal:
        return self.quantity * self.unit_cost

@dataclass
class CrewAssignment:
    """Crew assignment for installation"""
    crew_id: str
    crew_leader: str
    crew_members: List[str]
    size: CrewSize
    hourly_rate: Decimal
    
    def total_labor_cost(self, hours: int) -> Decimal:
        """Calculate total labor cost for given hours"""
        return Decimal(self.size.value) * self.hourly_rate * Decimal(hours)

@dataclass
class Project:
    """Holiday decoration project"""
    id: str
    client_name: str
    client_contact: str
    site_address: str
    project_name: str
    design_theme: DesignTheme
    phase: ProjectPhase
    budget_min: Decimal
    budget_max: Decimal
    current_cost: Decimal = Decimal('0.00')
    
    # Dates
    created_date: datetime = field(default_factory=datetime.now)
    install_date: Optional[date] = None
    takedown_date: Optional[date] = None
    completion_date: Optional[datetime] = None
    
    # Project details
    materials: List[Material] = field(default_factory=list)
    crew_assignment: Optional[CrewAssignment] = None
    install_duration: InstallDuration = InstallDuration.MEDIUM
    
    # Status tracking
    requirements_notes: str = ""
    design_approved: bool = False
    materials_sourced: bool = False
    installation_complete: bool = False
    maintenance_schedule: List[date] = field(default_factory=list)
    
    # Special considerations
    special_requirements: List[str] = field(default_factory=list)
    safety_notes: str = ""
    
    def add_material(self, material: Material):
        """Add material to project and update cost"""
        self.materials.append(material)
        self.current_cost += material.total_cost
    
    def calculate_total_cost(self) -> Decimal:
        """Calculate total project cost including materials and labor"""
        material_cost = sum(m.total_cost for m in self.materials)
        
        labor_cost = Decimal('0.00')
        if self.crew_assignment:
            labor_cost = self.crew_assignment.total_labor_cost(self.install_duration.value)
        
        return material_cost + labor_cost
    
    def is_within_budget(self) -> bool:
        """Check if project is within budget constraints"""
        total_cost = self.calculate_total_cost()
        return self.budget_min <= total_cost <= self.budget_max

class HolidayDecorPlanner:
    """Complete holiday decoration project management system"""
    
    def __init__(self, db_path: str = "holiday_decor.db"):
        """Initialize the holiday decor planner"""
        self.db_path = db_path
        self._init_database()
        logger.info(f"Holiday Decor Planner initialized with database: {db_path}")
    
    def _init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Projects table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                client_name TEXT NOT NULL,
                client_contact TEXT NOT NULL,
                site_address TEXT NOT NULL,
                project_name TEXT NOT NULL,
                design_theme TEXT NOT NULL,
                phase TEXT NOT NULL,
                budget_min DECIMAL NOT NULL,
                budget_max DECIMAL NOT NULL,
                current_cost DECIMAL DEFAULT 0.00,
                created_date TEXT NOT NULL,
                install_date TEXT,
                takedown_date TEXT,
                completion_date TEXT,
                install_duration INTEGER NOT NULL,
                requirements_notes TEXT DEFAULT '',
                design_approved BOOLEAN DEFAULT 0,
                materials_sourced BOOLEAN DEFAULT 0,
                installation_complete BOOLEAN DEFAULT 0,
                special_requirements TEXT DEFAULT '[]',
                safety_notes TEXT DEFAULT '',
                maintenance_schedule TEXT DEFAULT '[]'
            )
        ''')
        
        # Materials table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS materials (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                material_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_cost DECIMAL NOT NULL,
                supplier TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                in_stock BOOLEAN DEFAULT 1,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        ''')
        
        # Crew assignments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crew_assignments (
                crew_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                crew_leader TEXT NOT NULL,
                crew_members TEXT NOT NULL,
                size INTEGER NOT NULL,
                hourly_rate DECIMAL NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_project_client ON projects(client_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_project_phase ON projects(phase)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_project_install_date ON projects(install_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_material_project ON materials(project_id)')
        
        conn.commit()
        conn.close()
    
    def create_project(self,
                      client_name: str,
                      client_contact: str,
                      site_address: str,
                      project_name: str,
                      design_theme: DesignTheme,
                      budget_min: Decimal,
                      budget_max: Decimal,
                      special_requirements: List[str] = None) -> str:
        """
        Create a new holiday decoration project
        
        Returns:
            Project ID
        """
        project_id = f"HD_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{client_name[:3].upper()}"
        
        project = Project(
            id=project_id,
            client_name=client_name,
            client_contact=client_contact,
            site_address=site_address,
            project_name=project_name,
            design_theme=design_theme,
            phase=ProjectPhase.REQUIREMENTS,
            budget_min=budget_min,
            budget_max=budget_max,
            special_requirements=special_requirements or []
        )
        
        self._insert_project(project)
        logger.info(f"Created project: {project_id} for {client_name}")
        return project_id
    
    def _insert_project(self, project: Project):
        """Insert project into database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO projects (
                id, client_name, client_contact, site_address, project_name,
                design_theme, phase, budget_min, budget_max, current_cost,
                created_date, install_date, takedown_date, completion_date,
                install_duration, requirements_notes, design_approved,
                materials_sourced, installation_complete, special_requirements,
                safety_notes, maintenance_schedule
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            project.id, project.client_name, project.client_contact,
            project.site_address, project.project_name, project.design_theme.value,
            project.phase.value, float(project.budget_min), float(project.budget_max),
            float(project.current_cost), project.created_date.isoformat(),
            project.install_date.isoformat() if project.install_date else None,
            project.takedown_date.isoformat() if project.takedown_date else None,
            project.completion_date.isoformat() if project.completion_date else None,
            project.install_duration.value, project.requirements_notes,
            project.design_approved, project.materials_sourced,
            project.installation_complete, json.dumps(project.special_requirements),
            project.safety_notes, json.dumps([d.isoformat() for d in project.maintenance_schedule])
        ))
        
        conn.commit()
        conn.close()
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """Retrieve project by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        # Get materials
        cursor.execute('SELECT * FROM materials WHERE project_id = ?', (project_id,))
        material_rows = cursor.fetchall()
        
        # Get crew assignment
        cursor.execute('SELECT * FROM crew_assignments WHERE project_id = ?', (project_id,))
        crew_row = cursor.fetchone()
        
        conn.close()
        
        project = self._row_to_project(row, material_rows, crew_row)
        return project
    
    def _row_to_project(self, row, material_rows=None, crew_row=None) -> Project:
        """Convert database row to Project object"""
        materials = []
        if material_rows:
            for m_row in material_rows:
                material = Material(
                    id=m_row[0],
                    name=m_row[2],
                    material_type=MaterialType(m_row[3]),
                    quantity=m_row[4],
                    unit_cost=Decimal(str(m_row[5])),
                    supplier=m_row[6] or "",
                    notes=m_row[7] or "",
                    in_stock=bool(m_row[8])
                )
                materials.append(material)
        
        crew_assignment = None
        if crew_row:
            crew_assignment = CrewAssignment(
                crew_id=crew_row[0],
                crew_leader=crew_row[2],
                crew_members=json.loads(crew_row[3]),
                size=CrewSize(crew_row[4]),
                hourly_rate=Decimal(str(crew_row[5]))
            )
        
        # Parse maintenance schedule
        maintenance_schedule = []
        if row[21]:
            schedule_data = json.loads(row[21])
            maintenance_schedule = [date.fromisoformat(d) for d in schedule_data]
        
        return Project(
            id=row[0],
            client_name=row[1],
            client_contact=row[2],
            site_address=row[3],
            project_name=row[4],
            design_theme=DesignTheme(row[5]),
            phase=ProjectPhase(row[6]),
            budget_min=Decimal(str(row[7])),
            budget_max=Decimal(str(row[8])),
            current_cost=Decimal(str(row[9])),
            created_date=datetime.fromisoformat(row[10]),
            install_date=date.fromisoformat(row[11]) if row[11] else None,
            takedown_date=date.fromisoformat(row[12]) if row[12] else None,
            completion_date=datetime.fromisoformat(row[13]) if row[13] else None,
            materials=materials,
            crew_assignment=crew_assignment,
            install_duration=InstallDuration(row[14]),
            requirements_notes=row[15] or "",
            design_approved=bool(row[16]),
            materials_sourced=bool(row[17]),
            installation_complete=bool(row[18]),
            special_requirements=json.loads(row[19]) if row[19] else [],
            safety_notes=row[20] or "",
            maintenance_schedule=maintenance_schedule
        )
    
    def update_project_phase(self, project_id: str, new_phase: ProjectPhase) -> bool:
        """Update project phase"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE projects 
            SET phase = ?
            WHERE id = ?
        ''', (new_phase.value, project_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if success:
            logger.info(f"Updated project {project_id} to phase {new_phase.value}")
        
        return success
    
    def add_material_to_project(self, project_id: str, material: Material) -> bool:
        """Add material to project"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Insert material
        cursor.execute('''
            INSERT INTO materials (
                id, project_id, name, material_type, quantity, unit_cost,
                supplier, notes, in_stock
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            material.id, project_id, material.name, material.material_type.value,
            material.quantity, float(material.unit_cost), material.supplier,
            material.notes, material.in_stock
        ))
        
        # Update project current cost
        cursor.execute('''
            UPDATE projects 
            SET current_cost = current_cost + ?
            WHERE id = ?
        ''', (float(material.total_cost), project_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Added material {material.name} to project {project_id}")
        return True
    
    def assign_crew(self, project_id: str, crew_assignment: CrewAssignment) -> bool:
        """Assign crew to project"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete existing assignment if any
        cursor.execute('DELETE FROM crew_assignments WHERE project_id = ?', (project_id,))
        
        # Insert new assignment
        cursor.execute('''
            INSERT INTO crew_assignments (
                crew_id, project_id, crew_leader, crew_members, size, hourly_rate
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            crew_assignment.crew_id, project_id, crew_assignment.crew_leader,
            json.dumps(crew_assignment.crew_members), crew_assignment.size.value,
            float(crew_assignment.hourly_rate)
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Assigned crew {crew_assignment.crew_id} to project {project_id}")
        return True
    
    def schedule_installation(self, project_id: str, install_date: date, duration: InstallDuration) -> bool:
        """Schedule installation for project"""
        # Auto-calculate takedown date (typically Jan 2-15)
        if install_date.month in [11, 12]:  # Nov/Dec installation
            takedown_year = install_date.year + 1
            takedown_date = date(takedown_year, 1, 7)  # Default Jan 7th
        else:
            takedown_date = install_date + timedelta(days=45)  # 45-day default
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE projects 
            SET install_date = ?, takedown_date = ?, install_duration = ?
            WHERE id = ?
        ''', (install_date.isoformat(), takedown_date.isoformat(), 
              duration.value, project_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if success:
            logger.info(f"Scheduled installation for project {project_id}: {install_date} -> {takedown_date}")
        
        return success
    
    def get_active_projects(self) -> List[Project]:
        """Get all active projects (not completed or cancelled)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM projects 
            WHERE phase NOT IN (?, ?)
            ORDER BY install_date ASC, created_date ASC
        ''', (ProjectPhase.COMPLETED.value, ProjectPhase.CANCELLED.value))
        
        rows = cursor.fetchall()
        conn.close()
        
        projects = []
        for row in rows:
            project = self.get_project(row[0])  # Get full project with materials/crew
            if project:
                projects.append(project)
        
        return projects
    
    def get_dashboard_summary(self) -> Dict:
        """Get dashboard summary for managing multiple projects"""
        projects = self.get_active_projects()
        
        summary = {
            "total_active_projects": len(projects),
            "by_phase": {},
            "by_theme": {},
            "installations_this_week": 0,
            "takedowns_this_week": 0,
            "total_revenue": Decimal('0.00'),
            "average_project_value": Decimal('0.00'),
            "crew_utilization": {},
            "urgent_tasks": []
        }
        
        # Current week dates
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        for project in projects:
            # Count by phase
            phase = project.phase.value
            summary["by_phase"][phase] = summary["by_phase"].get(phase, 0) + 1
            
            # Count by theme
            theme = project.design_theme.value
            summary["by_theme"][theme] = summary["by_theme"].get(theme, 0) + 1
            
            # Check installations/takedowns this week
            if project.install_date and week_start <= project.install_date <= week_end:
                summary["installations_this_week"] += 1
            
            if project.takedown_date and week_start <= project.takedown_date <= week_end:
                summary["takedowns_this_week"] += 1
            
            # Revenue calculation
            project_value = project.calculate_total_cost()
            summary["total_revenue"] += project_value
            
            # Crew utilization
            if project.crew_assignment:
                crew_leader = project.crew_assignment.crew_leader
                summary["crew_utilization"][crew_leader] = summary["crew_utilization"].get(crew_leader, 0) + 1
            
            # Urgent tasks
            if project.install_date and (project.install_date - today).days <= 7:
                if not project.materials_sourced:
                    summary["urgent_tasks"].append(f"Materials needed: {project.project_name}")
                if not project.crew_assignment:
                    summary["urgent_tasks"].append(f"Crew assignment needed: {project.project_name}")
        
        # Calculate average project value
        if projects:
            summary["average_project_value"] = summary["total_revenue"] / len(projects)
        
        # Round monetary values
        summary["total_revenue"] = summary["total_revenue"].quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        summary["average_project_value"] = summary["average_project_value"].quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        return summary
    
    def generate_installation_schedule(self, start_date: date, end_date: date) -> List[Dict]:
        """Generate installation schedule for date range"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.*, ca.crew_leader, ca.crew_members, ca.size
            FROM projects p
            LEFT JOIN crew_assignments ca ON p.id = ca.project_id
            WHERE p.install_date >= ? AND p.install_date <= ?
            AND p.phase NOT IN (?, ?)
            ORDER BY p.install_date ASC, ca.crew_leader
        ''', (start_date.isoformat(), end_date.isoformat(),
              ProjectPhase.COMPLETED.value, ProjectPhase.CANCELLED.value))
        
        rows = cursor.fetchall()
        conn.close()
        
        schedule = []
        for row in rows:
            schedule_item = {
                "date": row[11],  # install_date
                "project_id": row[0],
                "project_name": row[4],
                "client_name": row[1],
                "site_address": row[3],
                "duration_hours": row[14],  # install_duration
                "crew_leader": row[22] if len(row) > 22 else "Unassigned",
                "crew_size": row[24] if len(row) > 24 else "Unknown",
                "design_theme": row[5]
            }
            schedule.append(schedule_item)
        
        return schedule
    
    def get_material_requirements(self) -> Dict[MaterialType, Dict]:
        """Get aggregated material requirements across all active projects"""
        projects = self.get_active_projects()
        
        requirements = {}
        for material_type in MaterialType:
            requirements[material_type] = {
                "total_quantity": 0,
                "total_cost": Decimal('0.00'),
                "projects": [],
                "suppliers": set()
            }
        
        for project in projects:
            for material in project.materials:
                mat_type = material.material_type
                requirements[mat_type]["total_quantity"] += material.quantity
                requirements[mat_type]["total_cost"] += material.total_cost
                requirements[mat_type]["projects"].append(project.project_name)
                if material.supplier:
                    requirements[mat_type]["suppliers"].add(material.supplier)
        
        # Convert sets to lists and round costs
        for mat_type in requirements:
            requirements[mat_type]["suppliers"] = list(requirements[mat_type]["suppliers"])
            requirements[mat_type]["total_cost"] = requirements[mat_type]["total_cost"].quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        return requirements


def main():
    """Example usage and testing"""
    planner = HolidayDecorPlanner("test_holiday_decor.db")
    
    print("Holiday Decor Planner initialized successfully!")
    
    # Example: Create a project
    project_id = planner.create_project(
        client_name="Manhattan Office Building LLC",
        client_contact="John Smith (555-0123)",
        site_address="123 Madison Ave, New York, NY 10016",
        project_name="Corporate Holiday Display 2024",
        design_theme=DesignTheme.FESTIVE_CORPORATE,
        budget_min=Decimal('15000.00'),
        budget_max=Decimal('25000.00'),
        special_requirements=["Must be fireproof", "LED lights only", "No live trees"]
    )
    
    print(f"Created project: {project_id}")
    
    # Example: Add materials
    lights_material = Material(
        id="MAT_001",
        name="LED String Lights (Commercial Grade)",
        material_type=MaterialType.LIGHTS,
        quantity=50,
        unit_cost=Decimal('45.00'),
        supplier="NYC Holiday Supply Co"
    )
    
    planner.add_material_to_project(project_id, lights_material)
    
    # Example: Get dashboard summary
    summary = planner.get_dashboard_summary()
    print(f"\nDashboard Summary:")
    print(f"Active Projects: {summary['total_active_projects']}")
    print(f"Total Revenue: ${summary['total_revenue']}")
    print(f"Installations This Week: {summary['installations_this_week']}")


if __name__ == "__main__":
    main()