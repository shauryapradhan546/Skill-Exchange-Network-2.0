from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Count
import json
from .models import ExchangeRequest, User, Skill, UserTeaches


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_request_exchange(request):
    try:
        data = json.loads(request.body)
        teacher_id = data.get('teacher_id')
        skill_name = data.get('skill_name')
        offering_skill = data.get('offering_skill')
        preferred_time = data.get('preferred_time')
        message = data.get('message', '')

        teacher = User.objects.get(id=teacher_id)
        skill = Skill.objects.get(name=skill_name)

        if teacher == request.user:
            return JsonResponse({'status': 'error', 'message': 'You cannot request exchange with yourself!'}, status=400)

        existing = ExchangeRequest.objects.filter(
            requester=request.user, receiver=teacher, skill=skill, status='pending'
        ).exists()

        if existing:
            return JsonResponse({'status': 'error', 'message': 'You already have a pending request with this teacher!'}, status=400)

        ExchangeRequest.objects.create(
            requester=request.user, receiver=teacher, skill=skill,
            offering_skill=offering_skill, preferred_time=preferred_time, message=message
        )
        return JsonResponse({'status': 'success', 'message': 'Request sent successfully!'})

    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Teacher not found!'}, status=404)
    except Skill.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Skill not found!'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_http_methods(["GET"])
def api_notifications(request):
    pending_count = ExchangeRequest.objects.filter(receiver=request.user, status='pending').count()
    sent_count = ExchangeRequest.objects.filter(requester=request.user, status='pending').count()
    accepted_count = (
        ExchangeRequest.objects.filter(requester=request.user, status='accepted').count() +
        ExchangeRequest.objects.filter(receiver=request.user, status='accepted').count()
    )
    return JsonResponse({
        'pending_requests': pending_count,
        'sent_requests': sent_count,
        'accepted_exchanges': accepted_count,
        'total_notifications': pending_count
    })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_schedule_session(request, exchange_id):
    try:
        data = json.loads(request.body)
        session_date = data.get('date')
        session_time = data.get('time')

        exchange = ExchangeRequest.objects.get(id=exchange_id, status='accepted')

        if exchange.requester != request.user and exchange.receiver != request.user:
            return JsonResponse({'status': 'error', 'message': 'You are not authorized to schedule this session!'}, status=403)

        exchange.scheduled_date = session_date
        exchange.scheduled_time = session_time
        exchange.save()

        try:
            from .utils import send_schedule_notification
            send_schedule_notification(exchange, request.user)
        except Exception as e:
            print(f"Notification error: {e}")

        return JsonResponse({
            'status': 'success',
            'message': f'Session scheduled for {session_date} at {session_time}. Notification sent!',
            'exchange_id': exchange_id,
            'date': session_date,
            'time': session_time
        })

    except ExchangeRequest.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Exchange not found or not accepted yet!'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@require_http_methods(["GET"])
def api_live_users(request):
    return JsonResponse({
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'total_skills': Skill.objects.count(),
        'total_exchanges': ExchangeRequest.objects.filter(status='accepted').count()
    })


@require_http_methods(["GET"])
def api_available_skills(request):
    qs = UserTeaches.objects.all()

    if request.user.is_authenticated:
        qs = qs.exclude(user=request.user)

    skills_with_teachers = (
        qs.values('skill__id', 'skill__name', 'skill__category')
        .annotate(teacher_count=Count('user__id', distinct=True))
        .filter(teacher_count__gt=0)
        .order_by('-teacher_count')
    )

    if not skills_with_teachers.exists():
        skills_with_teachers = (
            UserTeaches.objects
            .values('skill__id', 'skill__name', 'skill__category')
            .annotate(teacher_count=Count('user__id', distinct=True))
            .filter(teacher_count__gt=0)
            .order_by('-teacher_count')
        )

    result = []
    for item in skills_with_teachers:
        teachers_qs = (
            UserTeaches.objects
            .filter(skill__id=item['skill__id'])
            .select_related('user')
            .order_by('-created_at')
        )
        if request.user.is_authenticated:
            teachers_qs_filtered = teachers_qs.exclude(user=request.user)
            teachers_qs = teachers_qs_filtered if teachers_qs_filtered.exists() else teachers_qs

        # Keep distinct users
        seen_users = set()
        distinct_teachers = []
        for t in teachers_qs:
            if t.user.id not in seen_users:
                seen_users.add(t.user.id)
                distinct_teachers.append(t)
            if len(distinct_teachers) >= 2:
                break

        teacher_names = [t.user.first_name or t.user.username for t in distinct_teachers]
        result.append({
            'skill_id': item['skill__id'],
            'skill_name': item['skill__name'],
            'category': item['skill__category'],
            'teacher_count': item['teacher_count'],
            'teachers': teacher_names,
        })

    return JsonResponse({'skills': result, 'total': len(result)})


@require_http_methods(["GET"])
def api_health(request):
    return JsonResponse({
        "status": "ok",
        "message": "Skill Exchange API v1.0 working!",
        "version": "1.0.0",
        "endpoints": [
            "/api/health/", "/api/notifications/",
            "/api/request-exchange/", "/api/live-users/",
            "/api/exchanges/<id>/schedule/"
        ]
    })
