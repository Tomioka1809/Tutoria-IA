import asyncio
import getpass
from app.infrastructure.database.session import SessionLocal
import app.infrastructure.database.base  # Importa todos los modelos para que SQLAlchemy no lance error de Mapper
from app.infrastructure.database.models.user import User
from app.infrastructure.database.models.profiles import AdminProfile
from app.infrastructure.security.security import get_password_hash

async def create_superuser():
    print("=== Crear Superusuario (Admin) ===")
    email = input("Email: ")
    full_name = input("Nombre completo: ")
    password = getpass.getpass("Contraseña: ")
    
    hashed_password = get_password_hash(password)
    
    async with SessionLocal() as db:
        try:
            admin_user = User(
                email=email,
                password_hash=hashed_password,
                role="admin",
                is_active=True
            )
            
            admin_user.admin_profile = AdminProfile(
                full_name=full_name,
                administrative_position="Superadmin"
            )
            
            db.add(admin_user)
            await db.commit()
            print(f"\n✅ Superusuario '{email}' creado exitosamente.")
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error al crear superusuario: {str(e)}")

if __name__ == "__main__":
    asyncio.run(create_superuser())
