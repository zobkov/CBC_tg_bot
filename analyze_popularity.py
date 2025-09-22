#!/usr/bin/env python3
"""
Скрипт для анализа популярности отделов и позиций в КБК.
Генерирует детальную статистику по выбору участников.
"""
import asyncio
import csv
import logging
from datetime import datetime, timezone
from pathlib import Path
import psycopg
import json

from config.config import load_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def analyze_department_popularity():
    """Анализирует популярность отделов и позиций"""
    config = load_config()
    
    connection_string = (
        f"postgresql://{config.db_applications.user}:"
        f"{config.db_applications.password}@"
        f"{config.db_applications.host}:"
        f"{config.db_applications.port}/"
        f"{config.db_applications.database}"
    )
    
    connection = await psycopg.AsyncConnection.connect(connection_string)
    
    try:
        # Статистика по отделам (все три выбора)
        cursor = await connection.execute("""
            WITH department_choices AS (
                SELECT department_1 as department, position_1 as position, subdepartment_1 as subdepartment, 1 as choice_order FROM applications WHERE department_1 IS NOT NULL
                UNION ALL
                SELECT department_2 as department, position_2 as position, subdepartment_2 as subdepartment, 2 as choice_order FROM applications WHERE department_2 IS NOT NULL  
                UNION ALL
                SELECT department_3 as department, position_3 as position, subdepartment_3 as subdepartment, 3 as choice_order FROM applications WHERE department_3 IS NOT NULL
            )
            SELECT 
                department,
                COUNT(*) as total_selections,
                COUNT(*) FILTER (WHERE choice_order = 1) as first_choice,
                COUNT(*) FILTER (WHERE choice_order = 2) as second_choice,
                COUNT(*) FILTER (WHERE choice_order = 3) as third_choice,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
            FROM department_choices
            GROUP BY department
            ORDER BY total_selections DESC;
        """)
        
        dept_stats = []
        rows = await cursor.fetchall()
        for row in rows:
            dept_stats.append({
                'department': row[0],
                'total_selections': row[1],
                'first_choice': row[2],
                'second_choice': row[3], 
                'third_choice': row[4],
                'percentage': row[5]
            })
        
        # Статистика по позициям
        cursor = await connection.execute("""
            WITH position_choices AS (
                SELECT department_1 as department, position_1 as position, 1 as choice_order FROM applications WHERE position_1 IS NOT NULL
                UNION ALL
                SELECT department_2 as department, position_2 as position, 2 as choice_order FROM applications WHERE position_2 IS NOT NULL
                UNION ALL  
                SELECT department_3 as department, position_3 as position, 3 as choice_order FROM applications WHERE position_3 IS NOT NULL
            )
            SELECT 
                department,
                position,
                COUNT(*) as selections,
                COUNT(*) FILTER (WHERE choice_order = 1) as first_choice,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
            FROM position_choices
            GROUP BY department, position
            ORDER BY department, selections DESC;
        """)
        
        position_stats = []
        rows = await cursor.fetchall()
        for row in rows:
            position_stats.append({
                'department': row[0],
                'position': row[1],
                'selections': row[2],
                'first_choice': row[3],
                'percentage': row[4]
            })
        
        # Статистика по каналам узнавания
        cursor = await connection.execute("""
            SELECT 
                how_found_kbk,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
            FROM applications 
            WHERE how_found_kbk IS NOT NULL
            GROUP BY how_found_kbk
            ORDER BY count DESC;
        """)
        
        how_found_stats = []
        rows = await cursor.fetchall()
        for row in rows:
            how_found_stats.append({
                'how_found': row[0],
                'count': row[1],
                'percentage': row[2]
            })
        
        # Статистика по курсам
        cursor = await connection.execute("""
            SELECT 
                course,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
            FROM applications 
            WHERE course IS NOT NULL
            GROUP BY course
            ORDER BY course;
        """)
        
        course_stats = []
        rows = await cursor.fetchall()
        for row in rows:
            course_stats.append({
                'course': row[0],
                'count': row[1],
                'percentage': row[2]
            })
        
        # Сохраняем в CSV файлы
        output_dir = Path("storage/analytics")
        output_dir.mkdir(exist_ok=True, parents=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Сохраняем статистику отделов
        with open(output_dir / f"department_popularity_{timestamp}.csv", 'w', newline='', encoding='utf-8') as f:
            if dept_stats:
                writer = csv.DictWriter(f, fieldnames=dept_stats[0].keys())
                writer.writeheader()
                writer.writerows(dept_stats)
        
        # Сохраняем статистику позиций
        with open(output_dir / f"position_popularity_{timestamp}.csv", 'w', newline='', encoding='utf-8') as f:
            if position_stats:
                writer = csv.DictWriter(f, fieldnames=position_stats[0].keys())
                writer.writeheader()
                writer.writerows(position_stats)
        
        # Сохраняем статистику каналов
        with open(output_dir / f"how_found_stats_{timestamp}.csv", 'w', newline='', encoding='utf-8') as f:
            if how_found_stats:
                writer = csv.DictWriter(f, fieldnames=how_found_stats[0].keys())
                writer.writeheader()
                writer.writerows(how_found_stats)
        
        # Сохраняем статистику курсов
        with open(output_dir / f"course_distribution_{timestamp}.csv", 'w', newline='', encoding='utf-8') as f:
            if course_stats:
                writer = csv.DictWriter(f, fieldnames=course_stats[0].keys())
                writer.writeheader()
                writer.writerows(course_stats)
        
        # Выводим в консоль
        print("\n" + "="*60)
        print("КБК - АНАЛИЗ ПОПУЛЯРНОСТИ ОТДЕЛОВ И ПОЗИЦИЙ")
        print("="*60)
        print(f"Время генерации: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print()
        
        print("ПОПУЛЯРНОСТЬ ОТДЕЛОВ:")
        print("-" * 60)
        for dept in dept_stats[:10]:  # Топ 10 отделов
            print(f"{dept['department']:<30} | {dept['total_selections']:>3} выборов ({dept['percentage']:>5.1f}%)")
            print(f"{'':>30} | 1-й выбор: {dept['first_choice']}, 2-й: {dept['second_choice']}, 3-й: {dept['third_choice']}")
            print()
        
        print("\nТОП ПОЗИЦИЙ:")
        print("-" * 60)
        top_positions = sorted(position_stats, key=lambda x: x['selections'], reverse=True)[:15]
        for pos in top_positions:
            print(f"{pos['position']:<35} | {pos['selections']:>3} выборов ({pos['percentage']:>5.1f}%)")
            print(f"{'Отдел: ' + pos['department']:<35} | 1-й выбор: {pos['first_choice']}")
            print()
        
        print("\nКАК УЗНАЛИ ПРО КБК:")
        print("-" * 60)
        for hf in how_found_stats[:8]:
            print(f"{hf['how_found']:<45} | {hf['count']:>3} ({hf['percentage']:>5.1f}%)")
        
        print("\nРАСПРЕДЕЛЕНИЕ ПО КУРСАМ:")
        print("-" * 60)
        for course in course_stats:
            print(f"Курс {course['course']:<2} | {course['count']:>3} студентов ({course['percentage']:>5.1f}%)")
        
        print("\n" + "="*60)
        print(f"Файлы сохранены в storage/analytics/ с timestamp {timestamp}")
        
        return {
            'departments': dept_stats,
            'positions': position_stats,
            'how_found': how_found_stats,
            'courses': course_stats
        }
        
    finally:
        await connection.close()


if __name__ == "__main__":
    asyncio.run(analyze_department_popularity())