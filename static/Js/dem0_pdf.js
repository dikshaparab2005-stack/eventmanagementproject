document.addEventListener("DOMContentLoaded", () => {
    const name = localStorage.getItem("userName") || "";
    const mobile = localStorage.getItem("userMobile") || "";
    const eventName = localStorage.getItem("eventName") || "";
    const venue = localStorage.getItem("venue") || "";
    const food = localStorage.getItem("foodPrice") || "0";
    const deco = localStorage.getItem("decPrice") || "0";
    const service = localStorage.getItem("serviceCharge") || "0";
    const total = localStorage.getItem("totalAmount") || "0";
    const advance = localStorage.getItem("advanceAmount") || "0";
    const remaining = localStorage.getItem("remainingAmount") || "0";
    let status = localStorage.getItem("paymentStatus") || "";
    let txn = localStorage.getItem("transactionId") || "";

    function normalizeNumber(value) {
        const num = Number(String(value).replace(/[^\d.]/g, "")) || 0;
        return num;
    }

    if (!status) {
        const remainingNum = normalizeNumber(remaining);
        const advanceNum = normalizeNumber(advance);
        if (remainingNum <= 0 && advanceNum > 0) {
            status = "Fully Paid";
        } else if (advanceNum > 0) {
            status = "Advance Paid";
        } else {
            status = "Pending";
        }
        localStorage.setItem("paymentStatus", status);
    }

    if (!txn || txn === "-") {
        txn = `TXN-${Date.now()}-${Math.floor(1000 + Math.random() * 9000)}`;
        localStorage.setItem("transactionId", txn);
    }

    const amountPaid = status === "Fully Paid"
        ? String(normalizeNumber(total))
        : String(normalizeNumber(advance));

    document.getElementById("rName").textContent = name;
    document.getElementById("rMobile").textContent = mobile;
    document.getElementById("rEvent").textContent = eventName;
    document.getElementById("rVenue").textContent = venue;
    document.getElementById("rFood").textContent = food;
    document.getElementById("rDec").textContent = deco;
    document.getElementById("rService").textContent = service;
    document.getElementById("rTotal").textContent = total;
    document.getElementById("rAdvance").textContent = advance;
    document.getElementById("rRemaining").textContent = remaining;
    document.getElementById("rTxn").textContent = txn;
    document.getElementById("rStatus").textContent = status;
    document.getElementById("rPaid").textContent = amountPaid;

    const downloadBtn = document.getElementById("downloadPdf");
    if (downloadBtn) {
        downloadBtn.addEventListener("click", () => {
            const { jsPDF } = window.jspdf;
            const pdf = new jsPDF();

            pdf.setFont("helvetica", "bold");
            pdf.setFontSize(16);
            pdf.text("EVENT BOOKING RECEIPT", 45, 18);

            pdf.setFont("helvetica", "normal");
            pdf.setFontSize(12);
            pdf.text(`Name: ${name}`, 15, 30);
            pdf.text(`Mobile: ${mobile}`, 15, 38);
            pdf.text(`Event: ${eventName}`, 15, 46);
            pdf.text(`Venue: ${venue}`, 15, 54);

            // Use ASCII-friendly currency label to avoid font issues in jsPDF.
            pdf.text(`Food Price: Rs. ${food}`, 15, 66);
            pdf.text(`Decoration Price: Rs. ${deco}`, 15, 74);
            pdf.text(`Service Charge: Rs. ${service}`, 15, 82);
            pdf.text(`Total Amount: Rs. ${total}`, 15, 90);
            pdf.text(`Advance Paid: Rs. ${advance}`, 15, 98);
            pdf.text(`Remaining Amount: Rs. ${remaining}`, 15, 106);
            pdf.text(`Transaction ID: ${txn}`, 15, 114);
            pdf.text(`Status: ${status}`, 15, 122);

            pdf.setFont("helvetica", "bold");
            pdf.text(`Amount Paid: Rs. ${amountPaid}`, 15, 134);

            pdf.save("Event_Receipt.pdf");
        });
    }
});
