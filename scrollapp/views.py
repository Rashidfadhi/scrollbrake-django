from django.shortcuts import render,redirect
from django.utils import timezone
from django.db.models import Sum,Count
from django.core.paginator import Paginator
from .forms import ScrollSessionform
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required


from django.contrib import messages
from django.views.decorators.http import require_POST


from datetime import date
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
import csv
from django.http import HttpResponse
from .models import ScrollSession,BreakEvent,UserGoal
# Create your views here.

@login_required
def home(request):
    today = timezone.localdate()
    sessions = ScrollSession.objects.filter(user=request.user)
    today = timezone.localdate()

    today_sessions = sessions.filter(created_at__date=today)

    week_start = today - timedelta(days=today.weekday())

    week_sessions = sessions.filter(
        created_at__date__gte=week_start,
        created_at__date__lte=today,
    )

    today_duration = today_sessions.aggregate(
        total=Sum("duration")
    )["total"] or 0

    week_duration = week_sessions.aggregate(
        total=Sum("duration")
    )["total"] or 0

    today_minutes = round(today_duration / 60, 1)
    week_hours = round(week_duration / 3600, 2)

    user_goal, created = UserGoal.objects.get_or_create(
    user=request.user,
    defaults={"daily_limit_minutes": 60},
    )

    daily_goal_minutes = user_goal.daily_limit_minutes

    goal_progress = min(
        round((today_minutes / daily_goal_minutes) * 100),
        100,
    )

    goal_remaining = max(
        daily_goal_minutes - today_minutes,
        0,
    )

    today_scroll_count = today_sessions.aggregate(
        total=Sum("scroll_count")
    )["total"] or 0
    selected_date = request.GET.get('date', str(today))

    try:
        selected_date = date.fromisoformat(selected_date)
    except ValueError:
        selected_date = today

    selected_sessions = ScrollSession.objects.filter(
        created_at__date=selected_date
    )

    selected_duration = selected_sessions.aggregate(
        total=Sum('duration')
    )['total'] or 0

    selected_count = selected_sessions.count()


    total_sessions = sessions.count()

    total_duration = (
        sessions.aggregate(total=Sum('duration'))['total'] or 0
    )

    high_momentum_sessions = sessions.filter(
        momentum='HIGH'
    ).count()

    today_sessions = sessions.filter(
        created_at__date=today
    )

    today_duration = (
        today_sessions.aggregate(total=Sum('duration'))['total'] or 0
    )

    today_high_momentum = today_sessions.filter(
        momentum='HIGH'
    ).count()

    total_breaks = BreakEvent.objects.filter(
        user=request.user
    ).count()


    recent_breaks = BreakEvent.objects.filter(
        user=request.user
    ).order_by("-created_at")[:10]

    app_stats = (
    sessions.values('app_name')
    .annotate(session_count=Count('id'))
    .order_by('-session_count'))

    return render(request, 'index.html', {
        'total_sessions': total_sessions,
        'total_duration': total_duration,
        'high_momentum_sessions': high_momentum_sessions,
        'today_duration': today_duration,
        'today_high_momentum': today_high_momentum,
        'app_stats': app_stats,
        'selected_date': selected_date.isoformat(),
        'selected_duration': selected_duration,
        'selected_count': selected_count,
        "total_breaks": total_breaks,
        "recent_breaks": recent_breaks,
        "today_duration": today_duration,
        "week_duration": week_duration,
        "today_scroll_count": today_scroll_count,
        "today_minutes": today_minutes,
        "week_hours": week_hours,
        "daily_goal_minutes": daily_goal_minutes,
        "goal_progress": goal_progress,
        "goal_remaining": goal_remaining,
    })


@login_required
@require_POST
def update_goal(request):
    try:
        minutes = int(request.POST.get("daily_limit_minutes", ""))
    except (TypeError, ValueError):
        messages.error(request, "Enter a valid number of minutes.")
        return redirect("home")

    if not 1 <= minutes <= 1440:
        messages.error(request, "Choose a limit between 1 and 1440 minutes.")
        return redirect("home")

    UserGoal.objects.update_or_create(
        user=request.user,
        defaults={"daily_limit_minutes": minutes},
    )

    messages.success(request, "Your daily scrolling goal has been saved.")
    return redirect("home")


@login_required
def session_list(request):
    search_query = request.GET.get('search', '')
    momentum_filter = request.GET.get('momentum', '')

    sessions = ScrollSession.objects.filter(user=request.user)

    if search_query:
        sessions = sessions.filter(
            app_name__icontains=search_query
        )

    if momentum_filter in ['LOW', 'MEDIUM', 'HIGH']:
        sessions = sessions.filter(momentum=momentum_filter)

    paginator = Paginator(sessions, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'sessions.html', {
        'sessions': sessions,
        'page_obj': page_obj,
        'search_query': search_query,
        'momentum_filter': momentum_filter,
    })


@login_required
def create_session(request):
    if request.method=='POST':
        form = ScrollSessionform(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.user = request.user
            session.save()
            return redirect('session_list')

    else:
        form = ScrollSessionform()

    return render(request, 'create_session.html',{'form' : form})

@login_required
def update_sessions(request, pk):
    session = ScrollSession.objects.get(pk=pk,user=request.user)

    if request.method =='POST':
        form = ScrollSessionform(request.POST, instance=session)

        if form.is_valid():
            form.save()
            return redirect('session_list')
    else:
        form = ScrollSessionform(instance=session)

    return render(request, 'update_session.html', {'form' : form, 'session': session})


@login_required
def delete_session(request,pk):
    session = ScrollSession.objects.get(pk=pk,user=request.user)

    if request.method=='POST':
        session.delete()
        return redirect('session list')
    return render(request,'delete_session.html',{'session' : session})



@login_required
def export_sessions(request):
    search_query = request.GET.get('search', '').strip()
    momentum_filter = request.GET.get('momentum', '').strip()

    sessions = ScrollSession.objects.filter(user=request.user)

    if search_query:
        sessions = sessions.filter(
            app_name__icontains=search_query
        )

    if momentum_filter in ['LOW', 'MEDIUM', 'HIGH']:
        sessions = sessions.filter(
            momentum=momentum_filter
        )

    sessions = sessions.order_by('-created_at')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        'attachment; filename="scroll_sessions.csv"'
    )

    writer = csv.writer(response)

    writer.writerow([
        'App Name',
        'Duration (seconds)',
        'Scroll Count',
        'Momentum',
        'Created At',
    ])

    for session in sessions:
        writer.writerow([
            session.app_name,
            session.duration,
            session.scroll_count,
            session.momentum,
            session.created_at,
        ])

    return response




@login_required
def session_detail(request, pk):
    session = get_object_or_404(ScrollSession, pk=pk,user=request.user)

    return render(
        request,
        'session_details.html',
        {'session': session}
    )