import json
import requests

from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST


OLLAMA_URL = getattr(settings, 'OLLAMA_URL', 'http://5.149.249.212:11434')
OLLAMA_MODEL = getattr(settings, 'OLLAMA_MODEL', 'mistral-nemo:custom')

PROMPT_TEMPLATES = {
    'cve': 'You are a cybersecurity expert. Explain this CVE in simple terms, its potential impact, affected systems, and recommended mitigations: {text}',
    'control': 'You are a compliance specialist. Explain this compliance control and why it matters for organizations: {text}',
    'mitigation': 'You are a security architect. Suggest a detailed mitigation strategy for: {text}',
    'threat': 'You are a threat intelligence analyst. Analyze this threat and provide assessment: {text}',
    'general': 'You are an AI security assistant for a GRC (Governance, Risk, Compliance) platform. Help the user with: {text}',
}


@login_required
@require_POST
def ai_explain(request):
    """
    Accept a query and context_type, send to Ollama LLM, return explanation.
    Uses mistral-nemo:custom model at the configured Ollama endpoint.
    """
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)

    query = body.get('query', '').strip()
    context_type = body.get('context_type', 'general').strip()

    if not query:
        return JsonResponse({'error': 'A query is required.'}, status=400)

    template = PROMPT_TEMPLATES.get(context_type, PROMPT_TEMPLATES['general'])
    prompt = template.format(text=query)

    # Try configured model first, then fallbacks
    models_to_try = [OLLAMA_MODEL, 'mistral-nemo:custom', 'mistral', 'llama3.2']
    # Deduplicate while preserving order
    seen = set()
    models_to_try = [m for m in models_to_try if not (m in seen or seen.add(m))]

    for model in models_to_try:
        try:
            response = requests.post(
                f'{OLLAMA_URL}/api/generate',
                json={
                    'model': model,
                    'prompt': prompt,
                    'stream': False,
                },
                timeout=30,
            )
            if response.status_code == 200:
                data = response.json()
                return JsonResponse({
                    'response': data.get('response', ''),
                    'model': model,
                    'context_type': context_type,
                })
        except (requests.ConnectionError, requests.Timeout):
            continue
        except requests.RequestException:
            continue

    # Fallback when Ollama is unavailable
    fallback_messages = {
        'cve': (
            'AI analysis is currently unavailable. For CVE information, '
            'please consult the NVD database at https://nvd.nist.gov/ '
            'or review the CVE details in the system.'
        ),
        'control': (
            'AI analysis is currently unavailable. Please review the '
            'control documentation and associated framework guidance '
            'for detailed information.'
        ),
        'mitigation': (
            'AI analysis is currently unavailable. Consider reviewing '
            'industry best practices and your organization\'s risk '
            'management playbook for mitigation strategies.'
        ),
        'threat': (
            'AI analysis is currently unavailable. Please review threat '
            'feeds manually and check the dark web monitoring dashboard '
            'for latest intelligence.'
        ),
        'general': (
            'AI assistant is currently unavailable. Please try again later '
            'or contact the SOC team for immediate assistance.'
        ),
    }

    return JsonResponse({
        'response': fallback_messages.get(context_type, fallback_messages['general']),
        'model': 'fallback',
        'context_type': context_type,
    })


@login_required
@require_POST
def ai_chat_message(request):
    """
    General-purpose AI chat endpoint. Accepts any message and responds
    using the configured Ollama model with security/GRC context.
    """
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)

    message = body.get('message', '').strip()
    if not message:
        return JsonResponse({'error': 'Message is required.'}, status=400)

    system_prompt = (
        "You are SWARM_AI, an advanced AI security assistant integrated into a "
        "Governance, Risk, and Compliance (GRC) platform. You help security analysts, "
        "compliance managers, and SOC teams with:\n"
        "- CVE analysis and vulnerability assessment\n"
        "- Threat intelligence interpretation\n"
        "- Dark web monitoring insights\n"
        "- Compliance framework guidance (ISO 27001, SOC 2, GDPR, RBI, SEBI)\n"
        "- Risk assessment and mitigation strategies\n"
        "- Incident response recommendations\n"
        "Be concise, technical, and actionable. Use security terminology appropriately."
    )

    prompt = f"{system_prompt}\n\nUser: {message}\n\nAssistant:"

    try:
        response = requests.post(
            f'{OLLAMA_URL}/api/generate',
            json={
                'model': OLLAMA_MODEL,
                'prompt': prompt,
                'stream': False,
            },
            timeout=30,
        )
        if response.status_code == 200:
            data = response.json()
            return JsonResponse({
                'response': data.get('response', ''),
                'model': OLLAMA_MODEL,
            })
    except (requests.ConnectionError, requests.Timeout):
        pass
    except requests.RequestException:
        pass

    return JsonResponse({
        'response': 'AI assistant is temporarily unavailable. The Ollama server may be offline. Please try again shortly.',
        'model': 'fallback',
    })


@login_required
def ai_chat(request):
    """Render the AI chat interface template."""
    return render(request, 'ai_assist/chat.html', {
        'ollama_model': OLLAMA_MODEL,
        'ollama_url': OLLAMA_URL,
    })
