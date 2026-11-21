from django.db import connection, transaction
from django.utils import timezone
from datetime import timedelta
from .calendar import DAY, add_work, worked, deadlines

def rows(sql, params=()):
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        if not cursor.description:
            return []
        keys = [field[0] for field in cursor.description]
        return [dict(zip(keys, row)) for row in cursor.fetchall()]

def event(ticket, actor, now, kind, body=""):
    rows("INSERT INTO fd_event(ticket,actor,happened,kind,body) VALUES (%s,%s,%s,%s,%s)",(ticket,actor,now,kind,body))

@transaction.atomic
def create(customer, subject, priority, actor):
    now = timezone.now()
    reply, fix = deadlines(now, priority)
    ticket = rows("INSERT INTO fd_ticket(customer,subject,priority,created,reply_due,fix_due) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",(customer,subject,priority,now,reply,fix))[0]["id"]
    event(ticket,actor,now,"Created")
    return ticket

def advance_clocks(t, now):
    if t["state"] == "waiting":
        pause = worked(t["waiting_since"],now)
        if not t["first_reply"]:
            t["reply_due"] = add_work(t["reply_due"],pause)
        t["fix_due"] = add_work(t["fix_due"],pause)

@transaction.atomic
def change(pk, user, action, body=""):
    records = rows("SELECT * FROM fd_ticket WHERE id=%s FOR UPDATE",(pk,))
    if not records:
        raise ValueError("Ticket unavailable.")
    t = records[0]
    now = timezone.now()
    if not user.is_staff and t["customer"] != user.pk:
        raise ValueError("Ticket unavailable.")
    if action == "claim" and user.is_staff and t["owner"] is None and t["state"] == "open":
        t["owner"] = user.pk
        kind = "Claimed"
    elif action == "reopen" and not user.is_staff and t["state"] == "resolved" and now <= t["finished"] + timedelta(days=7):
        t["state"], t["finished"] = "open", None
        t["fix_due"] = deadlines(now,t["priority"])[1]
        kind = "Reopened"
    elif t["state"] in ("resolved","closed"):
        raise ValueError("This ticket is finished. Create a new ticket if the reopening window has passed.")
    elif action == "reply" and body and (not user.is_staff or t["owner"] == user.pk):
        if user.is_staff and t["first_reply"] is None:
            advance_clocks(t,now)
            t["first_reply"] = now
            if t["state"] == "waiting":
                t["waiting_since"] = now
        if not user.is_staff and t["state"] == "waiting":
            advance_clocks(t,now)
            t["state"], t["waiting_since"] = "open", None
        kind = "Agent reply" if user.is_staff else "Customer reply"
    elif user.is_staff and t["owner"] == user.pk:
        if action == "note" and body:
            kind = "Private note"
        elif action == "wait" and t["state"] == "open":
            t["state"], t["waiting_since"] = "waiting", now
            kind = "Waiting for customer"
        elif action == "resolve":
            advance_clocks(t,now)
            t["state"], t["finished"], t["waiting_since"] = "resolved", now, None
            kind = "Resolved"
        elif action == "priority" and body in ("urgent","medium","low") and body != t["priority"]:
            t["priority"] = body
            reply, t["fix_due"] = deadlines(now,body)
            if not t["first_reply"]:
                t["reply_due"] = reply
            if t["state"] == "waiting":
                # Preserve the original customer inactivity timer.
                start = t["waiting_since"]
                reply_remaining = worked(now, reply)
                fix_remaining = worked(now, t["fix_due"])
                if not t["first_reply"]:
                    t["reply_due"] = add_work(start,reply_remaining)
                t["fix_due"] = add_work(start,fix_remaining)
            kind = "Priority changed"
        else:
            raise ValueError("This action is unavailable.")
    else:
        raise ValueError("This ticket may already be claimed. Refresh to see its owner.")
    rows("UPDATE fd_ticket SET owner=%s,state=%s,first_reply=%s,waiting_since=%s,finished=%s,reply_due=%s,fix_due=%s,priority=%s WHERE id=%s",tuple(t[k] for k in ("owner","state","first_reply","waiting_since","finished","reply_due","fix_due","priority"))+(pk,))
    event(pk,user.pk,now,kind,body if action in ("reply","note","priority") else "")

@transaction.atomic
def close_waiting():
    now = timezone.now()
    for t in rows("SELECT id,waiting_since FROM fd_ticket WHERE state='waiting' FOR UPDATE"):
        due = add_work(t["waiting_since"], 5*DAY)
        if now >= due:
            rows("UPDATE fd_ticket SET state='closed',finished=%s WHERE id=%s",(now,t["id"]))
            event(t["id"],None,now,"Closed after customer inactivity")
