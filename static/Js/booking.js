document.addEventListener("DOMContentLoaded", () => {

    let eventName = localStorage.getItem("eventName") || "Not Selected";
    let foodPrice = Number(localStorage.getItem("foodPrice")) || 0;
    let venuePrice = Number(localStorage.getItem("venuePrice")) || 0;
    let decorationPrice = Number(localStorage.getItem("decorationPrice")) || 0;
    let serviceCharge = Number(localStorage.getItem("serviceCharge")) || 500;
    let venueName = localStorage.getItem("venue") || "";
    let venueLocation = localStorage.getItem("venueLocation") || "";
    let venueCapacity = localStorage.getItem("venueCapacity") || "";
    let decorationTheme = localStorage.getItem("decorationTheme") || "";
    let decorationRequirements = localStorage.getItem("decoration_selection_demo") || "";

    const eventEl = document.getElementById("eventName");
    const foodEl = document.getElementById("foodPrice");
    const venueEl = document.getElementById("venuePrice");
    const decorationEl = document.getElementById("decorationPrice");
    const serviceEl = document.getElementById("serviceCharge");

    if (eventEl && !eventEl.value) eventEl.value = eventName;
    if (foodEl && !foodEl.value) foodEl.value = foodPrice;
    if (venueEl && !venueEl.value) venueEl.value = venuePrice;
    if (decorationEl && !decorationEl.value) decorationEl.value = decorationPrice;
    if (serviceEl && !serviceEl.value) serviceEl.value = serviceCharge;
    if (document.getElementById("venueName") && !document.getElementById("venueName").value) {
        document.getElementById("venueName").value = venueName;
    }
    if (document.getElementById("venueLocation") && !document.getElementById("venueLocation").value) {
        document.getElementById("venueLocation").value = venueLocation;
    }
    if (document.getElementById("venueCapacity") && !document.getElementById("venueCapacity").value) {
        document.getElementById("venueCapacity").value = venueCapacity;
    }
    if (document.getElementById("decorationTheme") && !document.getElementById("decorationTheme").value) {
        document.getElementById("decorationTheme").value = decorationTheme;
    }
    if (document.getElementById("decorationRequirements")) {
        if (!document.getElementById("decorationRequirements").value) {
            document.getElementById("decorationRequirements").value = decorationRequirements;
        }
    }

    const getVenuePriceFromPincode = (pincodeStr) => {
        if (!pincodeStr) return null;
        const match = String(pincodeStr).match(/\b\d{6}\b/);
        if (!match) return null;
        const userPincode = Number(match[0]);
        if (Number.isNaN(userPincode)) return null;
        const basePincode = 400058;
        const basePrice = 2000;
        const distance = Math.abs(userPincode - basePincode);
        const calculated = basePrice + (distance * 0.5);
        return Math.min(20000, Math.round(calculated));
    };

    const recalcTotal = () => {
        const currentFood = Number((foodEl && foodEl.value) || 0);
        const currentVenue = Number((venueEl && venueEl.value) || 0);
        const currentDecoration = Number((decorationEl && decorationEl.value) || 0);
        const currentService = Number((serviceEl && serviceEl.value) || 0);
        let total = currentFood + currentVenue + currentDecoration + currentService;
        const totalEl = document.getElementById("totalPrice");
        if (totalEl) totalEl.textContent = total;
        return total;
    };

    const storedPincode = localStorage.getItem("venuePincode") || "";
    const calculatedVenuePrice = getVenuePriceFromPincode(storedPincode);
    if (calculatedVenuePrice !== null && venueEl) {
        venueEl.value = calculatedVenuePrice;
        localStorage.setItem("venuePrice", String(calculatedVenuePrice));
    }

    let total = recalcTotal();

    const bookingForm = document.getElementById("bookingForm");
    bookingForm.addEventListener("submit", () => {
        localStorage.setItem("userName", document.getElementById("name").value || "");
        localStorage.setItem("userMobile", document.getElementById("mobile").value || "");
        localStorage.setItem("eventName", document.getElementById("eventName").value || "");
        localStorage.setItem("foodPrice", document.getElementById("foodPrice").value || "0");
        localStorage.setItem("venuePrice", document.getElementById("venuePrice").value || "0");
        localStorage.setItem("decorationPrice", document.getElementById("decorationPrice").value || "0");
        localStorage.setItem("decPrice", document.getElementById("decorationPrice").value || "0");
        localStorage.setItem("serviceCharge", document.getElementById("serviceCharge").value || "0");
        localStorage.setItem("totalAmount", String(total));
        if (document.getElementById("decorationRequirements")) {
            localStorage.setItem(
                "decoration_selection_demo",
                document.getElementById("decorationRequirements").value || ""
            );
        }
    });


    // UPDATE BOOKING
    document.getElementById("updateBtn").addEventListener("click", () => {
        window.location.href = "/update_booking";
    });

    // DELETE ORDER
    document.getElementById("deleteBtn").addEventListener("click", () => {
        if (confirm("Delete your order?")) {
            localStorage.clear();
            alert("Order Deleted.");
            location.reload();
        }
    });

});
