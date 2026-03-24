const citySelect = document.getElementById("city");
const localitySelect = document.getElementById("locality");
const predictionForm = document.getElementById("predictionForm");
const predictButton = document.getElementById("predictBtn");
const backToHomeButton = document.getElementById("backToHomeBtn");
const formError = document.getElementById("formError");
const cityLocalityData = document.getElementById("city-locality-data");
let cityLocalityMap = {};

// Read the city-locality mapping injected by Flask into the page.
if (cityLocalityData) {
    try {
        cityLocalityMap = JSON.parse(cityLocalityData.textContent);
    } catch (error) {
        console.error("Unable to parse city-locality data:", error);
    }
}

function showError(message) {
    // Show a friendly error below the form button.
    if (!formError) {
        return;
    }

    formError.textContent = message;
    formError.hidden = false;
}

function clearError() {
    // Clear the previous error before a new action starts.
    if (!formError) {
        return;
    }

    formError.textContent = "";
    formError.hidden = true;
}

function getFieldValue(id) {
    const field = document.getElementById(id);
    return field ? field.value.trim() : "";
}

function populateLocalities() {
    // Rebuild the locality dropdown based on the chosen city.
    if (!citySelect || !localitySelect) {
        return;
    }

    const selectedCity = citySelect.value;
    localitySelect.innerHTML = "<option value=''>Select locality</option>";

    (cityLocalityMap[selectedCity] || []).forEach((locality) => {
        const option = document.createElement("option");
        option.value = locality;
        option.textContent = locality;
        localitySelect.appendChild(option);
    });
}

function setLoadingState(isLoading) {
    // Update the button so the user knows prediction is running.
    if (!predictButton) {
        return;
    }

    predictButton.textContent = isLoading ? "Predicting..." : "Predict Rent";
    predictButton.disabled = isLoading;
}

async function predictRent() {
    // Validate the form, request a prediction, then open the result page.
    clearError();
    setLoadingState(true);

    const payload = {
        area: getFieldValue("area"),
        beds: getFieldValue("beds"),
        bathrooms: getFieldValue("bathrooms"),
        balconies: getFieldValue("balconies"),
        city: citySelect ? citySelect.value.trim() : "",
        locality: localitySelect ? localitySelect.value.trim() : "",
        furnishing: getFieldValue("furnishing"),
    };

    const hasEmptyField = Object.values(payload).some((value) => value === "");
    if (hasEmptyField) {
        showError("Please fill in all fields before predicting.");
        setLoadingState(false);
        return;
    }

    payload.area = Number(payload.area);
    payload.beds = Number(payload.beds);
    payload.bathrooms = Number(payload.bathrooms);
    payload.balconies = Number(payload.balconies);

    const hasInvalidNumber =
        payload.area <= 0 ||
        payload.beds <= 0 ||
        payload.bathrooms <= 0 ||
        payload.balconies < 0;

    if (hasInvalidNumber) {
        showError("Please enter valid numeric values before predicting.");
        setLoadingState(false);
        return;
    }

    try {
        // Send the property details to the backend prediction API.
        const response = await fetch("/predict", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        const data = await response.json();
        if (!response.ok || !data.success) {
            throw new Error(data.error || "Prediction failed");
        }

        // Pass the values to the result page through the query string.
        const resultParams = new URLSearchParams({
            prediction: String(data.prediction),
            area: String(payload.area),
            beds: String(payload.beds),
            bathrooms: String(payload.bathrooms),
            balconies: String(payload.balconies),
            city: data.city,
            locality: data.locality,
            furnishing: payload.furnishing,
        });

        window.location.href = `/result?${resultParams.toString()}`;
    } catch (error) {
        showError(error.message || "Prediction failed. Please try again.");
    } finally {
        setLoadingState(false);
    }
}

if (citySelect) {
    // Load locality options whenever the city changes.
    citySelect.addEventListener("change", populateLocalities);
}

if (predictionForm) {
    // Use the form submit event so the button and Enter key both work reliably.
    predictionForm.addEventListener("submit", (event) => {
        event.preventDefault();
        predictRent();
    });
}

if (backToHomeButton) {
    // Keep result-page navigation logic inside JavaScript instead of inline HTML.
    backToHomeButton.addEventListener("click", () => {
        window.location.href = "/";
    });
}
