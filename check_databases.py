#!/usr/bin/env python3
"""
Скрипт для проверки состояния баз данных
"""
import asyncio
import os
from typing import Dict, Any

import asyncpg
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

async def check_database(db_config: Dict[str, Any], db_name: str) -> Dict[str, Any]:
    """Проверяем состояние базы данных"""
    print(f"\n{'='*50}")
    print(f"Проверка базы данных: {db_name}")
    print(f"{'='*50}")
    
    try:
        # Подключаемся к базе
        conn = await asyncpg.connect(
            host=db_config["host"],
            port=db_config["port"],
            user=db_config["user"],
            password=db_config["password"],
            database=db_config["database"]
        )
        
        print(f"✅ Подключение установлено")
        print(f"📍 Хост: {db_config['host']}:{db_config['port']}")
        print(f"🗄️  База данных: {db_config['database']}")
        
        # Получаем информацию о версии PostgreSQL
        version = await conn.fetchval("SELECT version()")
        print(f"🔧 Версия PostgreSQL: {version.split(',')[0]}")
        
        # Получаем список таблиц
        tables_query = """
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename;
        """
        tables = await conn.fetch(tables_query)
        
        print(f"\n📋 Таблицы в базе данных:")
        if tables:
            for table in tables:
                table_name = table['tablename']
                
                # Получаем количество записей в таблице
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
                print(f"   📊 {table_name}: {count} записей")
                
                # Для таблицы users показываем структуру
                if table_name == 'users':
                    print(f"      └── Структура:")
                    columns = await conn.fetch("""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns 
                        WHERE table_name = 'users' AND table_schema = 'public'
                        ORDER BY ordinal_position;
                    """)
                    for col in columns:
                        nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                        print(f"          • {col['column_name']}: {col['data_type']} {nullable}")
                
                # Для таблицы applications показываем структуру
                elif table_name == 'applications':
                    print(f"      └── Структура:")
                    columns = await conn.fetch("""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns 
                        WHERE table_name = 'applications' AND table_schema = 'public'
                        ORDER BY ordinal_position;
                    """)
                    for col in columns:
                        nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                        print(f"          • {col['column_name']}: {col['data_type']} {nullable}")
        else:
            print("   ❌ Таблицы не найдены")
        
        await conn.close()
        return {"status": "success", "tables": [t['tablename'] for t in tables]}
        
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return {"status": "error", "error": str(e)}


async def main():
    """Основная функция проверки"""
    print("🔍 Проверка состояния баз данных КБК")
    
    # Конфигурация для базы пользователей
    users_db_config = {
        "host": os.getenv("DB_HOST"),
        "port": int(os.getenv("DB_PORT")),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASS"),
        "database": os.getenv("DB_NAME")
    }
    
    # Конфигурация для базы заявок
    applications_db_config = {
        "host": os.getenv("DB_APPLICATIONS_HOST"),
        "port": int(os.getenv("DB_APPLICATIONS_PORT")),
        "user": os.getenv("DB_APPLICATIONS_USER"),
        "password": os.getenv("DB_APPLICATIONS_PASS"),
        "database": os.getenv("DB_APPLICATIONS_NAME")
    }
    
    # Проверяем обе базы данных
    users_result = await check_database(users_db_config, "База пользователей")
    apps_result = await check_database(applications_db_config, "База заявок")
    
    # Финальный отчет
    print(f"\n{'='*50}")
    print("📝 ИТОГОВЫЙ ОТЧЕТ")
    print(f"{'='*50}")
    
    print(f"🗂️  База пользователей (порт {users_db_config['port']}):")
    if users_result["status"] == "success":
        print(f"   ✅ Статус: Подключение успешно")
        print(f"   📊 Таблицы: {', '.join(users_result['tables'])}")
        if 'users' in users_result['tables']:
            print(f"   ✅ Таблица users: Присутствует")
        else:
            print(f"   ❌ Таблица users: Отсутствует")
    else:
        print(f"   ❌ Статус: Ошибка подключения")
        print(f"   📝 Ошибка: {users_result['error']}")
    
    print(f"\n🗂️  База заявок (порт {applications_db_config['port']}):")
    if apps_result["status"] == "success":
        print(f"   ✅ Статус: Подключение успешно")
        print(f"   📊 Таблицы: {', '.join(apps_result['tables'])}")
        if 'applications' in apps_result['tables']:
            print(f"   ✅ Таблица applications: Присутствует")
        else:
            print(f"   ❌ Таблица applications: Отсутствует")
    else:
        print(f"   ❌ Статус: Ошибка подключения")
        print(f"   📝 Ошибка: {apps_result['error']}")
    
    # Проверка корректности разделения
    print(f"\n🔍 АНАЛИЗ КОРРЕКТНОСТИ НАСТРОЙКИ:")
    
    both_success = (users_result["status"] == "success" and 
                   apps_result["status"] == "success")
    
    if both_success:
        users_tables = set(users_result["tables"])
        apps_tables = set(apps_result["tables"])
        
        # Проверяем правильность разделения
        correct_users = 'users' in users_tables and 'applications' not in users_tables
        correct_apps = 'applications' in apps_tables and 'users' not in apps_tables
        
        if correct_users and correct_apps:
            print("   ✅ Разделение баз данных настроено КОРРЕКТНО")
            print("   ✅ База пользователей содержит только таблицу users")
            print("   ✅ База заявок содержит только таблицу applications")
        else:
            print("   ⚠️  Обнаружены проблемы в разделении:")
            if not correct_users:
                print("   ❌ В базе пользователей неправильные таблицы")
            if not correct_apps:
                print("   ❌ В базе заявок неправильные таблицы")
    else:
        print("   ❌ Невозможно проанализировать из-за ошибок подключения")


if __name__ == "__main__":
    asyncio.run(main())
