import os

# Список папок, которые мы ИГНОРИРУЕМ (мусор и большие файлы)
IGNORE_DIRS = {
    '.git', '__pycache__', '.venv', 'venv', 'env', '.idea', '.vscode',
    'node_modules', 'logs', 'outputs', 'models',  # models содержит большие файлы моделей
    'migrations/__pycache__',  # кэш миграций
}

# Список расширений файлов, которые мы БЕРЕМ
INCLUDE_EXT = {
    '.py', '.ts', '.tsx', '.json', '.md', '.yml', '.yaml', '.toml',
    '.ini', '.txt', '.sh', '.ps1', '.conf', '.css'
}

# Конкретные файлы, которые мы игнорируем
IGNORE_FILES = {
    'desktop.ini', 'poetry.lock', 'yarn.lock', 'package-lock.json',
    # Большие файлы моделей
    'AmaFusion_V1.safetensors', 'dreamshaper_6NoVae.safetensors',
}

# Расширения файлов, которые мы игнорируем (большие бинарные файлы)
IGNORE_EXT = {'.safetensors', '.bin', '.pt', '.pth', '.ckpt'}


def should_include_file(file_path: str, file: str) -> bool:
    """Проверяет, нужно ли включать файл в контекст."""
    # Проверяем конкретные файлы
    if file in IGNORE_FILES:
        return False
    
    # Проверяем расширение файла
    _, ext = os.path.splitext(file)
    if ext in IGNORE_EXT:
        return False
    
    # Проверяем, есть ли расширение в списке включаемых
    if ext in INCLUDE_EXT:
        return True
    
    # Специальные файлы без расширения
    if file in ('Dockerfile', 'alembic.ini'):
        return True
    
    return False


def generate_context():
    """Генерирует полный контекст проекта в один файл."""
    output_file = 'full_project_context_genai.txt'
    
    file_count = 0
    total_size = 0
    
    with open(output_file, 'w', encoding='utf-8') as outfile:
        # Заголовок
        outfile.write("=" * 80 + "\n")
        outfile.write("ПОЛНЫЙ КОНТЕКСТ ПРОЕКТА\n")
        outfile.write("=" * 80 + "\n\n")
        
        # Проходим по всем файлам
        for root, dirs, files in os.walk('.'):
            # Фильтруем папки на лету
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            # Дополнительная фильтрация для вложенных папок
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if not should_include_file(os.path.join(root, file), file):
                    continue
                
                path = os.path.join(root, file)
                
                # Нормализуем путь для Windows
                path = os.path.normpath(path)
                
                # Пропускаем сам выходной файл
                if path == output_file or path == os.path.normpath(output_file):
                    continue
                
                # Пишем заголовок файла
                outfile.write(f"\n{'='*80}\n")
                outfile.write(f"FILE: {path}\n")
                outfile.write(f"{'='*80}\n\n")
                
                try:
                    # Проверяем размер файла (пропускаем слишком большие)
                    file_size = os.path.getsize(path)
                    if file_size > 1_000_000:  # Пропускаем файлы больше 1MB
                        outfile.write(f"[File too large: {file_size} bytes, skipped]\n")
                        continue
                    
                    with open(path, 'r', encoding='utf-8', errors='ignore') as infile:
                        content = infile.read()
                        outfile.write(content)
                        if not content.endswith('\n'):
                            outfile.write('\n')
                    
                    file_count += 1
                    total_size += file_size
                    
                except Exception as e:
                    outfile.write(f"[Error reading file: {e}]\n")
        
        # Статистика в конце
        outfile.write(f"\n\n{'='*80}\n")
        outfile.write(f"СТАТИСТИКА\n")
        outfile.write(f"{'='*80}\n")
        outfile.write(f"Обработано файлов: {file_count}\n")
        outfile.write(f"Общий размер: {total_size:,} байт ({total_size / 1024:.2f} KB)\n")
    
    print(f"Готово. Файл {output_file} создан.")
    print(f"Обработано файлов: {file_count}")
    print(f"Общий размер: {total_size:,} байт ({total_size / 1024:.2f} KB)")


if __name__ == '__main__':
    generate_context()

