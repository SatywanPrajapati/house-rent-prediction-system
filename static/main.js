const citySelect = document.getElementById("city");
const localitySelect = document.getElementById("locality");
const predictionForm = document.getElementById("predictionForm");
const predictButton = document.getElementById("predictBtn");
const backToHomeButton = document.getElementById("backToHomeBtn");
const formError = document.getElementById("formError");
const cityLocalityData = document.getElementById("city-locality-data");

let cityLocalityMap = {};

// LOAD CITY-LOCALITY DATA
if (cityLocalityData) {
    try {
        cityLocalityMap = JSON.parse(cityLocalityData.textContent);
    } catch (error) {
        console.error("Unable to parse city-locality data:", error);
    }
}


// ERROR HANDLING

function showError(message) {
    if (!formError) return;
    formError.textContent = message;
    formError.hidden = false;
}

function clearError() {
    if (!formError) return;
    formError.textContent = "";
    formError.hidden = true;
}


// HELPER

function getFieldValue(id) {
    const field = document.getElementById(id);
    return field ? field.value.trim() : "";
}


// LOCALITY POPULATION

function populateLocalities() {
    if (!citySelect || !localitySelect) return;

    const selectedCity = citySelect.value;
    localitySelect.innerHTML = "<option value=''>Select locality</option>";

    (cityLocalityMap[selectedCity] || []).forEach((locality) => {
        const option = document.createElement("option");
        option.value = locality;
        option.textContent = locality;
        localitySelect.appendChild(option);
    });
}


// BUTTON LOADING STATE

function setLoadingState(isLoading) {
    if (!predictButton) return;

    predictButton.textContent = isLoading ? "Predicting..." : "Predict Rent";
    predictButton.disabled = isLoading;
}


// MAIN PREDICTION FUNCTION

async function predictRent() {
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

    // VALIDATION
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
        Number.isNaN(payload.area) ||
        Number.isNaN(payload.beds) ||
        Number.isNaN(payload.bathrooms) ||
        Number.isNaN(payload.balconies) ||
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

        // API CALL

        const response = await fetch("/predict", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.error || "Prediction failed");
        }


        // PASS DATA TO RESULT PAGE

        const resultParams = new URLSearchParams({
            rent: String(data.rent),
            median_rent: String(data.median_rent),
            percent_diff: String(data.percent_diff),
            price_level: data.price_level,

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

// EVENTS

if (citySelect) {
    citySelect.addEventListener("change", populateLocalities);
}

if (predictionForm) {
    predictionForm.addEventListener("submit", (event) => {
        event.preventDefault();
        predictRent();
    });
}

if (backToHomeButton) {
    backToHomeButton.addEventListener("click", () => {
        window.location.href = "/";
    });
}