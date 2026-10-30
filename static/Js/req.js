 

// Get references to the form and the venue output container
const venueForm = document.getElementById('venue-form');
const venuesOutput = document.getElementById('venues-output');
const nextBtn = document.getElementById('nextBtn');

// Add an event listener for the form submission
venueForm.addEventListener('submit', function(event) {
    // Prevent the default form submission behavior, which would reload the page
    event.preventDefault();

    // Get the values from the form inputs
    const venueName = document.getElementById('venue-name').value;
    const venueLocation = document.getElementById('venue-location').value;
    const venueCapacity = document.getElementById('venue-capacity').value;

    // Create a new venue element to display the information
    const venueCard = document.createElement('div');
    venueCard.classList.add('venue-card');

    // Populate the new element with the venue data
    venueCard.innerHTML = `
        <h3>${venueName}</h3>
        <p><strong>Location:</strong> ${venueLocation}</p>
        <p><strong>Capacity:</strong> ${venueCapacity > 0 ? venueCapacity : 'N/A'}</p>
    `;

    // Append the new venue card to the output container
    venuesOutput.appendChild(venueCard);

    // Clear the form fields for the next entry
    venueForm.reset();
});
if (nextBtn) {
    nextBtn.addEventListener('click', () => {
        window.location.href = "/booking";
    });
}
