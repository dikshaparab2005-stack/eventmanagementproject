document.addEventListener("DOMContentLoaded", () => {

    // Fetch data from localStorage (set from previous pages)
    const name = localStorage.getItem("userName");
    const mobile = localStorage.getItem("userMobile");
    const eventName = localStorage.getItem("eventName");
    const venue = localStorage.getItem("venue");
    const venuePrice = parseInt(localStorage.getItem("venuePrice")) || 0;
    const food = parseInt(localStorage.getItem("foodPrice")) || 0;
    const deco = parseInt(localStorage.getItem("decPrice")) || 0;

    const serviceCharge = Math.round((food + venuePrice + deco) * 0.10);
    const total = food + venuePrice + deco + serviceCharge;
    const advanceAmount = Math.round(total * 0.30);
    const remainingAmount = total - advanceAmount;

    // Display on page
    document.getElementById("userName").textContent = name;
    document.getElementById("userMobile").textContent = mobile;
    document.getElementById("eventName").textContent = eventName;
    document.getElementById("venue").textContent = venue ? `${venue} (₹${venuePrice})` : `₹${venuePrice}`;
    document.getElementById("foodPrice").textContent = food;
    document.getElementById("decPrice").textContent = deco;
    document.getElementById("serviceCharge").textContent = serviceCharge;
    document.getElementById("totalAmount").textContent = total;
    document.getElementById("advanceAmount").textContent = advanceAmount;
    document.getElementById("remainingAmount").textContent = remainingAmount;
    localStorage.setItem("serviceCharge", String(serviceCharge));
    localStorage.setItem("totalAmount", String(total));
    localStorage.setItem("decPrice", String(deco));
    localStorage.setItem("advanceAmount", String(advanceAmount));
    localStorage.setItem("remainingAmount", String(remainingAmount));



    const mode = new URLSearchParams(window.location.search).get("mode") || "advance";
    const container = document.querySelector(".container");
    const paymentStatus = (container?.dataset.paymentStatus || "").toLowerCase();

    function getAmountFromSpan() {
        const spanId = mode === "remaining" ? "remainingAmount" : "advanceAmount";
        const raw = document.getElementById(spanId)?.textContent || "0";
        const numeric = Number(String(raw).replace(/[^\d.]/g, "")) || 0;
        return Math.round(numeric);
    }

    const payingModeLabel = document.getElementById("payingMode");
    if (payingModeLabel) {
        payingModeLabel.textContent =
            mode === "remaining" ? "Paying Remaining Amount" : "Paying Advance Amount";
    }

    // Payment Button Action (Razorpay Test Mode)
    document.getElementById("payBtn").addEventListener("click", () => {
        if (mode === "remaining" && paymentStatus !== "advance paid") {
            alert("Please pay the advance amount first.");
            return;
        }
        const amount = getAmountFromSpan();
        if (!amount || amount <= 0) {
            alert("Invalid amount. Please refresh and try again.");
            return;
        }

        const options = {
            key: "rzp_test_SX1YRxJYHXMQuX", // Add your Razorpay TEST key here
            amount: amount * 100, // Razorpay expects amount in paise
            currency: "INR",
            name: "Event Management",
            description: mode === "remaining" ? "Remaining Payment" : "Advance Payment",
            prefill: {
                name: name || "",
                contact: mobile || "",
            },
            method: {
                upi: true,
                card: true,
                netbanking: true,
                wallet: true,
                emi: true,
                paylater: true
            },
            handler: async function (response) {
                try {
                    const res = await fetch("/api/payments/razorpay-success", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            razorpay_payment_id: response.razorpay_payment_id || "",
                            mode: mode
                        })
                    });
                    const data = await res.json();
                    if (!res.ok) {
                        alert(data.message || "Payment update failed.");
                        return;
                    }
                    if (data.total_amount !== undefined) {
                        localStorage.setItem("totalAmount", String(data.total_amount));
                    }
                    if (data.advance_amount !== undefined) {
                        localStorage.setItem("advanceAmount", String(data.advance_amount));
                    }
                    if (data.remaining_amount !== undefined) {
                        localStorage.setItem("remainingAmount", String(data.remaining_amount));
                    }
                    if (data.payment_status) {
                        localStorage.setItem("paymentStatus", data.payment_status);
                    }
                    if (data.transaction_id) {
                        localStorage.setItem("transactionId", data.transaction_id);
                    }
                    alert("Payment Successful");
                    window.location.href = "/demo_pdf";
                } catch (err) {
                    alert("Network error. Please try again.");
                }
            },
            theme: { color: "#1f2937" }
        };

        const rzp = new Razorpay(options);
        rzp.open();
    });

});
