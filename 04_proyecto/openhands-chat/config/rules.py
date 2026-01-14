"""
ARCHIVO DE REFERENCIA - NO SE USA EN PRODUCCIÓN

El agente ahora usa los prompts oficiales de OpenHands SDK directamente.
Ver: /home/openhands/.local/lib/python3.12/site-packages/openhands/sdk/agent/prompts/

Los prompts oficiales incluyen:
- system_prompt.j2 (prompt principal)
- security_policy.j2
- security_risk_assessment.j2  
- self_documentation.j2
- in_context_learning_example.j2
- model_specific/*.j2

El agente en core/agent.py solo agrega contexto adicional via system_message_suffix:
- Instrucción de idioma (responder en español)
- Runtime info (working directory)
- Repo info (GitHub repository)
- Browser tools (CLI commands)

Esto garantiza 100% compatibilidad con OpenHands oficial.
"""

# Este archivo ya no exporta nada - solo es documentación
