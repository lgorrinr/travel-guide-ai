"use strict";

// =====================================================
// CONFIG
// =====================================================
// Update this URL if your Chalice backend runs elsewhere.
const serverUrl = "http://127.0.0.1:8000";

// =====================================================
// DYNAMIC / FALLBACK DATA
// =====================================================
// Filled from backend /languages route
let languages = [];

const teamMembers = [
  {
    name: "Lissette Gorrin Rodriguez",
    role: "Backend Developer",
  },
  {
    name: "Jason Lee",
    role: "AI Services",
  },
  {
    name: "Wardatul Keskin",
    role: "Frontend Developer",
  },
  {
    name: "Bin Liu",
    role: "Data and Cloud Services",
  },
  {
    name: "Samer Al Fattouhi Aljundi",
    role: "Testing and Architecture Integration",
  }
];

// =====================================================
// DOM ELEMENTS
// =====================================================
const imageInput = document.getElementById("imageInput");
const languageSelect = document.getElementById("languageSelect");
const translateBtn = document.getElementById("translateBtn");
const statusMessage = document.getElementById("statusMessage");
const imagePreview = document.getElementById("imagePreview");
const previewPlaceholder = document.getElementById("previewPlaceholder");
const extractedText = document.getElementById("extractedText");
const translatedText = document.getElementById("translatedText");
const targetLanguageDisplay = document.getElementById("targetLanguageDisplay");
const teamList = document.getElementById("teamList");

// =====================================================
// UI RENDERING
// =====================================================
function renderLanguageOptions() {
  languageSelect.innerHTML = "";

  const defaultOption = document.createElement("option");
  defaultOption.value = "";
  defaultOption.textContent = "-- Choose language --";
  languageSelect.appendChild(defaultOption);

  languages.forEach((lang) => {
    const option = document.createElement("option");
    option.value = lang.code;
    option.textContent = lang.name;
    languageSelect.appendChild(option);
  });
}

async function loadLanguages() {
  try {
    const response = await fetch(`${serverUrl}/languages`, {
      method: "GET",
      headers: {
        "Accept": "application/json"
      }
    });

    let result;
    try {
      result = await response.json();
    } catch (error) {
      throw new Error("Invalid response received from /languages.");
    }

    if (!response.ok || !result.success) {
      throw new Error(result.message || "Failed to load supported languages.");
    }

    const apiLanguages = result?.data?.languages;

    if (!Array.isArray(apiLanguages)) {
      throw new Error("Language list format is invalid.");
    }

    languages = apiLanguages
      .filter((lang) => lang.code && lang.name)
      .map((lang) => ({
        code: lang.code,
        name: lang.name
      }));

    renderLanguageOptions();
  } catch (error) {
    console.error("Language loading error:", error);

    // Minimal safe fallback in case backend fails
    languages = [
      { code: "en", name: "English" },
      { code: "es", name: "Spanish" },
      { code: "fr", name: "French" }
    ];

    renderLanguageOptions();
    setStatus("Could not load languages from backend. Fallback list is being used.", "warning");
  }
}

function getInitials(fullName) {
  if (!fullName || typeof fullName !== "string") {
    return "TM";
  }

  const parts = fullName.trim().split(/\s+/);
  const initials = parts
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join("");

  return initials || "TM";
}

function loadTeamMembers() {
  teamList.innerHTML = "";

  teamMembers.forEach((member) => {
    const wrapper = document.createElement("div");
    wrapper.className = "d-flex align-items-center gap-3 p-2 border rounded bg-white";

    const avatar = document.createElement("div");
    avatar.className =
      "rounded-circle bg-secondary text-white d-flex align-items-center justify-content-center flex-shrink-0";
    avatar.style.width = "48px";
    avatar.style.height = "48px";
    avatar.style.fontWeight = "600";
    avatar.textContent = member.initials;

    const info = document.createElement("div");

    const name = document.createElement("div");
    name.className = "fw-semibold";
    name.textContent = member.name;

    const role = document.createElement("div");
    role.className = "text-muted small";
    role.textContent = member.role;

    info.appendChild(name);
    info.appendChild(role);

    wrapper.appendChild(avatar);
    wrapper.appendChild(info);
    teamList.appendChild(wrapper);
  });
}

function setStatus(message, type = "danger") {
  statusMessage.className = `mt-3 alert alert-${type}`;
  statusMessage.textContent = message;
}

function clearStatus() {
  statusMessage.className = "mt-3";
  statusMessage.textContent = "";
}

function resetResults() {
  extractedText.textContent = "---";
  translatedText.textContent = "---";
  targetLanguageDisplay.textContent = "N/A";
}

function showPreview(file) {
  if (!file) {
    imagePreview.src = "";
    imagePreview.classList.add("d-none");
    previewPlaceholder.classList.remove("d-none");
    previewPlaceholder.textContent = "No image selected";
    return;
  }

  const imageUrl = URL.createObjectURL(file);
  imagePreview.src = imageUrl;
  imagePreview.classList.remove("d-none");
  previewPlaceholder.classList.add("d-none");
}

// =====================================================
// HELPERS
// =====================================================
function getLanguageName(code) {
  const match = languages.find((lang) => lang.code === code);
  return match ? match.name : code || "N/A";
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = () => {
      try {
        const result = reader.result;
        if (typeof result !== "string") {
          reject(new Error("Failed to read file as base64."));
          return;
        }

        // Remove the data URL prefix:
        // data:image/png;base64,xxxxx
        const base64String = result.split(",")[1];
        resolve(base64String);
      } catch (error) {
        reject(error);
      }
    };

    reader.onerror = () => {
      reject(new Error("Could not read the selected image file."));
    };

    reader.readAsDataURL(file);
  });
}

async function processImageRequest(base64Image, targetLanguage) {
  const response = await fetch(`${serverUrl}/process-image`, {
    method: "POST",
    headers: {
      "Accept": "application/json",
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      image: base64Image,
      target_language: targetLanguage
    })
  });

  let result;
  try {
    result = await response.json();
  } catch (error) {
    throw new Error("Server returned an invalid JSON response.");
  }

  if (!response.ok || !result.success) {
    const message = result && result.message
      ? result.message
      : `Request failed with status ${response.status}`;
    throw new Error(message);
  }

  return result;
}

// =====================================================
// MAIN ACTION
// =====================================================
async function handleTranslateImage() {
  clearStatus();
  resetResults();

  const file = imageInput.files[0];
  const selectedLanguage = languageSelect.value;

  if (!file) {
    setStatus("Please choose an image before translating.", "warning");
    return;
  }

  if (!selectedLanguage) {
    setStatus("Please select a target language.", "warning");
    return;
  }

  try {
    translateBtn.disabled = true;
    translateBtn.textContent = "Processing...";

    setStatus("Uploading image and processing translation...", "info");

    const base64Image = await fileToBase64(file);
    const result = await processImageRequest(base64Image, selectedLanguage);

    const data = result.data || {};

    extractedText.textContent = data.extracted_text || "No text detected.";
    translatedText.textContent = data.translated_text || "No translation available.";
    targetLanguageDisplay.textContent = getLanguageName(data.target_language || selectedLanguage);

    if (!data.extracted_text) {
      setStatus("No text was detected in the selected image.", "warning");
    } else {
      setStatus("Image translated successfully.", "success");
    }

  } catch (error) {
    setStatus(`Error: ${error.message}`, "danger");
  } finally {
    translateBtn.disabled = false;
    translateBtn.textContent = "Translate Image";
  }
}

// =====================================================
// EVENT LISTENERS
// =====================================================
imageInput.addEventListener("change", () => {
  const file = imageInput.files[0];
  showPreview(file);
  clearStatus();
  resetResults();
});

translateBtn.addEventListener("click", handleTranslateImage);

// =====================================================
// INITIALIZE PAGE
// =====================================================
window.addEventListener("DOMContentLoaded", async () => {
  loadTeamMembers();
  resetResults();
  clearStatus();
  await loadLanguages();
});