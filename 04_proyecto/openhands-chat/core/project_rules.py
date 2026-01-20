"""
Project Rules - Sistema de reglas persistentes como Cursor

Implementa archivos de reglas que persisten entre sesiones:
1. .openhands/rules.md - Reglas del proyecto
2. .openhands/context.md - Contexto arquitectónico
3. .openhands/gotchas.md - Cosas a evitar

Estos archivos se cargan automáticamente y se incluyen en el contexto del agente.

Uso:
    rules = ProjectRules("/path/to/project")
    context = rules.get_full_context()  # Para incluir en system prompt
    rules.add_rule("Always use TypeScript for new files")
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Rule:
    """Una regla del proyecto"""
    text: str
    category: str = "general"  # "general", "architecture", "patterns", "gotchas"
    priority: str = "normal"  # "high", "normal", "low"
    added_at: str = field(default_factory=lambda: datetime.now().isoformat())


class ProjectRules:
    """
    Gestiona reglas persistentes del proyecto.
    
    Las reglas se guardan en archivos Markdown dentro de .openhands/
    y se cargan automáticamente al iniciar una conversación.
    """
    
    # Estructura de archivos de reglas
    RULES_DIR = ".openhands"
    FILES = {
        "rules": "rules.md",
        "context": "context.md", 
        "gotchas": "gotchas.md",
        "patterns": "patterns.md"
    }
    
    # Template para archivo de reglas nuevo
    RULES_TEMPLATE = """# 📋 Project Rules

## Architecture
<!-- Describe la arquitectura del proyecto -->
- 

## Coding Standards
<!-- Estándares de código a seguir -->
-

## Testing
<!-- Reglas de testing -->
-

## Dependencies
<!-- Notas sobre dependencias -->
-

---
*Este archivo es leído automáticamente por el agente.*
*Edita para agregar reglas que el agente debe seguir.*
"""

    CONTEXT_TEMPLATE = """# 🏗️ Project Context

## Overview
<!-- Descripción general del proyecto -->


## Main Components
<!-- Componentes principales y su propósito -->
| Component | Purpose | Location |
|-----------|---------|----------|
| | | |

## Data Flow
<!-- Cómo fluyen los datos en la aplicación -->


## External Services
<!-- APIs o servicios externos que usa -->


## Environment
<!-- Variables de entorno importantes -->


---
*Este archivo ayuda al agente a entender el proyecto.*
"""

    GOTCHAS_TEMPLATE = """# ⚠️ Gotchas & Warnings

## Do NOT Modify
<!-- Archivos o código que NO se debe modificar -->
- 

## Known Issues
<!-- Bugs conocidos o comportamientos extraños -->
-

## Legacy Code
<!-- Código legacy que existe por razones específicas -->
-

## Common Mistakes
<!-- Errores comunes a evitar -->
-

---
*El agente leerá esto para evitar errores comunes.*
"""

    PATTERNS_TEMPLATE = """# 🔧 Code Patterns

## Creating a New Endpoint
<!-- Ejemplo de cómo crear un nuevo endpoint -->
```python
# Ver ejemplo en: 
```

## Adding a New Component
<!-- Ejemplo de cómo agregar un componente -->
```javascript
// Ver ejemplo en:
```

## Database Migrations
<!-- Cómo hacer migraciones de DB -->


## Testing Patterns
<!-- Patrones de testing -->


---
*Estos patrones guían al agente sobre cómo escribir código.*
"""

    def __init__(self, workspace: str):
        """
        Inicializa el gestor de reglas.
        
        Args:
            workspace: Directorio raíz del proyecto
        """
        self.workspace = Path(workspace)
        self.rules_dir = self.workspace / self.RULES_DIR
        self._cache: Dict[str, str] = {}
        self._ensure_rules_dir()
    
    def _ensure_rules_dir(self):
        """Crea el directorio de reglas si no existe"""
        self.rules_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_file_path(self, file_type: str) -> Path:
        """Obtiene la ruta de un archivo de reglas"""
        filename = self.FILES.get(file_type, f"{file_type}.md")
        return self.rules_dir / filename
    
    def _read_file(self, file_type: str) -> str:
        """Lee un archivo de reglas"""
        path = self._get_file_path(file_type)
        
        if path.exists():
            try:
                return path.read_text(encoding="utf-8")
            except:
                return ""
        return ""
    
    def _write_file(self, file_type: str, content: str):
        """Escribe un archivo de reglas"""
        path = self._get_file_path(file_type)
        path.write_text(content, encoding="utf-8")
        self._cache[file_type] = content
    
    def init_rules(self, force: bool = False):
        """
        Inicializa archivos de reglas con templates.
        
        Args:
            force: Si True, sobrescribe archivos existentes
        """
        templates = {
            "rules": self.RULES_TEMPLATE,
            "context": self.CONTEXT_TEMPLATE,
            "gotchas": self.GOTCHAS_TEMPLATE,
            "patterns": self.PATTERNS_TEMPLATE
        }
        
        for file_type, template in templates.items():
            path = self._get_file_path(file_type)
            if force or not path.exists():
                self._write_file(file_type, template)
                print(f"[RULES] Created {path}")
    
    def get_rules(self) -> str:
        """Obtiene las reglas del proyecto"""
        return self._read_file("rules")
    
    def get_context(self) -> str:
        """Obtiene el contexto del proyecto"""
        return self._read_file("context")
    
    def get_gotchas(self) -> str:
        """Obtiene los gotchas/warnings"""
        return self._read_file("gotchas")
    
    def get_patterns(self) -> str:
        """Obtiene los patrones de código"""
        return self._read_file("patterns")
    
    def get_full_context(self) -> str:
        """
        Obtiene todo el contexto del proyecto para incluir en el system prompt.
        
        Returns:
            String con todo el contexto formateado
        """
        sections = []
        
        # Reglas
        rules = self.get_rules()
        if rules and not self._is_template(rules):
            sections.append(f"<PROJECT_RULES>\n{rules}\n</PROJECT_RULES>")
        
        # Contexto
        context = self.get_context()
        if context and not self._is_template(context):
            sections.append(f"<PROJECT_CONTEXT>\n{context}\n</PROJECT_CONTEXT>")
        
        # Gotchas
        gotchas = self.get_gotchas()
        if gotchas and not self._is_template(gotchas):
            sections.append(f"<PROJECT_GOTCHAS>\n{gotchas}\n</PROJECT_GOTCHAS>")
        
        # Patterns
        patterns = self.get_patterns()
        if patterns and not self._is_template(patterns):
            sections.append(f"<CODE_PATTERNS>\n{patterns}\n</CODE_PATTERNS>")
        
        if sections:
            return "\n\n".join(sections)
        return ""
    
    def _is_template(self, content: str) -> bool:
        """Verifica si el contenido es solo el template vacío"""
        # Si tiene muchos placeholders de comentarios HTML, es template
        placeholder_count = content.count("<!-- ")
        actual_content = len([line for line in content.split('\n') 
                            if line.strip() and not line.startswith('#') 
                            and not line.startswith('<!--') and not line.startswith('*')
                            and not line.startswith('|') and not line.startswith('-')])
        
        return actual_content < 5 and placeholder_count > 3
    
    def add_rule(self, rule: str, category: str = "general"):
        """
        Agrega una nueva regla al proyecto.
        
        Args:
            rule: Texto de la regla
            category: Categoría (architecture, testing, etc.)
        """
        rules = self.get_rules()
        
        # Buscar la sección de la categoría
        section_marker = f"## {category.title()}"
        
        if section_marker in rules:
            # Agregar bajo la sección existente
            lines = rules.split('\n')
            new_lines = []
            found_section = False
            added = False
            
            for line in lines:
                new_lines.append(line)
                if line.startswith(section_marker) and not found_section:
                    found_section = True
                elif found_section and line.startswith('##') and not added:
                    # Nueva sección, insertar antes
                    new_lines.insert(-1, f"- {rule}")
                    added = True
                elif found_section and line.startswith('-') and not added:
                    # Agregar después del último item
                    pass
            
            if found_section and not added:
                new_lines.append(f"- {rule}")
            
            rules = '\n'.join(new_lines)
        else:
            # Agregar sección nueva
            rules += f"\n\n## {category.title()}\n- {rule}\n"
        
        self._write_file("rules", rules)
    
    def add_gotcha(self, warning: str, category: str = "Known Issues"):
        """
        Agrega un nuevo gotcha/warning.
        
        Args:
            warning: Texto del warning
            category: Categoría dentro de gotchas
        """
        gotchas = self.get_gotchas()
        
        section_marker = f"## {category}"
        
        if section_marker in gotchas:
            gotchas = gotchas.replace(
                f"{section_marker}\n-", 
                f"{section_marker}\n- {warning}\n-"
            )
        else:
            gotchas += f"\n\n## {category}\n- {warning}\n"
        
        self._write_file("gotchas", gotchas)
    
    def add_pattern(self, name: str, code: str, language: str = "python"):
        """
        Agrega un nuevo patrón de código.
        
        Args:
            name: Nombre del patrón
            code: Código de ejemplo
            language: Lenguaje del código
        """
        patterns = self.get_patterns()
        
        new_pattern = f"""
## {name}
```{language}
{code}
```
"""
        
        patterns += new_pattern
        self._write_file("patterns", patterns)
    
    def update_context(self, section: str, content: str):
        """
        Actualiza una sección del contexto del proyecto.
        
        Args:
            section: Nombre de la sección (Overview, Main Components, etc.)
            content: Nuevo contenido
        """
        context = self.get_context()
        
        section_marker = f"## {section}"
        
        if section_marker in context:
            # Reemplazar sección
            lines = context.split('\n')
            new_lines = []
            skip = False
            
            for line in lines:
                if line.startswith(section_marker):
                    new_lines.append(line)
                    new_lines.append(content)
                    skip = True
                elif line.startswith('## ') and skip:
                    skip = False
                    new_lines.append(line)
                elif not skip:
                    new_lines.append(line)
            
            context = '\n'.join(new_lines)
        else:
            context += f"\n\n{section_marker}\n{content}\n"
        
        self._write_file("context", context)
    
    def get_summary(self) -> Dict[str, Any]:
        """Obtiene resumen de las reglas configuradas"""
        return {
            "rules_dir": str(self.rules_dir),
            "files_exist": {
                name: self._get_file_path(name).exists()
                for name in self.FILES.keys()
            },
            "has_custom_rules": not self._is_template(self.get_rules()),
            "has_custom_context": not self._is_template(self.get_context()),
            "has_gotchas": not self._is_template(self.get_gotchas()),
            "has_patterns": not self._is_template(self.get_patterns())
        }
    
    def auto_generate_context(self) -> str:
        """
        Genera contexto automático analizando el proyecto.
        
        Útil para proyectos nuevos sin reglas definidas.
        """
        context_parts = []
        
        # Detectar tipo de proyecto
        project_type = self._detect_project_type()
        if project_type:
            context_parts.append(f"**Project Type:** {project_type}")
        
        # Listar archivos principales
        main_files = self._find_main_files()
        if main_files:
            context_parts.append("\n**Main Files:**")
            for f in main_files[:10]:
                context_parts.append(f"- {f}")
        
        # Detectar dependencias
        deps = self._detect_dependencies()
        if deps:
            context_parts.append(f"\n**Dependencies detected:** {', '.join(deps[:10])}")
        
        return '\n'.join(context_parts)
    
    def _detect_project_type(self) -> Optional[str]:
        """Detecta el tipo de proyecto"""
        indicators = {
            "package.json": "Node.js/JavaScript",
            "requirements.txt": "Python",
            "pyproject.toml": "Python (modern)",
            "Cargo.toml": "Rust",
            "go.mod": "Go",
            "pom.xml": "Java/Maven",
            "build.gradle": "Java/Gradle",
            "Gemfile": "Ruby",
            "composer.json": "PHP"
        }
        
        for file, proj_type in indicators.items():
            if (self.workspace / file).exists():
                return proj_type
        
        return None
    
    def _find_main_files(self) -> List[str]:
        """Encuentra archivos principales del proyecto"""
        main_patterns = [
            "app.py", "main.py", "index.py", "server.py",
            "index.js", "index.ts", "app.js", "server.js",
            "main.go", "main.rs"
        ]
        
        found = []
        for pattern in main_patterns:
            matches = list(self.workspace.glob(f"**/{pattern}"))
            found.extend(str(m.relative_to(self.workspace)) for m in matches[:3])
        
        return found
    
    def _detect_dependencies(self) -> List[str]:
        """Detecta dependencias principales"""
        deps = []
        
        # Python
        req_file = self.workspace / "requirements.txt"
        if req_file.exists():
            try:
                content = req_file.read_text()
                for line in content.split('\n')[:20]:
                    if line and not line.startswith('#'):
                        dep = line.split('==')[0].split('>=')[0].strip()
                        if dep:
                            deps.append(dep)
            except:
                pass
        
        # Node.js
        pkg_file = self.workspace / "package.json"
        if pkg_file.exists():
            try:
                import json
                pkg = json.loads(pkg_file.read_text())
                deps.extend(list(pkg.get("dependencies", {}).keys())[:10])
            except:
                pass
        
        return deps


# Instancia global
_global_rules: Optional[ProjectRules] = None


def get_project_rules(workspace: str = None) -> Optional[ProjectRules]:
    """Obtiene o crea el gestor de reglas global"""
    global _global_rules
    
    if _global_rules is None and workspace:
        _global_rules = ProjectRules(workspace)
    
    return _global_rules


def set_project_rules(rules: ProjectRules):
    """Establece el gestor de reglas global"""
    global _global_rules
    _global_rules = rules
