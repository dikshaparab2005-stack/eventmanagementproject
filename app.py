import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

from admin_panel import admin_bp
from db import get_db, get_next_sequence, init_db

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")
app.register_blueprint(admin_bp)
init_db()


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


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/about_us")
def about_us():
    return render_template("about_us.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fullname = request.form["fullname"].strip()
        number = request.form["number"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        address = request.form["address"].strip()

        try:
            db = get_db_connection()
            existing_user = db.users.find_one({"email": email}, {"id": 1})
            if existing_user:
                return "Email already registered. Please login."

            user_id = get_next_sequence("users")
            db.users.insert_one(
                {
                    "id": user_id,
                    "fullname": fullname,
                    "number": number,
                    "email": email,
                    "password": generate_password_hash(password),
                    "address": address,
                    "role": "user",
                    "created_at": datetime.utcnow(),
                }
            )
            return redirect(url_for("login"))
        except Exception as exc:
            return f"Registration failed: {exc}"

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        try:
            db = get_db_connection()
            user = db.users.find_one(
                {
                    "$or": [
                        {"fullname": username},
                        {"email": username.lower()},
                    ],
                }
            )
        except Exception as exc:
            return f"Login failed: {exc}"

        if user:
            ok, upgraded = _verify_password(user.get("password"), password)
            if ok and upgraded:
                db.users.update_one({"id": user["id"]}, {"$set": {"password": upgraded}})
            session["user"] = int(user["id"])
            session["username"] = user.get("fullname", "")
            return redirect(url_for("select_event"))
        return "Invalid login details"

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/book_event")
def book_event_redirect():
    return redirect(url_for("select_event"))


@app.route("/select_event", methods=["GET", "POST"])
def select_event():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        event_name = request.form.get("event_name", "").strip()
        if not event_name:
            return "Please select an event"

        try:
            db = get_db_connection()
            booking_id = get_next_sequence("bookings")
            db.bookings.insert_one(
                {
                    "id": booking_id,
                    "user_id": int(session["user"]),
                    "event_name": event_name,
                    "booking_date": datetime.utcnow(),
                }
            )
            session["current_booking_id"] = booking_id
            session["event_name"] = event_name
            return redirect(url_for("food", booking_id=booking_id))
        except Exception as exc:
            return f"Could not create booking: {exc}"

    return render_template("select_event.html")


@app.route("/food", methods=["GET", "POST"])
def food():
    if "user" not in session:
        return redirect(url_for("login"))

    try:
        db = get_db_connection()

        if request.method == "POST":
            booking_id = request.form.get("booking_id")
            if not booking_id:
                return "Missing booking id"

            food_ids = request.form.getlist("food_id[]")
            quantities = request.form.getlist("quantity[]")

            inserted_rows = 0
            for fid, qty in zip(food_ids, quantities):
                qty_int = int(qty) if qty else 0
                if qty_int <= 0:
                    continue

                row = db.food_items.find_one({"id": int(fid)}, {"price": 1})
                if not row:
                    continue

                subtotal = float(row["price"]) * qty_int
                db.booking_food.insert_one(
                    {
                        "id": get_next_sequence("booking_food"),
                        "booking_id": int(booking_id),
                        "food_id": int(fid),
                        "quantity": qty_int,
                        "subtotal": subtotal,
                        "created_at": datetime.utcnow(),
                    }
                )
                inserted_rows += 1

            if inserted_rows == 0:
                return "No food items selected"
            session["current_booking_id"] = int(booking_id)
            return redirect(url_for("venue_page", booking_id=booking_id))

        booking_id = request.args.get("booking_id") or session.get("current_booking_id")
        if not booking_id:
            return redirect(url_for("select_event"))
        foods = list(db.food_items.find({}, {"_id": 0}).sort([("category", 1), ("name", 1)]))
        return render_template("food.html", foods=foods, booking_id=booking_id)
    except Exception as exc:
        return f"Food selection failed: {exc}"


@app.route("/my_bookings")
def my_bookings():
    if "user" not in session:
        return redirect(url_for("login"))

    try:
        db = get_db_connection()
        bookings = list(
            db.bookings.find(
                {"user_id": int(session["user"])},
                {
                    "_id": 0,
                    "id": 1,
                    "event_name": 1,
                    "booking_date": 1,
                    "event_date": 1,
                    "venue_name": 1,
                    "decoration_theme": 1,
                    "guest_count": 1,
                    "total_amount": 1,
                    "advance_amount": 1,
                    "remaining_amount": 1,
                    "payment_status": 1,
                },
            ).sort("id", -1)
        )
        for booking in bookings:
            if booking.get("booking_date"):
                booking["booking_date"] = booking["booking_date"].strftime("%Y-%m-%d %H:%M")
        return render_template("my_bookings.html", bookings=bookings)
    except Exception as exc:
        return f"Could not fetch bookings: {exc}"


def _get_user_booking(db, booking_id, user_id):
    booking = db.bookings.find_one(
        {"id": booking_id, "user_id": user_id},
        {
            "_id": 0,
            "id": 1,
            "user_id": 1,
            "event_name": 1,
            "booking_date": 1,
            "event_date": 1,
            "venue_name": 1,
            "venue_location": 1,
            "venue_capacity": 1,
            "decoration_theme": 1,
            "decoration_requirements": 1,
            "guest_count": 1,
            "food_price": 1,
            "venue_price": 1,
            "decoration_price": 1,
            "service_charge": 1,
        },
    )
    if not booking:
        return None

    user = db.users.find_one(
        {"id": booking.get("user_id")},
        {"_id": 0, "fullname": 1, "email": 1, "number": 1},
    ) or {}
    booking["user_name"] = user.get("fullname", "")
    booking["user_email"] = user.get("email", "")
    booking["user_number"] = user.get("number", "")

    if booking.get("booking_date"):
        booking["booking_date"] = booking["booking_date"].strftime("%Y-%m-%d %H:%M")
    return booking


@app.route("/my_bookings/<int:booking_id>/edit")
def edit_booking(booking_id):
    if "user" not in session:
        return redirect(url_for("login"))

    try:
        db = get_db_connection()
        booking = _get_user_booking(db, booking_id, int(session["user"]))
        if not booking:
            return "Booking not found"
        session["current_booking_id"] = booking_id
        return render_template("booking.html", booking=booking)
    except Exception as exc:
        return f"Could not load booking: {exc}"


@app.route("/my_bookings/<int:booking_id>/delete", methods=["POST"])
def delete_booking(booking_id):
    if "user" not in session:
        return redirect(url_for("login"))

    try:
        db = get_db_connection()
        db.bookings.delete_one({"id": booking_id, "user_id": int(session["user"])})
        db.booking_food.delete_many({"booking_id": booking_id})
        if session.get("current_booking_id") == booking_id:
            session.pop("current_booking_id", None)
    except Exception as exc:
        return f"Could not delete booking: {exc}"

    return redirect(url_for("my_bookings"))


@app.route("/venue")
def venue_page():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("venu.html")


@app.route("/decoration")
def decoration_page():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("decoration.html")


@app.route("/booking", methods=["GET", "POST"])
def booking_page():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("booking.html")


@app.route("/update_booking", methods=["GET", "POST"])
def update_booking():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        try:
            db = get_db_connection()
            booking_id = request.form.get("booking_id") or session.get("current_booking_id")
            if not booking_id:
                return redirect(url_for("my_bookings"))

            booking = db.bookings.find_one(
                {"id": int(booking_id), "user_id": int(session["user"])},
                {"id": 1},
            )
            if not booking:
                return "Booking not found"

            venue_name = request.form.get("venue_name", "").strip()
            event_date = request.form.get("event_date", "").strip()
            guest_count = request.form.get("guest_count", "").strip()

            db.bookings.update_one(
                {"id": int(booking_id), "user_id": int(session["user"])},
                {
                    "$set": {
                        "venue_name": venue_name,
                        "event_date": event_date,
                        "guest_count": guest_count,
                    }
                },
            )
            session["current_booking_id"] = int(booking_id)
            return redirect(url_for("my_bookings"))
        except Exception as exc:
            return f"Update booking failed: {exc}"

    return render_template("update_booking.html")


@app.route("/my_bookings/<int:booking_id>/food", methods=["GET", "POST"])
def update_food(booking_id):
    if "user" not in session:
        return redirect(url_for("login"))

    try:
        db = get_db_connection()
        booking = db.bookings.find_one(
            {"id": booking_id, "user_id": int(session["user"])},
            {"id": 1, "venue_price": 1, "decoration_price": 1},
        )
        if not booking:
            return "Booking not found"

        if request.method == "POST":
            food_ids = request.form.getlist("food_id[]")
            quantities = request.form.getlist("quantity[]")

            db.booking_food.delete_many({"booking_id": booking_id})

            total_food = 0.0
            inserted = 0
            for fid, qty in zip(food_ids, quantities):
                qty_int = int(qty) if qty else 0
                if qty_int <= 0:
                    continue
                food = db.food_items.find_one({"id": int(fid)}, {"price": 1})
                if not food:
                    continue
                subtotal = float(food.get("price", 0)) * qty_int
                db.booking_food.insert_one(
                    {
                        "id": get_next_sequence("booking_food"),
                        "booking_id": booking_id,
                        "food_id": int(fid),
                        "quantity": qty_int,
                        "subtotal": subtotal,
                        "created_at": datetime.utcnow(),
                    }
                )
                total_food += subtotal
                inserted += 1

            if inserted == 0:
                return "No food items selected"

            venue_price = float(booking.get("venue_price") or 0)
            decoration_price = float(booking.get("decoration_price") or 0)
            service_charge = round((total_food + venue_price + decoration_price) * 0.10, 2)
            total_amount = round(total_food + venue_price + decoration_price + service_charge, 2)

            db.bookings.update_one(
                {"id": booking_id, "user_id": int(session["user"])},
                {
                    "$set": {
                        "food_price": round(total_food, 2),
                        "service_charge": service_charge,
                        "total_amount": total_amount,
                    }
                },
            )
            session["current_booking_id"] = booking_id
            return redirect(url_for("my_bookings"))

        foods = list(db.food_items.find({}, {"_id": 0}).sort([("category", 1), ("name", 1)]))
        existing = list(
            db.booking_food.find(
                {"booking_id": booking_id},
                {"_id": 0, "food_id": 1, "quantity": 1},
            )
        )
        food_map = {
            f["id"]: f
            for f in db.food_items.find(
                {"id": {"$in": [e["food_id"] for e in existing]}},
                {"_id": 0, "id": 1, "name": 1, "category": 1, "price": 1},
            )
        }
        existing_items = []
        for e in existing:
            food = food_map.get(e.get("food_id"), {})
            existing_items.append(
                {
                    "id": e.get("food_id"),
                    "name": food.get("name", "Unknown"),
                    "category": food.get("category", "Other"),
                    "price": food.get("price", 0),
                    "qty": e.get("quantity", 0),
                }
            )

        return render_template(
            "update_food.html",
            foods=foods,
            booking_id=booking_id,
            existing_items=existing_items,
        )
    except Exception as exc:
        return f"Update food failed: {exc}"


@app.route("/payment", methods=["GET", "POST"])
def payment_page():
    if "user" not in session:
        return redirect(url_for("login"))
    booking_id_arg = request.args.get("booking_id")
    if booking_id_arg:
        try:
            session["current_booking_id"] = int(booking_id_arg)
        except (TypeError, ValueError):
            pass
    if request.method == "POST":
        booking_id = request.form.get("booking_id") or session.get("current_booking_id")

        try:
            db = get_db_connection()
            if not booking_id:
                latest = db.bookings.find_one(
                    {"user_id": int(session["user"])},
                    {"id": 1},
                    sort=[("id", -1)],
                )
                if latest:
                    booking_id = latest.get("id")
                    session["current_booking_id"] = booking_id
            if not booking_id:
                return redirect(url_for("select_event"))

            event_date = request.form.get("date", "").strip()
            venue_name = request.form.get("venue_name", "").strip()
            venue_location = request.form.get("venue_location", "").strip()
            venue_capacity = request.form.get("venue_capacity", "").strip()
            decoration_theme = request.form.get("decoration_theme", "").strip()
            decoration_requirements = request.form.get("decoration_requirements", "").strip()
            guest_count = request.form.get("guest_count", "").strip()

            food_price = float(request.form.get("food_items") or 0)
            venue_price = float(request.form.get("venue") or 0)
            decoration_price = float(request.form.get("decoration") or 0)
            service_charge = float(request.form.get("service_charge") or 0)
            total_amount = round(
                food_price + venue_price + decoration_price + service_charge, 2
            )

            db.bookings.update_one(
                {"id": int(booking_id)},
                {
                    "$set": {
                        "event_date": event_date,
                        "venue_name": venue_name,
                        "venue_location": venue_location,
                        "venue_capacity": venue_capacity,
                        "decoration_theme": decoration_theme,
                        "decoration_requirements": decoration_requirements,
                        "guest_count": guest_count,
                        "food_price": food_price,
                        "venue_price": venue_price,
                        "decoration_price": decoration_price,
                        "service_charge": service_charge,
                        "total_amount": total_amount,
                        "payment_status": "Pending",
                    }
                },
            )
        except Exception as exc:
            return f"Payment summary save failed: {exc}"

    payment_status = None
    remaining_amount = None
    advance_amount = None
    booking_id = session.get("current_booking_id")
    if booking_id:
        try:
            db = get_db_connection()
            booking = db.bookings.find_one(
                {"id": int(booking_id)},
                {"_id": 0, "payment_status": 1, "remaining_amount": 1, "advance_amount": 1},
            ) or {}
            payment_status = booking.get("payment_status")
            remaining_amount = booking.get("remaining_amount")
            advance_amount = booking.get("advance_amount")
        except Exception:
            pass

    return render_template(
        "payment.html",
        payment_status=payment_status,
        remaining_amount=remaining_amount,
        advance_amount=advance_amount,
    )


@app.route("/demo_pdf")
def demo_pdf():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("demo_pdf.html")


@app.route("/forget_password")
def forget_password():
    return render_template("forget_password.html")


@app.route("/reset-password", methods=["POST"])
def reset_password():
    try:
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        if not email or not password:
            return jsonify({"message": "Email and password are required."}), 400

        db = get_db_connection()
        user = db.users.find_one({"email": email}, {"id": 1})
        if not user:
            return jsonify({"message": "Email not found."}), 404

        hashed = generate_password_hash(password)
        db.users.update_one({"id": user["id"]}, {"$set": {"password": hashed}})
        return jsonify({"message": "Password updated successfully."})
    except Exception as exc:
        return jsonify({"message": f"Password reset failed: {exc}"}), 500


@app.route("/success")
def success_page():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("success.html")


@app.route("/api/get_food_items")
def get_food_items_api():
    try:
        db = get_db_connection()
        foods = list(
            db.food_items.find(
                {}, {"_id": 0, "id": 1, "name": 1, "category": 1, "price": 1}
            ).sort([("category", 1), ("name", 1)])
        )
        return jsonify(foods)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/payments/razorpay-success", methods=["POST"])
def razorpay_success():
    if "user" not in session:
        return jsonify({"message": "Unauthorized"}), 401
    try:
        data = request.get_json(silent=True) or {}
        payment_id = (data.get("razorpay_payment_id") or "").strip()
        mode = (data.get("mode") or "advance").strip().lower()
        if not payment_id:
            return jsonify({"message": "Missing payment id."}), 400

        booking_id = session.get("current_booking_id")
        if not booking_id:
            return jsonify({"message": "Booking not found."}), 404

        db = get_db_connection()
        booking = db.bookings.find_one({"id": int(booking_id)}, {"_id": 0})
        if not booking:
            return jsonify({"message": "Booking not found."}), 404

        total_amount = booking.get("total_amount")
        if total_amount is None:
            food_total = sum(
                float(i.get("subtotal", 0.0))
                for i in db.booking_food.find({"booking_id": int(booking_id)}, {"subtotal": 1})
            )
            venue_price = float(booking.get("venue_price") or 0)
            decoration_price = float(booking.get("decoration_price") or 0)
            service_charge = booking.get("service_charge")
            if service_charge is None:
                service_charge = round((food_total + venue_price + decoration_price) * 0.10, 2)
            total_amount = round(food_total + venue_price + decoration_price + float(service_charge), 2)

        advance_amount = round(float(total_amount) * 0.30, 2)
        remaining_amount = round(float(total_amount) - advance_amount, 2)

        current_status = (booking.get("payment_status") or "Pending").lower()
        if mode == "advance" and current_status in {"advance paid", "fully paid"}:
            return jsonify({"message": "Advance payment already received."}), 400
        if mode == "remaining" and current_status not in {"advance paid", "partially paid"}:
            return jsonify({"message": "Please pay the advance amount first."}), 400

        if mode == "remaining":
            paid_amount = float(booking.get("remaining_amount") or remaining_amount)
            payment_type = "Full"
            payment_status = "Paid"
            db.bookings.update_one(
                {"id": int(booking_id)},
                {
                    "$set": {
                        "total_amount": float(total_amount),
                        "advance_amount": advance_amount,
                        "remaining_amount": 0,
                        "payment_status": "Fully Paid",
                        "transaction_id": payment_id,
                    }
                },
            )
            db.payments.insert_one(
                {
                    "booking_id": int(booking_id),
                    "total_amount": float(total_amount),
                    "paid_amount": float(paid_amount),
                    "remaining_amount": 0,
                    "payment_type": payment_type,
                    "status": payment_status,
                    "razorpay_payment_id": payment_id,
                    "created_at": datetime.utcnow(),
                }
            )
            return jsonify(
                {
                    "total_amount": float(total_amount),
                    "advance_amount": advance_amount,
                    "remaining_amount": 0,
                    "payment_status": "Fully Paid",
                    "transaction_id": payment_id,
                }
            )

        paid_amount = advance_amount
        payment_type = "Advance"
        payment_status = "Partially Paid"
        db.bookings.update_one(
            {"id": int(booking_id)},
            {
                "$set": {
                    "total_amount": float(total_amount),
                    "advance_amount": advance_amount,
                    "remaining_amount": remaining_amount,
                    "payment_status": "Advance Paid",
                    "transaction_id": payment_id,
                }
            },
        )
        db.payments.insert_one(
            {
                "booking_id": int(booking_id),
                "total_amount": float(total_amount),
                "paid_amount": float(paid_amount),
                "remaining_amount": float(remaining_amount),
                "payment_type": payment_type,
                "status": payment_status,
                "razorpay_payment_id": payment_id,
                "created_at": datetime.utcnow(),
            }
        )

        return jsonify(
            {
                "total_amount": float(total_amount),
                "advance_amount": advance_amount,
                "remaining_amount": remaining_amount,
                "payment_status": "Advance Paid",
                "transaction_id": payment_id,
            }
        )
    except Exception as exc:
        return jsonify({"message": f"Payment update failed: {exc}"}), 500


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(debug=True)
