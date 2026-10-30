document.addEventListener("DOMContentLoaded", () => {
    const eventCards = document.querySelectorAll(".event-card");
    const eventInput = document.getElementById("event_name");
    const nextBtn = document.getElementById("nextBtn");
    const eventForm = document.getElementById("eventForm");

    const selectCard = (card) => {
        eventCards.forEach((c) => c.classList.remove("selected"));
        card.classList.add("selected");

        const selectedEvent = card.dataset.event || "";
        eventInput.value = selectedEvent;
        nextBtn.disabled = selectedEvent === "";

        localStorage.setItem("eventName", selectedEvent);
    };

    eventCards.forEach((card) => {
        card.addEventListener("click", (e) => {
            e.preventDefault();
            selectCard(card);
        });

        card.addEventListener("keydown", (e) => {
            if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                selectCard(card);
            }
        });
    });

    eventForm.addEventListener("submit", (e) => {
        if (!eventInput.value.trim()) {
            e.preventDefault();
            alert("Please select an event first.");
        }
    });
});

