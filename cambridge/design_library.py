"""
Cambridge NY Design Library
===========================

Library of design templates including holiday decor themes, plantscape layouts,
and flower arrangement styles organized by space type, season, and budget tier.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
import json
import sqlite3
import uuid
from pathlib import Path


class DesignCategory(Enum):
    HOLIDAY_DECOR = "holiday_decor"
    PLANTSCAPE = "plantscape"
    FLOWER_ARRANGEMENT = "flower_arrangement"
    LANDSCAPE_DESIGN = "landscape_design"
    SEASONAL_DISPLAY = "seasonal_display"


class SpaceType(Enum):
    LOBBY = "lobby"
    CONFERENCE_ROOM = "conference_room"
    EXECUTIVE_OFFICE = "executive_office"
    ATRIUM = "atrium"
    RECEPTION_AREA = "reception_area"
    RESTAURANT = "restaurant"
    RETAIL_SPACE = "retail_space"
    OUTDOOR_PLAZA = "outdoor_plaza"
    ROOFTOP_GARDEN = "rooftop_garden"


class Season(Enum):
    SPRING = "spring"
    SUMMER = "summer"
    FALL = "fall"
    WINTER = "winter"
    YEAR_ROUND = "year_round"


class BudgetTier(Enum):
    ECONOMY = "economy"      # $500-1500
    STANDARD = "standard"    # $1500-5000
    PREMIUM = "premium"      # $5000-15000
    LUXURY = "luxury"        # $15000+


class HolidayTheme(Enum):
    CLASSIC_CHRISTMAS = "classic_christmas"
    WINTER_WONDERLAND = "winter_wonderland"
    MODERN_MINIMALIST = "modern_minimalist"
    FESTIVE_CORPORATE = "festive_corporate"
    RUSTIC_CHARM = "rustic_charm"
    ELEGANT_GOLD = "elegant_gold"
    SILVER_SOPHISTICATION = "silver_sophistication"
    TRADITIONAL_RED_GREEN = "traditional_red_green"
    SCANDINAVIAN_STYLE = "scandinavian_style"
    BOTANICAL_HOLIDAY = "botanical_holiday"


@dataclass
class ColorPalette:
    """Color scheme for design templates"""
    palette_id: str
    name: str
    primary_colors: List[str]
    accent_colors: List[str]
    neutral_colors: List[str]
    description: str
    hex_codes: Dict[str, str] = field(default_factory=dict)
    season_compatibility: List[Season] = field(default_factory=list)


@dataclass
class Material:
    """Material specification for designs"""
    material_id: str
    name: str
    category: str  # "plant", "container", "decoration", "lighting", etc.
    description: str
    supplier: str = ""
    average_cost: float = 0.0
    availability_seasons: List[Season] = field(default_factory=list)
    care_requirements: str = ""
    lifespan: str = ""


@dataclass
class DesignElement:
    """Individual element within a design template"""
    element_id: str
    name: str
    description: str
    materials: List[str]  # material_ids
    position: str  # "center", "left", "right", "corner", etc.
    size_category: str  # "small", "medium", "large", "extra_large"
    maintenance_level: str  # "low", "medium", "high"
    cost_estimate: float = 0.0
    installation_time: float = 0.0  # hours


@dataclass
class DesignTemplate:
    """Complete design template"""
    template_id: str
    name: str
    description: str
    category: DesignCategory
    
    # Classification
    space_types: List[SpaceType]
    seasons: List[Season]
    budget_tier: BudgetTier
    holiday_theme: Optional[HolidayTheme] = None
    
    # Design specification
    color_palette: ColorPalette
    design_elements: List[DesignElement]
    layout_notes: str = ""
    style_notes: str = ""
    
    # Practical information
    space_size_min: int = 0  # sq ft
    space_size_max: int = 10000  # sq ft
    installation_time_estimate: float = 0.0  # hours
    maintenance_schedule: str = ""
    
    # Costs and logistics
    material_cost_estimate: float = 0.0
    labor_cost_estimate: float = 0.0
    total_cost_estimate: float = 0.0
    
    # Usage and popularity
    usage_count: int = 0
    client_satisfaction_avg: float = 0.0
    tags: Set[str] = field(default_factory=set)
    
    # Reference materials
    inspiration_images: List[str] = field(default_factory=list)
    reference_projects: List[str] = field(default_factory=list)  # project_ids
    
    # Metadata
    created_date: datetime = field(default_factory=datetime.now)
    updated_date: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    is_active: bool = True
    
    def __post_init__(self):
        """Calculate total cost estimate"""
        if self.material_cost_estimate and self.labor_cost_estimate:
            self.total_cost_estimate = self.material_cost_estimate + self.labor_cost_estimate


@dataclass
class DesignVariation:
    """Variation of a base template for different conditions"""
    variation_id: str
    base_template_id: str
    name: str
    description: str
    
    # What makes this variation different
    modifications: Dict[str, str]  # element_id -> modification description
    space_adaptations: Dict[SpaceType, str]  # space-specific notes
    budget_adaptations: Dict[BudgetTier, str]  # budget-specific modifications
    
    cost_adjustment: float = 0.0  # + or - from base template
    time_adjustment: float = 0.0  # + or - hours from base template


class DesignLibrary:
    """
    Cambridge NY Design Library
    
    Manages design templates, variations, and material specifications
    for all Cambridge NY services with smart recommendations.
    """
    
    def __init__(self, db_path: str = "cambridge_design_library.db"):
        self.db_path = Path(db_path)
        self.init_database()
        
        # Load initial templates if database is empty
        if self._is_database_empty():
            self._populate_initial_templates()
    
    def init_database(self):
        """Initialize design library database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS design_templates (
                    template_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT NOT NULL,
                    space_types TEXT,
                    seasons TEXT,
                    budget_tier TEXT NOT NULL,
                    holiday_theme TEXT,
                    color_palette_data TEXT,
                    design_elements_data TEXT,
                    layout_notes TEXT,
                    style_notes TEXT,
                    space_size_min INTEGER DEFAULT 0,
                    space_size_max INTEGER DEFAULT 10000,
                    installation_time_estimate REAL DEFAULT 0.0,
                    maintenance_schedule TEXT,
                    material_cost_estimate REAL DEFAULT 0.0,
                    labor_cost_estimate REAL DEFAULT 0.0,
                    total_cost_estimate REAL DEFAULT 0.0,
                    usage_count INTEGER DEFAULT 0,
                    client_satisfaction_avg REAL DEFAULT 0.0,
                    tags TEXT,
                    inspiration_images TEXT,
                    reference_projects TEXT,
                    created_date TIMESTAMP,
                    updated_date TIMESTAMP,
                    created_by TEXT,
                    is_active BOOLEAN DEFAULT TRUE
                );
                
                CREATE TABLE IF NOT EXISTS materials_library (
                    material_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT,
                    supplier TEXT,
                    average_cost REAL DEFAULT 0.0,
                    availability_seasons TEXT,
                    care_requirements TEXT,
                    lifespan TEXT,
                    created_date TIMESTAMP,
                    updated_date TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS color_palettes (
                    palette_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    primary_colors TEXT,
                    accent_colors TEXT,
                    neutral_colors TEXT,
                    description TEXT,
                    hex_codes TEXT,
                    season_compatibility TEXT,
                    created_date TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS design_variations (
                    variation_id TEXT PRIMARY KEY,
                    base_template_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    modifications TEXT,
                    space_adaptations TEXT,
                    budget_adaptations TEXT,
                    cost_adjustment REAL DEFAULT 0.0,
                    time_adjustment REAL DEFAULT 0.0,
                    created_date TIMESTAMP,
                    FOREIGN KEY (base_template_id) REFERENCES design_templates(template_id)
                );
                
                CREATE TABLE IF NOT EXISTS template_usage (
                    usage_id TEXT PRIMARY KEY,
                    template_id TEXT NOT NULL,
                    client_id TEXT,
                    project_id TEXT,
                    usage_date DATE,
                    satisfaction_score INTEGER,
                    modifications_made TEXT,
                    notes TEXT,
                    FOREIGN KEY (template_id) REFERENCES design_templates(template_id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_template_category ON design_templates(category);
                CREATE INDEX IF NOT EXISTS idx_template_budget ON design_templates(budget_tier);
                CREATE INDEX IF NOT EXISTS idx_template_space ON design_templates(space_types);
                CREATE INDEX IF NOT EXISTS idx_material_category ON materials_library(category);
                CREATE INDEX IF NOT EXISTS idx_template_usage ON template_usage(template_id, usage_date);
            """)
    
    def create_template(self, template: DesignTemplate) -> str:
        """Create a new design template"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO design_templates (
                    template_id, name, description, category, space_types, seasons,
                    budget_tier, holiday_theme, color_palette_data, design_elements_data,
                    layout_notes, style_notes, space_size_min, space_size_max,
                    installation_time_estimate, maintenance_schedule,
                    material_cost_estimate, labor_cost_estimate, total_cost_estimate,
                    usage_count, client_satisfaction_avg, tags, inspiration_images,
                    reference_projects, created_date, updated_date, created_by, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                template.template_id, template.name, template.description,
                template.category.value, json.dumps([st.value for st in template.space_types]),
                json.dumps([s.value for s in template.seasons]), template.budget_tier.value,
                template.holiday_theme.value if template.holiday_theme else None,
                json.dumps(template.color_palette.__dict__),
                json.dumps([elem.__dict__ for elem in template.design_elements]),
                template.layout_notes, template.style_notes, template.space_size_min,
                template.space_size_max, template.installation_time_estimate,
                template.maintenance_schedule, template.material_cost_estimate,
                template.labor_cost_estimate, template.total_cost_estimate,
                template.usage_count, template.client_satisfaction_avg,
                json.dumps(list(template.tags)), json.dumps(template.inspiration_images),
                json.dumps(template.reference_projects), template.created_date,
                template.updated_date, template.created_by, template.is_active
            ))
        
        return template.template_id
    
    def get_template(self, template_id: str) -> Optional[DesignTemplate]:
        """Retrieve design template by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM design_templates WHERE template_id = ?", (template_id,)
            ).fetchone()
            
            if not row:
                return None
            
            # Reconstruct color palette
            palette_data = json.loads(row['color_palette_data']) if row['color_palette_data'] else {}
            color_palette = ColorPalette(**palette_data) if palette_data else ColorPalette(
                palette_id="default", name="Default", primary_colors=[], 
                accent_colors=[], neutral_colors=[], description=""
            )
            
            # Reconstruct design elements
            elements_data = json.loads(row['design_elements_data']) if row['design_elements_data'] else []
            design_elements = [DesignElement(**elem_data) for elem_data in elements_data]
            
            template = DesignTemplate(
                template_id=row['template_id'],
                name=row['name'],
                description=row['description'] or '',
                category=DesignCategory(row['category']),
                space_types=[SpaceType(st) for st in json.loads(row['space_types'])] if row['space_types'] else [],
                seasons=[Season(s) for s in json.loads(row['seasons'])] if row['seasons'] else [],
                budget_tier=BudgetTier(row['budget_tier']),
                holiday_theme=HolidayTheme(row['holiday_theme']) if row['holiday_theme'] else None,
                color_palette=color_palette,
                design_elements=design_elements,
                layout_notes=row['layout_notes'] or '',
                style_notes=row['style_notes'] or '',
                space_size_min=row['space_size_min'] or 0,
                space_size_max=row['space_size_max'] or 10000,
                installation_time_estimate=row['installation_time_estimate'] or 0.0,
                maintenance_schedule=row['maintenance_schedule'] or '',
                material_cost_estimate=row['material_cost_estimate'] or 0.0,
                labor_cost_estimate=row['labor_cost_estimate'] or 0.0,
                total_cost_estimate=row['total_cost_estimate'] or 0.0,
                usage_count=row['usage_count'] or 0,
                client_satisfaction_avg=row['client_satisfaction_avg'] or 0.0,
                tags=set(json.loads(row['tags'])) if row['tags'] else set(),
                inspiration_images=json.loads(row['inspiration_images']) if row['inspiration_images'] else [],
                reference_projects=json.loads(row['reference_projects']) if row['reference_projects'] else [],
                created_date=datetime.fromisoformat(row['created_date']) if row['created_date'] else datetime.now(),
                updated_date=datetime.fromisoformat(row['updated_date']) if row['updated_date'] else datetime.now(),
                created_by=row['created_by'] or '',
                is_active=bool(row['is_active'])
            )
            
            return template
    
    def search_templates(self, category: Optional[DesignCategory] = None,
                        space_type: Optional[SpaceType] = None,
                        season: Optional[Season] = None,
                        budget_tier: Optional[BudgetTier] = None,
                        holiday_theme: Optional[HolidayTheme] = None,
                        space_size: Optional[int] = None,
                        tags: List[str] = None) -> List[DesignTemplate]:
        """Search design templates with filters"""
        
        conditions = ["is_active = TRUE"]
        params = []
        
        if category:
            conditions.append("category = ?")
            params.append(category.value)
        
        if space_type:
            conditions.append("space_types LIKE ?")
            params.append(f'%{space_type.value}%')
        
        if season:
            conditions.append("seasons LIKE ?")
            params.append(f'%{season.value}%')
        
        if budget_tier:
            conditions.append("budget_tier = ?")
            params.append(budget_tier.value)
        
        if holiday_theme:
            conditions.append("holiday_theme = ?")
            params.append(holiday_theme.value)
        
        if space_size:
            conditions.append("space_size_min <= ? AND space_size_max >= ?")
            params.extend([space_size, space_size])
        
        if tags:
            for tag in tags:
                conditions.append("tags LIKE ?")
                params.append(f'%{tag}%')
        
        where_clause = " AND ".join(conditions)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(f"""
                SELECT template_id FROM design_templates 
                WHERE {where_clause}
                ORDER BY client_satisfaction_avg DESC, usage_count DESC
            """, params).fetchall()
        
        templates = []
        for row in rows:
            template = self.get_template(row['template_id'])
            if template:
                templates.append(template)
        
        return templates
    
    def get_recommendations(self, space_type: SpaceType, season: Season,
                          budget_tier: BudgetTier, space_size: int,
                          category: Optional[DesignCategory] = None) -> Dict:
        """Get personalized template recommendations"""
        
        # Search for matching templates
        matching_templates = self.search_templates(
            category=category,
            space_type=space_type,
            season=season,
            budget_tier=budget_tier,
            space_size=space_size
        )
        
        # Also get templates from adjacent budget tiers
        adjacent_budget_templates = []
        budget_order = [BudgetTier.ECONOMY, BudgetTier.STANDARD, BudgetTier.PREMIUM, BudgetTier.LUXURY]
        current_idx = budget_order.index(budget_tier)
        
        for adjacent_idx in [current_idx - 1, current_idx + 1]:
            if 0 <= adjacent_idx < len(budget_order):
                adjacent_budget = budget_order[adjacent_idx]
                adjacent_templates = self.search_templates(
                    space_type=space_type,
                    season=season,
                    budget_tier=adjacent_budget,
                    space_size=space_size
                )[:3]  # Limit to top 3
                adjacent_budget_templates.extend(adjacent_templates)
        
        # Get seasonal alternatives
        seasonal_alternatives = []
        other_seasons = [s for s in Season if s != season and s != Season.YEAR_ROUND]
        for other_season in other_seasons[:2]:  # Limit to 2 other seasons
            alt_templates = self.search_templates(
                space_type=space_type,
                season=other_season,
                budget_tier=budget_tier,
                space_size=space_size
            )[:2]  # Limit to top 2 per season
            seasonal_alternatives.extend(alt_templates)
        
        recommendations = {
            "exact_matches": matching_templates[:5],  # Top 5 exact matches
            "budget_alternatives": adjacent_budget_templates[:4],  # Top 4 budget alternatives
            "seasonal_alternatives": seasonal_alternatives[:4],  # Top 4 seasonal alternatives
            "popular_choices": self._get_popular_templates(space_type, budget_tier)[:3],  # Top 3 popular
            "criteria": {
                "space_type": space_type.value,
                "season": season.value,
                "budget_tier": budget_tier.value,
                "space_size": space_size,
                "category": category.value if category else "any"
            }
        }
        
        return recommendations
    
    def record_template_usage(self, template_id: str, client_id: str,
                            project_id: Optional[str] = None,
                            satisfaction_score: Optional[int] = None,
                            modifications_made: str = "",
                            notes: str = "") -> str:
        """Record template usage for analytics"""
        
        usage_id = f"USAGE-{uuid.uuid4().hex[:10].upper()}"
        
        with sqlite3.connect(self.db_path) as conn:
            # Record usage
            conn.execute("""
                INSERT INTO template_usage (
                    usage_id, template_id, client_id, project_id,
                    usage_date, satisfaction_score, modifications_made, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                usage_id, template_id, client_id, project_id,
                date.today(), satisfaction_score, modifications_made, notes
            ))
            
            # Update template usage count
            conn.execute("""
                UPDATE design_templates 
                SET usage_count = usage_count + 1,
                    updated_date = ?
                WHERE template_id = ?
            """, (datetime.now(), template_id))
            
            # Update satisfaction average if score provided
            if satisfaction_score:
                self._update_template_satisfaction(conn, template_id, satisfaction_score)
        
        return usage_id
    
    def add_material(self, material: Material) -> str:
        """Add material to the library"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO materials_library (
                    material_id, name, category, description, supplier,
                    average_cost, availability_seasons, care_requirements,
                    lifespan, created_date, updated_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                material.material_id, material.name, material.category,
                material.description, material.supplier, material.average_cost,
                json.dumps([s.value for s in material.availability_seasons]),
                material.care_requirements, material.lifespan,
                datetime.now(), datetime.now()
            ))
        
        return material.material_id
    
    def get_materials_by_category(self, category: str, season: Optional[Season] = None) -> List[Material]:
        """Get materials filtered by category and optionally season"""
        conditions = ["category = ?"]
        params = [category]
        
        if season:
            conditions.append("(availability_seasons LIKE ? OR availability_seasons LIKE ?)")
            params.extend([f'%{season.value}%', '%year_round%'])
        
        where_clause = " AND ".join(conditions)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(f"""
                SELECT * FROM materials_library 
                WHERE {where_clause}
                ORDER BY name
            """, params).fetchall()
        
        materials = []
        for row in rows:
            material = Material(
                material_id=row['material_id'],
                name=row['name'],
                category=row['category'],
                description=row['description'] or '',
                supplier=row['supplier'] or '',
                average_cost=row['average_cost'] or 0.0,
                availability_seasons=[Season(s) for s in json.loads(row['availability_seasons'])] if row['availability_seasons'] else [],
                care_requirements=row['care_requirements'] or '',
                lifespan=row['lifespan'] or ''
            )
            materials.append(material)
        
        return materials
    
    def create_color_palette(self, palette: ColorPalette) -> str:
        """Create a color palette"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO color_palettes (
                    palette_id, name, primary_colors, accent_colors,
                    neutral_colors, description, hex_codes, season_compatibility,
                    created_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                palette.palette_id, palette.name,
                json.dumps(palette.primary_colors),
                json.dumps(palette.accent_colors),
                json.dumps(palette.neutral_colors),
                palette.description,
                json.dumps(palette.hex_codes),
                json.dumps([s.value for s in palette.season_compatibility]),
                datetime.now()
            ))
        
        return palette.palette_id
    
    def get_color_palettes(self, season: Optional[Season] = None) -> List[ColorPalette]:
        """Get color palettes, optionally filtered by season"""
        conditions = []
        params = []
        
        if season:
            conditions.append("season_compatibility LIKE ?")
            params.append(f'%{season.value}%')
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(f"""
                SELECT * FROM color_palettes 
                WHERE {where_clause}
                ORDER BY name
            """, params).fetchall()
        
        palettes = []
        for row in rows:
            palette = ColorPalette(
                palette_id=row['palette_id'],
                name=row['name'],
                primary_colors=json.loads(row['primary_colors']) if row['primary_colors'] else [],
                accent_colors=json.loads(row['accent_colors']) if row['accent_colors'] else [],
                neutral_colors=json.loads(row['neutral_colors']) if row['neutral_colors'] else [],
                description=row['description'] or '',
                hex_codes=json.loads(row['hex_codes']) if row['hex_codes'] else {},
                season_compatibility=[Season(s) for s in json.loads(row['season_compatibility'])] if row['season_compatibility'] else []
            )
            palettes.append(palette)
        
        return palettes
    
    def _is_database_empty(self) -> bool:
        """Check if database needs initial population"""
        with sqlite3.connect(self.db_path) as conn:
            count = conn.execute("SELECT COUNT(*) FROM design_templates").fetchone()[0]
            return count == 0
    
    def _populate_initial_templates(self):
        """Populate database with initial design templates"""
        
        # Create color palettes first
        self._create_initial_color_palettes()
        
        # Create materials library
        self._create_initial_materials()
        
        # Create design templates
        self._create_holiday_decor_templates()
        self._create_plantscape_templates()
        self._create_flower_arrangement_templates()
    
    def _create_initial_color_palettes(self):
        """Create initial color palettes"""
        palettes = [
            ColorPalette(
                palette_id="CP-CLASSIC-XMAS",
                name="Classic Christmas",
                primary_colors=["Deep Red", "Forest Green"],
                accent_colors=["Gold", "Cream"],
                neutral_colors=["White", "Natural Wood"],
                description="Traditional Christmas color scheme",
                hex_codes={"Deep Red": "#8B0000", "Forest Green": "#228B22", "Gold": "#FFD700"},
                season_compatibility=[Season.WINTER]
            ),
            ColorPalette(
                palette_id="CP-WINTER-WHITE",
                name="Winter Wonderland",
                primary_colors=["Pure White", "Silver"],
                accent_colors=["Ice Blue", "Crystal"],
                neutral_colors=["Pewter Gray", "Soft Blue"],
                description="Elegant winter white theme",
                hex_codes={"Pure White": "#FFFFFF", "Silver": "#C0C0C0", "Ice Blue": "#B0E0E6"},
                season_compatibility=[Season.WINTER]
            ),
            ColorPalette(
                palette_id="CP-SPRING-FRESH",
                name="Fresh Spring",
                primary_colors=["Sage Green", "Soft Yellow"],
                accent_colors=["Lavender", "Peach"],
                neutral_colors=["Cream", "Light Gray"],
                description="Fresh spring color palette",
                hex_codes={"Sage Green": "#9CAF88", "Soft Yellow": "#FFFFE0", "Lavender": "#E6E6FA"},
                season_compatibility=[Season.SPRING]
            )
        ]
        
        for palette in palettes:
            self.create_color_palette(palette)
    
    def _create_initial_materials(self):
        """Create initial materials library"""
        materials = [
            # Plants
            Material(
                material_id="MAT-FICUS-TREE",
                name="Ficus Benjamina Tree",
                category="plant",
                description="Classic indoor tree, 6-8 feet tall",
                supplier="NYC Plant Wholesale",
                average_cost=150.00,
                availability_seasons=[Season.YEAR_ROUND],
                care_requirements="Medium light, weekly watering",
                lifespan="5+ years with proper care"
            ),
            # Holiday Decor
            Material(
                material_id="MAT-FRASER-FIR",
                name="Fraser Fir Christmas Tree",
                category="holiday_tree",
                description="Premium Christmas tree, 8-12 feet",
                supplier="Vermont Tree Farm",
                average_cost=120.00,
                availability_seasons=[Season.WINTER],
                care_requirements="Daily watering, cool location",
                lifespan="6-8 weeks"
            ),
            # Containers
            Material(
                material_id="MAT-CERAMIC-PLANTER",
                name="Large Ceramic Planter",
                category="container",
                description="High-quality ceramic planter, various sizes",
                supplier="Design Ceramics Inc",
                average_cost=75.00,
                availability_seasons=[Season.YEAR_ROUND],
                care_requirements="Drainage holes required",
                lifespan="10+ years"
            )
        ]
        
        for material in materials:
            self.add_material(material)
    
    def _create_holiday_decor_templates(self):
        """Create holiday decoration templates"""
        
        # Get color palette
        classic_palette = ColorPalette(
            palette_id="CP-CLASSIC-XMAS",
            name="Classic Christmas",
            primary_colors=["Deep Red", "Forest Green"],
            accent_colors=["Gold", "Cream"],
            neutral_colors=["White", "Natural Wood"],
            description="Traditional Christmas color scheme"
        )
        
        # Design elements
        elements = [
            DesignElement(
                element_id="ELEM-MAIN-TREE",
                name="Main Christmas Tree",
                description="9-foot Fraser Fir with warm LED lights",
                materials=["MAT-FRASER-FIR", "MAT-LED-LIGHTS", "MAT-TREE-STAND"],
                position="center",
                size_category="large",
                maintenance_level="medium",
                cost_estimate=800.00,
                installation_time=3.0
            ),
            DesignElement(
                element_id="ELEM-GARLAND",
                name="Entrance Garland",
                description="Fresh garland with ribbon accents",
                materials=["MAT-FRESH-GARLAND", "MAT-RIBBON", "MAT-ORNAMENTS"],
                position="entrance",
                size_category="medium",
                maintenance_level="low",
                cost_estimate=200.00,
                installation_time=1.5
            )
        ]
        
        # Classic Christmas template
        template = DesignTemplate(
            template_id="TMPL-CLASSIC-XMAS-LOBBY",
            name="Classic Christmas Lobby",
            description="Traditional Christmas decoration for corporate lobbies",
            category=DesignCategory.HOLIDAY_DECOR,
            space_types=[SpaceType.LOBBY, SpaceType.RECEPTION_AREA],
            seasons=[Season.WINTER],
            budget_tier=BudgetTier.STANDARD,
            holiday_theme=HolidayTheme.CLASSIC_CHRISTMAS,
            color_palette=classic_palette,
            design_elements=elements,
            layout_notes="Center tree with supporting garland elements",
            style_notes="Warm, inviting, professionally elegant",
            space_size_min=500,
            space_size_max=2000,
            installation_time_estimate=6.0,
            maintenance_schedule="Weekly watering and light maintenance",
            material_cost_estimate=1200.00,
            labor_cost_estimate=800.00,
            tags={"classic", "professional", "traditional", "lobby"},
            created_by="Design Team"
        )
        
        self.create_template(template)
    
    def _create_plantscape_templates(self):
        """Create plantscape templates"""
        
        green_palette = ColorPalette(
            palette_id="CP-NATURAL-GREEN",
            name="Natural Green",
            primary_colors=["Forest Green", "Sage Green"],
            accent_colors=["Earth Brown", "Stone Gray"],
            neutral_colors=["White", "Natural Wood"],
            description="Natural plant-focused color scheme"
        )
        
        elements = [
            DesignElement(
                element_id="ELEM-FEATURE-PLANT",
                name="Feature Plant Display",
                description="Large statement plant in premium container",
                materials=["MAT-FICUS-TREE", "MAT-CERAMIC-PLANTER"],
                position="corner",
                size_category="large",
                maintenance_level="medium",
                cost_estimate=400.00,
                installation_time=1.0
            )
        ]
        
        template = DesignTemplate(
            template_id="TMPL-EXEC-OFFICE-PLANTS",
            name="Executive Office Plantscape",
            description="Professional plant arrangement for executive offices",
            category=DesignCategory.PLANTSCAPE,
            space_types=[SpaceType.EXECUTIVE_OFFICE],
            seasons=[Season.YEAR_ROUND],
            budget_tier=BudgetTier.PREMIUM,
            color_palette=green_palette,
            design_elements=elements,
            layout_notes="Corner placement with accent plants",
            style_notes="Sophisticated, low-maintenance, air-purifying",
            space_size_min=200,
            space_size_max=800,
            installation_time_estimate=3.0,
            maintenance_schedule="Bi-weekly professional care",
            material_cost_estimate=800.00,
            labor_cost_estimate=400.00,
            tags={"executive", "professional", "plants", "low-maintenance"},
            created_by="Design Team"
        )
        
        self.create_template(template)
    
    def _create_flower_arrangement_templates(self):
        """Create flower arrangement templates"""
        
        # Implementation for flower arrangement templates
        # Similar structure to above methods
        pass
    
    def _get_popular_templates(self, space_type: SpaceType, budget_tier: BudgetTier) -> List[DesignTemplate]:
        """Get popular templates for space type and budget"""
        return self.search_templates(space_type=space_type, budget_tier=budget_tier)[:5]
    
    def _update_template_satisfaction(self, conn, template_id: str, new_score: int):
        """Update template satisfaction average"""
        # Get current satisfaction data
        current_data = conn.execute("""
            SELECT client_satisfaction_avg, usage_count FROM design_templates
            WHERE template_id = ?
        """, (template_id,)).fetchone()
        
        if current_data:
            current_avg, usage_count = current_data
            # Calculate new average
            total_score = (current_avg * usage_count) + new_score
            new_avg = total_score / (usage_count + 1)
            
            conn.execute("""
                UPDATE design_templates 
                SET client_satisfaction_avg = ?
                WHERE template_id = ?
            """, (new_avg, template_id))


# Example usage
if __name__ == "__main__":
    # Initialize design library
    library = DesignLibrary()
    
    # Search for holiday decor templates
    holiday_templates = library.search_templates(
        category=DesignCategory.HOLIDAY_DECOR,
        space_type=SpaceType.LOBBY,
        season=Season.WINTER,
        budget_tier=BudgetTier.STANDARD
    )
    
    print(f"Found {len(holiday_templates)} holiday decoration templates")
    
    # Get recommendations
    recommendations = library.get_recommendations(
        space_type=SpaceType.LOBBY,
        season=Season.WINTER,
        budget_tier=BudgetTier.STANDARD,
        space_size=1200,
        category=DesignCategory.HOLIDAY_DECOR
    )
    
    print(f"Recommendations:")
    print(f"- Exact matches: {len(recommendations['exact_matches'])}")
    print(f"- Budget alternatives: {len(recommendations['budget_alternatives'])}")
    print(f"- Popular choices: {len(recommendations['popular_choices'])}")
    
    # Record template usage
    if holiday_templates:
        usage_id = library.record_template_usage(
            template_id=holiday_templates[0].template_id,
            client_id="CL001",
            satisfaction_score=9,
            notes="Client loved the classic Christmas theme"
        )
        print(f"Recorded usage: {usage_id}")
    
    print("Design library ready for use!")