document.addEventListener("DOMContentLoaded", () => {

    // Load Old Data
    const venueEl = document.getElementById("updateVenue");
    const eventDateEl = document.getElementById("updateEventDate");
    const guestEl = document.getElementById("updateguest_count");

    if (venueEl) venueEl.value = localStorage.getItem("venue") || "";
    if (eventDateEl) eventDateEl.value = localStorage.getItem("eventDate") || "";
    if (guestEl) guestEl.value = localStorage.getItem("guestCount") || "";

    // Save Updated Data
    const form = document.getElementById("updateBookingForm");
    if (form) {
        form.addEventListener("submit", () => {
            if (venueEl) localStorage.setItem("venue", venueEl.value);
            if (eventDateEl) localStorage.setItem("eventDate", eventDateEl.value);
            if (guestEl) localStorage.setItem("guestCount", guestEl.value);
        });
    }

});
