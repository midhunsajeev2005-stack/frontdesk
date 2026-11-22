from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db import DatabaseError
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from .store import rows, create, change, close_waiting, late_reasons, database_now

PUBLIC_EVENTS = ("Created","Agent reply","Customer reply","Reopened","Resolved","Closed after customer inactivity","Waiting for customer")
SELECT = "SELECT t.*, u.username AS agent FROM fd_ticket t LEFT JOIN auth_user u ON u.id=t.owner"

@require_http_methods(["GET", "HEAD"])
def health(request):
    try:
        rows("SELECT 1")
    except DatabaseError:
        return HttpResponse("unavailable", status=503, content_type="text/plain")
    return HttpResponse("ok", content_type="text/plain")

@login_required
@require_http_methods(["GET","POST"])
def inbox(request):
    close_waiting()
    user = request.user
    customers = get_user_model().objects.filter(is_staff=False,is_active=True) if user.is_staff else []
    if request.method == "POST":
        subject = request.POST.get("subject","").strip()
        priority = request.POST.get("priority")
        customer = user.pk
        if user.is_staff:
            candidate = request.POST.get("customer","")
            if not candidate.isdecimal() or not customers.filter(pk=candidate).exists():
                return HttpResponseBadRequest("Choose a customer.")
            customer = int(candidate)
        if not subject or len(subject)>180 or priority not in ("urgent","medium","low"):
            return HttpResponseBadRequest("Enter a subject and choose a priority.")
        return redirect("ticket",pk=create(customer,subject,priority,user.pk))
    tickets = rows(SELECT+" ORDER BY t.id DESC") if user.is_staff else rows(SELECT+" WHERE t.customer=%s ORDER BY t.id DESC",(user.pk,))
    selected = request.GET.get("show","all")
    now = database_now()
    for t in tickets:
        t["late"] = late_reasons(t, now)
    if selected == "late":
        tickets = [t for t in tickets if t["late"]]
    elif selected == "mine" and user.is_staff:
        tickets = [t for t in tickets if t["owner"]==user.pk]
    elif selected == "unclaimed":
        tickets = [t for t in tickets if t["owner"] is None]
    elif selected == "waiting":
        tickets = [t for t in tickets if t["state"]=="waiting"]
    return render(request,"inbox.html",{"tickets":tickets,"customers":customers})

@login_required
@require_http_methods(["GET","POST"])
def ticket(request, pk):
    close_waiting()
    user = request.user
    found = rows(SELECT+" WHERE t.id=%s",(pk,)) if user.is_staff else rows(SELECT+" WHERE t.id=%s AND t.customer=%s",(pk,user.pk))
    if not found:
        raise Http404
    error = ""
    if request.method=="POST":
        body = request.POST.get("body","").strip()
        try:
            if len(body)>10000:
                raise ValueError("Keep the message under 10,000 characters.")
            change(pk,user,request.POST.get("action"),body)
            return redirect("ticket",pk=pk)
        except ValueError as exc:
            error = str(exc)
            found = rows(SELECT+" WHERE t.id=%s",(pk,))
    found[0]["late"] = late_reasons(found[0], database_now())
    sql = "SELECT e.kind,e.body,e.happened,u.username FROM fd_event e LEFT JOIN auth_user u ON u.id=e.actor WHERE e.ticket=%s"
    params = [pk]
    if not user.is_staff:
        sql += " AND e.kind IN (" + ",".join(["%s"]*len(PUBLIC_EVENTS)) + ")"
        params.extend(PUBLIC_EVENTS)
    events = rows(sql+" ORDER BY e.id DESC",params)
    return render(request,"ticket.html",{"t":found[0],"events":events,"error":error},status=409 if error else 200)
