from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from db import get_db, get_next_sequence

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def get_db_connection():
    return get_db()


def _verify_password(stored_password, provided_password):
    # Support both legacy plain-text and hashed passwords.
    if not stored_password:
        return False, None
    if stored_password.startswith(("pbkdf2:", "scrypt:", "argon2:")):
        return check_password_hash(stored_password, provided_password), stored_password
    if stored_password == provided_password:
        return True, generate_password_hash(provided_password)
    return False, None


def _build_booking_rows(db, limit=None):
    cursor = db.bookings.find(
        {},
        {
            "_id": 0,
            "id": 1,
            "user_id": 1,
            "event_name": 1,
            "booking_date": 1,
            "event_date": 1,
            "venue_name": 1,
            "venue_capacity": 1,
            "decoration_theme": 1,
            "guest_count": 1,
            "total_amount": 1,
            "advance_amount": 1,
            "remaining_amount": 1,
            "payment_status": 1,
        },
    ).sort("id", -1)
    if limit:
        cursor = cursor.limit(limit)
    bookings = list(cursor)
    if not bookings:
        return []

    user_ids = {b.get("user_id") for b in bookings if b.get("user_id") is not None}
    users = {
        u["id"]: u
        for u in db.users.find(
            {"id": {"$in": list(user_ids)}},
            {"_id": 0, "id": 1, "fullname": 1, "email": 1, "number": 1},
        )
    }

    booking_ids = [b["id"] for b in bookings if "id" in b]
    food_rows = list(
        db.booking_food.find(
            {"booking_id": {"$in": booking_ids}},
            {"_id": 0, "booking_id": 1, "quantity": 1, "subtotal": 1},
        )
    )
    totals = {}
    for row in food_rows:
        bid = row.get("booking_id")
        if bid is None:
            continue
        if bid not in totals:
            totals[bid] = {"items": 0, "total": 0.0}
        totals[bid]["items"] += int(row.get("quantity", 0))
        totals[bid]["total"] += float(row.get("subtotal", 0.0))

    result = []
    for b in bookings:
        user = users.get(b.get("user_id"), {})
        booking_date = b.get("booking_date")
        if booking_date:
            booking_date = booking_date.strftime("%Y-%m-%d %H:%M")
        event_date = b.get("event_date") or ""
        if not event_date:
            event_date = booking_date or ""

        total_amount = b.get("total_amount")
        if total_amount is None:
            total_amount = totals.get(b.get("id"), {}).get("total", 0.0)
        result.append(
            {
                "id": b.get("id"),
                "event_name": b.get("event_name", ""),
                "booking_date": booking_date or "",
                "event_date": event_date,
                "venue_name": b.get("venue_name", ""),
                "venue_capacity": b.get("venue_capacity", ""),
                "decoration_theme": b.get("decoration_theme", ""),
                "guest_count": b.get("guest_count", ""),
                "user_name": user.get("fullname", "Unknown"),
                "user_email": user.get("email", ""),
                "user_number": user.get("number", ""),
                "items_count": totals.get(b.get("id"), {}).get("items", 0),
                "total": round(float(total_amount or 0.0), 2),
                "advance_amount": b.get("advance_amount", 0),
                "remaining_amount": b.get("remaining_amount", 0),
                "payment_status": b.get("payment_status", "Pending"),
            }
        )
    return result


def _build_booking_detail(db, booking_id):
    booking = db.bookings.find_one(
        {"id": booking_id},
        {
            "_id": 0,
            "id": 1,
            "user_id": 1,
            "event_name": 1,
            "booking_date": 1,
            "event_date": 1,
            "date": 1,
            "venue_name": 1,
            "venue": 1,
            "venue_location": 1,
            "venue_capacity": 1,
            "decoration_theme": 1,
            "decoration_requirements": 1,
            "decoration": 1,
            "guest_count": 1,
            "guest": 1,
            "payment_status": 1,
            "total_amount": 1,
            "advance_amount": 1,
            "remaining_amount": 1,
            "transaction_id": 1,
            "venue_price": 1,
            "decoration_price": 1,
            "service_charge": 1,
        },
    )
    if not booking:
        return None

    user = db.users.find_one(
        {"id": booking.get("user_id")},
        {"_id": 0, "fullname": 1, "email": 1, "number": 1, "address": 1},
    ) or {}

    items = list(
        db.booking_food.find(
            {"booking_id": booking_id},
            {"_id": 0, "food_id": 1, "quantity": 1, "subtotal": 1},
        )
    )
    if items:
        food_ids = [i["food_id"] for i in items if "food_id" in i]
        foods = {
            f["id"]: f
            for f in db.food_items.find(
                {"id": {"$in": food_ids}},
                {"_id": 0, "id": 1, "name": 1, "category": 1, "price": 1},
            )
        }
        for i in items:
            food = foods.get(i.get("food_id"), {})
            i["name"] = food.get("name", "Unknown")
            i["category"] = food.get("category", "")
            i["price"] = food.get("price", 0.0)

    booking_date = booking.get("booking_date")
    if booking_date:
        booking_date = booking_date.strftime("%Y-%m-%d %H:%M")

    event_date = booking.get("event_date") or booking.get("date") or ""
    venue_name = booking.get("venue_name") or booking.get("venue") or ""
    decoration_theme = booking.get("decoration_theme") or booking.get("decoration") or ""
    decoration_requirements = booking.get("decoration_requirements") or ""
    guest_count = booking.get("guest_count")
    if guest_count in (None, ""):
        guest_count = booking.get("guest", "")

    total_items = sum(int(i.get("quantity", 0)) for i in items)
    stored_total = booking.get("total_amount")
    if stored_total is None:
        total_amount = round(sum(float(i.get("subtotal", 0.0)) for i in items), 2)
    else:
        total_amount = round(float(stored_total), 2)

    return {
        "id": booking.get("id"),
        "event_name": booking.get("event_name", ""),
        "booking_date": booking_date or "",
        "event_date": event_date,
        "user_name": user.get("fullname", "Unknown"),
        "user_email": user.get("email", ""),
        "user_number": user.get("number", ""),
        "user_address": user.get("address", ""),
        "venue_name": venue_name,
        "venue_location": booking.get("venue_location", ""),
        "venue_capacity": booking.get("venue_capacity", ""),
        "decoration_theme": decoration_theme,
        "decoration_requirements": decoration_requirements,
        "guest_count": guest_count,
        "payment_status": booking.get("payment_status", "Pending"),
        "advance_amount": booking.get("advance_amount", 0),
        "remaining_amount": booking.get("remaining_amount", 0),
        "transaction_id": booking.get("transaction_id", ""),
        "venue_price": booking.get("venue_price", 0),
        "decoration_price": booking.get("decoration_price", 0),
        "service_charge": booking.get("service_charge", 0),
        "booking_items": items,
        "total_items": total_items,
        "total_amount": total_amount,
    }


def _group_items_by_category(items):
    grouped = {}
    for item in items or []:
        category = item.get("category") or "Other"
        grouped.setdefault(category, []).append(item)
    return grouped


@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']

        try:
            db = get_db_connection()
            admin = db.users.find_one(
                {"email": email, "role": "admin"}
            )
        except Exception as exc:
            return f"Admin login failed: {exc}"

        if admin:
            ok, upgraded = _verify_password(admin.get("password"), password)
            if ok and upgraded:
                db.users.update_one({"id": admin["id"]}, {"$set": {"password": upgraded}})
            session['admin'] = int(admin['id'])
            return redirect(url_for('admin.admin_dashboard'))
        return "Invalid Admin Login"

    return render_template("Admin/Admin_login.html")


@admin_bp.route('/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin.admin_login'))

    try:
        db = get_db_connection()

        food_count = db.food_items.count_documents({})
        booking_count = db.bookings.count_documents({})
        user_count = db.users.count_documents({"role": "user"})
        recent_bookings = _build_booking_rows(db, limit=10)
    except Exception as exc:
        return f"Could not load admin dashboard: {exc}"

    return render_template(
        "Admin/Admin_dasboard.html",
        food_count=food_count,
        booking_count=booking_count,
        user_count=user_count,
        recent_bookings=recent_bookings
    )


@admin_bp.route('/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin.admin_login'))


@admin_bp.route('/food', methods=['GET', 'POST'])
def manage_food():
    if 'admin' not in session:
        return redirect(url_for('admin.admin_login'))

    try:
        db = get_db_connection()

        if request.method == 'POST':
            action = request.form.get('action')

            if action == 'add':
                name = request.form['name']
                category = request.form['category']
                price = float(request.form['price'])
                food_id = get_next_sequence("food_items")
                db.food_items.insert_one(
                    {
                        "id": food_id,
                        "name": name,
                        "category": category,
                        "price": price,
                        "created_at": datetime.utcnow(),
                    }
                )

            elif action == 'edit':
                food_id = int(request.form['food_id'])
                name = request.form['name']
                category = request.form['category']
                price = float(request.form['price'])
                db.food_items.update_one(
                    {"id": food_id},
                    {"$set": {"name": name, "category": category, "price": price}},
                )

            elif action == 'delete':
                food_id = int(request.form['food_id'])
                db.food_items.delete_one({"id": food_id})

            return redirect(url_for('admin.manage_food'))

        foods = list(db.food_items.find({}, {"_id": 0}).sort([("category", 1), ("name", 1)]))
    except (Exception, ValueError) as exc:
        return f"Food management failed: {exc}"

    return render_template("Admin/food_management.html", foods=foods)


@admin_bp.route('/bookings')
def view_bookings():
    if 'admin' not in session:
        return redirect(url_for('admin.admin_login'))

    try:
        db = get_db_connection()
        bookings = _build_booking_rows(db, limit=None)
    except Exception as exc:
        return f"Could not load bookings: {exc}"

    return render_template("Admin/bookings.html", bookings=bookings)


@admin_bp.route('/bookings/<int:booking_id>/delete', methods=['POST'])
def delete_booking(booking_id):
    if 'admin' not in session:
        return redirect(url_for('admin.admin_login'))

    try:
        db = get_db_connection()
        db.bookings.delete_one({"id": booking_id})
    except Exception as exc:
        return f"Could not delete booking: {exc}"

    return redirect(url_for('admin.view_bookings'))


@admin_bp.route('/bookings/<int:booking_id>')
def booking_detail(booking_id):
    if 'admin' not in session:
        return redirect(url_for('admin.admin_login'))

    try:
        db = get_db_connection()
        booking = _build_booking_detail(db, booking_id)
        if not booking:
            return "Booking not found"
    except Exception as exc:
        return f"Could not load booking: {exc}"

    return render_template("Admin/booking_detail.html", booking=booking)


@admin_bp.route('/bookings/<int:booking_id>/json')
def booking_detail_json(booking_id):
    if 'admin' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        db = get_db_connection()
        booking = _build_booking_detail(db, booking_id)
        if not booking:
            return jsonify({"error": "Booking not found"}), 404
        booking["items_by_category"] = _group_items_by_category(
            booking.get("booking_items", [])
        )
        return jsonify(booking)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
