// Get containers
const startupList = document.getElementById("startupList");
const mainList = document.getElementById("mainList");
const dessertList = document.getElementById("dessertList");
const orderTableBody = document.getElementById("orderTableBody");
const grandTotalEl = document.getElementById("grandTotal");

let dishes = { Startup: [], Main: [], Dessert: [] };

// Fetch dishes from server (from your food_items table)
async function fetchDishes() {
    try {
        const res = await fetch("/api/get_food_items"); // new Flask route
        const data = await res.json();
        dishes = { Startup: [], Main: [], Dessert: [] };
        data.forEach(item => {
            dishes[item.category].push({ name: item.name, price: item.price });
        });
    } catch (err) {
        console.error("Failed to fetch food items:", err);
    }
}

// Add Dish row
function addDish(category){
    const listDiv = category === "Startup" ? startupList : category === "Main" ? mainList : dessertList;

    const dishDiv = document.createElement("div");
    dishDiv.className = "dish-item";

    const select = document.createElement("select");
    select.innerHTML = `<option value="" data-price="0">--Select Dish--</option>`;
    dishes[category].forEach(d => {
        select.innerHTML += `<option value="${d.name}" data-price="${d.price}">${d.name} - ₹${d.price}</option>`;
    });

    const qty = document.createElement("input");
    qty.type = "number";
    qty.min = 0;
    qty.placeholder = "0";

    dishDiv.appendChild(select);
    dishDiv.appendChild(qty);
    listDiv.appendChild(dishDiv);

    select.addEventListener("change", updateOrder);
    qty.addEventListener("input", updateOrder);
}

// Update Order Summary
function updateOrder(){
    let grandTotal = 0;
    let rows = [];

    ["startupList","mainList","dessertList"].forEach(listId => {
        const listDiv = document.getElementById(listId);
        const category = listId === "startupList" ? "Startup"
                     : listId === "mainList" ? "Main Course"
                     : "Dessert";

        listDiv.querySelectorAll(".dish-item").forEach(item => {
            const select = item.querySelector("select");
            const qtyInput = item.querySelector("input");

            const name = select.value;
            const price = Number(select.selectedOptions[0].dataset.price);
            const qty = Number(qtyInput.value) || 0;

            if(name && qty > 0){
                const subtotal = price * qty;
                grandTotal += subtotal;
                rows.push(`
                <tr>
                    <td>${category}</td>
                    <td>${name}</td>
                    <td>₹${price}</td>
                    <td>${qty}</td>
                    <td>₹${subtotal}</td>
                </tr>`);
            }
        });
    });

    orderTableBody.innerHTML = rows.length ? rows.join("") :
        '<tr><td colspan="5" style="text-align:center;">No items selected</td></tr>';
    grandTotalEl.textContent = grandTotal;
}

// Confirm Order
function confirmOrder(){
    alert("Order confirmed!\nTotal: ₹" + grandTotalEl.textContent);
}

// Next Page
function nextPage(){
    window.location.href = "/venue";
}

// Initial fetch
fetchDishes();
