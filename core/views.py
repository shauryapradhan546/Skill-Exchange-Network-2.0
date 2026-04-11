from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from datetime import timedelta
import json
from .models import Skill, User, UserTeaches, ExchangeRequest
from .utils import send_schedule_notification, send_meeting_link_notification, send_custom_notification


@csrf_protect
def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        if not email or not password:
            messages.error(request, "Please provide both email and password!")
            return render(request, "core/login.html")

        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                next_page = request.GET.get('next', 'index')
                return redirect(next_page)
            else:
                messages.error(request, "Incorrect password!")
        except User.DoesNotExist:
            messages.error(request, "No account found with this email!")
        except Exception as e:
            messages.error(request, f"Login error: {str(e)}")

    return render(request, "core/login.html")


@csrf_exempt
@require_http_methods(["POST"])
def firebase_login(request):
    try:
        data = json.loads(request.body)
        uid = data.get('uid')
        email = data.get('email')
        display_name = data.get('displayName', '')
        photo_url = data.get('photoURL', '')

        if not email:
            return JsonResponse({'success': False, 'error': 'Email is required'}, status=400)

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email.split('@')[0],
                'first_name': display_name.split(' ')[0] if display_name else '',
                'last_name': ' '.join(display_name.split(' ')[1:]) if display_name else ''
            }
        )

        if created:
            user.set_unusable_password()
            user.save()

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        return JsonResponse({
            'success': True,
            'message': f'Welcome {user.first_name or user.username}!',
            'user': {
                'email': user.email,
                'name': f"{user.first_name} {user.last_name}".strip(),
                'created': created
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_protect
def register_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if not Skill.objects.exists():
        Skill.objects.bulk_create([
            Skill(name="Python Programming", category="Programming"),
            Skill(name="JavaScript", category="Programming"),
            Skill(name="Java Programming", category="Programming"),
            Skill(name="C++ Programming", category="Programming"),
            Skill(name="React.js", category="Web Development"),
            Skill(name="Node.js", category="Web Development"),
            Skill(name="Django", category="Web Development"),
            Skill(name="Flask", category="Web Development"),
            Skill(name="Angular", category="Web Development"),
            Skill(name="Vue.js", category="Web Development"),
            Skill(name="Android Development", category="Mobile Development"),
            Skill(name="iOS Development", category="Mobile Development"),
            Skill(name="React Native", category="Mobile Development"),
            Skill(name="Flutter", category="Mobile Development"),
            Skill(name="Data Science", category="Data & AI"),
            Skill(name="Machine Learning", category="Data & AI"),
            Skill(name="Deep Learning", category="Data & AI"),
            Skill(name="Data Analysis", category="Data & AI"),
            Skill(name="SQL & Databases", category="Data & AI"),
            Skill(name="UI/UX Design", category="Design"),
            Skill(name="Graphic Design", category="Design"),
            Skill(name="Adobe Photoshop", category="Design"),
            Skill(name="Figma", category="Design"),
            Skill(name="Video Editing", category="Design"),
            Skill(name="3D Modeling", category="Design"),
            Skill(name="Digital Marketing", category="Marketing"),
            Skill(name="Content Writing", category="Marketing"),
            Skill(name="SEO", category="Marketing"),
            Skill(name="Social Media Marketing", category="Marketing"),
            Skill(name="Cloud Computing", category="Technology"),
            Skill(name="Cybersecurity", category="Technology"),
            Skill(name="DevOps", category="Technology"),
            Skill(name="Blockchain", category="Technology"),
            Skill(name="Game Development", category="Technology"),
        ])

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        name = request.POST.get('name', '').strip()

        if name and not first_name:
            parts = name.split(' ', 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ''

        email = request.POST.get('email', '').strip().lower()
        division = request.POST.get('division', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        password2 = request.POST.get('password2', '')

        if not confirm_password:
            confirm_password = password2

        teach_skills = request.POST.getlist('teach_skills')
        available_time = request.POST.get('available_time', 'Flexible')

        if not all([first_name, email, password]):
            messages.error(request, "Please fill all required fields!")
            return render(request, "core/register.html", {"skills": Skill.objects.all()})

        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters!")
            return render(request, "core/register.html", {"skills": Skill.objects.all()})

        if confirm_password and password != confirm_password:
            messages.error(request, "Passwords don't match!")
            return render(request, "core/register.html", {"skills": Skill.objects.all()})

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
            return render(request, "core/register.html", {"skills": Skill.objects.all()})

        username = email.split('@')[0]
        counter = 1
        original_username = username
        while User.objects.filter(username=username).exists():
            username = f"{original_username}{counter}"
            counter += 1

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password
            )
            user.division = division
            user.phone = phone
            user.save()

            if teach_skills:
                for skill_id in teach_skills:
                    try:
                        skill = Skill.objects.get(id=int(skill_id))
                        UserTeaches.objects.create(user=user, skill=skill, available_time=available_time)
                    except (Skill.DoesNotExist, ValueError):
                        continue

            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f"Welcome {first_name}! Your account has been created!")
            return redirect('index')

        except Exception as e:
            messages.error(request, f"Registration error: {str(e)}")
            return render(request, "core/register.html", {"skills": Skill.objects.all()})

    return render(request, "core/register.html", {"skills": Skill.objects.all()})


def logout_view(request):
    if request.user.is_authenticated:
        user_name = request.user.first_name or request.user.username
        logout(request)
        messages.success(request, f"Goodbye {user_name}! Logged out successfully!")
    return redirect('index')


def index(request):
    total_users = User.objects.count()
    total_skills = Skill.objects.count()
    total_exchanges = ExchangeRequest.objects.filter(status='accepted').count()

    seven_days_ago = timezone.now() - timedelta(days=7)

    recent_teachers_qs = UserTeaches.objects.filter(
        created_at__gte=seven_days_ago
    ).select_related('user', 'skill').order_by('-created_at')

    if request.user.is_authenticated:
        recent_teachers_qs = recent_teachers_qs.exclude(user=request.user)

    recent_teachers = recent_teachers_qs[:6]

    context = {
        'total_users': total_users,
        'total_skills': total_skills,
        'total_exchanges': total_exchanges,
        'recent_teachers': recent_teachers,
    }

    if request.user.is_authenticated:
        teaches_count = UserTeaches.objects.filter(user=request.user).count()
        incoming_count = ExchangeRequest.objects.filter(receiver=request.user, status='pending').count()
        context.update({'teaches_count': teaches_count, 'incoming_count': incoming_count})

    return render(request, "core/index.html", context)


@login_required
def profile_view(request):
    teaches = UserTeaches.objects.filter(user=request.user).select_related('skill')
    incoming_requests = ExchangeRequest.objects.filter(
        receiver=request.user, status='pending'
    ).select_related('requester', 'skill').order_by('-created_at')
    sent_requests = ExchangeRequest.objects.filter(
        requester=request.user
    ).select_related('receiver', 'skill').order_by('-created_at')
    accepted_exchanges = ExchangeRequest.objects.filter(
        Q(requester=request.user) | Q(receiver=request.user), status='accepted'
    ).select_related('requester', 'receiver', 'skill')

    return render(request, "core/profile.html", {
        'teaches': teaches,
        'incoming_requests': incoming_requests,
        'sent_requests': sent_requests,
        'accepted_exchanges': accepted_exchanges,
    })


def browse_view(request):
    skills = Skill.objects.annotate(teacher_count=Count('userteaches'))
    search_query = request.GET.get('search', '').strip()
    selected_category = request.GET.get('category', '').strip()

    if search_query:
        skills = skills.filter(Q(name__icontains=search_query) | Q(category__icontains=search_query))

    if selected_category:
        skills = skills.filter(category=selected_category)

    categories = Skill.objects.values_list('category', flat=True).distinct().order_by('category')

    return render(request, "core/browse.html", {
        "skills": skills.order_by('name'),
        "search_query": search_query,
        "selected_category": selected_category,
        "categories": categories,
        "total_skills": skills.count(),
    })


def match_view(request):
    skill_id = request.GET.get('skill_id')
    teachers = []
    skill = None

    if skill_id:
        try:
            skill = Skill.objects.get(id=skill_id)
            teachers = UserTeaches.objects.filter(skill=skill).select_related('user', 'skill')
        except Skill.DoesNotExist:
            messages.error(request, "Skill not found!")
        except Exception as e:
            messages.error(request, f"Error loading teachers: {str(e)}")

    return render(request, "core/match.html", {"teachers": teachers, "skill": skill})


@login_required
def sessions_view(request):
    teaching_sessions = ExchangeRequest.objects.filter(
        receiver=request.user, status='accepted'
    ).select_related('requester', 'skill')
    learning_sessions = ExchangeRequest.objects.filter(
        requester=request.user, status='accepted'
    ).select_related('receiver', 'skill')

    return render(request, "core/sessions.html", {
        'teaching_sessions': teaching_sessions,
        'learning_sessions': learning_sessions,
    })


@csrf_protect
@login_required
def request_exchange(request):
    if request.method == 'POST':
        teacher_id = request.POST.get('teacher_id')
        skill_id = request.POST.get('skill_id')
        skill_name = request.POST.get('skill_name')
        offering_skill = request.POST.get('offering_skill', '').strip()
        preferred_time = request.POST.get('preferred_time', 'Flexible')
        message = request.POST.get('message', '').strip()

        if not all([teacher_id, offering_skill]):
            messages.error(request, "Missing required information!")
            return redirect('browse')

        try:
            teacher = User.objects.get(id=teacher_id)
            if skill_id:
                skill = Skill.objects.get(id=skill_id)
            elif skill_name:
                skill = Skill.objects.get(name=skill_name)
            else:
                messages.error(request, "Skill not specified!")
                return redirect('browse')

            if teacher == request.user:
                messages.error(request, "You cannot request exchange with yourself!")
                return redirect('browse')

            existing = ExchangeRequest.objects.filter(
                requester=request.user, receiver=teacher, skill=skill, status='pending'
            ).exists()

            if existing:
                messages.warning(request, "You already have a pending request with this teacher!")
                return redirect('profile')

            ExchangeRequest.objects.create(
                requester=request.user,
                receiver=teacher,
                skill=skill,
                offering_skill=offering_skill,
                preferred_time=preferred_time,
                message=message
            )
            messages.success(request, f"Request sent to {teacher.first_name}!")
            return redirect('profile')

        except User.DoesNotExist:
            messages.error(request, "Teacher not found!")
        except Skill.DoesNotExist:
            messages.error(request, "Skill not found!")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

    return redirect('browse')


@csrf_protect
@login_required
def accept_exchange(request, exchange_id):
    if request.method == 'POST':
        try:
            exchange = ExchangeRequest.objects.get(id=exchange_id, receiver=request.user, status='pending')
            exchange.status = 'accepted'
            exchange.save()
            messages.success(request, f"Exchange with {exchange.requester.first_name} accepted!")
        except ExchangeRequest.DoesNotExist:
            messages.error(request, "Request not found or already processed!")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

    return redirect('profile')


@csrf_protect
@login_required
def reject_exchange(request, exchange_id):
    if request.method == 'POST':
        try:
            exchange = ExchangeRequest.objects.get(id=exchange_id, receiver=request.user, status='pending')
            exchange.status = 'rejected'
            exchange.save()
            messages.info(request, "Request declined!")
        except ExchangeRequest.DoesNotExist:
            messages.error(request, "Request not found!")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

    return redirect('profile')


@login_required
def add_skill(request):
    if request.method == 'POST':
        skill_id = request.POST.get('skill_id')
        proficiency = request.POST.get('proficiency', 'intermediate')
        available_time = request.POST.get('available_time', 'Flexible')
        notes = request.POST.get('notes', '').strip()

        if not skill_id:
            messages.error(request, "Please select a skill!")
            return redirect('add_skill')

        try:
            skill = Skill.objects.get(id=skill_id)
            if UserTeaches.objects.filter(user=request.user, skill=skill).exists():
                messages.warning(request, f"You are already teaching {skill.name}!")
                return redirect('profile')

            UserTeaches.objects.create(
                user=request.user, skill=skill,
                proficiency=proficiency, available_time=available_time, notes=notes
            )
            messages.success(request, f"Great! You can now teach {skill.name}!")
            return redirect('profile')

        except Skill.DoesNotExist:
            messages.error(request, "Skill not found!")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

    skills = Skill.objects.all().order_by('category', 'name')
    teaching_skill_ids = UserTeaches.objects.filter(user=request.user).values_list('skill_id', flat=True)
    return render(request, 'core/add_skill.html', {
        'skills': skills,
        'teaching_skill_ids': list(teaching_skill_ids),
    })


@login_required
@csrf_protect
def remove_skill(request, teach_id):
    if request.method == 'POST':
        try:
            teach = UserTeaches.objects.get(id=teach_id, user=request.user)
            skill_name = teach.skill.name
            teach.delete()
            messages.success(request, f"Removed {skill_name} from your teaching list!")
        except UserTeaches.DoesNotExist:
            messages.error(request, "Skill entry not found!")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

    return redirect('profile')


@csrf_protect
@login_required
def reschedule_session(request):
    if request.method == 'POST':
        session_id = request.POST.get('session_id')
        new_date = request.POST.get('new_date')
        new_time = request.POST.get('new_time')

        try:
            session = ExchangeRequest.objects.get(id=session_id, status='accepted')
            if session.requester == request.user or session.receiver == request.user:
                session.scheduled_date = new_date
                session.scheduled_time = new_time
                session.save()
                try:
                    send_schedule_notification(session, request.user)
                except Exception as e:
                    print(f"Notification error: {e}")
                messages.success(request, f"Session rescheduled to {new_date} at {new_time}! Notification sent.")
            else:
                messages.error(request, "You're not authorized to reschedule this session!")
        except ExchangeRequest.DoesNotExist:
            messages.error(request, "Session not found!")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

    return redirect('sessions')


@csrf_protect
@login_required
def save_meeting_link(request):
    if request.method == 'POST':
        session_id = request.POST.get('session_id')
        meeting_link = request.POST.get('meeting_link')
        platform = request.POST.get('platform', '').lower().replace(' ', '_')

        platform_map = {
            'google_meet': 'google_meet',
            'googlemeet': 'google_meet',
            'google meet': 'google_meet',
            'teams': 'teams',
            'microsoft_teams': 'teams',
            'microsoft teams': 'teams',
        }
        platform = platform_map.get(platform, platform)

        try:
            session = ExchangeRequest.objects.get(id=session_id, status='accepted')
            if session.requester == request.user or session.receiver == request.user:
                session.meeting_link = meeting_link
                session.meeting_platform = platform
                session.save()
                try:
                    send_meeting_link_notification(session, request.user)
                except Exception as e:
                    print(f"Notification error: {e}")
                return JsonResponse({'success': True, 'message': 'Link saved and notification sent!'})
            else:
                return JsonResponse({'error': 'Unauthorized'}, status=403)
        except ExchangeRequest.DoesNotExist:
            return JsonResponse({'error': 'Session not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_protect
@login_required
def send_notification(request):
    if request.method == 'POST':
        session_id = request.POST.get('session_id')
        notify_type = request.POST.get('notify_type', 'email')

        try:
            session = ExchangeRequest.objects.get(id=session_id, status='accepted')

            if session.requester != request.user and session.receiver != request.user:
                return JsonResponse({'error': 'Unauthorized'}, status=403)

            partner = session.receiver if session.requester == request.user else session.requester

            platform_display = session.get_meeting_platform_display() if session.meeting_platform else "Online"
            date_str = session.scheduled_date.strftime("%B %d, %Y") if session.scheduled_date else "To be confirmed"
            time_str = session.scheduled_time.strftime("%I:%M %p") if session.scheduled_time else "To be confirmed"

            subject = f"🔗 Skill Exchange Session: {session.skill.name}"
            body = (
                f"Hi {partner.first_name or partner.username},\n\n"
                f"Here are the details for your skill exchange session:\n\n"
                f"📚 Skill: {session.skill.name}\n"
                f"📅 Date: {date_str}\n"
                f"⏰ Time: {time_str}\n"
                f"🖥️ Platform: {platform_display}\n"
            )
            if session.meeting_link:
                body += f"🔗 Meeting Link: {session.meeting_link}\n"
            body += f"\nSent by: {request.user.first_name or request.user.username}\n\n— Skill Exchange Network"

            whatsapp_body = (
                f"📅 *Skill Exchange Session*\n\n"
                f"📚 Skill: {session.skill.name}\n"
                f"📅 Date: {date_str}\n"
                f"⏰ Time: {time_str}\n"
                f"🖥️ Platform: {platform_display}\n"
            )
            if session.meeting_link:
                whatsapp_body += f"🔗 Link: {session.meeting_link}\n"

            if notify_type == 'email':
                from .utils import send_email_to_user
                send_email_to_user(partner.email, subject, body)
                return JsonResponse({'success': True, 'message': f'Email sent to {partner.email}!'})
            elif notify_type == 'whatsapp':
                from .utils import send_whatsapp_to_user
                if not partner.phone:
                    return JsonResponse({'error': 'Partner has no phone number on their profile'}, status=400)
                send_whatsapp_to_user(partner.phone, whatsapp_body)
                return JsonResponse({'success': True, 'message': f'WhatsApp sent to {partner.phone}!'})
            else:
                return JsonResponse({'error': 'Invalid notify_type'}, status=400)

        except ExchangeRequest.DoesNotExist:
            return JsonResponse({'error': 'Session not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)
