"""
Cambridge NY Photo Organizer
============================

Organize project photos by client, location, date, and service type with tagging
and portfolio gallery generation for proposals.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
import json
import sqlite3
import uuid
import os
import shutil
from pathlib import Path
from PIL import Image, ExifTags
import hashlib


class ServiceType(Enum):
    LANDSCAPING = "landscaping"
    HOLIDAY_DECOR = "holiday_decor"
    PLANTS = "plants"
    LOBBY_FLOWERS = "lobby_flowers"
    MAINTENANCE = "maintenance"
    DESIGN_CONSULTATION = "design_consultation"


class PhotoType(Enum):
    BEFORE = "before"
    AFTER = "after"
    DURING = "during"
    ISSUE = "issue"
    DETAIL = "detail"
    OVERVIEW = "overview"
    PORTFOLIO = "portfolio"


class PhotoCategory(Enum):
    PROJECT_WORK = "project_work"
    MAINTENANCE_VISIT = "maintenance_visit"
    ISSUE_DOCUMENTATION = "issue_documentation"
    PORTFOLIO_SHOWCASE = "portfolio_showcase"
    MARKETING_MATERIAL = "marketing_material"


@dataclass
class PhotoMetadata:
    """Photo metadata extracted from file"""
    width: int
    height: int
    file_size: int
    taken_date: Optional[datetime] = None
    camera_make: str = ""
    camera_model: str = ""
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None


@dataclass
class Photo:
    """Photo record with organization metadata"""
    photo_id: str
    filename: str
    original_filename: str
    file_path: str
    file_hash: str  # For duplicate detection
    
    # Organization fields
    client_id: str
    client_name: str
    project_id: Optional[str] = None
    visit_id: Optional[str] = None
    location: str = ""
    
    # Categorization
    service_type: ServiceType
    photo_type: PhotoType
    photo_category: PhotoCategory
    
    # Tags and description
    tags: Set[str] = field(default_factory=set)
    description: str = ""
    notes: str = ""
    
    # Technical metadata
    metadata: Optional[PhotoMetadata] = None
    
    # Quality and usage flags
    portfolio_quality: bool = False
    client_approved: bool = False
    marketing_approved: bool = False
    public_use_approved: bool = False
    
    # Timestamps
    taken_date: datetime = field(default_factory=datetime.now)
    uploaded_date: datetime = field(default_factory=datetime.now)
    updated_date: datetime = field(default_factory=datetime.now)
    
    # Photographer and context
    photographer: str = ""
    weather_conditions: str = ""
    time_of_day: str = ""


@dataclass
class PhotoGallery:
    """Collection of photos for portfolio or presentation"""
    gallery_id: str
    name: str
    description: str
    client_id: Optional[str] = None
    service_type: Optional[ServiceType] = None
    photo_ids: List[str] = field(default_factory=list)
    cover_photo_id: Optional[str] = None
    
    # Gallery organization
    tags: Set[str] = field(default_factory=set)
    is_public: bool = False
    is_portfolio: bool = False
    
    # Metadata
    created_date: datetime = field(default_factory=datetime.now)
    updated_date: datetime = field(default_factory=datetime.now)
    created_by: str = ""


class PhotoOrganizer:
    """
    Cambridge NY Photo Organization System
    
    Manages project photos with intelligent organization, tagging,
    and portfolio gallery generation for business use.
    """
    
    def __init__(self, storage_root: str = "cambridge_photos", db_path: str = "cambridge_photos.db"):
        self.storage_root = Path(storage_root)
        self.db_path = Path(db_path)
        
        # Create storage directories
        self.storage_root.mkdir(exist_ok=True)
        self._create_directory_structure()
        
        # Initialize database
        self.init_database()
    
    def _create_directory_structure(self):
        """Create organized directory structure"""
        directories = [
            "raw_uploads",
            "organized/clients",
            "organized/service_types",
            "organized/dates",
            "portfolios",
            "galleries",
            "temp",
            "thumbnails"
        ]
        
        for directory in directories:
            (self.storage_root / directory).mkdir(parents=True, exist_ok=True)
    
    def init_database(self):
        """Initialize photo organization database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS photos (
                    photo_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    original_filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    client_id TEXT NOT NULL,
                    client_name TEXT NOT NULL,
                    project_id TEXT,
                    visit_id TEXT,
                    location TEXT,
                    service_type TEXT NOT NULL,
                    photo_type TEXT NOT NULL,
                    photo_category TEXT NOT NULL,
                    tags TEXT,
                    description TEXT,
                    notes TEXT,
                    portfolio_quality BOOLEAN DEFAULT FALSE,
                    client_approved BOOLEAN DEFAULT FALSE,
                    marketing_approved BOOLEAN DEFAULT FALSE,
                    public_use_approved BOOLEAN DEFAULT FALSE,
                    taken_date TIMESTAMP,
                    uploaded_date TIMESTAMP,
                    updated_date TIMESTAMP,
                    photographer TEXT,
                    weather_conditions TEXT,
                    time_of_day TEXT,
                    
                    -- Metadata
                    width INTEGER,
                    height INTEGER,
                    file_size INTEGER,
                    camera_make TEXT,
                    camera_model TEXT,
                    gps_latitude REAL,
                    gps_longitude REAL
                );
                
                CREATE TABLE IF NOT EXISTS photo_galleries (
                    gallery_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    client_id TEXT,
                    service_type TEXT,
                    photo_ids TEXT,
                    cover_photo_id TEXT,
                    tags TEXT,
                    is_public BOOLEAN DEFAULT FALSE,
                    is_portfolio BOOLEAN DEFAULT FALSE,
                    created_date TIMESTAMP,
                    updated_date TIMESTAMP,
                    created_by TEXT
                );
                
                CREATE TABLE IF NOT EXISTS photo_tags (
                    tag_id TEXT PRIMARY KEY,
                    tag_name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    color TEXT,
                    usage_count INTEGER DEFAULT 0,
                    created_date TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_photo_client ON photos(client_id);
                CREATE INDEX IF NOT EXISTS idx_photo_service ON photos(service_type);
                CREATE INDEX IF NOT EXISTS idx_photo_date ON photos(taken_date);
                CREATE INDEX IF NOT EXISTS idx_photo_type ON photos(photo_type);
                CREATE INDEX IF NOT EXISTS idx_photo_hash ON photos(file_hash);
                CREATE INDEX IF NOT EXISTS idx_gallery_client ON photo_galleries(client_id);
            """)
        
        # Initialize common tags
        self._initialize_default_tags()
    
    def upload_photo(self, file_path: str, client_id: str, client_name: str,
                    service_type: ServiceType, photo_type: PhotoType,
                    photo_category: PhotoCategory, **kwargs) -> str:
        """Upload and organize a photo"""
        
        if not os.path.exists(file_path):
            raise ValueError(f"Photo file not found: {file_path}")
        
        # Generate photo ID and calculate hash
        photo_id = f"PH-{uuid.uuid4().hex[:12].upper()}"
        file_hash = self._calculate_file_hash(file_path)
        
        # Check for duplicates
        existing = self._find_duplicate_by_hash(file_hash)
        if existing:
            raise ValueError(f"Duplicate photo detected. Existing photo ID: {existing}")
        
        # Extract metadata
        metadata = self._extract_photo_metadata(file_path)
        
        # Generate organized filename and path
        original_filename = os.path.basename(file_path)
        organized_filename = self._generate_organized_filename(
            photo_id, client_name, service_type, photo_type, original_filename
        )
        
        organized_path = self._get_organized_path(client_id, service_type, photo_category)
        full_organized_path = organized_path / organized_filename
        
        # Copy file to organized location
        os.makedirs(organized_path, exist_ok=True)
        shutil.copy2(file_path, full_organized_path)
        
        # Create photo record
        photo = Photo(
            photo_id=photo_id,
            filename=organized_filename,
            original_filename=original_filename,
            file_path=str(full_organized_path),
            file_hash=file_hash,
            client_id=client_id,
            client_name=client_name,
            service_type=service_type,
            photo_type=photo_type,
            photo_category=photo_category,
            metadata=metadata,
            **kwargs
        )
        
        # Auto-tag based on analysis
        photo.tags.update(self._auto_generate_tags(photo, metadata))
        
        # Save to database
        self._save_photo_to_db(photo)
        
        # Generate thumbnail
        self._generate_thumbnail(full_organized_path, photo_id)
        
        return photo_id
    
    def get_photo(self, photo_id: str) -> Optional[Photo]:
        """Retrieve photo by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM photos WHERE photo_id = ?", (photo_id,)
            ).fetchone()
            
            if not row:
                return None
            
            metadata = PhotoMetadata(
                width=row['width'] or 0,
                height=row['height'] or 0,
                file_size=row['file_size'] or 0,
                taken_date=datetime.fromisoformat(row['taken_date']) if row['taken_date'] else None,
                camera_make=row['camera_make'] or '',
                camera_model=row['camera_model'] or '',
                gps_latitude=row['gps_latitude'],
                gps_longitude=row['gps_longitude']
            ) if any([row['width'], row['height'], row['file_size']]) else None
            
            photo = Photo(
                photo_id=row['photo_id'],
                filename=row['filename'],
                original_filename=row['original_filename'],
                file_path=row['file_path'],
                file_hash=row['file_hash'],
                client_id=row['client_id'],
                client_name=row['client_name'],
                project_id=row['project_id'],
                visit_id=row['visit_id'],
                location=row['location'] or '',
                service_type=ServiceType(row['service_type']),
                photo_type=PhotoType(row['photo_type']),
                photo_category=PhotoCategory(row['photo_category']),
                tags=set(json.loads(row['tags'])) if row['tags'] else set(),
                description=row['description'] or '',
                notes=row['notes'] or '',
                portfolio_quality=bool(row['portfolio_quality']),
                client_approved=bool(row['client_approved']),
                marketing_approved=bool(row['marketing_approved']),
                public_use_approved=bool(row['public_use_approved']),
                taken_date=datetime.fromisoformat(row['taken_date']) if row['taken_date'] else datetime.now(),
                uploaded_date=datetime.fromisoformat(row['uploaded_date']) if row['uploaded_date'] else datetime.now(),
                updated_date=datetime.fromisoformat(row['updated_date']) if row['updated_date'] else datetime.now(),
                photographer=row['photographer'] or '',
                weather_conditions=row['weather_conditions'] or '',
                time_of_day=row['time_of_day'] or '',
                metadata=metadata
            )
            
            return photo
    
    def update_photo(self, photo: Photo) -> bool:
        """Update photo record"""
        photo.updated_date = datetime.now()
        
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute("""
                UPDATE photos SET
                    description = ?, notes = ?, tags = ?, location = ?,
                    portfolio_quality = ?, client_approved = ?, marketing_approved = ?,
                    public_use_approved = ?, photographer = ?, weather_conditions = ?,
                    time_of_day = ?, updated_date = ?
                WHERE photo_id = ?
            """, (
                photo.description, photo.notes, json.dumps(list(photo.tags)),
                photo.location, photo.portfolio_quality, photo.client_approved,
                photo.marketing_approved, photo.public_use_approved,
                photo.photographer, photo.weather_conditions, photo.time_of_day,
                photo.updated_date, photo.photo_id
            ))
            
            return result.rowcount > 0
    
    def search_photos(self, client_id: Optional[str] = None, 
                     service_type: Optional[ServiceType] = None,
                     photo_type: Optional[PhotoType] = None,
                     tags: List[str] = None,
                     date_from: Optional[date] = None,
                     date_to: Optional[date] = None,
                     portfolio_only: bool = False,
                     approved_only: bool = False) -> List[Photo]:
        """Search photos with flexible filters"""
        
        conditions = []
        params = []
        
        if client_id:
            conditions.append("client_id = ?")
            params.append(client_id)
        
        if service_type:
            conditions.append("service_type = ?")
            params.append(service_type.value)
        
        if photo_type:
            conditions.append("photo_type = ?")
            params.append(photo_type.value)
        
        if portfolio_only:
            conditions.append("portfolio_quality = TRUE")
        
        if approved_only:
            conditions.append("client_approved = TRUE")
        
        if date_from:
            conditions.append("date(taken_date) >= ?")
            params.append(date_from)
        
        if date_to:
            conditions.append("date(taken_date) <= ?")
            params.append(date_to)
        
        if tags:
            for tag in tags:
                conditions.append("tags LIKE ?")
                params.append(f'%{tag}%')
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(f"""
                SELECT photo_id FROM photos 
                WHERE {where_clause}
                ORDER BY taken_date DESC
            """, params).fetchall()
        
        photos = []
        for row in rows:
            photo = self.get_photo(row['photo_id'])
            if photo:
                photos.append(photo)
        
        return photos
    
    def create_gallery(self, name: str, description: str, photo_ids: List[str],
                      client_id: Optional[str] = None, 
                      service_type: Optional[ServiceType] = None,
                      **kwargs) -> str:
        """Create a photo gallery"""
        
        gallery_id = f"GAL-{uuid.uuid4().hex[:10].upper()}"
        
        # Validate photos exist
        valid_photos = []
        for photo_id in photo_ids:
            if self.get_photo(photo_id):
                valid_photos.append(photo_id)
        
        if not valid_photos:
            raise ValueError("No valid photos provided for gallery")
        
        gallery = PhotoGallery(
            gallery_id=gallery_id,
            name=name,
            description=description,
            client_id=client_id,
            service_type=service_type,
            photo_ids=valid_photos,
            cover_photo_id=valid_photos[0],  # First photo as default cover
            **kwargs
        )
        
        # Save to database
        self._save_gallery_to_db(gallery)
        
        return gallery_id
    
    def get_gallery(self, gallery_id: str) -> Optional[PhotoGallery]:
        """Retrieve gallery by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM photo_galleries WHERE gallery_id = ?", (gallery_id,)
            ).fetchone()
            
            if not row:
                return None
            
            gallery = PhotoGallery(
                gallery_id=row['gallery_id'],
                name=row['name'],
                description=row['description'] or '',
                client_id=row['client_id'],
                service_type=ServiceType(row['service_type']) if row['service_type'] else None,
                photo_ids=json.loads(row['photo_ids']) if row['photo_ids'] else [],
                cover_photo_id=row['cover_photo_id'],
                tags=set(json.loads(row['tags'])) if row['tags'] else set(),
                is_public=bool(row['is_public']),
                is_portfolio=bool(row['is_portfolio']),
                created_date=datetime.fromisoformat(row['created_date']) if row['created_date'] else datetime.now(),
                updated_date=datetime.fromisoformat(row['updated_date']) if row['updated_date'] else datetime.now(),
                created_by=row['created_by'] or ''
            )
            
            return gallery
    
    def generate_portfolio_gallery(self, service_type: ServiceType, 
                                  max_photos: int = 20) -> str:
        """Generate portfolio gallery for a service type"""
        
        # Find best portfolio-quality photos
        photos = self.search_photos(
            service_type=service_type,
            portfolio_only=True,
            approved_only=True
        )
        
        if not photos:
            raise ValueError(f"No portfolio-quality photos found for {service_type.value}")
        
        # Select diverse photos (before/after pairs, different clients, etc.)
        selected_photos = self._select_portfolio_photos(photos, max_photos)
        
        gallery_name = f"{service_type.value.replace('_', ' ').title()} Portfolio"
        
        gallery_id = self.create_gallery(
            name=gallery_name,
            description=f"Professional portfolio showcasing Cambridge NY's {service_type.value.replace('_', ' ')} services",
            photo_ids=[p.photo_id for p in selected_photos],
            service_type=service_type,
            is_portfolio=True,
            is_public=True,
            created_by="System Generated"
        )
        
        return gallery_id
    
    def get_client_photos(self, client_id: str, 
                         include_thumbnails: bool = True) -> Dict:
        """Get all photos for a client organized by service type"""
        
        photos = self.search_photos(client_id=client_id)
        
        organized = {
            "client_id": client_id,
            "total_photos": len(photos),
            "by_service_type": {},
            "by_photo_type": {},
            "recent_photos": []
        }
        
        # Organize by service type
        for photo in photos:
            service = photo.service_type.value
            if service not in organized["by_service_type"]:
                organized["by_service_type"][service] = []
            organized["by_service_type"][service].append({
                "photo_id": photo.photo_id,
                "filename": photo.filename,
                "photo_type": photo.photo_type.value,
                "taken_date": photo.taken_date.isoformat(),
                "description": photo.description,
                "thumbnail_path": self._get_thumbnail_path(photo.photo_id) if include_thumbnails else None
            })
        
        # Organize by photo type  
        for photo in photos:
            ptype = photo.photo_type.value
            if ptype not in organized["by_photo_type"]:
                organized["by_photo_type"][ptype] = 0
            organized["by_photo_type"][ptype] += 1
        
        # Recent photos (last 30 days)
        recent_cutoff = datetime.now() - datetime.timedelta(days=30)
        organized["recent_photos"] = [
            {
                "photo_id": p.photo_id,
                "filename": p.filename,
                "taken_date": p.taken_date.isoformat(),
                "service_type": p.service_type.value
            }
            for p in photos 
            if p.taken_date >= recent_cutoff
        ][:10]  # Latest 10
        
        return organized
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file for duplicate detection"""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def _find_duplicate_by_hash(self, file_hash: str) -> Optional[str]:
        """Find existing photo with same hash"""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT photo_id FROM photos WHERE file_hash = ?", (file_hash,)
            ).fetchone()
            return row[0] if row else None
    
    def _extract_photo_metadata(self, file_path: str) -> PhotoMetadata:
        """Extract metadata from photo file"""
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                file_size = os.path.getsize(file_path)
                
                # Extract EXIF data
                exif_data = {}
                if hasattr(img, '_getexif') and img._getexif():
                    exif = img._getexif()
                    for tag_id, value in exif.items():
                        tag = ExifTags.TAGS.get(tag_id, tag_id)
                        exif_data[tag] = value
                
                metadata = PhotoMetadata(
                    width=width,
                    height=height,
                    file_size=file_size,
                    camera_make=exif_data.get('Make', ''),
                    camera_model=exif_data.get('Model', '')
                )
                
                # Extract date taken
                if 'DateTime' in exif_data:
                    try:
                        metadata.taken_date = datetime.strptime(
                            exif_data['DateTime'], '%Y:%m:%d %H:%M:%S'
                        )
                    except:
                        pass
                
                # Extract GPS if available
                if 'GPSInfo' in exif_data:
                    gps_info = exif_data['GPSInfo']
                    if 2 in gps_info and 4 in gps_info:  # Latitude and Longitude
                        metadata.gps_latitude = self._convert_gps_coord(gps_info[2], gps_info[1])
                        metadata.gps_longitude = self._convert_gps_coord(gps_info[4], gps_info[3])
                
                return metadata
                
        except Exception as e:
            # Return basic metadata on error
            return PhotoMetadata(
                width=0,
                height=0,
                file_size=os.path.getsize(file_path) if os.path.exists(file_path) else 0
            )
    
    def _convert_gps_coord(self, coord, ref):
        """Convert GPS coordinates from EXIF format"""
        try:
            degrees = float(coord[0])
            minutes = float(coord[1])
            seconds = float(coord[2])
            
            decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
            
            if ref in ['S', 'W']:
                decimal = -decimal
                
            return decimal
        except:
            return None
    
    def _generate_organized_filename(self, photo_id: str, client_name: str,
                                   service_type: ServiceType, photo_type: PhotoType,
                                   original_filename: str) -> str:
        """Generate organized filename"""
        # Clean client name for filename
        clean_client = "".join(c for c in client_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        clean_client = clean_client.replace(' ', '_')
        
        # Get file extension
        _, ext = os.path.splitext(original_filename)
        
        # Generate filename: PhotoID_ClientName_ServiceType_PhotoType.ext
        filename = f"{photo_id}_{clean_client}_{service_type.value}_{photo_type.value}{ext}"
        
        return filename
    
    def _get_organized_path(self, client_id: str, service_type: ServiceType,
                          photo_category: PhotoCategory) -> Path:
        """Get organized storage path"""
        # Structure: organized/clients/CLIENT_ID/SERVICE_TYPE/CATEGORY/
        return (self.storage_root / "organized" / "clients" / 
               client_id / service_type.value / photo_category.value)
    
    def _auto_generate_tags(self, photo: Photo, metadata: Optional[PhotoMetadata]) -> Set[str]:
        """Auto-generate tags based on photo properties"""
        tags = set()
        
        # Service type tag
        tags.add(photo.service_type.value)
        
        # Photo type tag
        tags.add(photo.photo_type.value)
        
        # Season tag based on date
        if hasattr(photo, 'taken_date') and photo.taken_date:
            month = photo.taken_date.month
            if month in [12, 1, 2]:
                tags.add("winter")
            elif month in [3, 4, 5]:
                tags.add("spring")
            elif month in [6, 7, 8]:
                tags.add("summer")
            elif month in [9, 10, 11]:
                tags.add("fall")
        
        # Quality tags based on metadata
        if metadata:
            if metadata.width >= 1920 and metadata.height >= 1080:
                tags.add("high_resolution")
            if metadata.file_size > 5000000:  # > 5MB
                tags.add("large_file")
        
        # Location tags
        if photo.location:
            tags.add("location_tagged")
            if "outdoor" in photo.location.lower():
                tags.add("outdoor")
            elif "indoor" in photo.location.lower():
                tags.add("indoor")
        
        return tags
    
    def _save_photo_to_db(self, photo: Photo):
        """Save photo record to database"""
        metadata = photo.metadata
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO photos (
                    photo_id, filename, original_filename, file_path, file_hash,
                    client_id, client_name, project_id, visit_id, location,
                    service_type, photo_type, photo_category, tags, description,
                    notes, portfolio_quality, client_approved, marketing_approved,
                    public_use_approved, taken_date, uploaded_date, updated_date,
                    photographer, weather_conditions, time_of_day,
                    width, height, file_size, camera_make, camera_model,
                    gps_latitude, gps_longitude
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                photo.photo_id, photo.filename, photo.original_filename,
                photo.file_path, photo.file_hash, photo.client_id, photo.client_name,
                photo.project_id, photo.visit_id, photo.location,
                photo.service_type.value, photo.photo_type.value, photo.photo_category.value,
                json.dumps(list(photo.tags)), photo.description, photo.notes,
                photo.portfolio_quality, photo.client_approved, photo.marketing_approved,
                photo.public_use_approved, photo.taken_date, photo.uploaded_date,
                photo.updated_date, photo.photographer, photo.weather_conditions,
                photo.time_of_day,
                metadata.width if metadata else 0,
                metadata.height if metadata else 0,
                metadata.file_size if metadata else 0,
                metadata.camera_make if metadata else '',
                metadata.camera_model if metadata else '',
                metadata.gps_latitude if metadata else None,
                metadata.gps_longitude if metadata else None
            ))
    
    def _save_gallery_to_db(self, gallery: PhotoGallery):
        """Save gallery to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO photo_galleries (
                    gallery_id, name, description, client_id, service_type,
                    photo_ids, cover_photo_id, tags, is_public, is_portfolio,
                    created_date, updated_date, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                gallery.gallery_id, gallery.name, gallery.description,
                gallery.client_id, gallery.service_type.value if gallery.service_type else None,
                json.dumps(gallery.photo_ids), gallery.cover_photo_id,
                json.dumps(list(gallery.tags)), gallery.is_public, gallery.is_portfolio,
                gallery.created_date, gallery.updated_date, gallery.created_by
            ))
    
    def _generate_thumbnail(self, image_path: str, photo_id: str):
        """Generate thumbnail for photo"""
        try:
            thumbnail_dir = self.storage_root / "thumbnails"
            thumbnail_path = thumbnail_dir / f"{photo_id}_thumb.jpg"
            
            with Image.open(image_path) as img:
                # Create thumbnail maintaining aspect ratio
                img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                img.save(thumbnail_path, "JPEG", quality=85)
                
        except Exception as e:
            # Non-critical error, continue without thumbnail
            pass
    
    def _get_thumbnail_path(self, photo_id: str) -> Optional[str]:
        """Get thumbnail path if exists"""
        thumbnail_path = self.storage_root / "thumbnails" / f"{photo_id}_thumb.jpg"
        return str(thumbnail_path) if thumbnail_path.exists() else None
    
    def _select_portfolio_photos(self, photos: List[Photo], max_count: int) -> List[Photo]:
        """Select diverse photos for portfolio"""
        # Group by client and photo type for diversity
        by_client = {}
        by_type = {}
        
        for photo in photos:
            # Group by client
            if photo.client_id not in by_client:
                by_client[photo.client_id] = []
            by_client[photo.client_id].append(photo)
            
            # Group by type
            if photo.photo_type not in by_type:
                by_type[photo.photo_type] = []
            by_type[photo.photo_type].append(photo)
        
        selected = []
        
        # Try to get photos from different clients
        clients = list(by_client.keys())
        photos_per_client = max(1, max_count // len(clients))
        
        for client_id in clients:
            client_photos = by_client[client_id][:photos_per_client]
            selected.extend(client_photos)
            
            if len(selected) >= max_count:
                break
        
        # Fill remaining slots if needed
        if len(selected) < max_count:
            remaining = max_count - len(selected)
            all_remaining = [p for p in photos if p not in selected]
            selected.extend(all_remaining[:remaining])
        
        return selected[:max_count]
    
    def _initialize_default_tags(self):
        """Initialize commonly used tags"""
        default_tags = [
            ("before", "Before photos showing initial state"),
            ("after", "After photos showing completed work"),
            ("holiday_decor", "Holiday decoration projects"),
            ("plants", "Plant installation and care"),
            ("landscaping", "Outdoor landscaping work"),
            ("lobby", "Lobby and reception area work"),
            ("outdoor", "Outdoor photography"),
            ("indoor", "Indoor photography"),
            ("winter", "Winter season photos"),
            ("spring", "Spring season photos"),
            ("summer", "Summer season photos"),
            ("fall", "Fall season photos"),
            ("high_resolution", "High quality resolution photos"),
            ("portfolio_quality", "Portfolio worthy photos"),
            ("maintenance", "Maintenance visit documentation")
        ]
        
        with sqlite3.connect(self.db_path) as conn:
            for tag_name, description in default_tags:
                conn.execute("""
                    INSERT OR IGNORE INTO photo_tags (
                        tag_id, tag_name, description, created_date
                    ) VALUES (?, ?, ?, ?)
                """, (f"TAG-{uuid.uuid4().hex[:8]}", tag_name, description, datetime.now()))


# Example usage
if __name__ == "__main__":
    # Initialize photo organizer
    organizer = PhotoOrganizer()
    
    # Example: Upload a photo
    # photo_id = organizer.upload_photo(
    #     file_path="sample_photos/holiday_tree_before.jpg",
    #     client_id="CL001",
    #     client_name="Manhattan Plaza LLC",
    #     service_type=ServiceType.HOLIDAY_DECOR,
    #     photo_type=PhotoType.BEFORE,
    #     photo_category=PhotoCategory.PROJECT_WORK,
    #     location="Main lobby",
    #     description="9-foot Fraser Fir installation - before setup",
    #     photographer="Dave Rodriguez",
    #     portfolio_quality=True
    # )
    
    # print(f"Uploaded photo: {photo_id}")
    
    # Search for photos
    # holiday_photos = organizer.search_photos(
    #     service_type=ServiceType.HOLIDAY_DECOR,
    #     photo_type=PhotoType.BEFORE
    # )
    # 
    # print(f"Found {len(holiday_photos)} holiday decoration photos")
    
    # Create portfolio gallery
    # portfolio_id = organizer.generate_portfolio_gallery(
    #     service_type=ServiceType.HOLIDAY_DECOR,
    #     max_photos=15
    # )
    # 
    # print(f"Created portfolio gallery: {portfolio_id}")
    
    print("Photo organizer initialized and ready for use!")