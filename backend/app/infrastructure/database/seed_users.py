import asyncio
import os
import re
import unicodedata
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete

# Import SQLAlchemy Session
from app.infrastructure.database.session import SessionLocal

# Import base to ensure all models are registered with mapper
import app.infrastructure.database.base
from app.infrastructure.database.models.user import User
from app.infrastructure.database.models.profiles import StudentProfile, TutorProfile
from app.infrastructure.database.models.service_type import ServiceType
from app.infrastructure.database.models.tutor_assignment import TutorAssignment
from app.infrastructure.security.security import get_password_hash

def clean_string_for_email(s: str) -> str:
    # Convert to lowercase
    s = s.lower()
    # Replace ñ with n
    s = s.replace('ñ', 'n').replace('Ñ', 'n')
    # Normalize unicode to decompose accents (e.g. á -> a + ´)
    s = "".join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    # Remove all non-alphanumeric characters
    s = re.sub(r'[^a-z0-9]', '', s)
    return s

def get_tutor_email(full_name: str) -> str:
    # Tutor names are formatted as: "Lastnames, Firstnames"
    parts = full_name.split(",", 1)
    last_names = parts[0].strip()
    return f"{clean_string_for_email(last_names)}@unsaac.edu.pe"

async def seed_users():
    print("=== Starting custom database seeding for Tutors & Students ===")
    
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Distribucion_Tutoria_2026-I.txt")
    if not os.path.exists(file_path):
        print(f"Error: Distribution file not found at {file_path}")
        return
        
    # Parse the distribution text file
    tutors_data = []
    current_tutor = None
    
    print(f"Reading file: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            
            # Check tutor line (e.g. "- Acurio Usca, Nila")
            if line.startswith("-"):
                tutor_name = stripped.lstrip("-").strip()
                current_tutor = {"full_name": tutor_name, "students": []}
                tutors_data.append(current_tutor)
            # Check student line (e.g. "  - 110071: Munive Salas, Ciro")
            elif line.startswith("  -") or line.startswith("    -") or (":" in stripped and current_tutor is not None):
                content = stripped.lstrip("-").strip()
                if ":" in content:
                    code, student_name = content.split(":", 1)
                    current_tutor["students"].append({
                        "code": code.strip(),
                        "full_name": student_name.strip()
                    })

    print(f"Parsed {len(tutors_data)} tutors from the file.")
    total_parsed_students = sum(len(t["students"]) for t in tutors_data)
    print(f"Parsed {total_parsed_students} students in total.")

    async with SessionLocal() as db:
        # 1. Ensure "Tutoría Académica" service type exists
        print("Checking/creating default ServiceType...")
        res = await db.execute(select(ServiceType).where(ServiceType.name == "Tutoría Académica"))
        service_type = res.scalars().first()
        if not service_type:
            service_type = ServiceType(
                name="Tutoría Académica",
                description="Asesoría en materias específicas y rendimiento académico.",
                icon="book"
            )
            db.add(service_type)
            await db.flush()
            print("Created ServiceType: 'Tutoría Académica'")
        else:
            print("ServiceType: 'Tutoría Académica' already exists")
            
        service_type_id = service_type.id

        # 2. Clean existing tutors, students and assignments
        print("Cleaning existing students and tutors from database...")
        # Delete users with role 'tutor' or 'estudiante'
        # Due to ON DELETE CASCADE on profiles and assignments, this clears child tables
        await db.execute(delete(User).where(User.role.in_(["tutor", "estudiante"])))
        await db.commit()
        print("Database cleaned successfully.")

        # 3. Seed users and profiles
        tutor_password_hash = get_password_hash("tutor123")
        seen_student_codes = set()
        
        tutor_count = 0
        student_count = 0
        assignment_count = 0
        duplicate_students_skipped = 0
        
        print("Inserting records...")
        for idx, tutor_info in enumerate(tutors_data):
            tutor_email = get_tutor_email(tutor_info["full_name"])
            tutor_code = f"TUT-{idx+1:04d}"
            
            # Create Tutor User
            tutor_user = User(
                email=tutor_email,
                password_hash=tutor_password_hash,
                role="tutor",
                is_active=True
            )
            tutor_user.tutor_profile = TutorProfile(
                full_name=tutor_info["full_name"],
                tutor_code=tutor_code,
                max_capacity=20,
                expertise_areas="Tutoría Académica General",
                office_location="Cubículo por asignar"
            )
            
            db.add(tutor_user)
            await db.flush() # Get tutor_user.id
            tutor_count += 1
            
            for student_info in tutor_info["students"]:
                student_code = student_info["code"]
                
                # Check for duplicates in student codes
                if student_code in seen_student_codes:
                    print(f"  [Warning] Duplicate student code {student_code} skipped (Already assigned to another tutor).")
                    duplicate_students_skipped += 1
                    continue
                seen_student_codes.add(student_code)
                
                student_email = f"{student_code}@unsaac.edu.pe"
                # Password is the student code
                student_password_hash = get_password_hash(student_code)
                
                # Random semester and status for realism
                current_semester = random.randint(1, 10)
                academic_status = random.choice(["Regular", "Regular", "En Riesgo", "Sobresaliente"])
                
                # Create Student User
                student_user = User(
                    email=student_email,
                    password_hash=student_password_hash,
                    role="estudiante",
                    is_active=True
                )
                student_user.student_profile = StudentProfile(
                    full_name=student_info["full_name"],
                    student_code=student_code,
                    current_semester=current_semester,
                    academic_status=academic_status
                )
                
                db.add(student_user)
                await db.flush() # Get student_user.id
                student_count += 1
                
                # Create Tutor Assignment
                assignment = TutorAssignment(
                    student_id=student_user.id,
                    tutor_id=tutor_user.id,
                    service_type_id=service_type_id,
                    academic_period="2026-I",
                    assignment_method="sorteo"
                )
                db.add(assignment)
                assignment_count += 1
            
            # Commit each tutor batch to avoid huge memory/transaction overhead
            await db.commit()
            print(f"Seeded tutor {idx+1}/{len(tutors_data)}: {tutor_info['full_name']} with {len(tutor_info['students'])} students.")
            
        print("=== Seeding complete ===")
        print(f"Total Tutors Inserted: {tutor_count}")
        print(f"Total Students Inserted: {student_count}")
        print(f"Total Assignments Created: {assignment_count}")
        if duplicate_students_skipped > 0:
            print(f"Total Duplicate Students Skipped: {duplicate_students_skipped}")

if __name__ == "__main__":
    asyncio.run(seed_users())
