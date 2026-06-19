import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from haapar_unla_app.services.ai_client import generar_respuesta_llm


# ==========================================
# ENDPOINT DE IA UNIFICADO
# ==========================================
@login_required
@require_POST
def chatgpt_api(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse(
            {"success": False, "error": "JSON inválido en cuerpo"}, status=400
        )

    prompt = payload.get("prompt")
    if not prompt:
        return JsonResponse(
            {"success": False, "error": 'Falta campo "prompt"'}, status=400
        )

    result = generar_respuesta_llm(prompt)

    if not result.get("success"):
        return JsonResponse(
            {"success": False, "error": result.get("error")}, status=500
        )

    return JsonResponse({"success": True, "text": result.get("text")})
